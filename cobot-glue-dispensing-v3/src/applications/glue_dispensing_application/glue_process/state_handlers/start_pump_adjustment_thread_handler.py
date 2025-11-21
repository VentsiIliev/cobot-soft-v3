import threading
from collections import namedtuple

from applications.glue_dispensing_application.glue_process.glue_dispensing_operation import ADJUST_PUMP_SPEED_WHILE_SPRAY, glue_dispensing_logger_context
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from applications.glue_dispensing_application.settings.enums import GlueSettingKey
from backend.system.utils.custom_logging import log_debug_message, log_error_message
from applications.glue_dispensing_application.glue_process.dynamicPumpSpeedAdjustment import \
    start_dynamic_pump_speed_adjustment_thread

PumpAdjustmentResult = namedtuple(
    "PumpAdjustmentResult",
    ["handled", "next_state", "pump_thread", "pump_ready_event", "next_path_index", "next_point_index", "next_path", "next_settings"]
)

def handle_start_pump_adjustment_thread(context):
    """Start pump adjustment thread if enabled and spray_on is True."""
    pump_thread = None
    pump_ready_event = threading.Event()

    if ADJUST_PUMP_SPEED_WHILE_SPRAY and context.spray_on:

        try:
            pump_thread = start_dynamic_pump_speed_adjustment_thread(
                service=context.service,
                robotService=context.robot_service,
                settings=context.current_settings,
                glueType=context.glue_type,
                path=context.current_path,
                reach_end_threshold=float(context.current_settings.get(GlueSettingKey.REACH_END_THRESHOLD.value, 1.0)),
                pump_ready_event=pump_ready_event,
                start_point_index=context.current_point_index,
            )
            log_debug_message(glue_dispensing_logger_context, message="Pump adjustment thread started.")
        except Exception as e:
            log_error_message(glue_dispensing_logger_context, message=f"Failed to start pump adjustment thread: {e}")

            result = PumpAdjustmentResult(False, GlueProcessState.ERROR, None, None, context.current_path_index, context.current_point_index, context.current_path, context.current_settings)
            update_context_from_pump_adjustment_result(context, result)
            return result.next_state

        # Wait for thread readiness
        if not pump_ready_event.wait(timeout=5.0):
            log_error_message(glue_dispensing_logger_context, message="Pump adjustment thread failed to initialize in time.")
            result = PumpAdjustmentResult(False, GlueProcessState.ERROR, None, None, context.current_path_index, context.current_point_index, context.current_path, context.current_settings)
            handle_start_pump_adjustment_thread(context, result)
            return result.next_state

        log_debug_message(glue_dispensing_logger_context, message="Pump adjustment thread ready.")

    # ✅ Return the result with thread references
    result = PumpAdjustmentResult(
        handled=True,
        next_state=GlueProcessState.SENDING_PATH_POINTS,
        pump_thread=pump_thread,
        pump_ready_event=pump_ready_event,
        next_path_index=context.current_path_index,
        next_point_index=context.current_point_index,
        next_path=context.current_path,
        next_settings=context.current_settings,
    )
    update_context_from_pump_adjustment_result(context, result)
    return result.next_state

def update_context_from_pump_adjustment_result(context, result: PumpAdjustmentResult):
    """Update context based on PumpAdjustmentResult."""
    context.current_path_index = result.next_path_index
    context.current_point_index = result.next_point_index
    context.current_path = result.next_path
    context.current_settings = result.next_settings
    # ✅ store thread + event in context
    context.pump_thread = result.pump_thread
    context.pump_ready_event = result.pump_ready_event
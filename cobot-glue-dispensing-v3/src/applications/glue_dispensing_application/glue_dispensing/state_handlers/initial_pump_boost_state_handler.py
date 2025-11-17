from collections import namedtuple
from applications.glue_dispensing_application.glue_dispensing.glue_dispensing_operation import glue_dispensing_logger_context
from applications.glue_dispensing_application.glue_dispensing.state_machine.GlueProcessState import GlueProcessState
from backend.system.utils.custom_logging import log_debug_message, log_error_message
# Shared result type for all state handlers
InitialPumpBoostResult = namedtuple(
    "HandlerResult",
    [
        "handled",          # Whether logic was completed successfully
        "resume",           # Whether this state should be resumed later
        "next_state",       # Next FSM state (STARTING_PUMP, ERROR, etc.)
        "next_path_index",  # Path index for continuation
        "next_point_index", # Point index for continuation
        "next_path",        # Path (can be same as context.current_path)
        "next_settings",    # Settings for continuation
        "motor_started"     # New motor state flag
    ]
)


def handle_pump_initial_boost(context):
    """
    Handles initial pump boost logic in a pure, return-based way.
    Does not mutate the context directly or trigger transitions.
    Returns a HandlerResult describing next actions.
    """

    path_index = context.current_path_index
    point_index = context.current_point_index
    spray_on = context.spray_on

    # --- Case 1: Spray mode active and motor not started ---
    if spray_on and not context.motor_started:
        result = context.pump_controller.pump_on(context.service,context.robot_service,context.glue_type,context.current_settings)

        if not result:
            log_error_message(
                glue_dispensing_logger_context,
                message=f"Motor start failed for path {path_index}, point_offset={point_index}"
            )

            return InitialPumpBoostResult(
                handled=False,
                resume=False,
                next_state=GlueProcessState.ERROR,
                next_path_index=path_index,
                next_point_index=point_index,
                next_path=context.current_path,
                next_settings=context.current_settings,
                motor_started=False
            )

        log_debug_message(
            glue_dispensing_logger_context,
            message=f"Motor started successfully for path {path_index}, point_offset={point_index}"
        )

        return InitialPumpBoostResult(
            handled=True,
            resume=False,
            next_state=GlueProcessState.STARTING_PUMP_ADJUSTMENT_THREAD,
            next_path_index=path_index,
            next_point_index=point_index,
            next_path=context.current_path,
            next_settings=context.current_settings,
            motor_started=True
        )

    # --- Case 2: Spray off or already started ---
    log_debug_message(
        glue_dispensing_logger_context,
        message=(
            f"Motor already active or spray off — skipping boost for "
            f"path {path_index}, point_offset={point_index}"
        )
    )

    return InitialPumpBoostResult(
        handled=True,
        resume=False,
        next_state=GlueProcessState.STARTING_PUMP_ADJUSTMENT_THREAD,
        next_path_index=path_index,
        next_point_index=point_index,
        next_path=context.current_path,
        next_settings=context.current_settings,
        motor_started=context.motor_started
    )

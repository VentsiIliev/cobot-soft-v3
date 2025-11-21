from collections import namedtuple


from applications.glue_dispensing_application.glue_process.glue_dispensing_operation import \
    glue_dispensing_logger_context
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from backend.system.settings.RobotConfigKey import RobotSettingKey
from backend.system.utils.custom_logging import log_debug_message, log_error_message
from core.services.robot_service.impl.base_robot_service import CancellationToken

HandlerResult = namedtuple(
    "HandlerResult",
    [
        "handled",
        "resume",
        "next_state",
        "next_path_index",
        "next_point_index",
        "next_path",
        "next_settings",
    ]
)

def handle_send_path_to_robot(context):
    """
    Sends path points to robot with immediate pause support using cancellation tokens.
    Returns a HandlerResult describing success/failure and next FSM state.
    """
    path = context.current_path
    settings = context.current_settings
    start_point_index = context.current_point_index
    path_index = context.current_path_index

    log_debug_message(
        glue_dispensing_logger_context,
        message=f"Sending {len(path)} points to robot with pause support (path index {path_index})"
    )

    # Create a cancellation token that monitors state machine
    cancellation_token = CancellationToken()
    
    for i, point in enumerate(path, start_point_index):
        # Check for pause/stop before each movement
        if context.state_machine.state == GlueProcessState.PAUSED:
            context.save_progress(path_index, i)
            log_debug_message(glue_dispensing_logger_context, message=f"Paused before point {i}")
            result = HandlerResult(True, True, GlueProcessState.PAUSED, path_index, i, path, settings)
            update_context_from_handler_result(context, result)
            return result.next_state

        if context.state_machine.state == GlueProcessState.STOPPED:
            log_debug_message(glue_dispensing_logger_context, message=f"Stopped before point {i}")
            result = HandlerResult(True, False, GlueProcessState.STOPPED, path_index, i, path, settings)
            update_context_from_handler_result(context, result)
            return result.next_state
        try:
            # Send move command (non-blocking)
            ret = context.robot_service.robot.move_liner(
                position=point,
                tool=context.robot_service.robot_config.robot_tool,
                user=context.robot_service.robot_config.robot_user,
                vel=settings.get(RobotSettingKey.VELOCITY.value, 10),
                acc=settings.get(RobotSettingKey.ACCELERATION.value, 30),
                blendR=1,
            )

            if ret != 0:
                log_error_message(glue_dispensing_logger_context, message=f"MoveL failed with code {ret} at point {i}")
                result = HandlerResult(False, False, GlueProcessState.ERROR, path_index, i, path, settings)
                update_context_from_handler_result(context, result)
                return result.next_state
        except Exception as e:
            import traceback
            traceback.print_exc()
            log_error_message(glue_dispensing_logger_context, message=f"Exception at point {i}: {e}")
            result = HandlerResult(False, False, GlueProcessState.ERROR, path_index, i, path, settings)
            update_context_from_handler_result(context, result)
            return result.next_state

    # All points completed successfully
    log_debug_message(glue_dispensing_logger_context, message="All points sent and reached. Path completed.")
    result = HandlerResult(True, False, GlueProcessState.WAIT_FOR_PATH_COMPLETION, path_index, 0, path, settings)
    update_context_from_handler_result(context, result)
    return result.next_state

def update_context_from_handler_result(context, result: HandlerResult):
    """Update context based on HandlerResult."""
    # Update context explicitly
    context.current_path_index = result.next_path_index
    context.current_point_index = result.next_point_index
    context.current_path = result.next_path
    context.current_settings = result.next_settings
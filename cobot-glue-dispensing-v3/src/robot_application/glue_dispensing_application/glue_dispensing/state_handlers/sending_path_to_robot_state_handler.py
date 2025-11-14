from collections import namedtuple
from modules.shared.shared.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey
from robot_application.glue_dispensing_application.glue_dispensing.glue_dispensing_operation import \
    glue_dispensing_logger_context
from robot_application.glue_dispensing_application.glue_dispensing.state_machine.GlueProcessState import GlueProcessState
from backend.system.utils.custom_logging import log_debug_message, log_error_message
from modules.robot.robotService.RobotService import CancellationToken

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
            return HandlerResult(True, True, GlueProcessState.PAUSED, path_index, i, path, settings)

        if context.state_machine.state == GlueProcessState.STOPPED:
            log_debug_message(glue_dispensing_logger_context, message=f"Stopped before point {i}")
            return HandlerResult(True, False, GlueProcessState.STOPPED, path_index, i, path, settings)

        try:
            # Send move command (non-blocking)
            ret = context.robot_service.robot.moveL(
                position=point,
                tool=context.robot_service.robot_config.robot_tool,
                user=context.robot_service.robot_config.robot_user,
                vel=settings.get(RobotSettingKey.VELOCITY.value, 10),
                acc=settings.get(RobotSettingKey.ACCELERATION.value, 30),
                blendR=1,
            )

            if ret != 0:
                log_error_message(glue_dispensing_logger_context, message=f"MoveL failed with code {ret} at point {i}")
                return HandlerResult(False, False, GlueProcessState.ERROR, path_index, i, path, settings)

        except Exception as e:
            import traceback
            traceback.print_exc()
            log_error_message(glue_dispensing_logger_context, message=f"Exception at point {i}: {e}")
            return HandlerResult(False, False, GlueProcessState.ERROR, path_index, i, path, settings)

    # All points completed successfully
    log_debug_message(glue_dispensing_logger_context, message="All points sent and reached. Path completed.")
    return HandlerResult(True, False, GlueProcessState.WAIT_FOR_PATH_COMPLETION, path_index, 0, path, settings)


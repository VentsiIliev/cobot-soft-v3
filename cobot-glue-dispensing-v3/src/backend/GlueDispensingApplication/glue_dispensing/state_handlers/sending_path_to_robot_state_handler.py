from collections import namedtuple
from modules.shared.shared.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey
from src.backend.GlueDispensingApplication.glue_dispensing.glue_dispensing_operation import glue_dispensing_logger_context
from src.backend.GlueDispensingApplication.robot.robotService.enums.RobotServiceState import RobotServiceState
from src.backend.GlueDispensingApplication.utils.custom_logging import log_debug_message, log_error_message

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
    Sends all path points to the robot.
    Returns a HandlerResult describing success/failure and next FSM state.
    """
    path = context.current_path
    settings = context.current_settings
    start_point_index = context.current_point_index
    path_index = context.current_path_index

    log_debug_message(
        glue_dispensing_logger_context,
        message=f"Sending all {len(path)} points to robot (path index {path_index})"
    )

    for i, point in enumerate(path, start_point_index):
        # Pause or stop handling
        if context.state_machine.state == RobotServiceState.PAUSED:
            context.save_progress(path_index, i)
            log_debug_message(glue_dispensing_logger_context, message=f"Paused before point {i}")
            return HandlerResult(True, True, RobotServiceState.PAUSED, path_index, i, path, settings)

        if context.state_machine.state == RobotServiceState.STOPPED:
            log_debug_message(glue_dispensing_logger_context, message=f"Stopped before point {i}")
            return HandlerResult(True, False, RobotServiceState.STOPPED, path_index, i, path, settings)

        try:
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
                return HandlerResult(False, False, RobotServiceState.ERROR, path_index, i, path, settings)

            log_debug_message(glue_dispensing_logger_context, message=f"Sent point {i} successfully")

        except Exception as e:
            import traceback
            traceback.print_exc()
            log_error_message(glue_dispensing_logger_context, message=f"Exception sending point {i}: {e}")
            return HandlerResult(False, False, RobotServiceState.ERROR, path_index, i, path, settings)

    # ✅ Don’t wait for anything here — just transition
    log_debug_message(glue_dispensing_logger_context, message="All points sent. Waiting for path completion...")
    return HandlerResult(True, False, RobotServiceState.WAIT_FOR_PATH_COMPLETION, path_index, 0, path, settings)


from backend.system.utils.custom_logging import log_info_message
from modules.robot.calibration.states.robot_calibration_states import RobotCalibrationStates

from modules.robot.calibration.states.state_result import StateResult


def handle_initializing_state(frame_provider,logger_context):
    handled = False
    if frame_provider is None:
        log_info_message(logger_context, "Waiting for camera to initialize...")
    else:
        handled= True
        log_info_message(logger_context, "System initialized ✅")


    if handled:
        return StateResult(success=True,message="Initialization complete",next_state=RobotCalibrationStates.AXIS_MAPPING)
    else:
        return StateResult(success=False,message="Waiting for camera to initialize...")
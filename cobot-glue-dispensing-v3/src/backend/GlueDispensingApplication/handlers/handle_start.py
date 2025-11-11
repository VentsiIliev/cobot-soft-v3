# Action functions

from src.backend.GlueDispensingApplication.GlueSprayApplicationState import GlueSprayApplicationState
from src.backend.GlueDispensingApplication.handlers.modes_handlers import contour_matching_mode_handler
from src.backend.GlueDispensingApplication.handlers.modes_handlers import direct_trace_mode_handler
from src.backend.GlueDispensingApplication.robot.robotService.enums.RobotServiceState import RobotServiceState


def start(application, contourMatching=True,nesting= False, debug=False):
    """
    Main method to start the robotic operation, either performing contour matching and nesting of workpieces
    or directly tracing contours. If contourMatching is False, only contour tracing is performed.
    """
    if contourMatching:
        print(f"Starting in Contour Matching Mode. Nesting: {nesting}, Debug: {debug}")
        result,message = contour_matching_mode_handler.handle_contour_matching_mode(application,nesting, debug)
    else:
        result,message = direct_trace_mode_handler.handle_direct_tracing_mode(application)

    # Only move to calibration position if robot service is not stopped/paused
    if application.robotService.state_machine.state not in [RobotServiceState.STOPPED, RobotServiceState.PAUSED,
                                                     RobotServiceState.ERROR]:
        application.move_to_spray_capture_position()
    application.state = GlueSprayApplicationState.IDLE
    return result, message






# Action functions

from applications.glue_dispensing_application.handlers.modes_handlers import \
    contour_matching_mode_handler, direct_trace_mode_handler

from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from core.base_robot_application import ApplicationState
from core.operation_state_management import OperationResult


def start(application, contourMatching=True,nesting= False, debug=False)->OperationResult:
    """
    Main method to start the robotic operation, either performing contour matching and nesting of workpieces
    or directly tracing contours. If contourMatching is False, only contour tracing is performed.
    """
    if contourMatching:
        print(f"Starting in Contour Matching Mode. Nesting: {nesting}, Debug: {debug}")
        result = contour_matching_mode_handler.handle_contour_matching_mode(application, nesting, debug)
    else:
        result = direct_trace_mode_handler.handle_direct_tracing_mode(application)

    # Only move to calibration position if robot service is not stopped/paused
    if application.glue_process_state_machine.state not in [GlueProcessState.STOPPED, GlueProcessState.PAUSED,GlueProcessState.ERROR]:
        application.move_to_spray_capture_position()
    application.state = ApplicationState.IDLE
    return result






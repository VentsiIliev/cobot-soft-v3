# Action functions

from robot_application.glue_dispensing_application.GlueDispensingApplicationState import GlueSprayApplicationState
from robot_application.glue_dispensing_application.handlers.modes_handlers import \
    contour_matching_mode_handler, direct_trace_mode_handler

from robot_application.glue_dispensing_application.glue_dispensing.state_machine.GlueProcessState import GlueProcessState


def start(application, contourMatching=True,nesting= False, debug=False):
    """
    Main method to start the robotic operation, either performing contour matching and nesting of workpieces
    or directly tracing contours. If contourMatching is False, only contour tracing is performed.
    """
    if contourMatching:
        print(f"Starting in Contour Matching Mode. Nesting: {nesting}, Debug: {debug}")
        result,message = contour_matching_mode_handler.handle_contour_matching_mode(application, nesting, debug)
    else:
        result,message = direct_trace_mode_handler.handle_direct_tracing_mode(application)

    # Only move to calibration position if robot service is not stopped/paused
    if application.glue_process_state_machine.state not in [GlueProcessState.STOPPED, GlueProcessState.PAUSED,GlueProcessState.ERROR]:
        application.move_to_spray_capture_position()
    application.state = GlueSprayApplicationState.IDLE
    return result, message






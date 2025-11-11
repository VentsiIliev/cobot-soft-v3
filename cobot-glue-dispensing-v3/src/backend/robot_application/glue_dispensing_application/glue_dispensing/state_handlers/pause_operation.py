from src.backend.robot_application.glue_dispensing_application.glue_dispensing.glue_dispensing_operation import glue_dispensing_logger_context
from src.backend.system.robot.robotService.enums.RobotServiceState import RobotServiceState
from src.backend.system.utils.custom_logging import log_debug_message


def pause_operation(glue_dispencing_operation,context):
    """Pause current operation or resume if already paused with debouncing"""

    current_state = glue_dispencing_operation.robot_service.state_machine.state

    if current_state == RobotServiceState.PAUSED:
        log_debug_message(glue_dispensing_logger_context, message=f"Already paused, resuming operation")
        return glue_dispencing_operation.resume_operation()

    log_debug_message(glue_dispensing_logger_context, message=f"Pausing operation")

    if glue_dispencing_operation.robot_service.state_machine.transition(RobotServiceState.PAUSED):
        context.paused_from_state = current_state
        
        # If there's an active pump thread, capture its progress before pausing
        if hasattr(context, 'pump_thread') and context.pump_thread and context.pump_thread.is_alive():
            log_debug_message(glue_dispensing_logger_context, 
                message=f"Pausing with active pump thread - current progress will be captured")
            # The pump thread will detect the PAUSED state and return its progress
            # The actual progress update happens when the thread terminates
        
        context.pump_controller.pump_off(context.service,context.robot_service,context.glue_type,context.current_settings)
        context.service.generatorOff()
        return True, "Operation paused"
    else:
        return False, "Cannot pause from current state"
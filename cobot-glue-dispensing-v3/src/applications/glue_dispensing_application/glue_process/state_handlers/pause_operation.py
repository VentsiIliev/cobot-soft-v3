from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from backend.system.utils.custom_logging import log_debug_message


def pause_operation(glue_dispensing_operation, context,logger_context):
    """Pause current operation or resume if already paused with debouncing"""

    current_state = context.state_machine.state

    if current_state == GlueProcessState.PAUSED:
        log_debug_message(logger_context, message=f"Already paused, resuming operation")
        return glue_dispensing_operation.resume()

    log_debug_message(logger_context, message=f"Pausing operation")

    if context.state_machine.transition(GlueProcessState.PAUSED):
        context.paused_from_state = current_state
        
        # If there's an active pump thread, capture its progress before pausing
        if hasattr(context, 'pump_thread') and context.pump_thread and context.pump_thread.is_alive():
            log_debug_message(logger_context,
                message=f"Pausing with active pump thread - current progress will be captured")
            # The pump thread will detect the PAUSED state and return its progress
            # The actual progress update happens when the thread terminates
        


        # Stop robot motion
        try:
            context.robot_service.stop_motion()

        except Exception as e:
            log_debug_message(logger_context,
                           message=f"Error stopping robot on pause: {e}")
        context.pump_controller.pump_off(context.service, context.robot_service, context.glue_type,
                                         context.current_settings)
        context.service.generatorOff()
        return True, "Operation paused"
    else:
        return False, "Cannot pause from current state"
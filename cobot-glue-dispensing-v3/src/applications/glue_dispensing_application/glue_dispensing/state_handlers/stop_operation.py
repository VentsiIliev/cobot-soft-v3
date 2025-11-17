from applications.glue_dispensing_application.glue_dispensing.glue_dispensing_operation import glue_dispensing_logger_context
from applications.glue_dispensing_application.glue_dispensing.state_machine.GlueProcessState import GlueProcessState
from backend.system.utils.custom_logging import log_debug_message


def stop_operation(glue_dispensing_operation,context):
    """Stop current operation"""
    if context.state_machine.transition(GlueProcessState.STOPPED):
        # Stop robot motion
        try:
            context.robot_service._stop_robot_motion()

        except Exception as e:
            log_debug_message(glue_dispensing_logger_context,
                           message=f"Error stopping robot on pause: {e}")
        context.pump_controller.pump_off(context.service, context.robot_service, context.glue_type,
                                         context.current_settings)
        context.service.generatorOff()
        context.pump_controller.pump_off(context.service,context.robot_service,context.glue_type,context.current_settings)
        context.service.generatorOff()
        log_debug_message(glue_dispensing_logger_context,
                          message=f"Operation stopped from current state: {context.state_machine.state}")

        context.robot_service.robotStateManager.trajectoryUpdate = False
        context.robot_service.message_publisher.publish_trajectory_stop_topic()
        return True, "Operation stopped"
    else:
        log_debug_message(glue_dispensing_logger_context,
                          message=f"Cannot stop from current state: {context.state_machine.state}")
        return False, "Cannot stop from current state"
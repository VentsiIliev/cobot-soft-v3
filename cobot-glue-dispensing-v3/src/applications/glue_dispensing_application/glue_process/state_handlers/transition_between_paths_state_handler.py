from applications.glue_dispensing_application.glue_process.glue_dispensing_operation import (
    glue_dispensing_logger_context,
    TURN_OFF_PUMP_BETWEEN_PATHS,
)
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState
from backend.system.utils.custom_logging import log_debug_message, log_error_message
from collections import namedtuple

TransitionResult = namedtuple(
    "TransitionResult",
    [
        "handled",           # whether transition was valid and completed
        "next_state",        # next state (STARTING or COMPLETED)
        "next_path_index",   # index for the next path
        "next_point_index",  # starting point index (usually 0)
    ]
)


def handle_transition_between_paths(context):
    """
    Handle TRANSITION_BETWEEN_PATHS state without mutating the context.
    Optionally turns off the pump and prepares for the next path.
    Returns a TransitionResult describing what to do next.
    """
    # Always notify trajectory break
    context.robot_service.message_publisher.publish_trajectory_break_topic()

    next_path_index = context.current_path_index + 1
    next_point_index = 0

    # ✅ Optional: Turn off motor between paths
    if TURN_OFF_PUMP_BETWEEN_PATHS:
        if context.motor_started and context.spray_on:
            try:
                log_debug_message(glue_dispensing_logger_context, message="Turning off motor between paths...")
                context.motor_controller.pump_off(context.service,context.robot_service,context.glue_type,context.current_settings)
                context.motor_started = False
                log_debug_message(glue_dispensing_logger_context, message="Motor stopped successfully.")
            except Exception as e:
                log_error_message(glue_dispensing_logger_context, message=f"Error stopping motor: {e}")

    # ✅ Decide next state
    if next_path_index >= len(context.paths):
        log_debug_message(glue_dispensing_logger_context, message="All paths completed.")
        next_state = GlueProcessState.COMPLETED
    else:
        log_debug_message(
            glue_dispensing_logger_context,
            message=f"Preparing to move to next path: {next_path_index}"
        )
        next_state = GlueProcessState.STARTING

    result = TransitionResult(
        handled=True,
        next_state=next_state,
        next_path_index=next_path_index,
        next_point_index=next_point_index,
    )
    update_context_from_transition_result(context, result)
    return result.next_state

def update_context_from_transition_result(context, result):
    """Update context based on TransitionResult."""
    context.current_path_index = result.next_path_index
    context.current_point_index = result.next_point_index

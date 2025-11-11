from collections import namedtuple
import time
from src.backend.GlueDispensingApplication.robot.robotService.enums.RobotServiceState import RobotServiceState
from src.backend.GlueDispensingApplication.utils.custom_logging import log_debug_message, log_error_message
from src.backend.GlueDispensingApplication.glue_dispensing.glue_dispensing_operation import glue_dispensing_logger_context

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

def handle_wait_for_path_completion(context):
    """
    Waits for the pump adjustment thread to finish.
    Since that thread runs until the robot reaches the last path point,
    this implicitly means waiting for robot motion completion.
    """
    path_index = context.current_path_index
    path = context.current_path
    settings = context.current_settings

    log_debug_message(glue_dispensing_logger_context, message=f"[WAIT_FOR_PATH_COMPLETION] Waiting for pump thread for path {path_index}...")

    pump_thread = getattr(context, "pump_thread", None)

    if pump_thread is None:
        log_error_message(glue_dispensing_logger_context, message="[WAIT] No pump thread found in context.")
        return HandlerResult(False, False, RobotServiceState.ERROR, path_index, 0, path, settings)

    try:
        # Wait indefinitely for the pump thread to finish.
        # You can add a soft timeout if you ever need to handle unexpected hangs.
        while pump_thread.is_alive():
            state = context.state_machine.state

            if state == RobotServiceState.PAUSED:
                log_debug_message(glue_dispensing_logger_context, message="[WAIT] Paused while waiting for pump thread - waiting for thread to finish and capture progress")
                # When paused, wait for pump thread to finish so we can capture its progress
                pump_thread.join(timeout=2.0)  # Give thread a moment to detect pause and finish
                
                # Get the progress from the pump thread result
                paused_point_index = context.current_point_index  # Default fallback
                if hasattr(pump_thread, 'result') and pump_thread.result is not None:
                    try:
                        success, progress_index = pump_thread.result[:2]
                        paused_point_index = progress_index
                        log_debug_message(glue_dispensing_logger_context, 
                            message=f"[WAIT] Captured pump thread progress on pause: {paused_point_index}")
                    except Exception as e:
                        log_debug_message(glue_dispensing_logger_context, 
                            message=f"[WAIT] Error capturing pump thread progress: {e}")
                
                return HandlerResult(True, True, RobotServiceState.PAUSED, path_index, paused_point_index, path, settings)

            if state == RobotServiceState.STOPPED:
                log_debug_message(glue_dispensing_logger_context, message="[WAIT] Stopped while waiting for pump thread")
                return HandlerResult(True, False, RobotServiceState.STOPPED, path_index, context.current_point_index, path, settings)

            time.sleep(0.1)

        # Get the pump thread result to capture final progress
        final_point_index = len(path) - 1  # Default to last point
        next_state = RobotServiceState.TRANSITION_BETWEEN_PATHS  # Default next state
        
        try:
            if hasattr(pump_thread, 'result') and pump_thread.result is not None:
                success, progress_index = pump_thread.result[:2]  # Unpack first two values
                if success:
                    final_point_index = progress_index
                    log_debug_message(glue_dispensing_logger_context, 
                        message=f"[WAIT] Pump thread completed successfully — final progress: {final_point_index}")
                else:
                    log_debug_message(glue_dispensing_logger_context, 
                        message=f"[WAIT] Pump thread completed with early termination — progress: {progress_index}")
                    final_point_index = progress_index
                    
                # If progress beyond current path, path is complete
                if final_point_index >= len(path):
                    log_debug_message(glue_dispensing_logger_context, 
                        message=f"[WAIT] Progress {final_point_index} beyond path length {len(path)}, path complete")
                    final_point_index = len(path) - 1  # Set to last valid point
                    next_state = RobotServiceState.TRANSITION_BETWEEN_PATHS
            else:
                log_debug_message(glue_dispensing_logger_context, message=f"[WAIT] Pump thread completed — path {path_index} done (no result captured).")
        except Exception as result_error:
            log_debug_message(glue_dispensing_logger_context, message=f"[WAIT] Could not get pump thread result: {result_error}")

    except Exception as e:
        log_error_message(glue_dispensing_logger_context, message=f"[WAIT] Error waiting for pump thread: {e}")
        return HandlerResult(False, False, RobotServiceState.ERROR, path_index, context.current_point_index, path, settings)
    finally:
        context.pump_thread = None

    # ✅ The thread finished — robot reached last point.
    return HandlerResult(
        handled=True,
        resume=False,
        next_state=next_state,
        next_path_index=path_index,
        next_point_index=final_point_index,  # Use actual final progress from pump thread
        next_path=path,
        next_settings=settings,
    )

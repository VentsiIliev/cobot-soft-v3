from collections import namedtuple

from applications.glue_dispensing_application.settings.enums import GlueSettingKey
from modules.robot.robotService.RobotService import CancellationToken

from applications.glue_dispensing_application.glue_dispensing.state_machine.GlueProcessState import GlueProcessState

MovingResult = namedtuple(
    "MovingResult",
    ["handled", "resume", "next_state", "next_path_index", "next_point_index", "next_path", "next_settings"]
)

def handle_moving_to_first_point_state(context, resume):
    """
    Handle MOVING_TO_FIRST_POINT state (pure / non-mutating).
    Returns MovingResult describing what to do next.
    """

    # --- Robot trajectory updates disabled at this step ---
    trajectory_update = False  # kept symbolic (can be applied by caller)

    # Ensure settings exist
    if context.current_settings is None:
        return MovingResult(
            handled=False,
            resume=False,
            next_state=GlueProcessState.ERROR,
            next_path_index=context.current_path_index,
            next_point_index=context.current_point_index,
            next_path=context.current_path,
            next_settings=context.current_settings,
        )

    # --- Wait for robot to reach first point ---
    reach_start_threshold = float(
        context.current_settings.get(GlueSettingKey.REACH_START_THRESHOLD.value, 1.0)
    )

    cancellation_token = CancellationToken()

    # Monitor state machine and cancel if needed
    def monitor_state_machine():
        import threading
        import time
        def check_state():
            while not cancellation_token.is_cancelled():
                if context.state_machine.state in [GlueProcessState.PAUSED, GlueProcessState.STOPPED]:
                    reason = f"State changed to {context.state_machine.state.value}"
                    cancellation_token.cancel(reason)
                    break
                time.sleep(0.01)  # Check every 10ms

        monitor_thread = threading.Thread(target=check_state, daemon=True)
        monitor_thread.start()

    monitor_state_machine()
    reached = context.robot_service._waitForRobotToReachPosition(
        context.current_path[0],
        reach_start_threshold,
        delay=0,
        timeout=30,
        cancellation_token=cancellation_token
    )

    # --- Check if movement was cancelled ---
    if cancellation_token.is_cancelled():
        reason = cancellation_token.get_cancellation_reason()
        if "PAUSED" in reason:
            # Determine which point to resume from later
            point_to_save = context.current_point_index if resume else 0
            return MovingResult(
                handled=True,
                resume=True,
                next_state=GlueProcessState.PAUSED,
                next_path_index=context.current_path_index,
                next_point_index=point_to_save,
                next_path=context.current_path,
                next_settings=context.current_settings,
            )
        else:  # STOPPED
            return MovingResult(
                handled=True,
                resume=False,
                next_state=GlueProcessState.STOPPED,
                next_path_index=context.current_path_index,
                next_point_index=context.current_point_index,
                next_path=context.current_path,
                next_settings=context.current_settings,
            )

    # --- Handle robot reaching / not reaching target ---
    if reached:
        # ✅ Robot reached the start point — proceed to EXECUTING_PATH
        return MovingResult(
            handled=True,
            resume=resume,
            next_state=GlueProcessState.EXECUTING_PATH,
            next_path_index=context.current_path_index,
            next_point_index=0,
            next_path=context.current_path,
            next_settings=context.current_settings,
        )

    # --- Timeout or other failure case ---
    return MovingResult(
        handled=False,
        resume=False,
        next_state=GlueProcessState.ERROR,
        next_path_index=context.current_path_index,
        next_point_index=context.current_point_index,
        next_path=context.current_path,
        next_settings=context.current_settings,
    )

from collections import namedtuple
from modules.shared.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from src.backend.GlueDispensingApplication.robot.robotService.enums.RobotServiceState import RobotServiceState

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
            next_state=RobotServiceState.ERROR,
            next_path_index=context.current_path_index,
            next_point_index=context.current_point_index,
            next_path=context.current_path,
            next_settings=context.current_settings,
        )

    # --- Wait for robot to reach first point ---
    reach_start_threshold = float(
        context.current_settings.get(GlueSettingKey.REACH_START_THRESHOLD.value, 1.0)
    )

    reached = context.robot_service._waitForRobotToReachPosition(
        context.current_path[0],
        reach_start_threshold,
        delay=0,
        timeout=30
    )

    # --- Handle robot reaching / not reaching target ---
    if reached:
        # ✅ Robot reached the start point — proceed to EXECUTING_PATH
        return MovingResult(
            handled=True,
            resume=resume,
            next_state=RobotServiceState.EXECUTING_PATH,
            next_path_index=context.current_path_index,
            next_point_index=0,
            next_path=context.current_path,
            next_settings=context.current_settings,
        )

    # --- Interrupted (pause / stop) case ---
    if context.state_machine.state == RobotServiceState.PAUSED:
        # Determine which point to resume from later
        point_to_save = context.current_point_index if resume else 0

        return MovingResult(
            handled=True,
            resume=True,
            next_state=RobotServiceState.PAUSED,
            next_path_index=context.current_path_index,
            next_point_index=point_to_save,
            next_path=context.current_path,
            next_settings=context.current_settings,
        )

    # --- Timeout or other failure case ---
    return MovingResult(
        handled=False,
        resume=False,
        next_state=RobotServiceState.ERROR,
        next_path_index=context.current_path_index,
        next_point_index=context.current_point_index,
        next_path=context.current_path,
        next_settings=context.current_settings,
    )

import time

from robot_application.glue_dispensing_application.glue_dispensing.glue_dispensing_operation import glue_dispensing_logger_context
from robot_application.glue_dispensing_application.glue_dispensing.state_machine.GlueProcessState import GlueProcessState
from backend.system.utils.custom_logging import log_debug_message
from collections import namedtuple

MoveResult = namedtuple("MoveResult", ["success", "next_state", "generator_should_start"])
ResumeResult = namedtuple(
    "ResumeResult",
    [
        "handled",               # whether resume logic handled the state
        "resume_flag",           # still resuming after this step?
        "next_state",            # what the next robot state should be
        "next_path_index",       # next path index
        "next_point_index",      # next point index
        "next_path",             # optional updated path slice
        "clear_paused_state",    # whether paused_from_state should be cleared
    ]
)
HandlerResult = namedtuple(
    "HandlerResult",
    ["handled", "resume", "next_path_index", "next_point_index", "next_state", "next_path", "next_settings"]
)


def move_to_first_point(context,path):
    """
    Try to move the robot to the first point of the current path.
    Does not mutate context; instead, returns a MoveResult describing outcome.
    """
    max_attempts = 5
    robot = context.robot_service.robot
    cfg = context.robot_service.robot_config

    for attempt in range(max_attempts):
        try:
            ret = robot.moveCart(
                position=path[0],
                tool=cfg.robot_tool,
                user=cfg.robot_user,
                vel=cfg.global_motion_settings.global_velocity,
                acc=cfg.global_motion_settings.global_acceleration,
            )

            log_debug_message(
                glue_dispensing_logger_context,
                message=f"move_to_first_point: robot.moveCart returned {ret} for attempt {attempt+1}"
            )

            # If movement failed
            if ret != 0:
                if attempt == max_attempts - 1:
                    # Max retries exhausted → signal error
                    return MoveResult(False, GlueProcessState.ERROR, False)
                time.sleep(0.2)
                continue

            # If movement succeeded
            # Determine whether generator should be started
            generator_needed = bool(context.spray_on and not context.generator_started and not context.service.generatorState())

            return MoveResult(True, GlueProcessState.MOVING_TO_FIRST_POINT, generator_needed)

        except Exception as e:
            import traceback
            traceback.print_exc()

            if "Request-sent" in str(e):
                time.sleep(0.2)
                continue
            else:
                # Unexpected failure
                return MoveResult(False, GlueProcessState.ERROR, False)

    # If we somehow exit the loop without success
    return MoveResult(False, GlueProcessState.ERROR, False)

def _handle_resume_case(context):
    """
    Handle a resume case without mutating the context.
    Returns a ResumeResult describing the next intended state.
    """
    print(f"RESUME: from {context.paused_from_state} (path {context.current_path_index}, point {context.current_point_index})")

    # 1️⃣ Out-of-bounds → completed
    if context.current_path_index >= len(context.paths):
        return ResumeResult(
            handled=True,
            resume_flag=False,
            next_state=GlueProcessState.COMPLETED,
            next_path_index=context.current_path_index,
            next_point_index=context.current_point_index,
            next_path=None,
            clear_paused_state=True
        )

    path, settings = context.paths[context.current_path_index]

    # 2️⃣ Handle by paused_from_state
    if context.paused_from_state == GlueProcessState.TRANSITION_BETWEEN_PATHS:
        print("RESUME: Paused between paths → move to next path's first point.")
        move_result = move_to_first_point(context, path)

        return ResumeResult(
            handled=move_result.success,
            resume_flag=True,
            next_state=move_result.next_state,
            next_path_index=context.current_path_index,
            next_point_index=context.current_point_index,
            next_path=path,
            clear_paused_state=True
        )

    elif context.paused_from_state == GlueProcessState.EXECUTING_PATH:
        if context.current_point_index >= len(path):
            print("RESUME: Path finished, move to next path.")
            return ResumeResult(
                handled=True,
                resume_flag=False,
                next_state=GlueProcessState.MOVING_TO_FIRST_POINT,
                next_path_index=context.current_path_index + 1,
                next_point_index=0,
                next_path=None,
                clear_paused_state=True
            )

        # Continue from current point - robot should resume moving towards current_point_index
        # Don't slice the path, include the current point since robot hasn't reached it yet
        new_path = path[context.current_point_index:]
        print(f"RESUME: Continuing path {context.current_path_index} from point {context.current_point_index}/{len(path)} (moving towards point {context.current_point_index})")

        return ResumeResult(
            handled=True,
            resume_flag=True,
            next_state=GlueProcessState.EXECUTING_PATH,
            next_path_index=context.current_path_index,
            next_point_index=context.current_point_index,  # Keep same target point
            next_path=new_path,
            clear_paused_state=True
        )

    elif context.paused_from_state == GlueProcessState.WAIT_FOR_PATH_COMPLETION:
        print(f"RESUME: Paused during path completion - continuing from current position towards point {context.current_point_index}")
        # Robot was paused while executing path, resume from current progress point
        if context.current_point_index >= len(path):
            print("RESUME: Path already completed, move to next path.")
            return ResumeResult(
                handled=True,
                resume_flag=False,
                next_state=GlueProcessState.MOVING_TO_FIRST_POINT,
                next_path_index=context.current_path_index + 1,
                next_point_index=0,
                next_path=None,
                clear_paused_state=True
            )
        
        # Resume from the point robot was moving towards when paused - skip any movement commands
        new_path = path[context.current_point_index:]
        print(f"RESUME: Skipping move commands, directly executing from point {context.current_point_index}/{len(path)} - {len(new_path)} points remaining")
        
        return ResumeResult(
            handled=True,
            resume_flag=True,
            next_state=GlueProcessState.EXECUTING_PATH,  # Skip MOVING_TO_FIRST_POINT
            next_path_index=context.current_path_index,
            next_point_index=context.current_point_index,
            next_path=new_path,
            clear_paused_state=True
        )

    elif context.paused_from_state == GlueProcessState.SENDING_PATH_POINTS:
        print(f"RESUME: Paused during sending path points - resuming from point {context.current_point_index}")
        # Robot was paused while sending points to robot controller
        # Resume from the same point index since robot hasn't completed moving to it
        new_path = path[context.current_point_index:]
        print(f"RESUME: Continuing to send from point {context.current_point_index}/{len(path)} - {len(new_path)} points remaining")
        
        return ResumeResult(
            handled=True,
            resume_flag=True,
            next_state=GlueProcessState.EXECUTING_PATH,
            next_path_index=context.current_path_index,
            next_point_index=context.current_point_index,
            next_path=new_path,
            clear_paused_state=True
        )

    elif context.paused_from_state == GlueProcessState.MOVING_TO_FIRST_POINT:
        print("RESUME: Re-attempting move to first point.")
        move_result = move_to_first_point(context, path)

        return ResumeResult(
            handled=move_result.success,
            resume_flag=True,
            next_state=move_result.next_state,
            next_path_index=context.current_path_index,
            next_point_index=context.current_point_index,
            next_path=path,
            clear_paused_state=True
        )

    # 3️⃣ Fallback — unknown paused_from_state
    print("Unknown paused_from_state — falling back to normal start.")
    return ResumeResult(
        handled=False,
        resume_flag=False,
        next_state=None,
        next_path_index=context.current_path_index,
        next_point_index=context.current_point_index,
        next_path=None,
        clear_paused_state=False
    )


def handle_starting_state(context):
    """
    Handle STARTING state without mutating the context.
    Returns a HandlerResult with all next state information.
    """
    # Always disable trajectory update at the start
    trajectory_update = False  # just for clarity (caller may apply to robotStateManager)

    resume = False

    # --- Resume flow ---
    if context.is_resuming and context.has_valid_context():
        resume_result = _handle_resume_case(context)
        if resume_result.handled:
            # Simply forward the resume result into our unified handler result
            return HandlerResult(
                handled=True,
                resume=resume_result.resume_flag,
                next_path_index=resume_result.next_path_index,
                next_point_index=resume_result.next_point_index,
                next_state=resume_result.next_state,
                next_path=resume_result.next_path,
                next_settings=context.current_settings,  # unchanged
            )
        else:
            resume = False  # fallback to normal start

    # --- Normal start ---
    if context.current_path_index >= len(context.paths):
        # Out of bounds — mark as completed
        return HandlerResult(
            handled=True,
            resume=False,
            next_path_index=context.current_path_index,
            next_point_index=context.current_point_index,
            next_state=GlueProcessState.COMPLETED,
            next_path=None,
            next_settings=context.current_settings,
        )

    # Fetch current path & settings
    path, settings = context.paths[context.current_path_index]

    # Determine if resuming within a path
    if resume and 0 < context.current_point_index < len(path):
        current_path = path[context.current_point_index:]
        log_debug_message(
            glue_dispensing_logger_context,
            message=f"RESUME: Continuing path {context.current_path_index} from point {context.current_point_index}/{len(path)} - skipping move_to_first_point",
        )
        
        # When resuming within a path, skip move_to_first_point and go directly to execution
        # Robot should continue from current position towards the next point in sequence
        return HandlerResult(
            handled=True,
            resume=True,
            next_path_index=context.current_path_index,
            next_point_index=context.current_point_index,
            next_state=GlueProcessState.EXECUTING_PATH,
            next_path=current_path,
            next_settings=settings,
        )
    else:
        current_path = path
        log_debug_message(
            glue_dispensing_logger_context,
            message=f"NEW START: Starting path {context.current_path_index} with {len(path)} points",
        )

    # If path empty → skip to next
    if not current_path:
        log_debug_message(
            glue_dispensing_logger_context,
            message=f"Empty path at index {context.current_path_index}, skipping.",
        )
        return HandlerResult(
            handled=True,
            resume=False,
            next_path_index=context.current_path_index + 1,
            next_point_index=0,
            next_state=GlueProcessState.STARTING,  # still starting next path
            next_path=None,
            next_settings=None,
        )

    # Only attempt to move to first point for new starts (not resumes)
    move_result = move_to_first_point(context,current_path)
    next_state = move_result.next_state if move_result.success else GlueProcessState.ERROR

    # Return a complete immutable result
    return HandlerResult(
        handled=move_result.success,
        resume=resume,
        next_path_index=context.current_path_index,
        next_point_index=context.current_point_index,
        next_state=next_state,
        next_path=current_path,
        next_settings=settings,
    )


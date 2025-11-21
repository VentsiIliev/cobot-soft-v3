from dataclasses import dataclass


@dataclass
class Context:
    pass


class ExecutionContext(Context):
    """Holds execution state for pause/resume functionality"""

    def __init__(self):
        self.reset()
        self.paused_from_state = None

    def reset(self):
        """Reset execution context"""
        self.paths = None
        self.spray_on = False
        self.service = None
        self.robot_service = None
        self.state_machine = None
        self.glue_type = None
        self.current_path_index = 0
        self.current_point_index = 0
        self.target_point_index = 0  # Point robot is moving towards (for resume)
        self.is_resuming = False
        self.generator_started = False
        self.generator_to_glue_delay = 0
        self.motor_started = False
        self.current_settings = None
        self.current_path = None
        self.paused_from_state = None
        self.pump_controller = None

        # ✅ Add these for pump adjustment
        self.pump_thread = None
        self.pump_ready_event = None

    def save_progress(self, path_index: int, point_index: int):
        """Save current execution progress"""
        self.current_path_index = path_index
        self.current_point_index = point_index
        print(f"📍 PAUSE: Saved progress - path={path_index}, point={point_index}")
        print(f"📍 PAUSE: Robot was paused at point {point_index} in path {path_index}")

    def has_valid_context(self) -> bool:
        """Check if context has valid execution data"""
        return self.paths is not None and len(self.paths) > 0

    def to_debug_dict(self) -> dict:
        """
        Serialize context to dictionary for debug output.
        Returns a human-readable representation of current execution state.
        """
        return {
            # Path execution state
            "current_path_index": self.current_path_index,
            "current_point_index": self.current_point_index,
            "target_point_index": self.target_point_index,
            "total_paths": len(self.paths) if self.paths else 0,
            "current_path_length": len(self.current_path) if self.current_path is not None else 0,

            # Execution flags
            "spray_on": self.spray_on,
            "motor_started": self.motor_started,
            "generator_started": self.generator_started,
            "is_resuming": self.is_resuming,

            # State information
            "current_state": str(self.state_machine.state) if self.state_machine else "None",
            "paused_from_state": str(self.paused_from_state) if self.paused_from_state else "None",

            # Thread state
            "pump_thread_alive": self.pump_thread.is_alive() if self.pump_thread else False,
            "pump_ready_event_set": self.pump_ready_event.is_set() if self.pump_ready_event else False,

            # Settings
            "has_current_settings": self.current_settings is not None,
            "settings_keys": list(self.current_settings.keys()) if self.current_settings else [],

            # Service availability
            "has_glue_service": self.service is not None,
            "has_robot_service": self.robot_service is not None,
            "has_pump_controller": self.pump_controller is not None,

            # Glue configuration
            "glue_type": self.glue_type,
            "generator_to_glue_delay": self.generator_to_glue_delay,
        }

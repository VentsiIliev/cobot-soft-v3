import enum

class GlueSprayApplicationState(enum.Enum):
    INITIALIZING = "initializing"
    IDLE = "idle"
    NESTING = "nesting"
    SPRAYING = "spraying"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    STARTED = "started"
from enum import Enum, auto


class RobotCalibrationStates(Enum):
    INITIALIZING = auto()
    AXIS_MAPPING = auto()
    LOOKING_FOR_CHESSBOARD = auto()
    CHESSBOARD_FOUND = auto()
    ALIGN_TO_CHESSBOARD_CENTER = auto()
    LOOKING_FOR_ARUCO_MARKERS = auto()
    ALL_ARUCO_FOUND = auto()
    COMPUTE_OFFSETS = auto()
    ALIGN_ROBOT = auto()
    ITERATE_ALIGNMENT = auto()
    DONE = auto()
    ERROR = auto()
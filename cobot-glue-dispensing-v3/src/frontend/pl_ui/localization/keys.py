"""
Translation keys for the application.
Provides a centralized, organized way to reference translation strings.
"""
from modules.shared.localization.enums.Message import Message


class TranslationKeys:
    """
    Centralized translation keys organized by functionality.
    Maps to the Message enum from the shared but provides better organization.
    """
    
    # Authentication & Login
    class Auth:
        LOGIN = Message.LOGIN
        PASSWORD = Message.PASSWORD
        ID = Message.ID
        USER_NOT_FOUND = Message.USER_NOT_FOUND
        INCORRECT_PASSWORD = Message.INCORRECT_PASSWORD
        INVALID_LOGIN_ID = Message.INVALID_LOGIN_ID
        ENTER_ID_AND_PASSWORD = Message.ENTER_ID_AND_PASSWORD
        SCAN_QR_TO_LOGIN = Message.SCAN_QR_TO_LOGIN
    
    # User Management & Session
    class User:
        FILTER_USERS = Message.FILTER_USERS
        FILTER_BY = Message.FILTER_BY
        ENTER_FILTER_VALUE = Message.ENTER_FILTER_VALUE
        APPLY_FILTERS = Message.APPLY_FILTERS
        CLEAR_FILTERS = Message.CLEAR_FILTERS
        ID = Message.ID
        USER = Message.USER
        FIRST_NAME = Message.FIRST_NAME
        LAST_NAME = Message.LAST_NAME
        ROLE = Message.ROLE
        LOGIN_TIME = Message.LOGIN_TIME
        SESSION_DURATION = Message.SESSION_DURATION
        ADD_USER = Message.ADD_USER
        EDIT_USER = Message.EDIT_USER
        DELETE_USER = Message.DELETE_USER
        ADD_NEW_USER = Message.ADD_NEW_USER
        ERROR_LOADING_USERS = Message.ERROR_LOADING_USERS
        GENERATE_QR = Message.GENERATE_QR
        EMAIL = Message.EMAIL
    
    # Dashboard & Control
    class Dashboard:
        START = Message.START
        STOP = Message.STOP
        PAUSE = Message.PAUSE
        CLEAN = Message.CLEAN
        READY = Message.READY
        GLUE = Message.GLUE
    
    # Navigation & UI
    class Navigation:
        WORK = Message.WORK
        SERVICE = Message.SERVICE
        ADMINISTRATION = Message.ADMINISTRATION
        STATISTICS = Message.STATISTICS
        BACK = Message.BACK
        NEXT = Message.NEXT
        REFRESH = Message.REFRESH
    
    # Setup & Robot Control  
    class Setup:
        SETUP_FIRST_STEP = Message.SETUP_FIRST_STEP
        SETUP_SECOND_STEP = Message.SETUP_SECOND_STEP
        HOME_ROBOT = Message.HOME_ROBOT
        ERROR_HOMING = Message.ERROR_HOMING

    class Warning:
        WARNING = Message.WARNING
        THE_ROBOT_WILL_START_MOVING_TO_THE_LOGIN_POSITION = Message.THE_ROBOT_WILL_START_MOVING_TO_THE_LOGIN_POSITION
        PLEASE_ENSURE_THE_AREA_IS_CLEAR_BEFORE_PROCEEDING = Message.PLEASE_ENSURE_THE_AREA_IS_CLEAR_BEFORE_PROCEEDING
        CANCEL = Message.CANCEL
    # Date & Time
    class Date:
        SELECT_DATE_RANGE = Message.SELECT_DATE_RANGE
        FROM = Message.FROM
        TO = Message.TO
    
    # General Status
    class Status:
        UNKNOWN = Message.UNKNOWN
        LOADED = Message.LOADED
        READY = Message.READY
        
    # Settings & Configuration
    class GlueSettings:
        SPRAY_SETTINGS = Message.SPRAY_SETTINGS
        SPRAY_WIDTH = Message.SPRAY_WIDTH
        SPRAYING_HEIGHT = Message.SPRAYING_HEIGHT
        FAN_SPEED = Message.FAN_SPEED
        GENERATOR_TO_GLUE_DELAY = Message.GENERATOR_TO_GLUE_DELAY
        MOTOR_SETTINGS = Message.MOTOR_SETTINGS
        MOTOR_SPEED = Message.MOTOR_SPEED
        REVERSE_DURATION = Message.REVERSE_DURATION
        REVERSE_SPEED = Message.REVERSE_SPEED
        GENERAL_SETTINGS = Message.GENERAL_SETTINGS
        RZ_ANGLE = Message.RZ_ANGLE
        GLUE_TYPE = Message.GLUE_TYPE
        DEVICE_CONTROL = Message.DEVICE_CONTROL
        MOTOR_CONTROL = Message.MOTOR_CONTROL
        OTHER_SETTINGS = Message.OTHER_SETTINGS
        GENERATOR = Message.GENERATOR
        FAN = Message.FAN
        MOTOR = Message.MOTOR
        DISPENSE_GLUE = Message.DISPENSE_GLUE

    class CameraSettings:
        CAMERA_STATUS = Message.CAMERA_STATUS
        CAMERA_SETTINGS = Message.CAMERA_SETTINGS
        CAMERA_INDEX = Message.CAMERA_INDEX
        WIDTH = Message.WIDTH
        HEIGHT = Message.HEIGHT
        SKIP_FRAMES = Message.SKIP_FRAMES
        CONTOUR_DETECTION = Message.CONTOUR_DETECTION
        ENABLE_DETECTION = Message.ENABLE_DETECTION
        DRAW_CONTOURS = Message.DRAW_CONTOURS
        THRESHOLD = Message.THRESHOLD
        EPSILON = Message.EPSILON
        MIN_CONTOUR_AREA = Message.MIN_CONTOUR_AREA
        MAX_CONTOUR_AREA = Message.MAX_CONTOUR_AREA
        PREPROCESSING = Message.PREPROCESSING
        GAUSSIAN_BLUR = Message.GAUSSIAN_BLUR
        BLUR_KERNEL_SIZE = Message.BLUR_KERNEL_SIZE
        THRESHOLD_TYPE = Message.THRESHOLD_TYPE
        DILATE = Message.DILATE
        DILATE_KERNEL = Message.DILATE_KERNEL
        DILATE_ITERATIONS = Message.DILATE_ITERATIONS
        ERODE = Message.ERODE
        ERODE_KERNEL = Message.ERODE_KERNEL
        ERODE_ITERATIONS = Message.ERODE_ITERATIONS
        CALIBRATION = Message.CALIBRATION
        CHESSBOARD_WIDTH = Message.CHESSBOARD_WIDTH
        CHESSBOARD_HEIGHT = Message.CHESSBOARD_HEIGHT
        SQUARE_SIZE = Message.SQUARE_SIZE
        BRIGHTNESS_CONTROL = Message.BRIGHTNESS_CONTROL
        AUTO_BRIGHTNESS = Message.AUTO_BRIGHTNESS
        TARGET_BRIGHTNESS = Message.TARGET_BRIGHTNESS
        ARUCO_DETECTION = Message.ARUCO_DETECTION
        ENABLE_ARUCO = Message.ENABLE_ARUCO
        DICTIONARY = Message.DICTIONARY
        FLIP_IMAGE = Message.FLIP_IMAGE
        EXIT_RAW_MODE = Message.EXIT_RAW_MODE
        RAW_MODE = Message.RAW_MODE

    # Settings & Configuration
    class RobotSettings:
        ROBOT_INFORMATION = Message.ROBOT_INFORMATION
        ROBOT_TOOL = Message.ROBOT_TOOL
        ROBOT_USER = Message.ROBOT_USER
        TCP_X_OFFSET = Message.TCP_X_OFFSET
        TCP_Y_OFFSET = Message.TCP_Y_OFFSET
        SAFETY_LIMITS = Message.SAFETY_LIMITS
        GLOBAL_MOTION_SETTINGS = Message.GLOBAL_MOTION_SETTINGS
        GLOBAL_VELOCITY = Message.GLOBAL_VELOCITY
        GLOBAL_ACCELERATION = Message.GLOBAL_ACCELERATION
        VELOCITY = Message.VELOCITY
        ACCELERATION = Message.ACCELERATION
        POSITION = Message.POSITION
        LOGIN_POSITION = Message.LOGIN_POSITION
        CALIBRATION_POSITION = Message.CALIBRATION_POSITION
        WORKPIECE_POSITION = Message.WORKPIECE_POSITION
        NOZZLE_CLEANING_POSITIONS = Message.NOZZLE_CLEANING_POSITIONS
        TOOL_CHANGER_POSITION = Message.TOOL_CHANGER_POSITION
        SLOT = Message.SLOT
        PICKUP_POSITIONS = Message.PICKUP_POSITIONS
        DROP_POSITIONS = Message.DROP_POSITIONS
        EXECUTE_TRAJECTORY = Message.EXECUTE_TRAJECTORY


    # Convenience aliases for commonly used keys
    LOGIN = Message.LOGIN
    PASSWORD = Message.PASSWORD
    START = Message.START
    STOP = Message.STOP
    BACK = Message.BACK
    ADD = Message.ADD
    DELETE = Message.REMOVE
    EDIT = Message.EDIT
    REMOVE = Message.REMOVE
    MOVE_TO = Message.MOVE_TO
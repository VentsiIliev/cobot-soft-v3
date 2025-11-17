"""
Description:
    This module defines all constant values used for shared request handling,
    including request types, actions, resources, and standard response statuses.

    These constants are shared across the system to ensure consistency when
    performing shared operations or interpreting requests/responses.

Usage:
    Import this module wherever shared requests or responses are handled to avoid
    hardcoding string literals and to centralize definitions.
"""


# ACTION_CALIBRATE_PICKUP_AREA = "calib pickup area"  # Calibrate pickup area using camera


# # === NEW REQUESTS ===
# TEST_RUN = "test_run"
# RUN_REMO = "run_demo"
# STOP_DEMO = "stop_demo"

# === RESPONSE STATUSES ===
RESPONSE_STATUS_SUCCESS = "success"               # Operation completed successfully
RESPONSE_STATUS_ERROR = "error"                   # Operation failed with an error
RESPONSE_STATUS_WARNING = "warning"               # Operation succeeded with a warning



# === REQUEST RESOURCES ===
REQUEST_RESOURCE_ROBOT = "Robot"                  # Robot resource group
REQUEST_RESOURCE_CAMERA = "Camera"
REQUEST_RESOURCE_SETTINGS = "Settings"
REQUEST_RESOURCE_WORKPIECE = "workpieces"


# LOGIN = "login"
# QR_LOGIN = "camera/login"
# START_CONTOUR_DETECTION = "camera/START_CONTOUR_DETECTION"
# STOP_CONTOUR_DETECTION = "camera/STOP_CONTOUR_DETECTION"
# START = "start"
# STOP = "stop"
# PAUSE = "pause"
# WORKPIECE_CREATE = "workpiece/create"
# WORKPIECE_CREATE_STEP_1 = "workpiece/create_step_1"
# WORKPIECE_CREATE_STEP_2 = "workpiece/create_step_2"
# WORKPIECE_SAVE = "workpiece/save"
# WORKPIECE_DELETE = "workpiece/delete"
# WORKPIECE_GET_BY_ID = "workpiece/getbyid"
# WORKPIECE_SAVE_DXF = "workpiece/dxf"
# WORKPIECE_GET_ALL = "workpiece/getall"
#
#
# ROBOT_ACTION_JOG_X_MINUS = "robot/jog/X/Minus"
# ROBOT_ACTION_JOG_X_PLUS = "robot/jog/X/Plus"
# ROBOT_ACTION_JOG_Y_MINUS = "robot/jog/Y/Minus"
# ROBOT_ACTION_JOG_Y_PLUS = "robot/jog/Y/Plus"
# ROBOT_ACTION_JOG_Z_MINUS = "robot/jog/Z/Minus"
# ROBOT_ACTION_JOG_Z_PLUS = "robot/jog/Z/Plus"
# ROBOT_MOVE_TO_CALIB_POS = "robot/move/calibPos"     # Move robot to predefined calibration position
# ROBOT_MOVE_TO_HOME_POS = "robot/move/home"           # Move robot to predefined home position
# ROBOT_MOVE_TO_LOGIN_POS = "robot/move/login"
# ROBOT_MOVE_TO_POSITION = "robot/move/position/{position}"   # Move robot to specified coordinates
# ROBOT_SLOT_0_PICKUP = "robot/move/slot/0/pickup"
# ROBOT_SLOT_0_DROP = "robot/move/slot/0/drop"
# ROBOT_SLOT_1_PICKUP = "robot/move/slot/1/pickup"
# ROBOT_SLOT_1_DROP = "robot/move/slot/1/drop"
# ROBOT_SLOT_2_PICKUP = "robot/move/slot/2/pickup"
# ROBOT_SLOT_2_DROP = "robot/move/slot/2/drop"
# ROBOT_SLOT_3_PICKUP = "robot/move/slot/3/pickup"
# ROBOT_SLOT_3_DROP = "robot/move/slot/3/drop"
# ROBOT_SLOT_4_PICKUP = "robot/move/slot/4/pickup"
# ROBOT_SLOT_4_DROP = "robot/move/slot/4/drop"
# ROBOT_EXECUTE_NOZZLE_CLEAN = "robot/move/clean"
# ROBOT_UPDATE_CONFIG = "robot/update/config"
#
# ROBOT_STOP = "robot/stop"
# ROBOT_SAVE_POINT = "robot/savePoint"
# ROBOT_GET_CURRENT_POSITION = "robot/getCurrentPosition"
# ROBOT_CALIBRATE = "robot/calibrate"
# ROBOT_CALIBRATE_PICKUP = "robot/calibPickup"
# ROBOT_RESET_ERRORS = "robot/resetErrors"
#
# CAMERA_ACTION_GET_LATEST_FRAME = "camera/getLatestFrame"
# CAMERA_ACTION_CAPTURE_CALIBRATION_IMAGE = "camera/captureCalibrationImage"  # Capture image for calibration
# CAMERA_ACTION_RAW_MODE_ON = "camera/rawModeOn"            # Enable raw image mode
# CAMERA_ACTION_RAW_MODE_OFF = "camera/rawModeOff"
# CAMERA_ACTION_CALIBRATE = "camera/calibrate"
# CAMERA_ACTION_TEST_CALIBRATION = "camera/testCalibration"  # Test camera calibration
# CAMERA_ACTION_SAVE_WORK_AREA_POINTS = "camera/saveWorkAreaPoints"  # Save work area points for camera
#
# SETTINGS_ROBOT_GET = "settings/robot/get"
# SETTINGS_ROBOT_SET = "settings/robot/set"
#
# SETTINGS_CAMERA_GET = "settings/camera/get"
# SETTINGS_CAMERA_SET = "settings/camera/set"
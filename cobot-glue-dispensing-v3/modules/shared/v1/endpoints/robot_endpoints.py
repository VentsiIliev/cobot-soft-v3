"""
Robot Endpoints - API v1

This module contains all robot-related endpoints for the internal API.
All endpoints follow the RESTful pattern: /api/v1/robot/{resource}/{action}
"""

# === ROBOT MOVEMENT ACTIONS ===

# Basic robot movements
ROBOT_MOVE_TO_HOME_POS = "/api/v1/robot/actions/home"
ROBOT_MOVE_TO_CALIB_POS = "/api/v1/robot/actions/move-to-calibration"
ROBOT_MOVE_TO_LOGIN_POS = "/api/v1/robot/actions/move-to-login"
ROBOT_EXECUTE_NOZZLE_CLEAN = "/api/v1/robot/actions/clean-nozzle"
ROBOT_STOP = "/api/v1/robot/actions/stop"

# Robot calibration actions
ROBOT_CALIBRATE = "/api/v1/robot/actions/calibrate"
ROBOT_CALIBRATE_PICKUP = "/api/v1/robot/actions/calibrate-pickup"

# === ROBOT JOGGING OPERATIONS ===

# X-axis jogging
ROBOT_ACTION_JOG_X_PLUS = "/api/v1/robot/jog/x/plus"
ROBOT_ACTION_JOG_X_MINUS = "/api/v1/robot/jog/x/minus"

# Y-axis jogging
ROBOT_ACTION_JOG_Y_PLUS = "/api/v1/robot/jog/y/plus"
ROBOT_ACTION_JOG_Y_MINUS = "/api/v1/robot/jog/y/minus"

# Z-axis jogging
ROBOT_ACTION_JOG_Z_PLUS = "/api/v1/robot/jog/z/plus"
ROBOT_ACTION_JOG_Z_MINUS = "/api/v1/robot/jog/z/minus"

# === ROBOT SLOT OPERATIONS ===

# Slot 0 operations
ROBOT_SLOT_0_PICKUP = "/api/v1/robot/slots/0/pickup"
ROBOT_SLOT_0_DROP = "/api/v1/robot/slots/0/drop"

# Slot 1 operations
ROBOT_SLOT_1_PICKUP = "/api/v1/robot/slots/1/pickup"
ROBOT_SLOT_1_DROP = "/api/v1/robot/slots/1/drop"

# Slot 2 operations
ROBOT_SLOT_2_PICKUP = "/api/v1/robot/slots/2/pickup"
ROBOT_SLOT_2_DROP = "/api/v1/robot/slots/2/drop"

# Slot 3 operations
ROBOT_SLOT_3_PICKUP = "/api/v1/robot/slots/3/pickup"
ROBOT_SLOT_3_DROP = "/api/v1/robot/slots/3/drop"

# Slot 4 operations
ROBOT_SLOT_4_PICKUP = "/api/v1/robot/slots/4/pickup"
ROBOT_SLOT_4_DROP = "/api/v1/robot/slots/4/drop"

# === ROBOT STATUS AND CONFIGURATION ===

# Position management
ROBOT_GET_CURRENT_POSITION = "/api/v1/robot/position/current"
ROBOT_MOVE_TO_POSITION = "/api/v1/robot/position/move-to"

# Calibration points
ROBOT_SAVE_POINT = "/api/v1/robot/calibration/save-point"

# Configuration and error handling
ROBOT_UPDATE_CONFIG = "/api/v1/robot/config/update"
ROBOT_RESET_ERRORS = "/api/v1/robot/errors/reset"

# === LEGACY ENDPOINTS (for backward compatibility) ===

# Legacy movement endpoints from pl_ui/Endpoints.py
HOME_ROBOT = "home_robot"
JOG_ROBOT = "jog_robot"
CALIBRATE_ROBOT = "calibrate_robot"
GO_TO_CALIBRATION_POS = "GO_to_calibration_pos"
GO_TO_LOGIN_POS = "got_to_login_pos"
SAVE_ROBOT_CALIBRATION_POINT = "SAVE_ROBOT_CALIBRATION_POINT"
MANUAL_MOVE_TOPIC = "robot/control/manual"
ROBOT_RESET_ERRORS_LEGACY = "robot/reset_errors"
ROBOT_UPDATE_CONFIG_LEGACY = "robot/update_config"

# Legacy Constants.py endpoints
ROBOT_EXECUTE_NOZZLE_CLEAN_LEGACY = "robot/move/clean"
ROBOT_MOVE_TO_HOME_POS_LEGACY = "robot/move/home"
ROBOT_MOVE_TO_CALIB_POS_LEGACY = "robot/move/calibPos"
ROBOT_MOVE_TO_LOGIN_POS_LEGACY = "robot/move/login"
ROBOT_MOVE_TO_POSITION_LEGACY = "robot/move/position/{position}"
ROBOT_UPDATE_CONFIG_LEGACY_2 = "robot/update/config"
ROBOT_STOP_LEGACY = "robot/stop"
ROBOT_SAVE_POINT_LEGACY = "robot/savePoint"
ROBOT_GET_CURRENT_POSITION_LEGACY = "robot/getCurrentPosition"
ROBOT_CALIBRATE_LEGACY = "robot/calibrate"
ROBOT_CALIBRATE_PICKUP_LEGACY = "robot/calibPickup"
ROBOT_RESET_ERRORS_LEGACY_2 = "robot/resetErrors"

# Legacy jog endpoints
ROBOT_ACTION_JOG_X_MINUS_LEGACY = "robot/jog/X/Minus"
ROBOT_ACTION_JOG_X_PLUS_LEGACY = "robot/jog/X/Plus"
ROBOT_ACTION_JOG_Y_MINUS_LEGACY = "robot/jog/Y/Minus"
ROBOT_ACTION_JOG_Y_PLUS_LEGACY = "robot/jog/Y/Plus"
ROBOT_ACTION_JOG_Z_MINUS_LEGACY = "robot/jog/Z/Minus"
ROBOT_ACTION_JOG_Z_PLUS_LEGACY = "robot/jog/Z/Plus"

# Legacy slot endpoints
ROBOT_SLOT_0_PICKUP_LEGACY = "robot/move/slot/0/pickup"
ROBOT_SLOT_0_DROP_LEGACY = "robot/move/slot/0/drop"
ROBOT_SLOT_1_PICKUP_LEGACY = "robot/move/slot/1/pickup"
ROBOT_SLOT_1_DROP_LEGACY = "robot/move/slot/1/drop"
ROBOT_SLOT_2_PICKUP_LEGACY = "robot/move/slot/2/pickup"
ROBOT_SLOT_2_DROP_LEGACY = "robot/move/slot/2/drop"
ROBOT_SLOT_3_PICKUP_LEGACY = "robot/move/slot/3/pickup"
ROBOT_SLOT_3_DROP_LEGACY = "robot/move/slot/3/drop"
ROBOT_SLOT_4_PICKUP_LEGACY = "robot/move/slot/4/pickup"
ROBOT_SLOT_4_DROP_LEGACY = "robot/move/slot/4/drop"
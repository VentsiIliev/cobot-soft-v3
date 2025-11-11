"""
Camera Endpoints - API v1

This module contains all camera and vision-related endpoints for the internal API.
All endpoints follow the RESTful pattern: /api/v1/camera/{resource}/{action}
"""

# === CAMERA FRAME OPERATIONS ===

# Frame retrieval
CAMERA_ACTION_GET_LATEST_FRAME = "/api/v1/camera/frame/latest"
UPDATE_CAMERA_FEED = "/api/v1/camera/feed/update"
GET_LATEST_IMAGE = "/api/v1/camera/image/latest"

# === CAMERA CALIBRATION ===

# Calibration actions
CAMERA_ACTION_CALIBRATE = "/api/v1/camera/actions/calibrate"
CAMERA_ACTION_CAPTURE_CALIBRATION_IMAGE = "/api/v1/camera/calibration/capture"
CAMERA_ACTION_TEST_CALIBRATION = "/api/v1/camera/calibration/test"

# === CAMERA MODES ===

# Raw mode control
CAMERA_ACTION_RAW_MODE_ON = "/api/v1/camera/mode/raw/on"
CAMERA_ACTION_RAW_MODE_OFF = "/api/v1/camera/mode/raw/off"

# === CAMERA WORK AREA ===

# Work area points management
CAMERA_ACTION_SAVE_WORK_AREA_POINTS = "/api/v1/camera/work-area/points"

# === VISION OPERATIONS ===

# Contour detection
START_CONTOUR_DETECTION = "/api/v1/camera/contour-detection/start"
STOP_CONTOUR_DETECTION = "/api/v1/camera/contour-detection/stop"

# === LEGACY ENDPOINTS (for backward compatibility) ===

# Legacy endpoints from pl_ui/Endpoints.py
QR_LOGIN = "camera/login"
CALIBRATE_CAMERA = "calibrate_camera"
CAPTURE_CALIBRATION_IMAGE = "capture_calibration_image"
TEST_CALIBRATION = "test_calibration"
RAW_MODE_ON = "rawModeOn"
RAW_MODE_OFF = "rawModeOff"
SAVE_WORK_AREA_POINTS = "save_work_area_points"
START_CONTOUR_DETECTION_LEGACY = "START_CONTOUR_DETECTION"
STOP_CONTOUR_DETECTION_LEGACY = "STOP_CONTOUR_DETECTION"
UPDATE_CAMERA_FEED_LEGACY = "cameraFeed/update"

# Legacy Constants.py endpoints
CAMERA_ACTION_GET_LATEST_FRAME_LEGACY = "camera/getLatestFrame"
CAMERA_ACTION_CAPTURE_CALIBRATION_IMAGE_LEGACY = "camera/captureCalibrationImage"
CAMERA_ACTION_RAW_MODE_ON_LEGACY = "camera/rawModeOn"
CAMERA_ACTION_RAW_MODE_OFF_LEGACY = "camera/rawModeOff"
CAMERA_ACTION_CALIBRATE_LEGACY = "camera/calibrate"
CAMERA_ACTION_TEST_CALIBRATION_LEGACY = "camera/testCalibration"
CAMERA_ACTION_SAVE_WORK_AREA_POINTS_LEGACY = "camera/saveWorkAreaPoints"
START_CONTOUR_DETECTION_LEGACY_2 = "camera/START_CONTOUR_DETECTION"
STOP_CONTOUR_DETECTION_LEGACY_2 = "camera/STOP_CONTOUR_DETECTION"
QR_LOGIN_LEGACY = "camera/login"
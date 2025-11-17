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




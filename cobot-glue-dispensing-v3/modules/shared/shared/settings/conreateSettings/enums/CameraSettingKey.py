from enum import Enum

class CameraSettingKey(Enum):
    # Core camera settings
    INDEX = "Index"
    WIDTH = "Width"
    HEIGHT = "Height"
    SKIP_FRAMES = "Skip frames"
    CAPTURE_POS_OFFSET = "Capture position offset"

    # Contour & shape detection
    THRESHOLD = "Threshold"
    THRESHOLD_PICKUP_AREA = "Threshold pickup area"
    EPSILON = "Epsilon"
    MIN_CONTOUR_AREA = "Min contour area"
    MAX_CONTOUR_AREA = "Max contour area"
    CONTOUR_DETECTION = "Contour detection"
    DRAW_CONTOURS = "Draw contours"

    # Preprocessing
    GAUSSIAN_BLUR = "Gaussian blur"
    BLUR_KERNEL_SIZE = "Blur kernel size"
    THRESHOLD_TYPE = "Threshold type"   # e.g., binary, binary_inv
    DILATE_ENABLED = "Dilate enabled"
    DILATE_KERNEL_SIZE = "Dilate kernel size"
    DILATE_ITERATIONS = "Dilate iterations"
    ERODE_ENABLED = "Erode enabled"
    ERODE_KERNEL_SIZE = "Erode kernel size"
    ERODE_ITERATIONS = "Erode iterations"

    # Calibration
    CHESSBOARD_WIDTH = "Chessboard width"
    CHESSBOARD_HEIGHT = "Chessboard height"
    SQUARE_SIZE_MM = "Square size (mm)"
    CALIBRATION_SKIP_FRAMES = "Calibration skip frames"  # Internal key for calibration skip frames

    # Brightness / PID
    BRIGHTNESS_AUTO = "Enable auto adjust"
    BRIGHTNESS_KP = "Kp"
    BRIGHTNESS_KI = "Ki"
    BRIGHTNESS_KD = "Kd"
    TARGET_BRIGHTNESS = "Target brightness"

    # Aruco marker detection
    ARUCO_ENABLED = "Enable Aruco detection"  # Internal key for ArUco enabled
    ARUCO_DICTIONARY = "Dictionary"
    ARUCO_FLIP_IMAGE = "Flip image"

    def getAsLabel(self):
        return self.value + ":"
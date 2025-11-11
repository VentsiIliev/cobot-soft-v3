from modules.shared.shared.settings.BaseSettings import Settings
from modules.shared.shared.settings.conreateSettings.enums.CameraSettingKey import CameraSettingKey


class CameraSettings(Settings):
    def __init__(self, data: dict = None):
        super().__init__()
        # Initialize default camera settings using the Enum

        # Core camera settings
        self.set_value(CameraSettingKey.INDEX.value, 0)
        self.set_value(CameraSettingKey.WIDTH.value, 1280)
        self.set_value(CameraSettingKey.HEIGHT.value, 720)
        self.set_value(CameraSettingKey.SKIP_FRAMES.value, 30)
        self.set_value(CameraSettingKey.CAPTURE_POS_OFFSET.value, 0)

        # Contour & shape detection
        self.set_value(CameraSettingKey.THRESHOLD.value, 100)
        self.set_value(CameraSettingKey.THRESHOLD_PICKUP_AREA.value, 150)
        self.set_value(CameraSettingKey.EPSILON.value, 0.004)
        self.set_value(CameraSettingKey.CONTOUR_DETECTION.value, True)
        self.set_value(CameraSettingKey.MIN_CONTOUR_AREA.value, 1000)
        self.set_value(CameraSettingKey.MAX_CONTOUR_AREA.value, 10000000)
        self.set_value(CameraSettingKey.DRAW_CONTOURS.value, False)

        # Preprocessing defaults
        self.set_value(CameraSettingKey.GAUSSIAN_BLUR.value, True)
        self.set_value(CameraSettingKey.BLUR_KERNEL_SIZE.value, 5)
        self.set_value(CameraSettingKey.THRESHOLD_TYPE.value, "binary_inv")
        self.set_value(CameraSettingKey.DILATE_ENABLED.value, True)
        self.set_value(CameraSettingKey.DILATE_KERNEL_SIZE.value, 3)
        self.set_value(CameraSettingKey.DILATE_ITERATIONS.value, 2)
        self.set_value(CameraSettingKey.ERODE_ENABLED.value, True)
        self.set_value(CameraSettingKey.ERODE_KERNEL_SIZE.value, 3)
        self.set_value(CameraSettingKey.ERODE_ITERATIONS.value, 4)

        # Calibration defaults
        self.set_value(CameraSettingKey.CHESSBOARD_WIDTH.value, 32)
        self.set_value(CameraSettingKey.CHESSBOARD_HEIGHT.value, 20)
        self.set_value(CameraSettingKey.SQUARE_SIZE_MM.value, 25)
        self.set_value(CameraSettingKey.CALIBRATION_SKIP_FRAMES.value, 30)

        # Brightness/PID defaults
        self.set_value(CameraSettingKey.BRIGHTNESS_AUTO.value, False)
        self.set_value(CameraSettingKey.BRIGHTNESS_KP.value, 0.7)
        self.set_value(CameraSettingKey.BRIGHTNESS_KI.value, 0.2)
        self.set_value(CameraSettingKey.BRIGHTNESS_KD.value, 0.05)
        self.set_value(CameraSettingKey.TARGET_BRIGHTNESS.value, 200)

        # Aruco defaults
        self.set_value(CameraSettingKey.ARUCO_ENABLED.value, False)
        self.set_value(CameraSettingKey.ARUCO_DICTIONARY.value, "DICT_4X4_1000")
        self.set_value(CameraSettingKey.ARUCO_FLIP_IMAGE.value, False)

        # Update settings with provided data (flattened from nested structure)
        if data:
            self._load_from_nested_data(data)

    def updateSettings(self, settings: dict):
        """
        Updates the camera settings based on the given dictionary.
        Handles both flat and nested JSON structures.

        Parameters
        ----------
        settings : dict
            A dictionary containing the camera settings to be updated.
            Can be flat (direct key-value pairs) or nested (with sections).

        Returns
        -------
        tuple
            (bool, str) - Success status and message
        """
        try:
            # Handle flat keys at root level
            if CameraSettingKey.INDEX.value in settings:
                self.set_camera_index(settings[CameraSettingKey.INDEX.value])
            if CameraSettingKey.WIDTH.value in settings:
                self.set_width(settings[CameraSettingKey.WIDTH.value])
            if CameraSettingKey.HEIGHT.value in settings:
                self.set_height(settings[CameraSettingKey.HEIGHT.value])
            if CameraSettingKey.SKIP_FRAMES.value in settings:
                self.set_skip_frames(settings[CameraSettingKey.SKIP_FRAMES.value])
            if CameraSettingKey.CAPTURE_POS_OFFSET.value in settings:
                self.set_capture_pos_offset(settings[CameraSettingKey.CAPTURE_POS_OFFSET.value])
            if CameraSettingKey.THRESHOLD.value in settings:
                self.set_threshold(settings[CameraSettingKey.THRESHOLD.value])
            if CameraSettingKey.THRESHOLD_PICKUP_AREA.value in settings:
                self.set_threshold_pickup_area(settings[CameraSettingKey.THRESHOLD_PICKUP_AREA.value])
            if CameraSettingKey.EPSILON.value in settings:
                self.set_epsilon(settings[CameraSettingKey.EPSILON.value])
            if CameraSettingKey.MIN_CONTOUR_AREA.value in settings:
                self.set_min_contour_area(settings[CameraSettingKey.MIN_CONTOUR_AREA.value])
            if CameraSettingKey.MAX_CONTOUR_AREA.value in settings:
                self.set_max_contour_area(settings[CameraSettingKey.MAX_CONTOUR_AREA.value])
            if CameraSettingKey.CONTOUR_DETECTION.value in settings:
                self.set_contour_detection(settings[CameraSettingKey.CONTOUR_DETECTION.value])
            if CameraSettingKey.DRAW_CONTOURS.value in settings:
                self.set_draw_contours(settings[CameraSettingKey.DRAW_CONTOURS.value])

            # Handle nested Preprocessing section
            if "Preprocessing" in settings:
                preprocessing = settings["Preprocessing"]
                if CameraSettingKey.GAUSSIAN_BLUR.value in preprocessing:
                    self.set_gaussian_blur(preprocessing[CameraSettingKey.GAUSSIAN_BLUR.value])
                if CameraSettingKey.BLUR_KERNEL_SIZE.value in preprocessing:
                    self.set_blur_kernel_size(preprocessing[CameraSettingKey.BLUR_KERNEL_SIZE.value])
                if CameraSettingKey.THRESHOLD_TYPE.value in preprocessing:
                    self.set_threshold_type(preprocessing[CameraSettingKey.THRESHOLD_TYPE.value])
                if CameraSettingKey.DILATE_ENABLED.value in preprocessing:
                    self.set_dilate_enabled(preprocessing[CameraSettingKey.DILATE_ENABLED.value])
                if CameraSettingKey.DILATE_KERNEL_SIZE.value in preprocessing:
                    self.set_dilate_kernel_size(preprocessing[CameraSettingKey.DILATE_KERNEL_SIZE.value])
                if CameraSettingKey.DILATE_ITERATIONS.value in preprocessing:
                    self.set_dilate_iterations(preprocessing[CameraSettingKey.DILATE_ITERATIONS.value])
                if CameraSettingKey.ERODE_ENABLED.value in preprocessing:
                    self.set_erode_enabled(preprocessing[CameraSettingKey.ERODE_ENABLED.value])
                if CameraSettingKey.ERODE_KERNEL_SIZE.value in preprocessing:
                    self.set_erode_kernel_size(preprocessing[CameraSettingKey.ERODE_KERNEL_SIZE.value])
                if CameraSettingKey.ERODE_ITERATIONS.value in preprocessing:
                    self.set_erode_iterations(preprocessing[CameraSettingKey.ERODE_ITERATIONS.value])

            # Handle nested Calibration section
            if "Calibration" in settings:
                calibration = settings["Calibration"]
                if CameraSettingKey.CHESSBOARD_WIDTH.value in calibration:
                    self.set_chessboard_width(calibration[CameraSettingKey.CHESSBOARD_WIDTH.value])
                if CameraSettingKey.CHESSBOARD_HEIGHT.value in calibration:
                    self.set_chessboard_height(calibration[CameraSettingKey.CHESSBOARD_HEIGHT.value])
                if CameraSettingKey.SQUARE_SIZE_MM.value in calibration:
                    self.set_square_size_mm(calibration[CameraSettingKey.SQUARE_SIZE_MM.value])
                if "Skip frames" in calibration:  # Special mapping
                    self.set_calibration_skip_frames(calibration["Skip frames"])


            # Handle nested Brightness Control section
            if "Brightness Control" in settings:
                brightness = settings["Brightness Control"]
                if CameraSettingKey.BRIGHTNESS_AUTO.value in brightness:
                    self.set_brightness_auto(brightness[CameraSettingKey.BRIGHTNESS_AUTO.value])
                if CameraSettingKey.BRIGHTNESS_KP.value in brightness:
                    self.set_brightness_kp(brightness[CameraSettingKey.BRIGHTNESS_KP.value])
                if CameraSettingKey.BRIGHTNESS_KI.value in brightness:
                    self.set_brightness_ki(brightness[CameraSettingKey.BRIGHTNESS_KI.value])
                if CameraSettingKey.BRIGHTNESS_KD.value in brightness:
                    self.set_brightness_kd(brightness[CameraSettingKey.BRIGHTNESS_KD.value])
                if CameraSettingKey.TARGET_BRIGHTNESS.value in brightness:
                    self.set_target_brightness(brightness[CameraSettingKey.TARGET_BRIGHTNESS.value])

            # Handle nested Aruco section
            if "Aruco" in settings:
                aruco = settings["Aruco"]
                if "Enable detection" in aruco:  # Special mapping
                    self.set_aruco_enabled(aruco["Enable detection"])
                if CameraSettingKey.ARUCO_DICTIONARY.value in aruco:
                    self.set_aruco_dictionary(aruco[CameraSettingKey.ARUCO_DICTIONARY.value])
                if CameraSettingKey.ARUCO_FLIP_IMAGE.value in aruco:
                    self.set_aruco_flip_image(aruco[CameraSettingKey.ARUCO_FLIP_IMAGE.value])

            # Handle flat keys for preprocessing (fallback for UI updates)
            if CameraSettingKey.GAUSSIAN_BLUR.value in settings:
                self.set_gaussian_blur(settings[CameraSettingKey.GAUSSIAN_BLUR.value])
            if CameraSettingKey.BLUR_KERNEL_SIZE.value in settings:
                self.set_blur_kernel_size(settings[CameraSettingKey.BLUR_KERNEL_SIZE.value])
            if CameraSettingKey.THRESHOLD_TYPE.value in settings:
                self.set_threshold_type(settings[CameraSettingKey.THRESHOLD_TYPE.value])
            if CameraSettingKey.DILATE_ENABLED.value in settings:
                self.set_dilate_enabled(settings[CameraSettingKey.DILATE_ENABLED.value])
            if CameraSettingKey.DILATE_KERNEL_SIZE.value in settings:
                self.set_dilate_kernel_size(settings[CameraSettingKey.DILATE_KERNEL_SIZE.value])
            if CameraSettingKey.DILATE_ITERATIONS.value in settings:
                self.set_dilate_iterations(settings[CameraSettingKey.DILATE_ITERATIONS.value])
            if CameraSettingKey.ERODE_ENABLED.value in settings:
                self.set_erode_enabled(settings[CameraSettingKey.ERODE_ENABLED.value])
            if CameraSettingKey.ERODE_KERNEL_SIZE.value in settings:
                self.set_erode_kernel_size(settings[CameraSettingKey.ERODE_KERNEL_SIZE.value])
            if CameraSettingKey.ERODE_ITERATIONS.value in settings:
                self.set_erode_iterations(settings[CameraSettingKey.ERODE_ITERATIONS.value])

            # Handle flat keys for calibration (fallback for UI updates)
            if CameraSettingKey.CHESSBOARD_WIDTH.value in settings:
                self.set_chessboard_width(settings[CameraSettingKey.CHESSBOARD_WIDTH.value])
            if CameraSettingKey.CHESSBOARD_HEIGHT.value in settings:
                self.set_chessboard_height(settings[CameraSettingKey.CHESSBOARD_HEIGHT.value])
            if CameraSettingKey.SQUARE_SIZE_MM.value in settings:
                self.set_square_size_mm(settings[CameraSettingKey.SQUARE_SIZE_MM.value])
            if CameraSettingKey.CALIBRATION_SKIP_FRAMES.value in settings:
                self.set_calibration_skip_frames(settings[CameraSettingKey.CALIBRATION_SKIP_FRAMES.value])

            # Handle flat keys for brightness control (fallback for UI updates)
            if CameraSettingKey.BRIGHTNESS_AUTO.value in settings:
                self.set_brightness_auto(settings[CameraSettingKey.BRIGHTNESS_AUTO.value])
            if CameraSettingKey.BRIGHTNESS_KP.value in settings:
                self.set_brightness_kp(settings[CameraSettingKey.BRIGHTNESS_KP.value])
            if CameraSettingKey.BRIGHTNESS_KI.value in settings:
                self.set_brightness_ki(settings[CameraSettingKey.BRIGHTNESS_KI.value])
            if CameraSettingKey.BRIGHTNESS_KD.value in settings:
                self.set_brightness_kd(settings[CameraSettingKey.BRIGHTNESS_KD.value])
            if CameraSettingKey.TARGET_BRIGHTNESS.value in settings:
                self.set_target_brightness(settings[CameraSettingKey.TARGET_BRIGHTNESS.value])

            # Handle flat keys for ArUco (fallback for UI updates)
            if CameraSettingKey.ARUCO_ENABLED.value in settings:
                self.set_aruco_enabled(settings[CameraSettingKey.ARUCO_ENABLED.value])
            if CameraSettingKey.ARUCO_DICTIONARY.value in settings:
                self.set_aruco_dictionary(settings[CameraSettingKey.ARUCO_DICTIONARY.value])
            if CameraSettingKey.ARUCO_FLIP_IMAGE.value in settings:
                self.set_aruco_flip_image(settings[CameraSettingKey.ARUCO_FLIP_IMAGE.value])

            return True, "Settings updated successfully"

        except Exception as e:
            return False, f"Error updating settings: {str(e)}"
    def _load_from_nested_data(self, data):
        """Load settings from nested JSON structure"""
        # Handle flat keys first
        for key, value in data.items():
            if not isinstance(value, dict):
                self.set_value(key, value)

        # Handle nested sections
        if "Preprocessing" in data:
            for key, value in data["Preprocessing"].items():
                self.set_value(key, value)

        if "Calibration" in data:
            for key, value in data["Calibration"].items():
                # Handle the special case where "Skip frames" maps to calibration skip frames
                if key == "Skip frames":
                    self.set_value(CameraSettingKey.CALIBRATION_SKIP_FRAMES.value, value)
                else:
                    self.set_value(key, value)

        if "Brightness Control" in data:
            for key, value in data["Brightness Control"].items():
                self.set_value(key, value)

        if "Aruco" in data:
            aruco_data = data["Aruco"]
            if "Enable detection" in aruco_data:
                self.set_value(CameraSettingKey.ARUCO_ENABLED.value, aruco_data["Enable detection"])
            for key, value in aruco_data.items():
                if key != "Enable detection":
                    self.set_value(key, value)

    def to_nested_json(self):
        """Convert internal flat structure back to nested JSON format"""
        nested_data = {}

        # Core camera settings (flat in root)
        nested_data[CameraSettingKey.INDEX.value] = self.get_value(CameraSettingKey.INDEX.value)
        nested_data[CameraSettingKey.WIDTH.value] = self.get_value(CameraSettingKey.WIDTH.value)
        nested_data[CameraSettingKey.HEIGHT.value] = self.get_value(CameraSettingKey.HEIGHT.value)
        nested_data[CameraSettingKey.SKIP_FRAMES.value] = self.get_value(CameraSettingKey.SKIP_FRAMES.value)
        nested_data[CameraSettingKey.CAPTURE_POS_OFFSET.value] = self.get_value(CameraSettingKey.CAPTURE_POS_OFFSET.value)

        # Contour detection (flat in root)
        nested_data[CameraSettingKey.THRESHOLD.value] = self.get_value(CameraSettingKey.THRESHOLD.value)
        nested_data[CameraSettingKey.THRESHOLD_PICKUP_AREA.value] = self.get_value(CameraSettingKey.THRESHOLD_PICKUP_AREA.value)
        nested_data[CameraSettingKey.EPSILON.value] = self.get_value(CameraSettingKey.EPSILON.value)
        nested_data[CameraSettingKey.MIN_CONTOUR_AREA.value] = self.get_value(CameraSettingKey.MIN_CONTOUR_AREA.value)
        nested_data[CameraSettingKey.MAX_CONTOUR_AREA.value] = self.get_value(CameraSettingKey.MAX_CONTOUR_AREA.value)
        nested_data[CameraSettingKey.CONTOUR_DETECTION.value] = self.get_value(CameraSettingKey.CONTOUR_DETECTION.value)
        nested_data[CameraSettingKey.DRAW_CONTOURS.value] = self.get_value(CameraSettingKey.DRAW_CONTOURS.value)

        # Preprocessing section
        nested_data["Preprocessing"] = {
            CameraSettingKey.GAUSSIAN_BLUR.value: self.get_value(CameraSettingKey.GAUSSIAN_BLUR.value),
            CameraSettingKey.BLUR_KERNEL_SIZE.value: self.get_value(CameraSettingKey.BLUR_KERNEL_SIZE.value),
            CameraSettingKey.THRESHOLD_TYPE.value: self.get_value(CameraSettingKey.THRESHOLD_TYPE.value),
            CameraSettingKey.DILATE_ENABLED.value: self.get_value(CameraSettingKey.DILATE_ENABLED.value),
            CameraSettingKey.DILATE_KERNEL_SIZE.value: self.get_value(CameraSettingKey.DILATE_KERNEL_SIZE.value),
            CameraSettingKey.DILATE_ITERATIONS.value: self.get_value(CameraSettingKey.DILATE_ITERATIONS.value),
            CameraSettingKey.ERODE_ENABLED.value: self.get_value(CameraSettingKey.ERODE_ENABLED.value),
            CameraSettingKey.ERODE_KERNEL_SIZE.value: self.get_value(CameraSettingKey.ERODE_KERNEL_SIZE.value),
            CameraSettingKey.ERODE_ITERATIONS.value: self.get_value(CameraSettingKey.ERODE_ITERATIONS.value),
        }

        # Calibration section
        nested_data["Calibration"] = {
            CameraSettingKey.CHESSBOARD_WIDTH.value: self.get_value(CameraSettingKey.CHESSBOARD_WIDTH.value),
            CameraSettingKey.CHESSBOARD_HEIGHT.value: self.get_value(CameraSettingKey.CHESSBOARD_HEIGHT.value),
            CameraSettingKey.SQUARE_SIZE_MM.value: self.get_value(CameraSettingKey.SQUARE_SIZE_MM.value),
            "Skip frames": self.get_value(CameraSettingKey.CALIBRATION_SKIP_FRAMES.value),  # Special mapping
        }

        # Brightness Control section
        nested_data["Brightness Control"] = {
            CameraSettingKey.BRIGHTNESS_AUTO.value: self.get_value(CameraSettingKey.BRIGHTNESS_AUTO.value),
            CameraSettingKey.BRIGHTNESS_KP.value: self.get_value(CameraSettingKey.BRIGHTNESS_KP.value),
            CameraSettingKey.BRIGHTNESS_KI.value: self.get_value(CameraSettingKey.BRIGHTNESS_KI.value),
            CameraSettingKey.BRIGHTNESS_KD.value: self.get_value(CameraSettingKey.BRIGHTNESS_KD.value),
            CameraSettingKey.TARGET_BRIGHTNESS.value: self.get_value(CameraSettingKey.TARGET_BRIGHTNESS.value),
        }

        # Aruco section
        nested_data["Aruco"] = {
            "Enable detection": self.get_value(CameraSettingKey.ARUCO_ENABLED.value),  # Special mapping
            CameraSettingKey.ARUCO_DICTIONARY.value: self.get_value(CameraSettingKey.ARUCO_DICTIONARY.value),
            CameraSettingKey.ARUCO_FLIP_IMAGE.value: self.get_value(CameraSettingKey.ARUCO_FLIP_IMAGE.value),
        }

        return nested_data

    # ======= CORE CAMERA METHODS =======
    def set_camera_index(self, index):
        """Set the camera index."""
        self.set_value(CameraSettingKey.INDEX.value, index)

    def get_camera_index(self):
        """Get the camera index."""
        return self.get_value(CameraSettingKey.INDEX.value)

    def get_camera_width(self):
        """Get the camera width."""
        return self.get_value(CameraSettingKey.WIDTH.value)

    def get_camera_height(self):
        """Get the camera height."""
        return self.get_value(CameraSettingKey.HEIGHT.value)

    def set_resolution(self, width, height):
        """Set the camera resolution."""
        self.set_value(CameraSettingKey.WIDTH.value, width)
        self.set_value(CameraSettingKey.HEIGHT.value, height)

    def set_width(self, width):
        """Set the camera width."""
        self.set_value(CameraSettingKey.WIDTH.value, width)

    def set_height(self, height):
        """Set the camera height."""
        self.set_value(CameraSettingKey.HEIGHT.value, height)

    def get_resolution(self):
        """Get the camera resolution."""
        return (self.get_value(CameraSettingKey.WIDTH.value), self.get_value(CameraSettingKey.HEIGHT.value))

    def get_skip_frames(self):
        """Get the number of frames to skip."""
        return self.get_value(CameraSettingKey.SKIP_FRAMES.value)



    def set_skip_frames(self, skipFrames):
        """Set the number of frames to skip."""
        self.set_value(CameraSettingKey.SKIP_FRAMES.value, skipFrames)

    def set_capture_pos_offset(self, offset):
        """Set the capture position offset."""
        self.set_value(CameraSettingKey.CAPTURE_POS_OFFSET.value, offset)

    def get_capture_pos_offset(self):
        """Get the capture position offset."""
        return self.get_value(CameraSettingKey.CAPTURE_POS_OFFSET.value)

    def get_capture_pos_offset(self):
        """Get the capture position offset."""
        return self.get_value(CameraSettingKey.CAPTURE_POS_OFFSET.value)

    def set_capture_pos_offset(self, offset):
        """Set the capture position offset."""
        self.set_value(CameraSettingKey.CAPTURE_POS_OFFSET.value, offset)

    # ======= CONTOUR & SHAPE DETECTION METHODS =======
    def get_threshold(self):
        """Get the threshold value."""
        return self.get_value(CameraSettingKey.THRESHOLD.value)

    def set_threshold(self, threshold):
        """Set the threshold value."""
        self.set_value(CameraSettingKey.THRESHOLD.value, threshold)

    def get_threshold_pickup_area(self):
        """Get the threshold pickup area value."""
        return self.get_value(CameraSettingKey.THRESHOLD_PICKUP_AREA.value)

    def set_threshold_pickup_area(self, threshold):
        self.set_value(CameraSettingKey.THRESHOLD_PICKUP_AREA.value,threshold)

    def get_epsilon(self):
        """Get the epsilon value."""
        return self.get_value(CameraSettingKey.EPSILON.value)

    def set_epsilon(self, epsilon):
        """Set the epsilon value."""
        self.set_value(CameraSettingKey.EPSILON.value, epsilon)

    def get_min_contour_area(self):
        return self.get_value(CameraSettingKey.MIN_CONTOUR_AREA.value)

    def set_min_contour_area(self, minContourArea):
        self.set_value(CameraSettingKey.MIN_CONTOUR_AREA.value, minContourArea)

    def get_max_contour_area(self):
        """Get the maximum contour area."""
        return self.get_value(CameraSettingKey.MAX_CONTOUR_AREA.value)

    def set_max_contour_area(self, maxContourArea):
        self.set_value(CameraSettingKey.MAX_CONTOUR_AREA.value, maxContourArea)

    def get_contour_detection(self):
        """Get the contour detection status."""
        return self.get_value(CameraSettingKey.CONTOUR_DETECTION.value)

    def set_contour_detection(self, contourDetection):
        """Set the contour detection status."""
        self.set_value(CameraSettingKey.CONTOUR_DETECTION.value, contourDetection)

    def get_draw_contours(self):
        """Get the draw contours status."""
        return self.get_value(CameraSettingKey.DRAW_CONTOURS.value)

    def set_draw_contours(self, drawContours):
        """Set the draw contours status."""
        self.set_value(CameraSettingKey.DRAW_CONTOURS.value, drawContours)

    # ======= PREPROCESSING METHODS =======
    def get_gaussian_blur(self):
        """Get gaussian blur enabled status."""
        return self.get_value(CameraSettingKey.GAUSSIAN_BLUR.value)

    def set_gaussian_blur(self, enabled):
        """Set gaussian blur enabled status."""
        self.set_value(CameraSettingKey.GAUSSIAN_BLUR.value, enabled)

    def get_blur_kernel_size(self):
        """Get blur kernel size."""
        return self.get_value(CameraSettingKey.BLUR_KERNEL_SIZE.value)

    def set_blur_kernel_size(self, size):
        """Set blur kernel size."""
        self.set_value(CameraSettingKey.BLUR_KERNEL_SIZE.value, size)

    def get_threshold_type(self):
        """Get threshold type."""
        return self.get_value(CameraSettingKey.THRESHOLD_TYPE.value)

    def set_threshold_type(self, threshold_type):
        """Set threshold type."""
        self.set_value(CameraSettingKey.THRESHOLD_TYPE.value, threshold_type)

    def get_dilate_enabled(self):
        """Get dilate enabled status."""
        return self.get_value(CameraSettingKey.DILATE_ENABLED.value)

    def set_dilate_enabled(self, enabled):
        """Set dilate enabled status."""
        self.set_value(CameraSettingKey.DILATE_ENABLED.value, enabled)

    def get_dilate_kernel_size(self):
        """Get dilate kernel size."""
        return self.get_value(CameraSettingKey.DILATE_KERNEL_SIZE.value)

    def set_dilate_kernel_size(self, size):
        """Set dilate kernel size."""
        self.set_value(CameraSettingKey.DILATE_KERNEL_SIZE.value, size)

    def get_dilate_iterations(self):
        """Get dilate iterations."""
        return self.get_value(CameraSettingKey.DILATE_ITERATIONS.value)

    def set_dilate_iterations(self, iterations):
        """Set dilate iterations."""
        self.set_value(CameraSettingKey.DILATE_ITERATIONS.value, iterations)

    def get_erode_enabled(self):
        """Get erode enabled status."""
        return self.get_value(CameraSettingKey.ERODE_ENABLED.value)

    def set_erode_enabled(self, enabled):
        """Set erode enabled status."""
        self.set_value(CameraSettingKey.ERODE_ENABLED.value, enabled)

    def get_erode_kernel_size(self):
        """Get erode kernel size."""
        return self.get_value(CameraSettingKey.ERODE_KERNEL_SIZE.value)

    def set_erode_kernel_size(self, size):
        """Set erode kernel size."""
        self.set_value(CameraSettingKey.ERODE_KERNEL_SIZE.value, size)

    def get_erode_iterations(self):
        """Get erode iterations."""
        return self.get_value(CameraSettingKey.ERODE_ITERATIONS.value)

    def set_erode_iterations(self, iterations):
        """Set erode iterations."""
        self.set_value(CameraSettingKey.ERODE_ITERATIONS.value, iterations)

    # ======= CALIBRATION METHODS =======
    def get_chessboard_width(self):
        """Get chessboard width."""
        return self.get_value(CameraSettingKey.CHESSBOARD_WIDTH.value)

    def set_chessboard_width(self, width):
        """Set chessboard width."""
        self.set_value(CameraSettingKey.CHESSBOARD_WIDTH.value, width)

    def get_chessboard_height(self):
        """Get chessboard height."""
        return self.get_value(CameraSettingKey.CHESSBOARD_HEIGHT.value)

    def set_chessboard_height(self, height):
        """Set chessboard height."""
        self.set_value(CameraSettingKey.CHESSBOARD_HEIGHT.value, height)

    def get_square_size_mm(self):
        """Get square size in mm."""
        return self.get_value(CameraSettingKey.SQUARE_SIZE_MM.value)

    def set_square_size_mm(self, size):
        """Set square size in mm."""
        self.set_value(CameraSettingKey.SQUARE_SIZE_MM.value, size)

    def get_calibration_skip_frames(self):
        """Get calibration skip frames."""
        return self.get_value(CameraSettingKey.CALIBRATION_SKIP_FRAMES.value)

    def set_calibration_skip_frames(self, frames):
        """Set calibration skip frames."""
        self.set_value(CameraSettingKey.CALIBRATION_SKIP_FRAMES.value, frames)

    def set_chessboard_config(self, width, height, square_size_mm):
        """Set complete chessboard configuration."""
        self.set_chessboard_width(width)
        self.set_chessboard_height(height)
        self.set_square_size_mm(square_size_mm)

    def get_chessboard_config(self):
        """Get complete chessboard configuration."""
        return (
            self.get_chessboard_width(),
            self.get_chessboard_height(),
            self.get_square_size_mm()
        )

    # ======= BRIGHTNESS/PID METHODS =======
    def get_brightness_auto(self):
        """Get auto brightness adjustment status."""
        return self.get_value(CameraSettingKey.BRIGHTNESS_AUTO.value)

    def set_brightness_auto(self, enabled):
        """Set auto brightness adjustment status."""
        self.set_value(CameraSettingKey.BRIGHTNESS_AUTO.value, enabled)

    def get_brightness_kp(self):
        """Get brightness PID Kp value."""
        return self.get_value(CameraSettingKey.BRIGHTNESS_KP.value)

    def set_brightness_kp(self, kp):
        """Set brightness PID Kp value."""
        self.set_value(CameraSettingKey.BRIGHTNESS_KP.value, kp)

    def get_brightness_ki(self):
        """Get brightness PID Ki value."""
        return self.get_value(CameraSettingKey.BRIGHTNESS_KI.value)

    def set_brightness_ki(self, ki):
        """Set brightness PID Ki value."""
        self.set_value(CameraSettingKey.BRIGHTNESS_KI.value, ki)

    def get_brightness_kd(self):
        """Get brightness PID Kd value."""
        return self.get_value(CameraSettingKey.BRIGHTNESS_KD.value)

    def set_brightness_kd(self, kd):
        """Set brightness PID Kd value."""
        self.set_value(CameraSettingKey.BRIGHTNESS_KD.value, kd)

    def get_target_brightness(self):
        """Get target brightness value."""
        return self.get_value(CameraSettingKey.TARGET_BRIGHTNESS.value)

    def set_target_brightness(self, brightness):
        """Set target brightness value."""
        self.set_value(CameraSettingKey.TARGET_BRIGHTNESS.value, brightness)

    def set_brightness_pid_config(self, kp, ki, kd, target):
        """Set complete brightness PID configuration."""
        self.set_brightness_kp(kp)
        self.set_brightness_ki(ki)
        self.set_brightness_kd(kd)
        self.set_target_brightness(target)

    def get_brightness_pid_config(self):
        """Get complete brightness PID configuration."""
        return (
            self.get_brightness_kp(),
            self.get_brightness_ki(),
            self.get_brightness_kd(),
            self.get_target_brightness()
        )

    # ======= ARUCO METHODS =======
    def get_aruco_enabled(self):
        """Get ArUco detection enabled status."""
        return self.get_value(CameraSettingKey.ARUCO_ENABLED.value)

    def set_aruco_enabled(self, enabled):
        """Set ArUco detection enabled status."""
        self.set_value(CameraSettingKey.ARUCO_ENABLED.value, enabled)

    def get_aruco_dictionary(self):
        """Get ArUco dictionary."""
        return self.get_value(CameraSettingKey.ARUCO_DICTIONARY.value)

    def set_aruco_dictionary(self, dictionary):
        """Set ArUco dictionary."""
        self.set_value(CameraSettingKey.ARUCO_DICTIONARY.value, dictionary)

    def get_aruco_flip_image(self):
        """Get ArUco flip image status."""
        return self.get_value(CameraSettingKey.ARUCO_FLIP_IMAGE.value)

    def set_aruco_flip_image(self, flip):
        """Set ArUco flip image status."""
        self.set_value(CameraSettingKey.ARUCO_FLIP_IMAGE.value, flip)

    def set_aruco_config(self, enabled, dictionary, flip_image):
        """Set complete ArUco configuration."""
        self.set_aruco_enabled(enabled)
        self.set_aruco_dictionary(dictionary)
        self.set_aruco_flip_image(flip_image)

    def get_aruco_config(self):
        """Get complete ArUco configuration."""
        return (
            self.get_aruco_enabled(),
            self.get_aruco_dictionary(),
            self.get_aruco_flip_image()
        )

    # ======= UTILITY METHODS =======
    def display_settings(self):
        """Utility method to display all camera settings."""
        print("=== CAMERA SETTINGS ===")
        print(f"Camera Index: {self.get_camera_index()}")
        print(f"Resolution: {self.get_camera_width()}x{self.get_camera_height()}")
        print(f"Skip Frames: {self.get_skip_frames()}")
        print(f"Capture Position Offset: {self.get_capture_pos_offset()}mm")

        print("\n=== CONTOUR DETECTION ===")
        print(f"Threshold: {self.get_threshold()}")
        print(f"Threshold Pickup Area: {self.get_threshold_pickup_area()}")
        print(f"Epsilon: {self.get_epsilon()}")
        print(f"Min Contour Area: {self.get_min_contour_area()}")
        print(f"Max Contour Area: {self.get_max_contour_area()}")
        print(f"Contour Detection: {self.get_contour_detection()}")
        print(f"Draw Contours: {self.get_draw_contours()}")

        print("\n=== PREPROCESSING ===")
        print(f"Gaussian Blur: {self.get_gaussian_blur()}")
        print(f"Blur Kernel Size: {self.get_blur_kernel_size()}")
        print(f"Threshold Type: {self.get_threshold_type()}")
        print(f"Dilate Enabled: {self.get_dilate_enabled()}")
        print(f"Dilate Kernel: {self.get_dilate_kernel_size()}, Iterations: {self.get_dilate_iterations()}")
        print(f"Erode Enabled: {self.get_erode_enabled()}")
        print(f"Erode Kernel: {self.get_erode_kernel_size()}, Iterations: {self.get_erode_iterations()}")

        print("\n=== CALIBRATION ===")
        print(f"Chessboard: {self.get_chessboard_width()}x{self.get_chessboard_height()}")
        print(f"Square Size: {self.get_square_size_mm()}mm")
        print(f"Calibration Skip Frames: {self.get_calibration_skip_frames()}")

        print("\n=== BRIGHTNESS CONTROL ===")
        print(f"Auto Brightness: {self.get_brightness_auto()}")
        print(
            f"PID Values - Kp: {self.get_brightness_kp()}, Ki: {self.get_brightness_ki()}, Kd: {self.get_brightness_kd()}")
        print(f"Target Brightness: {self.get_target_brightness()}")

        print("\n=== ARUCO DETECTION ===")
        print(f"ArUco Enabled: {self.get_aruco_enabled()}")
        print(f"Dictionary: {self.get_aruco_dictionary()}")
        print(f"Flip Image: {self.get_aruco_flip_image()}")

    def __str__(self):
        return (
            f"CameraSettings:\n"
            f"  Index: {self.get_camera_index()}\n"
            f"  Resolution: {self.get_camera_width()}x{self.get_camera_height()}\n"
            f"  Skip Frames: {self.get_skip_frames()}\n"
            f"  Threshold: {self.get_threshold()}\n"
            f"  Threshold Pickup Area: {self.get_threshold_pickup_area()}\n"
            f"  Epsilon: {self.get_epsilon()}\n"
            f"  Min Contour Area: {self.get_min_contour_area()}\n"
            f"  Max Contour Area: {self.get_max_contour_area()}\n"
            f"  Contour Detection: {self.get_contour_detection()}\n"
            f"  Draw Contours: {self.get_draw_contours()}\n"
            f"  Gaussian Blur: {self.get_gaussian_blur()}\n"
            f"  Blur Kernel Size: {self.get_blur_kernel_size()}\n"
            f"  Threshold Type: {self.get_threshold_type()}\n"
            f"  Dilate: {self.get_dilate_enabled()} (kernel: {self.get_dilate_kernel_size()}, iter: {self.get_dilate_iterations()})\n"
            f"  Erode: {self.get_erode_enabled()} (kernel: {self.get_erode_kernel_size()}, iter: {self.get_erode_iterations()})\n"
            f"  Chessboard: {self.get_chessboard_width()}x{self.get_chessboard_height()}\n"
            f"  Square Size: {self.get_square_size_mm()}mm\n"
            f"  Calibration Skip Frames: {self.get_calibration_skip_frames()}\n"
            f"  Auto Brightness: {self.get_brightness_auto()}\n"
            f"  PID - Kp: {self.get_brightness_kp()}, Ki: {self.get_brightness_ki()}, Kd: {self.get_brightness_kd()}\n"
            f"  Target Brightness: {self.get_target_brightness()}\n"
            f"  ArUco Enabled: {self.get_aruco_enabled()}\n"
            f"  ArUco Dictionary: {self.get_aruco_dictionary()}\n"
            f"  ArUco Flip Image: {self.get_aruco_flip_image()}"
        )
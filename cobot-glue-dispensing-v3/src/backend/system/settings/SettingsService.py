import json
import os

from modules.shared.shared.settings.conreateSettings.RobotSettings import RobotSettings
from modules.shared.shared.settings.conreateSettings.CameraSettings import CameraSettings
from modules.shared.shared.settings.conreateSettings.GlueSettings import GlueSettings
from modules.shared.shared.settings.robotConfig.robotConfigModel import RobotConfig,get_default_config
from modules.shared.v1 import Constants
from modules.shared.shared.settings.conreateSettings.enums.CameraSettingKey import CameraSettingKey
from modules.shared.shared.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey
from modules.shared.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from src.backend.system.tools.GlueCell import GlueType
import logging


class SettingsService:
    """
      Service responsible for managing application settings related to the robot and camera components.

      This class handles:
      - Loading and saving settings to JSON files
      - Providing settings objects for external access
      - Updating settings based on external input (e.g., from HTTP requests)
      - Returning settings in dictionary format for serialization

      Attributes:
          settings_dir (str): The root directory where settings JSON files are stored.
          settings_file_paths (dict): File paths for individual settings files.
          settings_objects (dict): Dictionary storing all current settings objects.
      """
    settings_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "storage", "settings")
    settings_dir = os.path.normpath(settings_dir)  # Normalize path to avoid issues

    settings_file_paths = {
        "camera": os.path.join(settings_dir, "camera_settings.json"),
        "robot_settings": os.path.join(settings_dir, "robot_settings.json"),
        "glue_settings": os.path.join(settings_dir, "glue_settings.json"),
    }

    ROBOT_CONFIG_FILE = os.path.join(settings_dir, "robot_config.json")

    def __init__(self):
        """
               Initialize the SettingsService by creating and loading camera and robot settings.
               """
        self.logger = logging.getLogger(self.__class__.__name__)
        # Initialize a dictionary to store settings objects
        self.settings_objects = {}

        # Initialize and load settings for each component
        self.camera_settings = CameraSettings()
        self.robot_settings = RobotSettings()
        self.glue_settings = GlueSettings()

        # Store them in the settings dictionary
        self.settings_objects["camera"] = self.camera_settings
        self.settings_objects["robot_settings"] = self.robot_settings
        self.settings_objects["glue_settings"] = self.glue_settings
        self.robot_config = self.load_robot_config()

        # Load settings from JSON files, or use default values if files do not exist
        self.load_all_settings()

    def set_camera_index(self, index):
        self.camera_settings.set_camera_index(index)

    def set_camera_width(self, width):
        self.camera_settings.set_width(width)

    def set_camera_height(self, height):
        self.camera_settings.set_height(height)

    def get_camera_index(self):
        return self.camera_settings.get_camera_index()

    def get_camera_width(self):
        return self.camera_settings.get_camera_width()

    def get_camera_height(self):
        return self.camera_settings.get_camera_height()

    def get_camera_settings(self):
        """Retrieve the camera settings object."""
        return self.camera_settings

    def getSettings(self, key):
        """
        Retrieve settings data based on the key provided.

        Args:
            key (str): The key corresponding to the settings type ("camera" or "robot").

        Returns:
            dict: The settings data as a dictionary.
        """
        if key == Constants.REQUEST_RESOURCE_CAMERA:
            # For camera settings, return the nested JSON structure
            data = self.camera_settings.to_nested_json()
            self.logger.debug("from Settings Service: ", data)
            return data
        elif key == Constants.REQUEST_RESOURCE_ROBOT:
            return self.robot_settings.toDict()
        elif key == Constants.REQUEST_RESOURCE_GLUE:
            return self.glue_settings.toDict()

    def save_all_settings(self):
        """Save all settings to their respective files."""
        for key, settings_obj in self.settings_objects.items():
            filename = self.settings_file_paths.get(key)
            if filename:
                self.save_settings_to_json(filename, settings_obj)
    #MUST BE REFACTORED load_robot_config AND  // TODO: MUST BE REFACTORED
    def load_robot_config(self):
        """Load configuration from JSON file"""

        try:
            if os.path.exists(self.ROBOT_CONFIG_FILE):
                with open(self.ROBOT_CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    config = RobotConfig.from_dict(data)
            else:
                config = get_default_config()
                self.save_robot_config_to_file(config.to_dict())

        except Exception as e:
            config = get_default_config()

        return config

    def save_robot_config_to_file(self, config: dict):
        """Save configuration to JSON file and send ROBOT_UPDATE_CONFIG request"""
        try:
            with open(self.ROBOT_CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def load_all_settings(self):
        """Load all settings from their respective JSON files. Use default values if file doesn't exist."""
        for key, settings_obj in self.settings_objects.items():
            filename = self.settings_file_paths.get(key)
            if filename and os.path.exists(filename):
                self.load_settings_from_json(filename, settings_obj)
            else:
                self.logger.debug(f"{filename} not found. Using default values for {key} settings.")
                # Automatically save default settings to the missing file
                self.save_settings_to_json(filename, settings_obj)

    def display_all_settings(self):
        """Utility function to display all settings in the manager."""
        for key, settings_obj in self.settings_objects.items():
            self.logger.debug(f"Settings for {key}:")
            settings_obj.display_settings()

    def load_settings_from_json(self, json_file, settings_obj):
        """
        Load settings from a JSON file into the given settings object.

        Args:
            json_file (str): Path to the JSON file.
            settings_obj (CameraSettings or RobotSettings): The object to load data into.
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)

                self.logger.debug(f"Settings loaded from {json_file} Settings: {settings_data}.")

            if isinstance(settings_obj, CameraSettings):
                # Use the existing _load_from_nested_data method that handles nested structure
                settings_obj._load_from_nested_data(settings_data)

            elif isinstance(settings_obj, RobotSettings):
                settings_obj.set_robot_ip(settings_data.get(RobotSettingKey.IP_ADDRESS.value, "192.168.58.2"))
                settings_obj.set_robot_velocity(settings_data.get(RobotSettingKey.VELOCITY.value, 100))
                settings_obj.set_robot_acceleration(settings_data.get(RobotSettingKey.ACCELERATION.value, 30))
                settings_obj.set_robot_tool(settings_data.get(RobotSettingKey.TOOL.value, 0))
                settings_obj.set_robot_user(settings_data.get(RobotSettingKey.USER.value, 0))

            elif isinstance(settings_obj, GlueSettings):
                settings_obj.set_spray_width(settings_data.get(GlueSettingKey.SPRAY_WIDTH.value, 10))
                settings_obj.set_spraying_height(settings_data.get(GlueSettingKey.SPRAYING_HEIGHT.value, 5))
                settings_obj.set_fan_speed(settings_data.get(GlueSettingKey.FAN_SPEED.value, 100))
                settings_obj.set_time_between_generator_and_glue(
                    settings_data.get(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value, 0.5))
                settings_obj.set_motor_speed(settings_data.get(GlueSettingKey.MOTOR_SPEED.value, 50))
                settings_obj.set_steps_reverse(settings_data.get(GlueSettingKey.REVERSE_DURATION.value, 100))
                settings_obj.set_speed_reverse(settings_data.get(GlueSettingKey.SPEED_REVERSE.value, 20))
                settings_obj.set_rz_angle(settings_data.get(GlueSettingKey.RZ_ANGLE.value, 0))
                settings_obj.set_glue_type(settings_data.get(GlueSettingKey.GLUE_TYPE.value, GlueType.TypeA.value))
                settings_obj.set_generator_timeout(settings_data.get(GlueSettingKey.GENERATOR_TIMEOUT.value, 5))
                settings_obj.set_time_before_motion(settings_data.get(GlueSettingKey.TIME_BEFORE_MOTION.value, 1))
                settings_obj.set_reach_position_threshold(
                    settings_data.get(GlueSettingKey.REACH_START_THRESHOLD.value, 1))
                settings_obj.set_time_before_stop(settings_data.get(GlueSettingKey.TIME_BEFORE_STOP.value, 1))
                settings_obj.set_reach_end_threshold(settings_data.get(GlueSettingKey.REACH_END_THRESHOLD.value, 1))
                settings_obj.set_initial_ramp_speed(settings_data.get(GlueSettingKey.INITIAL_RAMP_SPEED.value, 10))
                settings_obj.set_forward_ramp_steps(settings_data.get(GlueSettingKey.FORWARD_RAMP_STEPS.value, 10))
                settings_obj.set_reverse_ramp_steps(settings_data.get(GlueSettingKey.REVERSE_RAMP_STEPS.value, 10))
                settings_obj.set_initial_ramp_speed_duration(settings_data.get(GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value, 1.0))
                settings_obj.set_spray_on(settings_data.get(GlueSettingKey.SPRAY_ON.value, True))


        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error loading settings from {json_file}: {e}")
            self.logger.info(f"Using default values for {type(settings_obj).__name__}.")

    def save_settings_to_json(self, json_file, settings_obj):
        """
              Save the provided settings object to a JSON file.

              Args:
                  json_file (str): Path to the output JSON file.
                  settings_obj (CameraSettings or RobotSettings or GlueSettings): The object to serialize.
              """
        try:
            # Create the settings directory if it doesn't exist
            os.makedirs(self.settings_dir, exist_ok=True)

            settings_data = {}
            if isinstance(settings_obj, CameraSettings):
                # Use the new to_nested_json method to preserve proper structure
                settings_data = settings_obj.to_nested_json()

            elif isinstance(settings_obj, RobotSettings):
                settings_data = {
                    RobotSettingKey.IP_ADDRESS.value: settings_obj.get_robot_ip(),
                    RobotSettingKey.VELOCITY.value: settings_obj.get_robot_velocity(),
                    RobotSettingKey.ACCELERATION.value: settings_obj.get_robot_acceleration(),
                    RobotSettingKey.TOOL.value: settings_obj.get_robot_tool(),
                    RobotSettingKey.USER.value: settings_obj.get_robot_user()
                }

            elif isinstance(settings_obj, GlueSettings):
                settings_data = {
                    GlueSettingKey.SPRAY_WIDTH.value: settings_obj.get_spray_width(),
                    GlueSettingKey.SPRAYING_HEIGHT.value: settings_obj.get_spraying_height(),
                    GlueSettingKey.FAN_SPEED.value: settings_obj.get_fan_speed(),
                    GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value: settings_obj.get_time_between_generator_and_glue(),
                    GlueSettingKey.MOTOR_SPEED.value: settings_obj.get_motor_speed(),
                    GlueSettingKey.REVERSE_DURATION.value: settings_obj.get_steps_reverse(),
                    GlueSettingKey.SPEED_REVERSE.value: settings_obj.get_speed_reverse(),
                    GlueSettingKey.RZ_ANGLE.value: settings_obj.get_rz_angle(),
                    GlueSettingKey.GENERATOR_TIMEOUT.value: settings_obj.get_generator_timeout(),
                    GlueSettingKey.TIME_BEFORE_MOTION.value: settings_obj.get_time_before_motion(),
                    GlueSettingKey.REACH_START_THRESHOLD.value: settings_obj.get_reach_position_threshold(),
                    GlueSettingKey.TIME_BEFORE_STOP.value: settings_obj.get_time_before_stop(),
                    GlueSettingKey.REACH_END_THRESHOLD.value: settings_obj.get_reach_end_threshold(),
                    GlueSettingKey.REVERSE_RAMP_STEPS.value: settings_obj.get_reverse_ramp_steps(),
                    GlueSettingKey.FORWARD_RAMP_STEPS.value: settings_obj.get_forward_ramp_steps(),
                    GlueSettingKey.INITIAL_RAMP_SPEED.value: settings_obj.get_initial_ramp_speed(),
                    GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value:settings_obj.get_initial_ramp_speed_duration(),
                    GlueSettingKey.SPRAY_ON.value: settings_obj.get_spray_on()
                }

            with open(json_file, 'w') as f:
                json.dump(settings_data, f, indent=4)

            self.logger.info(f"Settings saved to {json_file}.")

        except Exception as e:
            self.logger.error(f"Error saving settings to {json_file}: {e}")

    def updateSettings(self, settings: dict):
        """
               Update the relevant settings object based on the header type.

               Args:
                   settings (dict): A dictionary containing settings data and a "header" field indicating the type.

               Raises:
                   ValueError: If the "header" key is missing or invalid.
               """
        header = settings['header']

        if header == Constants.REQUEST_RESOURCE_ROBOT:
            self.updateRobotSettings(settings)
        elif header == Constants.REQUEST_RESOURCE_CAMERA:
            self.updateCameraSettings(settings)
        elif header == Constants.REQUEST_RESOURCE_GLUE:
            self.updateGlueSettings(settings)
        else:
            raise ValueError("Invalid header")

    def updateGlueSettings(self, settings: dict):
        self.logger.info(f"Updating Glue Settings: {settings}")
        """
             Update glue-specific settings and persist them to file.

             Args:
                 settings (dict): Dictionary containing glue settings data.
             """
        print(settings)
        if GlueSettingKey.SPRAY_WIDTH.value in settings:
            self.glue_settings.set_spray_width(settings.get(GlueSettingKey.SPRAY_WIDTH.value))
        if GlueSettingKey.SPRAYING_HEIGHT.value in settings:
            self.glue_settings.set_spraying_height(settings.get(GlueSettingKey.SPRAYING_HEIGHT.value))
        if GlueSettingKey.FAN_SPEED.value in settings:
            self.glue_settings.set_fan_speed(settings.get(GlueSettingKey.FAN_SPEED.value))
        if GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value in settings:
            self.glue_settings.set_time_between_generator_and_glue(
                settings.get(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value))
        if GlueSettingKey.MOTOR_SPEED.value in settings:
            self.glue_settings.set_motor_speed(settings.get(GlueSettingKey.MOTOR_SPEED.value))
        if GlueSettingKey.REVERSE_DURATION.value in settings:
            self.glue_settings.set_steps_reverse(settings.get(GlueSettingKey.REVERSE_DURATION.value))
        if GlueSettingKey.SPEED_REVERSE.value in settings:
            self.glue_settings.set_speed_reverse(settings.get(GlueSettingKey.SPEED_REVERSE.value))
        if GlueSettingKey.RZ_ANGLE.value in settings:
            self.glue_settings.set_rz_angle(settings.get(GlueSettingKey.RZ_ANGLE.value))
        if GlueSettingKey.GLUE_TYPE.value in settings:
            self.glue_settings.set_glue_type(settings.get(GlueSettingKey.GLUE_TYPE.value))
        if GlueSettingKey.GENERATOR_TIMEOUT.value in settings:
            self.glue_settings.set_generator_timeout(settings.get(GlueSettingKey.GENERATOR_TIMEOUT.value))
        if GlueSettingKey.TIME_BEFORE_MOTION.value in settings:
            self.glue_settings.set_time_before_motion(settings.get(GlueSettingKey.TIME_BEFORE_MOTION.value))
        if GlueSettingKey.REACH_START_THRESHOLD.value in settings:
            self.glue_settings.set_reach_position_threshold(settings.get(GlueSettingKey.REACH_START_THRESHOLD.value))
        if GlueSettingKey.TIME_BEFORE_STOP.value in settings:
            self.glue_settings.set_time_before_stop(settings.get(GlueSettingKey.TIME_BEFORE_STOP.value))
        if GlueSettingKey.REACH_END_THRESHOLD.value in settings:
            self.glue_settings.set_reach_end_threshold(settings.get(GlueSettingKey.REACH_END_THRESHOLD.value))

        if GlueSettingKey.INITIAL_RAMP_SPEED.value in settings:
            self.glue_settings.set_initial_ramp_speed(settings.get(GlueSettingKey.INITIAL_RAMP_SPEED.value))
        if GlueSettingKey.FORWARD_RAMP_STEPS.value in settings:
            self.glue_settings.set_forward_ramp_steps(settings.get(GlueSettingKey.FORWARD_RAMP_STEPS.value))
        if GlueSettingKey.REVERSE_RAMP_STEPS.value in settings:
            self.glue_settings.set_reverse_ramp_steps(settings.get(GlueSettingKey.REVERSE_RAMP_STEPS.value))
        if GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value in settings:
            self.glue_settings.set_initial_ramp_speed_duration(settings.get(GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value))
        if GlueSettingKey.SPRAY_ON.value in settings:
            self.glue_settings.set_spray_on(settings.get(GlueSettingKey.SPRAY_ON.value))

        self.save_settings_to_json(self.settings_file_paths.get("glue_settings"), self.glue_settings)

    def updateRobotSettings(self, settings: dict):
        self.logger.info(f"Updating Robot Settings: {settings}")
        """
             Update robot-specific settings and persist them to file.

             Args:
                 settings (dict): Dictionary containing robot settings data.
             """

        if RobotSettingKey.IP_ADDRESS.value in settings:
            self.robot_settings.set_robot_ip(settings.get(RobotSettingKey.IP_ADDRESS.value))
        if RobotSettingKey.VELOCITY.value in settings:
            self.robot_settings.set_robot_velocity(settings.get(RobotSettingKey.VELOCITY.value))
        if RobotSettingKey.ACCELERATION.value in settings:
            self.robot_settings.set_robot_acceleration(settings.get(RobotSettingKey.ACCELERATION.value))
        if RobotSettingKey.TOOL.value in settings:
            self.robot_settings.set_robot_tool(settings.get(RobotSettingKey.TOOL.value))
        if RobotSettingKey.USER.value in settings:
            self.robot_settings.set_robot_user(settings.get(RobotSettingKey.USER.value))

        self.save_settings_to_json(self.settings_file_paths.get("robot_settings"), self.robot_settings)

    def updateCameraSettings(self, settings: dict):
        self.logger.info(f"Updating Camera Settings: {settings}")
        """
              Update camera-specific settings and persist them to file.

              Args:
                  settings (dict): Dictionary containing camera settings data.
              """
        # Handle both flat and nested input formats
        self._update_camera_settings_from_data(settings)
        self.save_settings_to_json(self.settings_file_paths.get("camera"), self.camera_settings)

    def _update_camera_settings_from_data(self, settings: dict):
        """
        Update camera settings from either flat or nested dictionary format.
        This handles updates from both UI changes and nested JSON structures.
        """
        # Handle flat keys directly in the root
        if CameraSettingKey.INDEX.value in settings:
            self.camera_settings.set_camera_index(settings.get(CameraSettingKey.INDEX.value))
        if CameraSettingKey.WIDTH.value in settings:
            self.camera_settings.set_width(settings.get(CameraSettingKey.WIDTH.value))
        if CameraSettingKey.HEIGHT.value in settings:
            self.camera_settings.set_height(settings.get(CameraSettingKey.HEIGHT.value))
        if CameraSettingKey.SKIP_FRAMES.value in settings:
            self.camera_settings.set_skip_frames(settings.get(CameraSettingKey.SKIP_FRAMES.value))
        if CameraSettingKey.CAPTURE_POS_OFFSET.value in settings:
            self.camera_settings.set_capture_pos_offset(settings.get(CameraSettingKey.CAPTURE_POS_OFFSET.value))
        if CameraSettingKey.THRESHOLD.value in settings:
            self.camera_settings.set_threshold(settings.get(CameraSettingKey.THRESHOLD.value))
        if CameraSettingKey.THRESHOLD_PICKUP_AREA.value in settings:
            self.camera_settings.set_threshold_pickup_area(settings.get(CameraSettingKey.THRESHOLD_PICKUP_AREA.value))
        if CameraSettingKey.EPSILON.value in settings:
            self.camera_settings.set_epsilon(settings.get(CameraSettingKey.EPSILON.value))
        if CameraSettingKey.MIN_CONTOUR_AREA.value in settings:
            self.camera_settings.set_min_contour_area(settings.get(CameraSettingKey.MIN_CONTOUR_AREA.value))
        if CameraSettingKey.MAX_CONTOUR_AREA.value in settings:
            self.camera_settings.set_max_contour_area(settings.get(CameraSettingKey.MAX_CONTOUR_AREA.value))
        if CameraSettingKey.CONTOUR_DETECTION.value in settings:
            self.camera_settings.set_contour_detection(settings.get(CameraSettingKey.CONTOUR_DETECTION.value))
        if CameraSettingKey.DRAW_CONTOURS.value in settings:
            self.camera_settings.set_draw_contours(settings.get(CameraSettingKey.DRAW_CONTOURS.value))

        # Handle nested Preprocessing section
        if "Preprocessing" in settings:
            preprocessing = settings["Preprocessing"]
            if CameraSettingKey.GAUSSIAN_BLUR.value in preprocessing:
                self.camera_settings.set_gaussian_blur(preprocessing.get(CameraSettingKey.GAUSSIAN_BLUR.value))
            if CameraSettingKey.BLUR_KERNEL_SIZE.value in preprocessing:
                self.camera_settings.set_blur_kernel_size(preprocessing.get(CameraSettingKey.BLUR_KERNEL_SIZE.value))
            if CameraSettingKey.THRESHOLD_TYPE.value in preprocessing:
                self.camera_settings.set_threshold_type(preprocessing.get(CameraSettingKey.THRESHOLD_TYPE.value))
            if CameraSettingKey.DILATE_ENABLED.value in preprocessing:
                self.camera_settings.set_dilate_enabled(preprocessing.get(CameraSettingKey.DILATE_ENABLED.value))
            if CameraSettingKey.DILATE_KERNEL_SIZE.value in preprocessing:
                self.camera_settings.set_dilate_kernel_size(
                    preprocessing.get(CameraSettingKey.DILATE_KERNEL_SIZE.value))
            if CameraSettingKey.DILATE_ITERATIONS.value in preprocessing:
                self.camera_settings.set_dilate_iterations(preprocessing.get(CameraSettingKey.DILATE_ITERATIONS.value))
            if CameraSettingKey.ERODE_ENABLED.value in preprocessing:
                self.camera_settings.set_erode_enabled(preprocessing.get(CameraSettingKey.ERODE_ENABLED.value))
            if CameraSettingKey.ERODE_KERNEL_SIZE.value in preprocessing:
                self.camera_settings.set_erode_kernel_size(preprocessing.get(CameraSettingKey.ERODE_KERNEL_SIZE.value))
            if CameraSettingKey.ERODE_ITERATIONS.value in preprocessing:
                self.camera_settings.set_erode_iterations(preprocessing.get(CameraSettingKey.ERODE_ITERATIONS.value))

        # Handle nested Calibration section
        if "Calibration" in settings:
            calibration = settings["Calibration"]
            if CameraSettingKey.CHESSBOARD_WIDTH.value in calibration:
                self.camera_settings.set_chessboard_width(calibration.get(CameraSettingKey.CHESSBOARD_WIDTH.value))
            if CameraSettingKey.CHESSBOARD_HEIGHT.value in calibration:
                self.camera_settings.set_chessboard_height(calibration.get(CameraSettingKey.CHESSBOARD_HEIGHT.value))
            if CameraSettingKey.SQUARE_SIZE_MM.value in calibration:
                self.camera_settings.set_square_size_mm(calibration.get(CameraSettingKey.SQUARE_SIZE_MM.value))
            if "Skip frames" in calibration:  # Special mapping for nested calibration skip frames
                self.camera_settings.set_calibration_skip_frames(calibration.get("Skip frames"))
            if CameraSettingKey.CAPTURE_POS_OFFSET.value in calibration:
                self.camera_settings.set_capture_pos_offset(calibration.get(CameraSettingKey.CAPTURE_POS_OFFSET.value))

        # Handle nested Brightness Control section
        if "Brightness Control" in settings:
            brightness = settings["Brightness Control"]
            if CameraSettingKey.BRIGHTNESS_AUTO.value in brightness:
                self.camera_settings.set_brightness_auto(brightness.get(CameraSettingKey.BRIGHTNESS_AUTO.value))
            if CameraSettingKey.BRIGHTNESS_KP.value in brightness:
                self.camera_settings.set_brightness_kp(brightness.get(CameraSettingKey.BRIGHTNESS_KP.value))
            if CameraSettingKey.BRIGHTNESS_KI.value in brightness:
                self.camera_settings.set_brightness_ki(brightness.get(CameraSettingKey.BRIGHTNESS_KI.value))
            if CameraSettingKey.BRIGHTNESS_KD.value in brightness:
                self.camera_settings.set_brightness_kd(brightness.get(CameraSettingKey.BRIGHTNESS_KD.value))
            if CameraSettingKey.TARGET_BRIGHTNESS.value in brightness:
                self.camera_settings.set_target_brightness(brightness.get(CameraSettingKey.TARGET_BRIGHTNESS.value))

        # Handle nested Aruco section
        if "Aruco" in settings:
            aruco = settings["Aruco"]
            if "Enable detection" in aruco:  # Special mapping for nested ArUco enabled
                self.camera_settings.set_aruco_enabled(aruco.get("Enable detection"))
            if CameraSettingKey.ARUCO_DICTIONARY.value in aruco:
                self.camera_settings.set_aruco_dictionary(aruco.get(CameraSettingKey.ARUCO_DICTIONARY.value))
            if CameraSettingKey.ARUCO_FLIP_IMAGE.value in aruco:
                self.camera_settings.set_aruco_flip_image(aruco.get(CameraSettingKey.ARUCO_FLIP_IMAGE.value))

        # Handle flat keys that might be from UI updates (fallback for direct enum-based updates)
        preprocessing_keys = [
            CameraSettingKey.GAUSSIAN_BLUR, CameraSettingKey.BLUR_KERNEL_SIZE, CameraSettingKey.THRESHOLD_TYPE,
            CameraSettingKey.DILATE_ENABLED, CameraSettingKey.DILATE_KERNEL_SIZE, CameraSettingKey.DILATE_ITERATIONS,
            CameraSettingKey.ERODE_ENABLED, CameraSettingKey.ERODE_KERNEL_SIZE, CameraSettingKey.ERODE_ITERATIONS
        ]

        calibration_keys = [
            CameraSettingKey.CHESSBOARD_WIDTH, CameraSettingKey.CHESSBOARD_HEIGHT,
            CameraSettingKey.SQUARE_SIZE_MM, CameraSettingKey.CALIBRATION_SKIP_FRAMES
        ]

        brightness_keys = [
            CameraSettingKey.BRIGHTNESS_AUTO, CameraSettingKey.BRIGHTNESS_KP, CameraSettingKey.BRIGHTNESS_KI,
            CameraSettingKey.BRIGHTNESS_KD, CameraSettingKey.TARGET_BRIGHTNESS
        ]

        aruco_keys = [
            CameraSettingKey.ARUCO_ENABLED, CameraSettingKey.ARUCO_DICTIONARY, CameraSettingKey.ARUCO_FLIP_IMAGE
        ]

        # Handle flat updates for preprocessing settings
        for key in preprocessing_keys:
            if key.value in settings:
                if key == CameraSettingKey.GAUSSIAN_BLUR:
                    self.camera_settings.set_gaussian_blur(settings.get(key.value))
                elif key == CameraSettingKey.BLUR_KERNEL_SIZE:
                    self.camera_settings.set_blur_kernel_size(settings.get(key.value))
                elif key == CameraSettingKey.THRESHOLD_TYPE:
                    self.camera_settings.set_threshold_type(settings.get(key.value))
                elif key == CameraSettingKey.DILATE_ENABLED:
                    self.camera_settings.set_dilate_enabled(settings.get(key.value))
                elif key == CameraSettingKey.DILATE_KERNEL_SIZE:
                    self.camera_settings.set_dilate_kernel_size(settings.get(key.value))
                elif key == CameraSettingKey.DILATE_ITERATIONS:
                    self.camera_settings.set_dilate_iterations(settings.get(key.value))
                elif key == CameraSettingKey.ERODE_ENABLED:
                    self.camera_settings.set_erode_enabled(settings.get(key.value))
                elif key == CameraSettingKey.ERODE_KERNEL_SIZE:
                    self.camera_settings.set_erode_kernel_size(settings.get(key.value))
                elif key == CameraSettingKey.ERODE_ITERATIONS:
                    self.camera_settings.set_erode_iterations(settings.get(key.value))

        # Handle flat updates for calibration settings
        for key in calibration_keys:
            if key.value in settings:
                if key == CameraSettingKey.CHESSBOARD_WIDTH:
                    self.camera_settings.set_chessboard_width(settings.get(key.value))
                elif key == CameraSettingKey.CHESSBOARD_HEIGHT:
                    self.camera_settings.set_chessboard_height(settings.get(key.value))
                elif key == CameraSettingKey.SQUARE_SIZE_MM:
                    self.camera_settings.set_square_size_mm(settings.get(key.value))
                elif key == CameraSettingKey.CALIBRATION_SKIP_FRAMES:
                    self.camera_settings.set_calibration_skip_frames(settings.get(key.value))
                elif key == CameraSettingKey.CAPTURE_POS_OFFSET:
                    self.camera_settings.set_capture_pos_offset(settings.get(key.value))

        # Handle flat updates for brightness settings
        for key in brightness_keys:
            if key.value in settings:
                if key == CameraSettingKey.BRIGHTNESS_AUTO:
                    self.camera_settings.set_brightness_auto(settings.get(key.value))
                elif key == CameraSettingKey.BRIGHTNESS_KP:
                    self.camera_settings.set_brightness_kp(settings.get(key.value))
                elif key == CameraSettingKey.BRIGHTNESS_KI:
                    self.camera_settings.set_brightness_ki(settings.get(key.value))
                elif key == CameraSettingKey.BRIGHTNESS_KD:
                    self.camera_settings.set_brightness_kd(settings.get(key.value))
                elif key == CameraSettingKey.TARGET_BRIGHTNESS:
                    self.camera_settings.set_target_brightness(settings.get(key.value))

        # Handle flat updates for ArUco settings
        for key in aruco_keys:
            if key.value in settings:
                if key == CameraSettingKey.ARUCO_ENABLED:
                    self.camera_settings.set_aruco_enabled(settings.get(key.value))
                elif key == CameraSettingKey.ARUCO_DICTIONARY:
                    self.camera_settings.set_aruco_dictionary(settings.get(key.value))
                elif key == CameraSettingKey.ARUCO_FLIP_IMAGE:
                    self.camera_settings.set_aruco_flip_image(settings.get(key.value))
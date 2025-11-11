import json
import os

from modules.shared.shared.settings.conreateSettings.enums.CameraSettingKey import CameraSettingKey
from src.backend.GlueDispensingApplication.utils.custom_logging import log_if_enabled, LoggingLevel
from libs.plvision.PLVision.Camera import Camera

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'config.json') # this is just a default path if not path provided

class SettingsManager:
    def __init__(self):
        pass

    def loadSettings(self, configFilePath):
        if configFilePath is None:
            configFilePath = CONFIG_FILE_PATH
        with open(configFilePath) as f:
            data = json.load(f)
        return data

    def updateSettings(self, vision_system, settings: dict,logging_enabled:bool,logger) -> tuple[bool, str]:
        """
        Updates the camera settings using the CameraSettings object.
        """
        try:
            # Update the camera_settings object
            success, message = vision_system.camera_settings.updateSettings(settings)

            if not success:
                return False, message

            # Update the brightness controller with new PID values
            vision_system.brightnessController.Kp = vision_system.camera_settings.get_brightness_kp()
            vision_system.brightnessController.Ki = vision_system.camera_settings.get_brightness_ki()
            vision_system.brightnessController.Kd = vision_system.camera_settings.get_brightness_kd()
            vision_system.brightnessController.target = vision_system.camera_settings.get_target_brightness()

            # Update camera resolution if changed
            if (CameraSettingKey.WIDTH.value in settings or
                    CameraSettingKey.HEIGHT.value in settings or
                    CameraSettingKey.INDEX.value in settings):
                # Reinitialize camera with new settings
                vision_system.camera = Camera(
                    vision_system.camera_settings.get_camera_index(),
                    vision_system.camera_settings.get_camera_width(),
                    vision_system.camera_settings.get_camera_height()
                )

            log_if_enabled(enabled=logging_enabled,
                           logger=logger,
                           level=LoggingLevel.INFO,
                           message=f"Settings updated successfully",
                           broadcast_to_ui=False)
            return True, "Settings updated successfully"

        except Exception as e:
            return False, f"Error updating settings: {str(e)}"
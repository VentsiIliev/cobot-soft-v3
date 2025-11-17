"""
Glue Application Settings Handler

This module provides the settings handler for the glue dispensing application,
implementing the ApplicationSettingsHandler interface to manage glue-specific
settings operations.
"""

import json
import os
import logging
from typing import Dict, Any
from core.application.interfaces.application_settings_interface import ApplicationSettingsHandler
from applications.glue_dispensing_application.settings.GlueSettings import GlueSettings
from applications.glue_dispensing_application.settings.enums.GlueSettingKey import GlueSettingKey
from backend.system.utils import PathResolver

class GlueSettingsHandler(ApplicationSettingsHandler):
    """
    Handler for glue application settings operations.
    
    This class manages the persistence, validation, and retrieval of
    glue-specific settings for the glue dispensing application.
    """
    
    def __init__(self, storage_path: str = None):
        """
        Initialize the glue settings handler.
        
        Args:
            storage_path: Custom path for storing settings files
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Default storage path if not provided
        if storage_path is None:
            self.settings_file = PathResolver.get_settings_file_path("glue_settings.json")
        else:
            self.settings_file = os.path.join(storage_path, "glue_settings.json")
        print(f"GLUE SETTINGS FILE PATH: {self.settings_file}")
        # Initialize glue settings
        self.glue_settings = GlueSettings()
        self._load_settings()
    
    def handle_get_settings(self) -> Dict[str, Any]:
        """
        Handle GET request for glue application settings.
        
        Returns:
            Dict[str, Any]: Current glue settings data
        """
        try:
            return self.glue_settings.to_dict()
        except Exception as e:
            self.logger.error(f"Error getting glue settings: {e}")
            return {}
    
    def handle_set_settings(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """
        Handle SET request for glue application settings.
        
        Args:
            settings: New glue settings data
            
        Returns:
            tuple[bool, str]: (success, message)
        """
        try:
            # Validate settings first
            is_valid, error_message = self.glue_settings.validate_settings(settings)
            if not is_valid:
                return False, f"Validation failed: {error_message}"
            
            # Update settings
            self._update_settings(settings)
            
            # Save to file
            success, message = self._save_settings()
            if not success:
                return False, f"Failed to save settings: {message}"
            
            self.logger.info("Glue settings updated successfully")
            return True, "Glue settings saved successfully"
            
        except Exception as e:
            self.logger.error(f"Error setting glue settings: {e}")
            return False, f"Error updating settings: {str(e)}"
    
    def get_settings_type(self) -> str:
        """
        Get the settings type this handler manages.
        
        Returns:
            str: Settings type identifier
        """
        return "glue"
    
    def get_settings_object(self) -> GlueSettings:
        """
        Get the glue settings object.
        
        Returns:
            GlueSettings: The settings object instance
        """
        return self.glue_settings
    
    def _load_settings(self) -> None:
        """Load settings from JSON file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                
                self.logger.debug(f"Loaded glue settings from {self.settings_file}")
                self.glue_settings.update_from_dict(settings_data)
            else:
                self.logger.info(f"Glue settings file not found at {self.settings_file}. Using defaults.")
                self._save_settings()  # Create file with defaults

        except Exception as e:
            raise ValueError(f"Failed to load glue settings: {e}") from e
            # self.logger.error(f"Error loading glue settings: {e}")
            # self.logger.info("Using default glue settings")
    
    def _save_settings(self) -> tuple[bool, str]:
        """
        Save current settings to JSON file.
        
        Returns:
            tuple[bool, str]: (success, message)
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            # Get settings data
            settings_data = self._get_settings_for_save()
            
            # Write to file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4)
            
            self.logger.info(f"Glue settings saved to {self.settings_file}")
            return True, "Settings saved successfully"
            
        except Exception as e:
            self.logger.error(f"Error saving glue settings: {e}")
            return False, str(e)
    
    def _get_settings_for_save(self) -> Dict[str, Any]:
        """Get settings data formatted for saving."""
        return {
            GlueSettingKey.SPRAY_WIDTH.value: self.glue_settings.get_spray_width(),
            GlueSettingKey.SPRAYING_HEIGHT.value: self.glue_settings.get_spraying_height(),
            GlueSettingKey.FAN_SPEED.value: self.glue_settings.get_fan_speed(),
            GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value: self.glue_settings.get_time_between_generator_and_glue(),
            GlueSettingKey.MOTOR_SPEED.value: self.glue_settings.get_motor_speed(),
            GlueSettingKey.REVERSE_DURATION.value: self.glue_settings.get_steps_reverse(),
            GlueSettingKey.SPEED_REVERSE.value: self.glue_settings.get_speed_reverse(),
            GlueSettingKey.RZ_ANGLE.value: self.glue_settings.get_rz_angle(),
            GlueSettingKey.GLUE_TYPE.value: self.glue_settings.get_glue_type(),
            GlueSettingKey.GENERATOR_TIMEOUT.value: self.glue_settings.get_generator_timeout(),
            GlueSettingKey.TIME_BEFORE_MOTION.value: self.glue_settings.get_time_before_motion(),
            GlueSettingKey.REACH_START_THRESHOLD.value: self.glue_settings.get_reach_position_threshold(),
            GlueSettingKey.TIME_BEFORE_STOP.value: self.glue_settings.get_time_before_stop(),
            GlueSettingKey.REACH_END_THRESHOLD.value: self.glue_settings.get_reach_end_threshold(),
            GlueSettingKey.INITIAL_RAMP_SPEED.value: self.glue_settings.get_initial_ramp_speed(),
            GlueSettingKey.FORWARD_RAMP_STEPS.value: self.glue_settings.get_forward_ramp_steps(),
            GlueSettingKey.REVERSE_RAMP_STEPS.value: self.glue_settings.get_reverse_ramp_steps(),
            GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value: self.glue_settings.get_initial_ramp_speed_duration(),
            GlueSettingKey.SPRAY_ON.value: self.glue_settings.get_spray_on()
        }
    
    def _update_settings(self, settings: Dict[str, Any]) -> None:
        """Update individual settings values."""
        for key, value in settings.items():
            if key == 'header':  # Skip API header
                continue
                
            # Update using specific setter methods
            if key == GlueSettingKey.SPRAY_WIDTH.value:
                self.glue_settings.set_spray_width(value)
            elif key == GlueSettingKey.SPRAYING_HEIGHT.value:
                self.glue_settings.set_spraying_height(value)
            elif key == GlueSettingKey.FAN_SPEED.value:
                self.glue_settings.set_fan_speed(value)
            elif key == GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value:
                self.glue_settings.set_time_between_generator_and_glue(value)
            elif key == GlueSettingKey.MOTOR_SPEED.value:
                self.glue_settings.set_motor_speed(value)
            elif key == GlueSettingKey.REVERSE_DURATION.value:
                self.glue_settings.set_steps_reverse(value)
            elif key == GlueSettingKey.SPEED_REVERSE.value:
                self.glue_settings.set_speed_reverse(value)
            elif key == GlueSettingKey.RZ_ANGLE.value:
                self.glue_settings.set_rz_angle(value)
            elif key == GlueSettingKey.GLUE_TYPE.value:
                self.glue_settings.set_glue_type(value)
            elif key == GlueSettingKey.GENERATOR_TIMEOUT.value:
                self.glue_settings.set_generator_timeout(value)
            elif key == GlueSettingKey.TIME_BEFORE_MOTION.value:
                self.glue_settings.set_time_before_motion(value)
            elif key == GlueSettingKey.REACH_START_THRESHOLD.value:
                self.glue_settings.set_reach_position_threshold(value)
            elif key == GlueSettingKey.TIME_BEFORE_STOP.value:
                self.glue_settings.set_time_before_stop(value)
            elif key == GlueSettingKey.REACH_END_THRESHOLD.value:
                self.glue_settings.set_reach_end_threshold(value)
            elif key == GlueSettingKey.INITIAL_RAMP_SPEED.value:
                self.glue_settings.set_initial_ramp_speed(value)
            elif key == GlueSettingKey.FORWARD_RAMP_STEPS.value:
                self.glue_settings.set_forward_ramp_steps(value)
            elif key == GlueSettingKey.REVERSE_RAMP_STEPS.value:
                self.glue_settings.set_reverse_ramp_steps(value)
            elif key == GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value:
                self.glue_settings.set_initial_ramp_speed_duration(value)
            elif key == GlueSettingKey.SPRAY_ON.value:
                self.glue_settings.set_spray_on(value)
            else:
                self.logger.warning(f"Unknown glue setting key: {key}")
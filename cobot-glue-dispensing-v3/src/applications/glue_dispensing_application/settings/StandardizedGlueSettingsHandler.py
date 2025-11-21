"""
Standardized Glue Settings Handler

This is the updated glue settings handler that uses the new standardized
base class, providing consistent behavior and eliminating the parameter
passing bugs we encountered earlier.
"""

import logging
from typing import Dict, Any, Tuple

from backend.system.settings.BaseApplicationSettingsHandler import BaseApplicationSettingsHandler
from applications.glue_dispensing_application.settings.GlueSettings import GlueSettings
from applications.glue_dispensing_application.settings.enums.GlueSettingKey import GlueSettingKey


class StandardizedGlueSettingsHandler(BaseApplicationSettingsHandler):
    """
    Standardized handler for glue application settings.
    
    This handler uses the new base class to provide:
    - Automatic path resolution using ApplicationStorageResolver
    - Consistent error handling and validation
    - Transaction-like save operations with rollback
    - Proper logging and debugging
    """
    
    def __init__(self):
        """Initialize the standardized glue settings handler."""
        super().__init__(
            app_name="glue_dispensing_application", 
            settings_type="glue_settings"
        )
    
    def create_default_settings(self) -> GlueSettings:
        """
        Create and return default glue settings.
        
        Returns:
            GlueSettings: Default glue settings object
        """
        return GlueSettings()
    
    def validate_settings_data(self, settings_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate glue settings data.
        
        Args:
            settings_data: Dictionary containing settings to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Use the existing GlueSettings validation
            temp_settings = GlueSettings()
            return temp_settings.validate_settings(settings_data)
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def update_settings_object(self, settings_data: Dict[str, Any]) -> None:
        """
        Update the glue settings object with new data.
        
        Args:
            settings_data: Dictionary containing new settings values
        """
        if self._settings_object is None:
            self._settings_object = self.create_default_settings()
        
        # Use the existing update_from_dict method
        self._settings_object.update_from_dict(settings_data)
    
    def get_settings_dict(self) -> Dict[str, Any]:
        """
        Get the current glue settings as a dictionary.
        
        Returns:
            Dict[str, Any]: Current glue settings as dictionary
        """
        if self._settings_object is None:
            self._settings_object = self.create_default_settings()
        
        # Use the standardized format for saving
        return {
            GlueSettingKey.SPRAY_WIDTH.value: self._settings_object.get_spray_width(),
            GlueSettingKey.SPRAYING_HEIGHT.value: self._settings_object.get_spraying_height(),
            GlueSettingKey.FAN_SPEED.value: self._settings_object.get_fan_speed(),
            GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value: self._settings_object.get_time_between_generator_and_glue(),
            GlueSettingKey.MOTOR_SPEED.value: self._settings_object.get_motor_speed(),
            GlueSettingKey.REVERSE_DURATION.value: self._settings_object.get_steps_reverse(),
            GlueSettingKey.SPEED_REVERSE.value: self._settings_object.get_speed_reverse(),
            GlueSettingKey.RZ_ANGLE.value: self._settings_object.get_rz_angle(),
            GlueSettingKey.GLUE_TYPE.value: self._settings_object.get_glue_type(),
            GlueSettingKey.GENERATOR_TIMEOUT.value: self._settings_object.get_generator_timeout(),
            GlueSettingKey.TIME_BEFORE_MOTION.value: self._settings_object.get_time_before_motion(),
            GlueSettingKey.REACH_START_THRESHOLD.value: self._settings_object.get_reach_position_threshold(),
            GlueSettingKey.TIME_BEFORE_STOP.value: self._settings_object.get_time_before_stop(),
            GlueSettingKey.REACH_END_THRESHOLD.value: self._settings_object.get_reach_end_threshold(),
            GlueSettingKey.INITIAL_RAMP_SPEED.value: self._settings_object.get_initial_ramp_speed(),
            GlueSettingKey.FORWARD_RAMP_STEPS.value: self._settings_object.get_forward_ramp_steps(),
            GlueSettingKey.REVERSE_RAMP_STEPS.value: self._settings_object.get_reverse_ramp_steps(),
            GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value: self._settings_object.get_initial_ramp_speed_duration(),
            GlueSettingKey.SPRAY_ON.value: self._settings_object.get_spray_on()
        }
    
    def get_glue_settings(self) -> GlueSettings:
        """
        Get the glue settings object directly.
        
        Returns:
            GlueSettings: The current glue settings object
        """
        return self.get_settings_object()
    
    def update_individual_setting(self, setting_key: str, value: Any) -> Tuple[bool, str]:
        """
        Update a single setting value.
        
        Args:
            setting_key: The setting key to update
            value: The new value
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Create a settings dict with just this one change
            settings_data = {setting_key: value}
            return self.handle_set_settings(settings_data)
        except Exception as e:
            self.logger.error(f"Error updating individual setting {setting_key}: {e}")
            return False, f"Failed to update {setting_key}: {str(e)}"
    
    def get_setting_value(self, setting_key: str) -> Any:
        """
        Get a single setting value.
        
        Args:
            setting_key: The setting key to retrieve
            
        Returns:
            Any: The setting value, or None if not found
        """
        try:
            settings_dict = self.get_settings_dict()
            return settings_dict.get(setting_key)
        except Exception as e:
            self.logger.error(f"Error getting setting {setting_key}: {e}")
            return None
    
    def reset_to_defaults(self) -> Tuple[bool, str]:
        """
        Reset all settings to their default values.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            default_settings = self.create_default_settings()
            default_dict = {
                GlueSettingKey.SPRAY_WIDTH.value: default_settings.get_spray_width(),
                GlueSettingKey.SPRAYING_HEIGHT.value: default_settings.get_spraying_height(),
                GlueSettingKey.FAN_SPEED.value: default_settings.get_fan_speed(),
                GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value: default_settings.get_time_between_generator_and_glue(),
                GlueSettingKey.MOTOR_SPEED.value: default_settings.get_motor_speed(),
                GlueSettingKey.REVERSE_DURATION.value: default_settings.get_steps_reverse(),
                GlueSettingKey.SPEED_REVERSE.value: default_settings.get_speed_reverse(),
                GlueSettingKey.RZ_ANGLE.value: default_settings.get_rz_angle(),
                GlueSettingKey.GLUE_TYPE.value: default_settings.get_glue_type(),
                GlueSettingKey.GENERATOR_TIMEOUT.value: default_settings.get_generator_timeout(),
                GlueSettingKey.TIME_BEFORE_MOTION.value: default_settings.get_time_before_motion(),
                GlueSettingKey.REACH_START_THRESHOLD.value: default_settings.get_reach_position_threshold(),
                GlueSettingKey.TIME_BEFORE_STOP.value: default_settings.get_time_before_stop(),
                GlueSettingKey.REACH_END_THRESHOLD.value: default_settings.get_reach_end_threshold(),
                GlueSettingKey.INITIAL_RAMP_SPEED.value: default_settings.get_initial_ramp_speed(),
                GlueSettingKey.FORWARD_RAMP_STEPS.value: default_settings.get_forward_ramp_steps(),
                GlueSettingKey.REVERSE_RAMP_STEPS.value: default_settings.get_reverse_ramp_steps(),
                GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value: default_settings.get_initial_ramp_speed_duration(),
                GlueSettingKey.SPRAY_ON.value: default_settings.get_spray_on()
            }
            
            return self.handle_set_settings(default_dict)
            
        except Exception as e:
            self.logger.error(f"Error resetting glue settings to defaults: {e}")
            return False, f"Failed to reset to defaults: {str(e)}"
from typing import Dict, Any, List
from modules.shared.shared.settings.BaseSettings import Settings
from robot_application.interfaces.application_settings_interface import ApplicationSettingsInterface
from robot_application.glue_dispensing_application.settings.enums.GlueSettingKey import GlueSettingKey
from robot_application.glue_dispensing_application.settings.GlueConstants import (
    SETTINGS_GLUE_GET, SETTINGS_GLUE_SET, SETTINGS_GLUE_GET_LEGACY, SETTINGS_GLUE_SET_LEGACY
)
from robot_application.glue_dispensing_application.tools.GlueCell import GlueType


class GlueSettings(Settings, ApplicationSettingsInterface):
    """
    Glue dispensing application-specific settings.
    
    This class handles all settings related to glue dispensing operations,
    including spray parameters, pump settings, timing, and process control.
    """
    
    def __init__(self, data: dict = None):
        super().__init__()
        
        # Set default values
        self.set_value(GlueSettingKey.SPRAY_WIDTH.value, 5)
        self.set_value(GlueSettingKey.SPRAYING_HEIGHT.value, 10)
        self.set_value(GlueSettingKey.FAN_SPEED.value, 50)
        self.set_value(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value, 1)
        self.set_value(GlueSettingKey.MOTOR_SPEED.value, 10000)
        self.set_value(GlueSettingKey.REVERSE_DURATION.value, 1)
        self.set_value(GlueSettingKey.SPEED_REVERSE.value, 1000)
        self.set_value(GlueSettingKey.RZ_ANGLE.value, 0)
        self.set_value(GlueSettingKey.GLUE_TYPE.value, GlueType.TypeA.value)
        self.set_value(GlueSettingKey.GENERATOR_TIMEOUT.value, 5.0)
        self.set_value(GlueSettingKey.TIME_BEFORE_MOTION.value, 1.0)
        self.set_value(GlueSettingKey.TIME_BEFORE_STOP.value, 1)
        self.set_value(GlueSettingKey.REACH_START_THRESHOLD.value, 1)
        self.set_value(GlueSettingKey.REACH_END_THRESHOLD.value, 1)
        self.set_value(GlueSettingKey.INITIAL_RAMP_SPEED.value, 5000)
        self.set_value(GlueSettingKey.FORWARD_RAMP_STEPS.value, 1)
        self.set_value(GlueSettingKey.REVERSE_RAMP_STEPS.value, 1)
        self.set_value(GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value, 1)
        self.set_value(GlueSettingKey.SPRAY_ON.value, True)

        # Update settings with provided data
        if data:
            for key, value in data.items():
                self.set_value(key, value)

    # ApplicationSettingsInterface implementation
    def get_settings_type_name(self) -> str:
        """Get the unique name for this settings type."""
        return "glue"
    
    def get_default_values(self) -> Dict[str, Any]:
        """Get default settings values for glue dispensing."""
        return {
            GlueSettingKey.SPRAY_WIDTH.value: 5,
            GlueSettingKey.SPRAYING_HEIGHT.value: 10,
            GlueSettingKey.FAN_SPEED.value: 50,
            GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value: 1,
            GlueSettingKey.MOTOR_SPEED.value: 10000,
            GlueSettingKey.REVERSE_DURATION.value: 1,
            GlueSettingKey.SPEED_REVERSE.value: 1000,
            GlueSettingKey.RZ_ANGLE.value: 0,
            GlueSettingKey.GLUE_TYPE.value: GlueType.TypeA.value,
            GlueSettingKey.GENERATOR_TIMEOUT.value: 5.0,
            GlueSettingKey.TIME_BEFORE_MOTION.value: 1.0,
            GlueSettingKey.TIME_BEFORE_STOP.value: 1,
            GlueSettingKey.REACH_START_THRESHOLD.value: 1,
            GlueSettingKey.REACH_END_THRESHOLD.value: 1,
            GlueSettingKey.INITIAL_RAMP_SPEED.value: 5000,
            GlueSettingKey.FORWARD_RAMP_STEPS.value: 1,
            GlueSettingKey.REVERSE_RAMP_STEPS.value: 1,
            GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value: 1,
            GlueSettingKey.SPRAY_ON.value: True,
        }
    
    def validate_settings(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """Validate glue settings data."""
        try:
            for key, value in settings.items():
                # Skip validation for 'header' key used in API
                if key == 'header':
                    continue
                    
                # Validate that key is a valid glue setting
                valid_keys = [setting_key.value for setting_key in GlueSettingKey]
                if key not in valid_keys:
                    return False, f"Invalid glue setting key: {key}"
                
                # Type-specific validations
                if key == GlueSettingKey.SPRAY_WIDTH.value and not isinstance(value, (int, float)):
                    return False, f"Spray width must be numeric, got: {type(value).__name__}"
                
                if key == GlueSettingKey.FAN_SPEED.value and not (0 <= value <= 100):
                    return False, f"Fan speed must be between 0 and 100, got: {value}"
                
                if key == GlueSettingKey.GLUE_TYPE.value:
                    valid_types = [glue_type.value for glue_type in GlueType]
                    if value not in valid_types:
                        return False, f"Invalid glue type: {value}, valid types: {valid_types}"
                
                # Add more validations as needed
                
            return True, ""
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def update_from_dict(self, settings: Dict[str, Any]) -> None:
        """Update settings from a dictionary."""
        for key, value in settings.items():
            if key != 'header':  # Skip API header
                self.set_value(key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary format."""
        return self.toDict()
    
    def get_supported_endpoints(self) -> List[str]:
        """Get list of API endpoints this settings type supports."""
        return [
            SETTINGS_GLUE_GET,
            SETTINGS_GLUE_SET,
            SETTINGS_GLUE_GET_LEGACY,
            SETTINGS_GLUE_SET_LEGACY,
        ]

    # Glue-specific methods (existing interface)
    def set_spray_width(self, sprayWidth):
        """Set the spray width."""
        self.set_value(GlueSettingKey.SPRAY_WIDTH.value, sprayWidth)

    def get_spray_width(self):
        """Get the spray width."""
        return self.get_value(GlueSettingKey.SPRAY_WIDTH.value)

    def set_spraying_height(self, sprayingHeight):
        """Set the spraying height."""
        self.set_value(GlueSettingKey.SPRAYING_HEIGHT.value, sprayingHeight)

    def get_spraying_height(self):
        """Get the spraying height."""
        return self.get_value(GlueSettingKey.SPRAYING_HEIGHT.value)

    def set_fan_speed(self, fanSpeed):
        """Set the fan speed."""
        self.set_value(GlueSettingKey.FAN_SPEED.value, fanSpeed)

    def get_fan_speed(self):
        """Get the fan speed."""
        return self.get_value(GlueSettingKey.FAN_SPEED.value)

    def set_time_between_generator_and_glue(self, time):
        """Set the time between generator activation and glue dispensing."""
        self.set_value(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value, time)

    def get_time_between_generator_and_glue(self):
        """Get the time between generator activation and glue dispensing."""
        return self.get_value(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value)

    def set_motor_speed(self, motorSpeed):
        """Set the motor speed."""
        self.set_value(GlueSettingKey.MOTOR_SPEED.value, motorSpeed)

    def get_motor_speed(self):
        """Get the motor speed."""
        return self.get_value(GlueSettingKey.MOTOR_SPEED.value)

    def set_steps_reverse(self, stepsReverse):
        """Set the reverse duration."""
        self.set_value(GlueSettingKey.REVERSE_DURATION.value, stepsReverse)

    def get_steps_reverse(self):
        """Get the reverse duration."""
        return self.get_value(GlueSettingKey.REVERSE_DURATION.value)

    def set_speed_reverse(self, speedReverse):
        """Set the reverse speed."""
        self.set_value(GlueSettingKey.SPEED_REVERSE.value, speedReverse)

    def get_speed_reverse(self):
        """Get the reverse speed."""
        return self.get_value(GlueSettingKey.SPEED_REVERSE.value)

    def set_rz_angle(self, rzAngle):
        """Set the RZ angle."""
        self.set_value(GlueSettingKey.RZ_ANGLE.value, rzAngle)

    def get_rz_angle(self):
        """Get the RZ angle."""
        return self.get_value(GlueSettingKey.RZ_ANGLE.value)

    def set_glue_type(self, glueType):
        """Set the glue type."""
        self.set_value(GlueSettingKey.GLUE_TYPE.value, glueType)

    def get_glue_type(self):
        """Get the glue type."""
        return self.get_value(GlueSettingKey.GLUE_TYPE.value)

    def set_generator_timeout(self, timeout):
        """Set the generator timeout."""
        self.set_value(GlueSettingKey.GENERATOR_TIMEOUT.value, timeout)

    def get_generator_timeout(self):
        """Get the generator timeout."""
        return self.get_value(GlueSettingKey.GENERATOR_TIMEOUT.value)

    def set_time_before_motion(self, time):
        """Set the time before motion."""
        self.set_value(GlueSettingKey.TIME_BEFORE_MOTION.value, time)

    def get_time_before_motion(self):
        """Get the time before motion."""
        return self.get_value(GlueSettingKey.TIME_BEFORE_MOTION.value)

    def set_reach_position_threshold(self, threshold):
        """Set the reach position threshold."""
        self.set_value(GlueSettingKey.REACH_START_THRESHOLD.value, threshold)

    def get_reach_position_threshold(self):
        """Get the reach position threshold."""
        return self.get_value(GlueSettingKey.REACH_START_THRESHOLD.value)

    def set_time_before_stop(self, time):
        """Set the time before stop."""
        self.set_value(GlueSettingKey.TIME_BEFORE_STOP.value, time)

    def get_time_before_stop(self):
        """Get the time before stop."""
        return self.get_value(GlueSettingKey.TIME_BEFORE_STOP.value)

    def set_reach_end_threshold(self, threshold):
        """Set the reach end threshold."""
        self.set_value(GlueSettingKey.REACH_END_THRESHOLD.value, threshold)

    def get_reach_end_threshold(self):
        """Get the reach end threshold."""
        return self.get_value(GlueSettingKey.REACH_END_THRESHOLD.value)

    def set_initial_ramp_speed(self, speed):
        """Set the initial ramp speed."""
        self.set_value(GlueSettingKey.INITIAL_RAMP_SPEED.value, speed)

    def get_initial_ramp_speed(self):
        """Get the initial ramp speed."""
        return self.get_value(GlueSettingKey.INITIAL_RAMP_SPEED.value)

    def set_forward_ramp_steps(self, steps):
        """Set the forward ramp steps."""
        self.set_value(GlueSettingKey.FORWARD_RAMP_STEPS.value, steps)

    def get_forward_ramp_steps(self):
        """Get the forward ramp steps."""
        return self.get_value(GlueSettingKey.FORWARD_RAMP_STEPS.value)

    def set_reverse_ramp_steps(self, steps):
        """Set the reverse ramp steps."""
        self.set_value(GlueSettingKey.REVERSE_RAMP_STEPS.value, steps)

    def get_reverse_ramp_steps(self):
        """Get the reverse ramp steps."""
        return self.get_value(GlueSettingKey.REVERSE_RAMP_STEPS.value)

    def set_initial_ramp_speed_duration(self, duration):
        """Set the initial ramp speed duration."""
        self.set_value(GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value, duration)

    def get_initial_ramp_speed_duration(self):
        """Get the initial ramp speed duration."""
        return self.get_value(GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value)

    def set_spray_on(self, sprayOn):
        """Set spray on/off."""
        self.set_value(GlueSettingKey.SPRAY_ON.value, sprayOn)

    def get_spray_on(self):
        """Get spray on/off."""
        return self.get_value(GlueSettingKey.SPRAY_ON.value)
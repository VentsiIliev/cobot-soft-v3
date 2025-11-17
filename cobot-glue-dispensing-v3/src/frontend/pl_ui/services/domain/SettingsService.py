"""
Settings Domain Service

Handles all settings-related operations with explicit return values.
No callbacks - just clean, clear method calls!
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Tuple
from enum import Enum

from ..types.ServiceResult import ServiceResult

# Import settings classes for type hints and validation
from modules.shared.core.settings.conreateSettings.CameraSettings import CameraSettings
from modules.shared.core.settings.conreateSettings.RobotSettings import RobotSettings
from applications.glue_dispensing_application.settings.GlueSettings import GlueSettings

# Import UI component classes for validation
from frontend.pl_ui.ui.windows.settings.CameraSettingsTabLayout import CameraSettingsTabLayout

from frontend.pl_ui.ui.windows.settings.GlueSettingsTabLayout import GlueSettingsTabLayout

if TYPE_CHECKING:
    from frontend.pl_ui.controller.Controller import Controller


class SettingComponentType(Enum):
    """Valid component types for settings updates"""
    CAMERA = CameraSettingsTabLayout.__name__
    GLUE = GlueSettingsTabLayout.__name__
    ROBOT = "RobotConfigUI"  # Robot settings component



class SettingsService:
    """
    Domain service for all settings operations.
    
    Provides explicit, type-safe methods for settings management.
    All methods return ServiceResult - no callbacks needed!
    
    Usage:
        result = settings_service.update_setting("width", 1920, "CameraSettingsTabLayout")
        if result:
            print("Setting updated successfully!")
        else:
            print(f"Failed: {result.message}")
    """
    
    def __init__(self, controller: 'Controller', logger: logging.Logger):
        """
        Initialize the settings service.
        
        Args:
            controller: The main controller instance
            logger: Logger for this service
        """
        self.controller = controller
        self.logger = logger.getChild(self.__class__.__name__)
    
    def update_setting(self, key: str, value: Any, component_type: str) -> ServiceResult:
        """
        Update a single setting value.
        
        Args:
            key: The setting key to update
            value: The new value for the setting
            component_type: The UI component type (determines setting category)
        
        Returns:
            ServiceResult with success/failure status and message
        """
        try:
            # Validate component type
            if not self._validate_component_type(component_type):
                return ServiceResult.error_result(
                    f"Invalid component type: {component_type}. "
                    f"Valid types: {[t.value for t in SettingComponentType]}"
                )
            
            # Validate key and value
            validation_result = self._validate_setting_value(key, value, component_type)
            if not validation_result.success:
                return validation_result
            
            # Log the operation
            self.logger.info(f"Updating {component_type} setting: {key} = {value}")
            
            # Call the controller
            self.controller.updateSettings(key, value, component_type)
            
            return ServiceResult.success_result(
                f"Setting '{key}' updated successfully",
                data={"key": key, "value": value, "component": component_type}
            )
            
        except Exception as e:
            error_msg = f"Failed to update setting '{key}': {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def get_all_settings(self) -> ServiceResult:
        """
        Get all settings (camera, robot, glue).
        
        Returns:
            ServiceResult with settings data or error message
        """
        try:
            self.logger.info("Retrieving all settings")
            
            # Call the controller
            camera_settings, robot_settings, glue_settings = self.controller.handleGetSettings()
            
            settings_data = {
                "camera": camera_settings,
                "robot": robot_settings,
                "glue": glue_settings
            }
            
            return ServiceResult.success_result(
                "Settings retrieved successfully",
                data=settings_data
            )
            
        except Exception as e:
            error_msg = f"Failed to retrieve settings: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def get_camera_settings(self) -> ServiceResult:
        """Get only camera settings"""
        try:
            result = self.get_all_settings()
            if result.success and result.data:
                camera_data = result.data.get("camera")
                return ServiceResult.success_result(
                    "Camera settings retrieved successfully",
                    data=camera_data
                )
            return result
        except Exception as e:
            error_msg = f"Failed to retrieve camera settings: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def get_robot_settings(self) -> ServiceResult:
        """Get only robot settings"""
        try:
            result = self.get_all_settings()
            if result.success and result.data:
                robot_data = result.data.get("robot")
                return ServiceResult.success_result(
                    "Robot settings retrieved successfully",
                    data=robot_data
                )
            return result
        except Exception as e:
            error_msg = f"Failed to retrieve robot settings: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def get_glue_settings(self) -> ServiceResult:
        """Get only glue settings"""
        try:
            result = self.get_all_settings()
            if result.success and result.data:
                glue_data = result.data.get("glue")
                return ServiceResult.success_result(
                    "Glue settings retrieved successfully",
                    data=glue_data
                )
            return result
        except Exception as e:
            error_msg = f"Failed to retrieve glue settings: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def _validate_component_type(self, component_type: str) -> bool:
        """Validate that the component type is supported"""
        valid_types = [t.value for t in SettingComponentType]
        return component_type in valid_types
    
    def _validate_setting_value(self, key: str, value: Any, component_type: str) -> ServiceResult:
        """
        Validate setting key and value based on component type.
        
        Args:
            key: Setting key to validate
            value: Setting value to validate
            component_type: Component type for context
        
        Returns:
            ServiceResult indicating validation success/failure
        """
        try:
            # Basic validation
            if not key or key.strip() == "":
                return ServiceResult.error_result("Setting key cannot be empty")
            
            if value is None:
                return ServiceResult.error_result("Setting value cannot be None")
            
            # Component-specific validation
            try:
                component = SettingComponentType(component_type)
            except ValueError:
                # Handle legacy component types that don't match enum values
                self.logger.warning(f"Unknown component type: {component_type}. Allowing for backward compatibility.")
                return ServiceResult.success_result("Validation passed (unknown component type)")
            
            if component == SettingComponentType.CAMERA:
                return self._validate_camera_setting(key, value)
            elif component == SettingComponentType.ROBOT:
                return self._validate_robot_setting(key, value)
            elif component == SettingComponentType.GLUE:
                return self._validate_glue_setting(key, value)
            
            return ServiceResult.success_result("Validation passed")
            
        except Exception as e:
            return ServiceResult.error_result(f"Validation error: {str(e)}")
    
    def _validate_camera_setting(self, key: str, value: Any) -> ServiceResult:
        """Validate camera-specific settings"""
        # Add camera-specific validation logic here
        # For now, just basic type checks
        if key in ["width", "height", "skip_frames"] and not isinstance(value, (int, float)):
            return ServiceResult.error_result(f"Camera setting '{key}' must be a number")
        
        return ServiceResult.success_result("Camera setting validation passed")
    
    def _validate_robot_setting(self, key: str, value: Any) -> ServiceResult:
        """Validate robot-specific settings"""
        # Add robot-specific validation logic here
        if key in ["velocity", "acceleration"] and not isinstance(value, (int, float)):
            return ServiceResult.error_result(f"Robot setting '{key}' must be a number")
        
        return ServiceResult.success_result("Robot setting validation passed")
    
    def _validate_glue_setting(self, key: str, value: Any) -> ServiceResult:
        """Validate glue-specific settings"""
        # Add glue-specific validation logic here
        if key in ["motor_speed", "fan_speed"] and not isinstance(value, (int, float)):
            return ServiceResult.error_result(f"Glue setting '{key}' must be a number")
        
        return ServiceResult.success_result("Glue setting validation passed")
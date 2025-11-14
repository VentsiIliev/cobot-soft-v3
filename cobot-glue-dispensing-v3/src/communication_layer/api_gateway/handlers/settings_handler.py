"""
Settings Handler - API Gateway

Handles all settings-related requests including robot, camera, and glue system configuration.
"""

from modules.shared.v1.Response import Response
from modules.shared.v1 import Constants
from modules.shared.v1.endpoints import settings_endpoints
from src.robot_application.glue_dispensing_application.settings.GlueConstants import (
    SETTINGS_GLUE_GET,
    SETTINGS_GLUE_SET,
    SETTINGS_GLUE_GET_LEGACY,
    SETTINGS_GLUE_SET_LEGACY
)


class SettingsHandler:
    """
    Handles settings operations for the API gateway.
    
    This handler manages configuration for robot, camera, glue system, and general settings.
    """
    
    def __init__(self, settingsController):
        """
        Initialize the SettingsHandler.
        
        Args:
            settingsController: Settings controller instance
        """
        self.settingsController = settingsController
    
    def handle(self, parts, request, data=None):
        """
        Route settings requests to appropriate handlers.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response dictionary with operation result
        """
        print(f"SettingsHandler: Handling request: {request} with parts: {parts}")
        
        # Handle both new RESTful endpoints and legacy endpoints
        # Robot settings
        if request in [settings_endpoints.SETTINGS_ROBOT_GET, settings_endpoints.SETTINGS_ROBOT_GET_LEGACY]:
            return self.handle_robot_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_ROBOT_SET, settings_endpoints.SETTINGS_ROBOT_SET_LEGACY]:
            return self.handle_robot_settings(parts, request, data)
        # Camera settings
        elif request in [settings_endpoints.SETTINGS_CAMERA_GET, settings_endpoints.SETTINGS_CAMERA_GET_LEGACY]:
            return self.handle_camera_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_CAMERA_SET, settings_endpoints.SETTINGS_CAMERA_SET_LEGACY]:
            return self.handle_camera_settings(parts, request, data)
        elif request in [SETTINGS_GLUE_GET, SETTINGS_GLUE_GET_LEGACY]:
            return self.handle_glue_settings(parts, request, data)
        elif request in [SETTINGS_GLUE_SET, SETTINGS_GLUE_SET_LEGACY]:
            return self.handle_glue_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_GET, settings_endpoints.GET_SETTINGS]:
            return self.handle_general_settings(parts, request, data)
        elif request in [settings_endpoints.SETTINGS_UPDATE, settings_endpoints.UPDATE_SETTINGS]:
            return self.handle_general_settings(parts, request, data)
        else:
            # Delegate to settings controller which handles all the logic
            return self.settingsController.handle(request, parts, data)
    
    def handle_robot_settings(self, parts, request, data=None):
        """
        Handle robot-specific settings operations.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response with robot settings data or operation result
        """
        print(f"SettingsHandler: Handling robot settings: {request}")
        
        return self.settingsController.handle(request, parts, data)
    
    def handle_camera_settings(self, parts, request, data=None):
        """
        Handle camera-specific settings operations.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response with camera settings data or operation result
        """
        print(f"SettingsHandler: Handling camera settings: {request}")
        print(f"SettingsHandler: Data received: {data}")
        print(f"SettingsHandler: Data type: {type(data)}")
        
        return self.settingsController.handle(request, parts, data)
    
    def handle_glue_settings(self, parts, request, data=None):
        """
        Handle glue system settings operations.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response with glue settings data or operation result
        """
        print(f"SettingsHandler: Handling glue settings: {request}")
        
        return self.settingsController.handle(request, parts, data)
    
    def handle_general_settings(self, parts, request, data=None):
        """
        Handle general system settings operations.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response with general settings data or operation result
        """
        print(f"SettingsHandler: Handling general settings: {request}")
        
        return self.settingsController.handle(request, parts, data)
    
    def handle_settings_get(self, domain=None):
        """
        Handle settings retrieval operations.
        
        Args:
            domain (str): Settings domain (robot, camera, glue, or None for all)
            
        Returns:
            dict: Response with settings data
        """
        print(f"SettingsHandler: Handling settings get for domain: {domain}")
        
        try:
            if domain:
                # Domain-specific settings
                request = f"settings/{domain}/get"
            else:
                # All settings
                request = "settings/get"
            
            return self.settingsController.handle(request, [], None)
            
        except Exception as e:
            print(f"SettingsHandler: Error getting settings: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error getting settings: {e}"
            ).to_dict()
    
    def handle_settings_set(self, domain, data):
        """
        Handle settings update operations.
        
        Args:
            domain (str): Settings domain (robot, camera, glue)
            data (dict): Settings data to update
            
        Returns:
            dict: Response indicating success or failure
        """
        print(f"SettingsHandler: Handling settings set for domain: {domain}")
        
        try:
            request = f"settings/{domain}/set"
            return self.settingsController.handle(request, [], data)
            
        except Exception as e:
            print(f"SettingsHandler: Error setting settings: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error setting settings: {e}"
            ).to_dict()
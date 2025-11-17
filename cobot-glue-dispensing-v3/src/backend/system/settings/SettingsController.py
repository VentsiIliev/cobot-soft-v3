import traceback

from modules.shared.v1 import Constants
from modules.shared.v1.Response import Response
import modules.shared.v1.endpoints.settings_endpoints as settings_endpoints

from backend.system.settings.SettingsService import SettingsService
from backend.system.vision.VisionService import VisionServiceSingleton
from core.application.interfaces.application_settings_interface import settings_registry




class SettingsController:
    """
    Controller for managing system settings via API requests.

    Supports:
        - Core settings (robot and camera)
        - Application-specific settings through registry
        - Generic settings routing
        - Dynamic endpoint handling
    """

    def __init__(self, settingsService: SettingsService):
        self.settingsService = settingsService

    def handle(self, request, parts, data=None):
        """
        Main handler for settings requests.

        Args:
            request (str): Full request string
            parts (list): Split request path parts
            data (dict, optional): Settings data for POST/set requests

        Returns:
            dict: Response dictionary
        """
        try:
            # === CORE SETTINGS - GET OPERATIONS ===
            if request in [
                settings_endpoints.SETTINGS_ROBOT_GET
            ]:
                return self._handleGet("robot")

            elif request in [
                settings_endpoints.SETTINGS_CAMERA_GET
            ]:
                return self._handleGet("camera")

            elif request in [
                settings_endpoints.SETTINGS_GET
            ]:
                return self._handleGet("general")

            # === CORE SETTINGS - SET / UPDATE OPERATIONS ===
            elif request in [
                settings_endpoints.SETTINGS_ROBOT_SET
            ]:
                return self._handleSet("robot", data)

            elif request in [
                settings_endpoints.SETTINGS_CAMERA_SET
            ]:
                return self._handleSet("camera", data)

            elif request in [
                settings_endpoints.SETTINGS_UPDATE
            ]:
                return self._handleSet("general", data)

            # === APPLICATION-SPECIFIC SETTINGS ===
            # Check if this is an application-specific settings endpoint
            else:
                return self._handle_application_settings(request, data)

        except Exception as e:
            traceback.print_exc()
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Unhandled exception in SettingsController: {e}"
            ).to_dict()

    # =========================
    # INTERNAL HELPERS
    # =========================

    def _handle_application_settings(self, request, data=None):
        """
        Handle application-specific settings requests using the registry.
        
        Args:
            request: The request endpoint
            data: Optional data for SET requests
            
        Returns:
            dict: Response dictionary
        """
        try:
            # Get mapping of endpoints to settings types
            endpoint_mapping = settings_registry.get_all_endpoints()
            
            if request not in endpoint_mapping:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR,
                    message=f"Unknown settings endpoint: {request}"
                ).to_dict()
            
            settings_type = endpoint_mapping[request]
            
            try:
                handler = settings_registry.get_handler(settings_type)
            except KeyError:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR,
                    message=f"Settings handler not found for type: {settings_type}"
                ).to_dict()
            
            # Determine if this is a GET or SET operation based on data presence
            if data is None:
                # GET operation
                result_data = handler.handle_get_settings()
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS,
                    message="Success",
                    data=result_data
                ).to_dict()
            else:
                # SET operation
                success, message = handler.handle_set_settings(data)
                if success:
                    return Response(
                        Constants.RESPONSE_STATUS_SUCCESS,
                        message=message
                    ).to_dict()
                else:
                    return Response(
                        Constants.RESPONSE_STATUS_ERROR,
                        message=message
                    ).to_dict()
                    
        except Exception as e:
            traceback.print_exc()
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error handling application settings: {e}"
            ).to_dict()

    def _handleGet(self, resource):
        """
        Get settings for a given domain.
        """
        try:
            # Map lowercase resource names to proper constants
            resource_map = {
                "robot": Constants.REQUEST_RESOURCE_ROBOT,
                "camera": Constants.REQUEST_RESOURCE_CAMERA
            }
            
            # Use mapped resource if available, otherwise use as-is (for application settings)
            actual_resource = resource_map.get(resource, resource)
            
            data = self.settingsService.getSettings(actual_resource)
            if data is not None:
                return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Success", data=data).to_dict()
            return Response(Constants.RESPONSE_STATUS_ERROR, message=f"Error getting {resource} settings").to_dict()
        except Exception as e:
            traceback.print_exc()
            return Response(Constants.RESPONSE_STATUS_ERROR, message=f"Error retrieving {resource} settings: {e}").to_dict()

    def _handleSet(self, resource, data):
        """
        Set/update settings for a given domain.
        """
        try:
            print(f"SettingsController._handleSet: resource={resource}, data={data}")
            self.settingsService.updateSettings(data)

            # Update camera settings separately
            if resource == "camera":
                result, message = VisionServiceSingleton().get_instance().updateCameraSettings(data)
                if not result:
                    return Response(Constants.RESPONSE_STATUS_ERROR, message=f"Error saving camera settings: {message}").to_dict()

            return Response(Constants.RESPONSE_STATUS_SUCCESS, message=f"{resource.capitalize()} settings saved successfully").to_dict()

        except Exception as e:
            traceback.print_exc()
            return Response(Constants.RESPONSE_STATUS_ERROR, message=f"Error saving {resource} settings: {e}").to_dict()

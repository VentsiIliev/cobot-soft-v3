import traceback

from modules.shared.v1 import Constants
from modules.shared.v1.Response import Response
import modules.shared.v1.endpoints.settings_endpoints as settings_endpoints

from src.backend.GlueDispensingApplication.settings.SettingsService import SettingsService
from src.backend.GlueDispensingApplication.vision.VisionService import VisionServiceSingleton


class SettingsController:
    """
    Controller for managing system settings via API requests.

    Supports:
        - Robot settings
        - Camera settings
        - Glue settings
        - Generic settings
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
            # === GET OPERATIONS ===
            if request in [
                settings_endpoints.SETTINGS_ROBOT_GET,
                settings_endpoints.SETTINGS_ROBOT_GET_LEGACY,
                settings_endpoints.GET_SETTINGS
            ]:
                return self._handleGet("robot")

            elif request in [
                settings_endpoints.SETTINGS_CAMERA_GET,
                settings_endpoints.SETTINGS_CAMERA_GET_LEGACY
            ]:
                return self._handleGet("camera")

            elif request in [
                settings_endpoints.SETTINGS_GLUE_GET,
                settings_endpoints.SETTINGS_GLUE_GET_LEGACY
            ]:
                return self._handleGet("glue")

            elif request in [
                settings_endpoints.SETTINGS_GET,
                settings_endpoints.GET_SETTINGS,
            ]:
                return self._handleGet("general")

            # === SET / UPDATE OPERATIONS ===
            elif request in [
                settings_endpoints.SETTINGS_ROBOT_SET,
                settings_endpoints.SETTINGS_ROBOT_SET_LEGACY,
                settings_endpoints.UPDATE_SETTINGS
            ]:
                return self._handleSet("robot", data)

            elif request in [
                settings_endpoints.SETTINGS_CAMERA_SET,
                settings_endpoints.SETTINGS_CAMERA_SET_LEGACY
            ]:
                return self._handleSet("camera", data)

            elif request in [
                settings_endpoints.SETTINGS_GLUE_SET,
                settings_endpoints.SETTINGS_GLUE_SET_LEGACY
            ]:
                return self._handleSet("glue", data)

            elif request in [
                settings_endpoints.SETTINGS_UPDATE,
                settings_endpoints.UPDATE_SETTINGS
            ]:
                return self._handleSet("general", data)

            else:
                raise ValueError(f"Unknown settings endpoint: {request}")

        except Exception as e:
            raise ValueError(f"Unknown request: {request}")
            traceback.print_exc()
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Unhandled exception in SettingsController: {e}"
            ).to_dict()

    # =========================
    # INTERNAL HELPERS
    # =========================

    def _handleGet(self, resource):
        """
        Get settings for a given domain.
        """
        try:
            data = self.settingsService.getSettings(resource)
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

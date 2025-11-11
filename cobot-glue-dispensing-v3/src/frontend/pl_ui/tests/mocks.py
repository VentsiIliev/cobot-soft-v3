# Mock classes for testing
from modules.shared.v1 import Constants
from src.frontend.pl_ui.Endpoints import QR_LOGIN,GO_TO_LOGIN_POS,UPDATE_CAMERA_FEED


class MockCameraService:
    def __init__(self):
        pass

    def handle(self, endpoint):
        if endpoint == QR_LOGIN:
            return {"status": Constants.RESPONSE_STATUS_SUCCESS, "data": {"id": "12345", "password": "password"}}
        elif endpoint == GO_TO_LOGIN_POS:
            return Constants.RESPONSE_STATUS_SUCCESS
        elif endpoint == UPDATE_CAMERA_FEED:
            # print("Updating camera feed...")
            pass
            return
        else:
            return Constants.RESPONSE_STATUS_ERROR


class MockController():
    def __init__(self):
        self.camera_service = MockCameraService()

    def handle(self, endpoint):
        return self.camera_service.handle(endpoint)

    def is_blue_button_pressed(self):
        return True  # Simulate blue button press for testing

    def handleLogin(self, username, password,fail=False):
        if fail:
            return "-1"  # Simulate user not found
        else:
            return 1  # Simulate successful login

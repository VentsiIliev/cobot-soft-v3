from modules.shared.v1 import Constants
from modules.shared.v1.Response import Response
from modules.shared.v1.endpoints import camera_endpoints
import traceback
import time


class CameraSystemController:
    """
    Handles all camera-related operations using defined API endpoints
    from shared.v1.endpoints.camera_endpoints.
    """

    def __init__(self, cameraService):
        self.cameraService = cameraService

    def handle(self, request, parts, data=None):
        """
        Central request handler for camera system operations.
        Supports both RESTful v1 and legacy endpoints.
        """
        # print(f"[CameraSystemController] Handling request: {request}")
        try:
            # === FRAME OPERATIONS ===
            if request in (
                camera_endpoints.CAMERA_ACTION_GET_LATEST_FRAME,
                camera_endpoints.CAMERA_ACTION_GET_LATEST_FRAME_LEGACY,
            ):
                return self.handleLatestFrame()

            elif request in (
                camera_endpoints.UPDATE_CAMERA_FEED,
                camera_endpoints.UPDATE_CAMERA_FEED_LEGACY,
            ):
                return self.handleLatestFrame()

            elif request == camera_endpoints.GET_LATEST_IMAGE:
                return self.handleLatestFrame()

            # === RAW MODE CONTROL ===
            elif request in (
                camera_endpoints.CAMERA_ACTION_RAW_MODE_ON,
                camera_endpoints.CAMERA_ACTION_RAW_MODE_ON_LEGACY,
                camera_endpoints.RAW_MODE_ON,
            ):
                return self.handleRawModeOn()

            elif request in (
                camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF,
                camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF_LEGACY,
                camera_endpoints.RAW_MODE_OFF,
            ):
                return self.handleRawModeOff()

            # === CALIBRATION ===
            elif request in (
                camera_endpoints.CAMERA_ACTION_CALIBRATE,
                camera_endpoints.CAMERA_ACTION_CALIBRATE_LEGACY,
            ):
                return self.cameraService.calibrate()

            elif request in (
                camera_endpoints.CAMERA_ACTION_CAPTURE_CALIBRATION_IMAGE,
                camera_endpoints.CAMERA_ACTION_CAPTURE_CALIBRATION_IMAGE_LEGACY,
                camera_endpoints.CAPTURE_CALIBRATION_IMAGE,
            ):
                return self.captureCalibrationImage()

            elif request in (
                camera_endpoints.CAMERA_ACTION_TEST_CALIBRATION,
                camera_endpoints.CAMERA_ACTION_TEST_CALIBRATION_LEGACY,
                camera_endpoints.TEST_CALIBRATION,
            ):
                return self.cameraService.testCalibration()

            # === WORK AREA ===
            elif request in (
                camera_endpoints.CAMERA_ACTION_SAVE_WORK_AREA_POINTS,
                camera_endpoints.CAMERA_ACTION_SAVE_WORK_AREA_POINTS_LEGACY,
                camera_endpoints.SAVE_WORK_AREA_POINTS,
            ):
                return self.saveWorkAreaPoints(data)

            # === CONTOUR DETECTION ===
            elif request in (
                camera_endpoints.START_CONTOUR_DETECTION,
                camera_endpoints.START_CONTOUR_DETECTION_LEGACY,
                camera_endpoints.START_CONTOUR_DETECTION_LEGACY_2,
            ):
                return self.startContourDetection()

            elif request in (
                camera_endpoints.STOP_CONTOUR_DETECTION,
                camera_endpoints.STOP_CONTOUR_DETECTION_LEGACY,
                camera_endpoints.STOP_CONTOUR_DETECTION_LEGACY_2,
            ):
                return self.stopContourDetection()

            # === LOGIN ===
            elif request in (
                camera_endpoints.QR_LOGIN,
                camera_endpoints.QR_LOGIN_LEGACY,
            ):
                return self.handleLogin()

            # === UNKNOWN ENDPOINT ===
            else:
                raise ValueError(f"Unknown camera endpoint: {request}")

        except Exception as e:
            traceback.print_exc()
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"CameraSystemController error handling {request}: {e}"
            ).to_dict()

    # === INDIVIDUAL OPERATION HANDLERS ===

    def handleLatestFrame(self):
        try:
            frame = self.cameraService.getLatestFrame()
            message = "Frame retrieved" if frame is not None else "Frame is None"
            return Response(
                Constants.RESPONSE_STATUS_SUCCESS,
                message=message,
                data={"frame": frame},
            ).to_dict()
        except Exception as e:
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error getting latest frame: {e}",
            ).to_dict()

    def handleRawModeOn(self):
        self.cameraService.setRawMode(True)
        return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Raw mode enabled").to_dict()

    def handleRawModeOff(self):
        self.cameraService.setRawMode(False)
        return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Raw mode disabled").to_dict()

    def captureCalibrationImage(self):
        result, message = self.cameraService.captureCalibrationImage()
        status = (
            Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
        )
        return Response(status, message=message).to_dict()

    def saveWorkAreaPoints(self, points):
        print("[CameraSystemController] Saving work area points:", points)
        result, message = self.cameraService.saveWorkAreaPoints(points)
        status = (
            Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
        )
        return Response(status, message=message).to_dict()

    def handleLogin(self):
        import re
        data = self.cameraService.detectQrCode()
        if data is None:
            return Response(Constants.RESPONSE_STATUS_ERROR, "No QR code detected").to_dict()

        pattern = r"id\s*=\s*(\S+)\s+password\s*=\s*(\S+)"
        match = re.search(pattern, data)
        if match:
            data = {"id": match.group(1), "password": match.group(2)}
            return Response(Constants.RESPONSE_STATUS_SUCCESS, data=data).to_dict()
        else:
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                "Invalid QR code format",
            ).to_dict()

    def startContourDetection(self):
        self.cameraService.startContourDetection()
        return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Contour detection started").to_dict()

    def stopContourDetection(self):
        self.cameraService.stopContourDetection()
        return Response(Constants.RESPONSE_STATUS_SUCCESS, message="Contour detection stopped").to_dict()

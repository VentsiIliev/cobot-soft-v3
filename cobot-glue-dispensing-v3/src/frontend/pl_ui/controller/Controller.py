from PyQt6.QtCore import QThread
from modules.shared.v1.Response import Response
from modules.shared.v1 import Constants
from modules.shared.shared.settings.conreateSettings.CameraSettings import CameraSettings
from src.backend.robot_application.glue_dispensing_application.settings.GlueSettings import GlueSettings
from modules.shared.shared.settings.conreateSettings.RobotSettings import RobotSettings

from .RequestWorker import RequestWorker
from src.frontend.pl_ui.ui.widgets.FeedbackProvider import FeedbackProvider

# Import new structured endpoints
from modules.shared.v1.endpoints import (
    auth_endpoints,
    operations_endpoints,
    robot_endpoints,
    camera_endpoints,
    workpiece_endpoints,
    settings_endpoints
)
# Import glue application constants
from src.backend.robot_application.glue_dispensing_application.settings.GlueConstants import (
    REQUEST_RESOURCE_GLUE,
    SETTINGS_GLUE_GET,
    SETTINGS_GLUE_SET
)
from src.backend.robot_application.glue_dispensing_application.workpiece import Workpiece

from src.frontend.pl_ui.ui.windows.settings.CameraSettingsTabLayout import CameraSettingsTabLayout
from src.frontend.pl_ui.ui.windows.settings.ContourSettingsTabLayout import ContourSettingsTabLayout
from src.frontend.pl_ui.ui.windows.settings.RobotSettingsTabLayout import RobotSettingsTabLayout
from src.frontend.pl_ui.ui.windows.settings.GlueSettingsTabLayout import GlueSettingsTabLayout

import logging


class Controller:
    def __init__(self, requestSender):
        self.logTag = self.__class__.__name__
        self.logger = logging.getLogger(self.__class__.__name__)
        self.requestSender = requestSender
        self.endpointsMap = {}
        self.registerEndpoints()

    def registerEndpoints(self):
        self.endpointsMap = {
            # Settings endpoints
            settings_endpoints.UPDATE_SETTINGS: self.updateSettings,
            settings_endpoints.GET_SETTINGS: self.handleGetSettings,
            
            # Authentication endpoints
            auth_endpoints.LOGIN: self.handleLogin,
            auth_endpoints.LEGACY_LOGIN: self.handleLogin,
            auth_endpoints.QR_LOGIN: self.handleQrLogin,
            auth_endpoints.LEGACY_QR_LOGIN: self.handleQrLogin,
            
            # Operations endpoints
            operations_endpoints.START: self.handleStart,
            operations_endpoints.START_LEGACY: self.handleStart,
            operations_endpoints.PAUSE: self.handlePause,
            operations_endpoints.PAUSE_LEGACY: self.handlePause,
            operations_endpoints.STOP: self.handleStop,
            operations_endpoints.STOP_LEGACY: self.handleStop,
            operations_endpoints.TEST_RUN: self.handleTestRun,
            operations_endpoints.TEST_RUN_LEGACY: self.handleTestRun,
            operations_endpoints.CALIBRATE: self.handleCalibrate,
            operations_endpoints.CALIBRATE_LEGACY: self.handleCalibrate,
            operations_endpoints.HELP: self.handleHelp,
            operations_endpoints.HELP_LEGACY: self.handleHelp,
            operations_endpoints.RUN_DEMO: self.handleRunDemo,
            operations_endpoints.RUN_REMO: self.handleRunDemo,
            operations_endpoints.STOP_DEMO: self.handleStopDemo,
            operations_endpoints.STOP_DEMO_LEGACY: self.handleStopDemo,
            
            # Camera endpoints
            camera_endpoints.CAMERA_ACTION_CALIBRATE: self.handleCalibrateCamera,
            camera_endpoints.CALIBRATE_CAMERA: self.handleCalibrateCamera,
            camera_endpoints.CAMERA_ACTION_CAPTURE_CALIBRATION_IMAGE: self.handleCaptureCalibrationImage,
            camera_endpoints.CAPTURE_CALIBRATION_IMAGE: self.handleCaptureCalibrationImage,
            camera_endpoints.CAMERA_ACTION_TEST_CALIBRATION: self.handleTestCalibration,
            camera_endpoints.TEST_CALIBRATION: self.handleTestCalibration,
            camera_endpoints.CAMERA_ACTION_SAVE_WORK_AREA_POINTS: self.handleSaveWorkAreaPoints,
            camera_endpoints.SAVE_WORK_AREA_POINTS: self.handleSaveWorkAreaPoints,
            camera_endpoints.UPDATE_CAMERA_FEED: self.updateCameraFeed,
            camera_endpoints.UPDATE_CAMERA_FEED_LEGACY: self.updateCameraFeed,
            camera_endpoints.START_CONTOUR_DETECTION: self.handleStartContourDetection,
            camera_endpoints.START_CONTOUR_DETECTION_LEGACY: self.handleStartContourDetection,
            camera_endpoints.STOP_CONTOUR_DETECTION: self.handleStopContourDetection,
            camera_endpoints.STOP_CONTOUR_DETECTION_LEGACY: self.handleStopContourDetection,
            camera_endpoints.CAMERA_ACTION_RAW_MODE_ON: self.handleRawModeOn,
            camera_endpoints.RAW_MODE_ON: self.handleRawModeOn,
            camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF: self.handleRawModeOff,
            camera_endpoints.RAW_MODE_OFF: self.handleRawModeOff,
            
            # Robot endpoints
            robot_endpoints.ROBOT_CALIBRATE: self.handleCalibrateRobot,
            robot_endpoints.CALIBRATE_ROBOT: self.handleCalibrateRobot,
            robot_endpoints.ROBOT_MOVE_TO_HOME_POS: self.homeRobot,
            robot_endpoints.HOME_ROBOT: self.homeRobot,
            robot_endpoints.ROBOT_MOVE_TO_CALIB_POS: self.handleMoveToCalibrationPos,
            robot_endpoints.GO_TO_CALIBRATION_POS: self.handleMoveToCalibrationPos,
            robot_endpoints.ROBOT_MOVE_TO_LOGIN_POS: self.handleLoginPos,
            robot_endpoints.GO_TO_LOGIN_POS: self.handleLoginPos,
            robot_endpoints.JOG_ROBOT: self.handleJog,
            robot_endpoints.ROBOT_SAVE_POINT: self.saveRobotCalibrationPoint,
            robot_endpoints.SAVE_ROBOT_CALIBRATION_POINT: self.saveRobotCalibrationPoint,
            robot_endpoints.ROBOT_EXECUTE_NOZZLE_CLEAN: self.handleCleanNozzle,
            robot_endpoints.ROBOT_RESET_ERRORS: self.handleResetErrors,
            robot_endpoints.ROBOT_RESET_ERRORS_LEGACY: self.handleResetErrors,
            robot_endpoints.ROBOT_UPDATE_CONFIG: self.handleRobotUpdateConfig,
            robot_endpoints.ROBOT_UPDATE_CONFIG_LEGACY: self.handleRobotUpdateConfig,
            
            # Workpiece endpoints
            workpiece_endpoints.WORKPIECE_SAVE: self.saveWorkpiece,
            workpiece_endpoints.SAVE_WORKPIECE: self.saveWorkpiece,
            workpiece_endpoints.WORKPIECE_SAVE_DXF: self.saveWorkpieceFromDXF,
            workpiece_endpoints.SAVE_WORKPIECE_DXF: self.saveWorkpieceFromDXF,
            workpiece_endpoints.WORKPIECE_CREATE: self.createWorkpieceAsync,
            workpiece_endpoints.CREATE_WORKPIECE_TOPIC: self.createWorkpieceAsync,
            workpiece_endpoints.WORKPIECE_CREATE_STEP_1: self.handleCreateWorkpieceStep1,
            workpiece_endpoints.CREATE_WORKPIECE_STEP_1: self.handleCreateWorkpieceStep1,
            workpiece_endpoints.WORKPIECE_CREATE_STEP_2: self.handleCreateWorkpieceStep2,
            workpiece_endpoints.CREATE_WORKPIECE_STEP_2: self.handleCreateWorkpieceStep2,
            workpiece_endpoints.WORKPIECE_GET_ALL: self.handleGetAllWorpieces,
            workpiece_endpoints.WORPIECE_GET_ALL: self.handleGetAllWorpieces,
            
            # Legacy special endpoints
            "executeFromGallery": self.handleExecuteFromGallery,
        }

    def handleRobotUpdateConfig(self):
        request = robot_endpoints.ROBOT_UPDATE_CONFIG
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error updating robot config:", response.message)

        return response.status

    def handleRunDemo(self):
        request = operations_endpoints.RUN_DEMO
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error starting demo:", response.message)

        return response.status

    def handleStopDemo(self):
        request = operations_endpoints.STOP_DEMO
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error stopping demo:", response.message)

        return response.status

    def handleResetErrors(self):
        request = robot_endpoints.ROBOT_RESET_ERRORS
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error resetting errors:", response.message)

        return response.status

    def handleCleanNozzle(self):
        print(f"UI Controller handle clean nozzle")
        request = robot_endpoints.ROBOT_EXECUTE_NOZZLE_CLEAN
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error cleaning nozzle:", response.message)

        return response.status

    def handleRawModeOn(self):
        print("Enabling raw mode")
        request = camera_endpoints.CAMERA_ACTION_RAW_MODE_ON
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error enabling raw mode:", response.message)

        return response.status

    def handleRawModeOff(self):
        request = camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error disabling raw mode:", response.message)

        return response.status

    def handleSetPreselectedWorkpiece(self, workpiece):
        self.requestSender.sendRequest("handleSetPreselectedWorkpiece", workpiece)

    def handleTestRun(self):
        self.requestSender.sendRequest("test_run")

    def handle(self, endpoint, *args):
        if endpoint in self.endpointsMap:
            try:
                return self.endpointsMap[endpoint](*args)
            except TypeError as e:
                self.logger.debug(f"{self.logTag} [Method: handle] Parameter mismatch for endpoint '{endpoint}': {e}")
        else:
            self.logger.debug(f"{self.logTag}] [Method: handle] Unknown endpoint: '{endpoint}'")
            return None

    def handlePause(self):
        request = operations_endpoints.PAUSE
        response = self.requestSender.sendRequest(request)

    def handleStop(self):
        request = operations_endpoints.STOP
        response = self.requestSender.sendRequest(request)

    def handleStartContourDetection(self):
        requests = camera_endpoints.START_CONTOUR_DETECTION
        self.requestSender.sendRequest(requests)

    def handleStopContourDetection(self):
        request = camera_endpoints.STOP_CONTOUR_DETECTION
        self.requestSender.sendRequest(request)

    def handleGetAllWorpieces(self):
        request = workpiece_endpoints.WORKPIECE_GET_ALL
        res = self.requestSender.sendRequest(request)
        response = Response.from_dict(res)
        workpieces = response.data
        print(f"Received workpieces: {workpieces}")
        return workpieces

    def handleHelp(self):
        self.logger.debug(f"{self.logTag}] [Method: handleHelp] HELP BUTTON PRESSED'")

    def handleGetSettings(self):
        robotSettingsRequest = settings_endpoints.SETTINGS_ROBOT_GET
        cameraSettingsRequest = settings_endpoints.SETTINGS_CAMERA_GET
        glueSettingsRequest = SETTINGS_GLUE_GET

        robotSettingsResponseDict = self.requestSender.sendRequest(robotSettingsRequest)
        robotSettingsResponse = Response.from_dict(robotSettingsResponseDict)

        cameraSettingsResponseDict = self.requestSender.sendRequest(cameraSettingsRequest)
        cameraSettingsResponse = Response.from_dict(cameraSettingsResponseDict)
        print(" get Camera settings response:", cameraSettingsResponse)
        glueSettingsResponseDict = self.requestSender.sendRequest(glueSettingsRequest)
        glueSettingsResponse = Response.from_dict(glueSettingsResponseDict)

        robotSettingsDict = robotSettingsResponse.data if robotSettingsResponse.status == Constants.RESPONSE_STATUS_SUCCESS else {}
        cameraSettingsDict = cameraSettingsResponse.data if cameraSettingsResponse.status == Constants.RESPONSE_STATUS_SUCCESS else {}
        glueSettingsDict = glueSettingsResponse.data if glueSettingsResponse.status == Constants.RESPONSE_STATUS_SUCCESS else {}

        cameraSettings = CameraSettings(data=cameraSettingsDict)
        robotSettings = RobotSettings(data=robotSettingsDict)
        glueSettings = GlueSettings(data=glueSettingsDict)

        return cameraSettings, robotSettings, glueSettings

    def saveWorkpieceFromDXF(self, data):

        request = workpiece_endpoints.SAVE_WORKPIECE_DXF
        responseDict = self.requestSender.sendRequest(request, data)
        response = Response.from_dict(responseDict)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            message = "Error saving workpieces"
            return False, response.message

        return True, response.message

    def saveWorkpiece(self, data):
        request = workpiece_endpoints.WORKPIECE_SAVE
        responseDict = self.requestSender.sendRequest(request, data)
        response = Response.from_dict(responseDict)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            message = "Error saving workpieces"
            return False, response.message

        return True, response.message

    def handleSaveWorkAreaPoints(self, points):
        print("handleSaveWorkAreaPoints Saving work area points:", points)
        request = camera_endpoints.CAMERA_ACTION_SAVE_WORK_AREA_POINTS
        self.requestSender.sendRequest(request, data=points)

    def handleTestCalibration(self):
        request = camera_endpoints.CAMERA_ACTION_TEST_CALIBRATION
        self.requestSender.sendRequest(request)

    def handleCalibrateRobot(self):
        request = robot_endpoints.CALIBRATE_ROBOT
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        print("Robot calibration response:", response)
        self.logger.debug(f"{self.logTag}] Calibrate robot response: {response}")
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            request = camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF
            response = self.requestSender.sendRequest(request)
            response = Response.from_dict(response)
            FeedbackProvider.showMessage(response.message)
            return False, response.message

        return True, response.message

    def handleCalibrateCamera(self):
        """ MOVE ROBOT TO CALIBRATION POSITION"""
        print("Calibrating camera")
        request = robot_endpoints.ROBOT_MOVE_TO_CALIB_POS
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        if response.status != Constants.RESPONSE_STATUS_SUCCESS:
            self.logger.debug(f"{self.logTag}] [Method: handleCalibrate] Error moving to calib pos")

        request = camera_endpoints.CAMERA_ACTION_RAW_MODE_ON
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)

        FeedbackProvider.showPlaceCalibrationPattern()

        request = camera_endpoints.CAMERA_ACTION_CALIBRATE
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            # FeedbackProvider.showMessage(response.message)
            request = camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF
            response = self.requestSender.sendRequest(request)
            response = Response.from_dict(response)
            return False, response.message

        FeedbackProvider.showMessage("Camera Calibration Success\nMove the chessboard")

    def handleCaptureCalibrationImage(self):
        request = camera_endpoints.CAMERA_ACTION_CAPTURE_CALIBRATION_IMAGE
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            FeedbackProvider.showMessage(response.message)
            return False, response.message

        FeedbackProvider.showMessage("Calibration image captured successfully")
        return True, "Calibration image captured successfully"

    def handleCalibrate(self):

        self.handleCalibrateCamera()
        self.handleCalibrateRobot()

        # SEND ROBOT CALIBRATION REQUEST

        request = robot_endpoints.ROBOT_CALIBRATE
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        print("Robot calibration response:", response)
        self.logger.debug(f"{self.logTag}] Calibrate robot response: {response}")
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            request = Constants.CAMERA_ACTION_RAW_MODE_OFF
            response = self.requestSender.sendRequest(request)
            response = Response.from_dict(response)
            FeedbackProvider.showMessage(response.message)
            return False, response.message

        # self.current_content.pause_feed(response.data['image'])
        # self.robotControl = RobotControl(self)
        # self.mainLayout.insertWidget(1, self.robotControl)
        return True, response.message

    def saveRobotCalibrationPoint(self):
        request = robot_endpoints.SAVE_ROBOT_CALIBRATION_POINT
        responseDict = self.requestSender.sendRequest(request)
        response = Response.from_dict(responseDict)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            return False, False

        pointsCount = response.data.get("pointsCount", 0)  # Default to 0 if key is missing

        if pointsCount == 9:
            return True, True
        else:
            return True, False

    # def calibPickupArea(self):
    #     # request = Request(Constants.REQUEST_TYPE_EXECUTE,Constants.ACTION_CALIBRATE_PICKUP_AREA,Constants.REQUEST_RESOURCE_ROBOT)
    #     request = Constants.ROBOT_CALIBRATE_PICKUP
    #     self.requestSender.sendRequest(request)
    #
    # def moveBelt(self):
    #     self.requestSender.handleBelt()

    def is_blue_button_pressed(self):
        return True

    def handleQrLogin(self):
        request = auth_endpoints.QR_LOGIN
        response = self.requestSender.sendRequest(request)
        # response = Response.from_dict(response)
        return response

    def handleLogin(self, username, password):
        request = auth_endpoints.LOGIN
        response_dict = self.requestSender.sendRequest(request, data=[username, password])
        response = Response.from_dict(response_dict)
        print("Response: ", response)

        message = response.message

        return message

    def updateSettings(self, key, value, className):
        if className == CameraSettingsTabLayout.__name__:
            resource = Constants.REQUEST_RESOURCE_CAMERA
            request = settings_endpoints.SETTINGS_CAMERA_SET
        elif className == ContourSettingsTabLayout.__name__:
            resource = Constants.REQUEST_RESOURCE_CAMERA
            request = settings_endpoints.SETTINGS_CAMERA_SET
        elif className == RobotSettingsTabLayout.__name__:
            resource = Constants.REQUEST_RESOURCE_ROBOT
            request = settings_endpoints.SETTINGS_ROBOT_SET
        elif className == GlueSettingsTabLayout.__name__:
            print("Updating Settings Glue", key, value)
            resource = REQUEST_RESOURCE_GLUE
            request = SETTINGS_GLUE_SET
        else:
            self.logger.error(f"{self.logTag}] Updating Unknown Settings {className} : {key} {value}")
            return

        data = {"header": resource,
                key: value}

        self.requestSender.sendRequest(request, data)

    """ REFACTORED METHODS BELOW """

    def updateCameraFeed(self):
        # print("Controller.updateCameraFeed: Requesting latest camera frame")
        request = camera_endpoints.CAMERA_ACTION_GET_LATEST_FRAME
        responseDict = self.requestSender.sendRequest(request)
        response = Response.from_dict(responseDict)
        # print("Update camera feed response, ",response)
        if response.status != Constants.RESPONSE_STATUS_SUCCESS:
            print(f"Image in updateCameraFeed not received: {response.message}")
            return
        frame = response.data['frame']
        # print(f"Returning image in updateCameraFeed")
        return frame

    def handleJog(self, axis, direction, step):
        request = f"robot/jog/{axis}/{direction}/{step}"

        def onSuccess(req, resp):
            if resp.status == Constants.RESPONSE_STATUS_ERROR:
                FeedbackProvider.showMessage(resp.message)
            else:
                pass

        def onError(req, err):
            self.logger.error(f"{self.logTag}] CALLBACK ERROR MESSAGE {err}")

        self._runAsyncRequest(request, onSuccess, onError)

    def handleLoginPos(self):
        request = robot_endpoints.ROBOT_MOVE_TO_LOGIN_POS
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        return response.status

    def handleMoveToCalibrationPos(self):
        request = robot_endpoints.GO_TO_CALIBRATION_POS
        self.requestSender.sendRequest(request)

    def homeRobot(self, asyncParam=True):
        request = robot_endpoints.ROBOT_MOVE_TO_HOME_POS
        def onSuccess(req, resp):
            if resp.status == Constants.RESPONSE_STATUS_ERROR:
                FeedbackProvider.showMessage(resp.message)
                return Constants.RESPONSE_STATUS_ERROR
            else:
                return Constants.RESPONSE_STATUS_SUCCESS

        def onError(req, err):
            self.logger.error(f"{self.logTag}] CALLBACK ERROR MESSAGE {err}")
            return Constants.RESPONSE_STATUS_ERROR

        if asyncParam:
            self._runAsyncRequest(request, onSuccess, onError)
        else:
            resp = self.requestSender.sendRequest(request)
            resp = Response.from_dict(resp)
            if resp.status == Constants.RESPONSE_STATUS_ERROR:
                FeedbackProvider.showMessage(resp.message)
                return Constants.RESPONSE_STATUS_ERROR
            else:
                return Constants.RESPONSE_STATUS_SUCCESS

    def handleStart(self):
        request = operations_endpoints.START
        def onSuccess(req, resp):
            if resp.status == Constants.RESPONSE_STATUS_ERROR:
                FeedbackProvider.showMessage(resp.message)
            else:
                pass

        def onError(req, err):
            self.logger.error(f"{self.logTag}] CALLBACK ERROR MESSAGE {err}")

        self._runAsyncRequest(request, onSuccess, onError)

    def getWorkpieceById(self, workpieceId):
        request = workpiece_endpoints.WORKPIECE_GET_BY_ID
        data = {"workpieceId": workpieceId}
        responseDict = self.requestSender.sendRequest(request, data)
        response = Response.from_dict(responseDict)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error fetching workpiece:", response.message)
            return False, response.message
        
        # Convert the response data to a Workpiece object
        try:
            if isinstance(response.data, dict):
                workpiece = Workpiece.fromDict(response.data)
                return True, workpiece
            else:
                # response.data is already a Workpiece object
                return True, response.data
        except Exception as e:
            print(f"Error converting response data to Workpiece: {e}")
            return False, f"Error converting response data: {e}"

    def handleDeleteWorkpiece(self,workpieceId):
        request = workpiece_endpoints.WORKPIECE_DELETE
        data = {"workpieceId": workpieceId}
        responseDict = self.requestSender.sendRequest(request, data)
        response = Response.from_dict(responseDict)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error deleting workpiece:", response.message)
            return False, response.message
        return True, response.message

    def handleCreateWorkpieceStep1(self):
        request = workpiece_endpoints.WORKPIECE_CREATE_STEP_1
        responseDict = self.requestSender.sendRequest(request)
        response = Response.from_dict(responseDict)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error in CreateWorkpieceStep1:", response.message)
            return False, response.message
        return True, response.message

    def handleCreateWorkpieceStep2(self):
        request = workpiece_endpoints.WORKPIECE_CREATE_STEP_2
        responseDict = self.requestSender.sendRequest(request)
        response = Response.from_dict(responseDict)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error in CreateWorkpieceStep2:", response.message)
            return False, response.message,None

        return True, response.message, response.data

    def createWorkpieceAsync(self, onSuccess, onError=None):
        request = workpiece_endpoints.CREATE_WORKPIECE_TOPIC
        print("CreateWorkpieceAsync request:", request)

        def successCallback(req, resp):
            if resp.status == Constants.RESPONSE_STATUS_ERROR:
                print("CreateWorkpieceAsync error response:", resp)
                if onError:
                    onError(req, resp.message)
            else:
                print("CreateWorkpieceAsync success response:", resp)
                frame = resp.data['image']
                contours = resp.data['contours']
                onSuccess(frame, contours, resp.data)

        self._runAsyncRequest(request, successCallback, onError)

    def _runAsyncRequest(self, request, onSuccess, onError=None):
        thread = QThread()
        worker = RequestWorker(self.requestSender, request)
        worker.moveToThread(thread)

        def cleanup():
            thread.quit()
            thread.wait()
            worker.deleteLater()
            thread.deleteLater()

        def handleFinished(req, resp):
            cleanup()
            if onSuccess:
                onSuccess(req, resp)

        def handleError(req, error):
            cleanup()
            if onError:
                self.logger.error(f"{self.logTag}] [_runAsyncRequest onError] {req} {error}")
                onError(req, error)


        thread.started.connect(worker.run)
        worker.finished.connect(handleFinished)
        worker.error.connect(handleError)
        thread.start()


    def handleExecuteFromGallery(self, workpiece):
        self.requestSender.sendRequest("handleExecuteFromGallery", workpiece)
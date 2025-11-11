from PyQt6.QtCore import QThread
from API.Response import Response
from API import Constants
from API.shared.settings.conreateSettings.CameraSettings import CameraSettings
from API.shared.settings.conreateSettings.GlueSettings import GlueSettings
from API.shared.settings.conreateSettings.RobotSettings import RobotSettings

from .RequestWorker import RequestWorker
from ..helpers.FeedbackProvider import FeedbackProvider
from deprecated.pl_gui.settings_view.CameraSettingsTabLayout import CameraSettingsTabLayout
from deprecated.pl_gui.settings_view.ContourSettingsTabLayout import ContourSettingsTabLayout
from deprecated.pl_gui.settings_view.RobotSettingsTabLayout import RobotSettingsTabLayout
from deprecated.pl_gui.settings_view.GlueSettingsTabLayout import GlueSettingsTabLayout
from deprecated.pl_gui.Endpoints import *
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
            UPDATE_SETTINGS: self.updateSettings,
            LOGIN: self.handleLogin,
            QR_LOGIN: self.handleQrLogin,
            GET_SETTINGS: self.handleGetSettings,
            START: self.handleStart,
            STOP: self.handleStop,
            CALIBRATE: self.handleCalibrate,
            CAPTURE_CALIBRATION_IMAGE: self.handleCaptureCalibrationImage,
            CALIBRATE_CAMERA: self.handleCalibrateCamera,
            CALIBRATE_ROBOT: self.handleCalibrateRobot,
            TEST_CALIBRATION: self.handleTestCalibration,
            SAVE_WORK_AREA_POINTS: self.handleSaveWorkAreaPoints,
            HOME_ROBOT: self.homeRobot,
            GO_TO_CALIBRATION_POS: self.handleMoveToCalibrationPos,
            JOG_ROBOT: self.handleJog,
            SAVE_WORKPIECE: self.saveWorkpiece,
            SAVE_WORKPIECE_DXF: self.saveWorkpieceFromDXF,
            UPDATE_CAMERA_FEED: self.updateCameraFeed,
            CREATE_WORKPIECE_TOPIC: self.createWorkpieceAsync,
            SAVE_ROBOT_CALIBRATION_POINT: self.saveRobotCalibrationPoint,
            HELP: self.handleHelp,
            GO_TO_LOGIN_POS: self.handleLoginPos,
            START_CONTOUR_DETECTION: self.handleStartContourDetection,
            STOP_CONTOUR_DETECTION: self.handleStopContourDetection,
            WORPIECE_GET_ALL: self.handleGetAllWorpieces,
            TEST_RUN: self.handleTestRun,
            RAW_MODE_ON: self.handleRawModeOn,
            RAW_MODE_OFF: self.handleRawModeOff,
            "executeFromGallery": self.handleExecuteFromGallery
        }

    def handleRawModeOn(self):
        print("Enabling raw mode")
        request = Constants.CAMERA_ACTION_RAW_MODE_ON
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error enabling raw mode:", response.message)

        return response.status

    def handleRawModeOff(self):
        request = Constants.CAMERA_ACTION_RAW_MODE_OFF
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        if response.status == Constants.RESPONSE_STATUS_ERROR:
            print("Error disabling raw mode:", response.message)

        return response.status

    def handleExecuteFromGallery(self, workpiece):
        self.requestSender.sendRequest("handleExecuteFromGallery", workpiece)

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

    def handleStop(self):
        request = Constants.ROBOT_STOP
        response = self.requestSender.sendRequest(request)

    def handleStartContourDetection(self):
        self.requestSender.sendRequest(Constants.START_CONTOUR_DETECTION)

    def handleStopContourDetection(self):
        self.requestSender.sendRequest(Constants.STOP_CONTOUR_DETECTION)

    def handleGetAllWorpieces(self):
        res = self.requestSender.sendRequest(Constants.WORKPIECE_GET_ALL)
        print("res", res)
        return res

    def handleHelp(self):
        self.logger.debug(f"{self.logTag}] [Method: handleHelp] HELP BUTTON PRESSED'")

    def handleGetSettings(self):
        robotSettingsRequest = Constants.SETTINGS_ROBOT_GET
        cameraSettingsRequest = Constants.SETTINGS_CAMERA_GET
        glueSettingsRequest = Constants.SETTINGS_GLUE_GET

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

        request = Constants.WORKPIECE_SAVE_DXF
        responseDict = self.requestSender.sendRequest(request, data)
        response = Response.from_dict(responseDict)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            message = "Error saving workpieces"
            return False, response.message

        return True, response.message

    def saveWorkpiece(self, data):
        request = Constants.WORKPIECE_SAVE
        responseDict = self.requestSender.sendRequest(request, data)
        response = Response.from_dict(responseDict)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            message = "Error saving workpieces"
            return False, response.message

        return True, response.message

    def handleSaveWorkAreaPoints(self, points):
        print("handleSaveWorkAreaPoints Saving work area points:", points)
        request = Constants.CAMERA_ACTION_SAVE_WORK_AREA_POINTS

        self.requestSender.sendRequest(request, data=points)

    def handleTestCalibration(self):
        request = Constants.CAMERA_ACTION_TEST_CALIBRATION
        self.requestSender.sendRequest(request)

    def handleCalibrateRobot(self):
        request = Constants.ROBOT_CALIBRATE
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

        return True, response.message

    def handleCalibrateCamera(self):
        """ MOVE ROBOT TO CALIBRATION POSITION"""
        print("Calibrating camera")
        request = Constants.ROBOT_MOVE_TO_CALIB_POS
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        if response.status != Constants.RESPONSE_STATUS_SUCCESS:
            self.logger.debug(f"{self.logTag}] [Method: handleCalibrate] Error moving to calib pos")

        request = Constants.CAMERA_ACTION_RAW_MODE_ON
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)

        FeedbackProvider.showPlaceCalibrationPattern()

        request = Constants.CAMERA_ACTION_CALIBRATE
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)

        if response.status == Constants.RESPONSE_STATUS_ERROR:
            # FeedbackProvider.showMessage(response.message)
            request = Constants.CAMERA_ACTION_RAW_MODE_OFF
            response = self.requestSender.sendRequest(request)
            response = Response.from_dict(response)
            return False, response.message

        FeedbackProvider.showMessage("Camera Calibration Success\nMove the chessboard")

    def handleCaptureCalibrationImage(self):
        request = Constants.CAMERA_ACTION_CAPTURE_CALIBRATION_IMAGE
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

        request = Constants.ROBOT_CALIBRATE
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
        request = Constants.ROBOT_SAVE_POINT
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
        response = self.requestSender.sendRequest(QR_LOGIN)
        # response = Response.from_dict(response)
        return response

    def handleLogin(self, username, password):
        request = "login"
        response = self.requestSender.sendRequest(request, data=[username, password])
        print("Response: ", response)

        message = response.message

        return message

    def updateSettings(self, key, value, className):
        if className == CameraSettingsTabLayout.__name__:
            resource = Constants.REQUEST_RESOURCE_CAMERA
            request = Constants.SETTINGS_CAMERA_SET
        elif className == ContourSettingsTabLayout.__name__:
            resource = Constants.REQUEST_RESOURCE_CAMERA
            request = Constants.SETTINGS_CAMERA_SET
        elif className == RobotSettingsTabLayout.__name__:
            resource = Constants.REQUEST_RESOURCE_ROBOT
            request = Constants.SETTINGS_ROBOT_SET
        elif className == GlueSettingsTabLayout.__name__:
            print("Updating Settings Glue", key, value)
            resource = Constants.REQUEST_RESOURCE_GLUE
            request = Constants.SETTINGS_GLUE_SET
        else:
            self.logger.error(f"{self.logTag}] Updating Unknown Settings {className} : {key} {value}")
            return

        data = {"header": resource,
                key: value}

        self.requestSender.sendRequest(request, data)

    """ REFACTORED METHODS BELOW """

    def updateCameraFeed(self):

        request = Constants.CAMERA_ACTION_GET_LATEST_FRAME
        responseDict = self.requestSender.sendRequest(request)
        response = Response.from_dict(responseDict)
        # print("Update camera feed response, ",response)
        if response.status != Constants.RESPONSE_STATUS_SUCCESS:
            return
        frame = response.data['frame']
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
        request = Constants.ROBOT_MOVE_TO_LOGIN_POS
        response = self.requestSender.sendRequest(request)
        response = Response.from_dict(response)
        return response.status

    def handleMoveToCalibrationPos(self):
        request = Constants.ROBOT_MOVE_TO_CALIB_POS
        self.requestSender.sendRequest(request)

    def homeRobot(self, asyncParam=True):
        request = Constants.ROBOT_MOVE_TO_HOME_POS

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
        request = Constants.START

        def onSuccess(req, resp):
            if resp.status == Constants.RESPONSE_STATUS_ERROR:
                FeedbackProvider.showMessage(resp.message)
            else:
                pass

        def onError(req, err):
            self.logger.error(f"{self.logTag}] CALLBACK ERROR MESSAGE {err}")

        self._runAsyncRequest(request, onSuccess, onError)

    def createWorkpieceAsync(self, onSuccess, onError=None):
        request = Constants.WORKPIECE_CREATE
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
                print("CreateWorkpieceAsync onSuccess")
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

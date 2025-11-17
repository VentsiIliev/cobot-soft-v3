from modules.shared.v1 import Constants
from modules.shared.v1.Response import Response
from modules.robot.robotService.RobotService import RobotService
from modules.robot.enums.axis import Direction, RobotAxis
import modules.shared.v1.endpoints.robot_endpoints as robot_endpoints


class RobotController:
    """
    RobotController handles high-level robot actions based on API-style or legacy requests.

    It interprets actions like jogging, calibration, homing, moving to positions, and resetting errors,
    delegating the actual execution to RobotService.
    """

    def __init__(self, robotService: RobotService):
        self.robotService = robotService

    def handle(self, request, parts):
        print(f"RobotController.handle -> request: {request}, parts: {parts}")

        try:
            # === MOVEMENT ENDPOINTS ===
            if request in [
                robot_endpoints.ROBOT_MOVE_TO_HOME_POS
            ]:
                return self._handleHome()

            elif request in [
                robot_endpoints.ROBOT_MOVE_TO_LOGIN_POS
            ]:
                return self._handleLoginPos()

            elif request in [
                robot_endpoints.ROBOT_MOVE_TO_CALIB_POS
            ]:
                return self._handleMoveToCalibPose()



            elif request in [
                robot_endpoints.ROBOT_STOP
            ]:
                return self._handleStop()

            # === POSITION / CALIBRATION ===
            elif request in [
                robot_endpoints.ROBOT_MOVE_TO_POSITION
            ]:
                return self._handleMoveToPosition(parts)

            elif request in [
                robot_endpoints.ROBOT_SAVE_POINT
            ]:
                return self._handleSaveCalibrationPoint()

            # === CONFIG / RESET ===
            elif request in [
                robot_endpoints.ROBOT_UPDATE_CONFIG
            ]:
                return self._handleReloadConfig()

            elif request in [
                robot_endpoints.ROBOT_RESET_ERRORS
            ]:
                return self._handleResetErrors()

            elif request in [
                robot_endpoints.ROBOT_GET_CURRENT_POSITION
            ]:
                return self._handleGetCurrentPosition()

            # === JOGGING ===
            elif any(j in request for j in [
                robot_endpoints.ROBOT_ACTION_JOG_X_PLUS,
                robot_endpoints.ROBOT_ACTION_JOG_X_MINUS,
                robot_endpoints.ROBOT_ACTION_JOG_Y_PLUS,
                robot_endpoints.ROBOT_ACTION_JOG_Y_MINUS,
                robot_endpoints.ROBOT_ACTION_JOG_Z_PLUS,
                robot_endpoints.ROBOT_ACTION_JOG_Z_MINUS
            ]):
                return self._handleJog(parts)

            # === SLOT OPERATIONS ===
            elif "slots" in request or "slot" in request:
                return self._handleSlotOperation(request, parts)

            else:
                raise ValueError(f"Unknown robot command: {request}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                status=Constants.RESPONSE_STATUS_ERROR,
                message=f"RobotController internal error: {str(e)}",
                data={}
            ).to_dict()

    # =========================
    # INDIVIDUAL HANDLERS
    # =========================

    def _handleHome(self):
        ret = self.robotService.moveToStartPosition()
        return self._moveSuccess(ret, "Failed moving to home", "Success moving to home")

    def _handleLoginPos(self):
        ret = self.robotService.moveToLoginPosition()
        return self._moveSuccess(ret, "Failed moving to login position", "Success moving to login position")

    def _handleMoveToCalibPose(self):
        ret = self.robotService.moveToCalibrationPosition()
        return self._moveSuccess(ret, "Failed moving to calibration pose", "Success moving to calibration pose")


    def _handleStop(self):
        ret = self.robotService.stopRobot()
        return self._moveSuccess(ret, "Failed stopping robot", "Robot stopped successfully")

    def _handleReloadConfig(self):
        result = self.robotService.loadConfig()
        if result:
            return Response(Constants.RESPONSE_STATUS_SUCCESS, "Robot config reloaded", {}).to_dict()
        return Response(Constants.RESPONSE_STATUS_ERROR, "Failed reloading robot config", {}).to_dict()

    def _handleResetErrors(self):
        ret = self.robotService.robot.resetAllErrors()
        return self._moveSuccess(ret, "Failed resetting robot errors", "Robot errors reset")

    def _handleGetCurrentPosition(self):
        pos = self.robotService.getCurrentPosition()
        if pos is None:
            return Response(Constants.RESPONSE_STATUS_ERROR, "Failed retrieving current position", {}).to_dict()
        return Response(Constants.RESPONSE_STATUS_SUCCESS, "Current position retrieved", {"position": pos}).to_dict()

    def _handleMoveToPosition(self, parts):
        # /api/v1/robot/position/move-to/x/y/z/rx/ry/rz
        try:
            position = [float(p) for p in parts[-6:]]
            ret = self.robotService.moveToPosition(position, 0, 0, 100, 30)
            return self._moveSuccess(ret, "Failed moving to position", "Success moving to position")
        except Exception:
            return Response(Constants.RESPONSE_STATUS_ERROR, "Invalid position format", {}).to_dict()

    def _handleJog(self, parts):
        axis = parts[-3]
        direction = parts[-2]
        step = float(parts[-1]) if parts[-1].isdigit() else 1.0
        ret = self.robotService.startJog(RobotAxis.get_by_string(axis), Direction.get_by_string(direction), step)
        return self._moveSuccess(ret, "Failed JOG", "Success JOG")

    def _handleSlotOperation(self, request, parts):
        try:
            slot_number = int(parts[-2])
            action = parts[-1]
            if action == "pickup":
                ret = self.robotService.pickupGripper(slot_number)
            elif action == "drop":
                ret = self.robotService.dropOffGripper(slot_number)
            else:
                raise ValueError(f"Invalid slot operation '{action}'")

            return self._moveSuccess(ret, f"Failed {action} at slot {slot_number}", f"Success {action} at slot {slot_number}")
        except Exception as e:
            return Response(Constants.RESPONSE_STATUS_ERROR, f"Invalid slot request: {e}", {}).to_dict()

    def _handleSaveCalibrationPoint(self):
        ret = self.robotService.saveCalibrationPoint()
        return self._moveSuccess(ret, "Failed saving calibration point", "Calibration point saved")

    # === Utility ===
    def _moveSuccess(self, ret, fail_msg, success_msg):
        if ret != 0:
            return Response(Constants.RESPONSE_STATUS_ERROR, fail_msg, {}).to_dict()
        return Response(Constants.RESPONSE_STATUS_SUCCESS, success_msg, {}).to_dict()

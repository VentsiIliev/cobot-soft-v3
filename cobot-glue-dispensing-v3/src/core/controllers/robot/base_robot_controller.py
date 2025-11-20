from communication_layer.api.v1 import Constants
from communication_layer.api.v1.Response import Response
from core.controllers.BaseController import BaseController


from core.model.robot.enums.axis import Direction, RobotAxis
import communication_layer.api.v1.endpoints.robot_endpoints as robot_endpoints
from core.services.robot_service.impl.base_robot_service import RobotService


class BaseRobotController(BaseController):
    """
    RobotController handles high-level robot actions based on API-style or legacy requests.

    It interprets actions like jogging, calibration, homing, moving to positions, and resetting errors,
    delegating the actual execution to RobotService.
    """

    def __init__(self, robot_service: RobotService):
        self.robot_service = robot_service
        self._dynamic_handler_resolver = self._resolve_dynamic_handler
        super().__init__()
        self._initialize_handlers()
    # ============================================================
    # REGISTER HANDLERS
    # ============================================================
    def _initialize_handlers(self):
        # MOVEMENT
        self.register_handler(robot_endpoints.ROBOT_MOVE_TO_HOME_POS, self._handle_home)
        self.register_handler(robot_endpoints.ROBOT_MOVE_TO_LOGIN_POS, self._handle_login_pos)
        self.register_handler(robot_endpoints.ROBOT_MOVE_TO_CALIB_POS, self._handle_move_to_calib_pose)
        self.register_handler(robot_endpoints.ROBOT_STOP, self._handle_stop)

        # POSITION / CALIBRATION
        self.register_handler(robot_endpoints.ROBOT_MOVE_TO_POSITION, self._handle_move_to_position)
        self.register_handler(robot_endpoints.ROBOT_SAVE_POINT, self._handleSaveCalibrationPoint)

        # CONFIG / RESET
        self.register_handler(robot_endpoints.ROBOT_UPDATE_CONFIG, self._handle_reload_config)
        self.register_handler(robot_endpoints.ROBOT_RESET_ERRORS, self._handleResetErrors)
        self.register_handler(robot_endpoints.ROBOT_GET_CURRENT_POSITION, self._handle_get_current_position)

        # JOGGING (wrap with lambda to pass parts)
        jog_endpoints = [
            robot_endpoints.ROBOT_ACTION_JOG_X_PLUS,
            robot_endpoints.ROBOT_ACTION_JOG_X_MINUS,
            robot_endpoints.ROBOT_ACTION_JOG_Y_PLUS,
            robot_endpoints.ROBOT_ACTION_JOG_Y_MINUS,
            robot_endpoints.ROBOT_ACTION_JOG_Z_PLUS,
            robot_endpoints.ROBOT_ACTION_JOG_Z_MINUS
        ]
        for ep in jog_endpoints:
            self.register_handler(ep, lambda parts=None: self._handle_jog(parts))

        # SLOT OPERATIONS
        self.register_handler("slot_operation", lambda request,parts: self._handleSlotOperation(request,parts))

    def _resolve_dynamic_handler(self, request):
        if request.startswith("robot/jog"):
            return lambda parts=None: self._handle_jog(parts or request.split("/"))
        return None
    # =========================
    # INDIVIDUAL HANDLERS
    # =========================

    def _handle_home(self):
        ret = self.robot_service.moveToStartPosition()
        return self._moveSuccess(ret, "Failed moving to home", "Success moving to home")

    def _handle_login_pos(self):
        ret = self.robot_service.moveToLoginPosition()
        return self._moveSuccess(ret, "Failed moving to login position", "Success moving to login position")

    def _handle_move_to_calib_pose(self):
        ret = self.robot_service.move_to_calibration_position()
        return self._moveSuccess(ret, "Failed moving to calibration pose", "Success moving to calibration pose")

    def _handle_stop(self):
        ret = self.robot_service.stop_motion()
        return self._moveSuccess(ret, "Failed stopping robot", "Robot stopped successfully")

    def _handle_reload_config(self):
        result = self.robot_service.reload_config()
        if result:
            return Response(Constants.RESPONSE_STATUS_SUCCESS, "Robot config reloaded", {}).to_dict()
        return Response(Constants.RESPONSE_STATUS_ERROR, "Failed reloading robot config", {}).to_dict()

    def _handleResetErrors(self):
        ret = self.robot_service.robot.resetAllErrors()
        return self._moveSuccess(ret, "Failed resetting robot errors", "Robot errors reset")

    def _handle_get_current_position(self):
        pos = self.robot_service.get_current_position()
        if pos is None:
            return Response(Constants.RESPONSE_STATUS_ERROR, "Failed retrieving current position", {}).to_dict()
        return Response(Constants.RESPONSE_STATUS_SUCCESS, "Current position retrieved", {"position": pos}).to_dict()

    def _handle_move_to_position(self, parts):
        # /api/v1/robot/position/move-to/x/y/z/rx/ry/rz
        try:
            position = [float(p) for p in parts[-6:]]
            ret = self.robot_service.move_to_position(position, 0, 0, 100, 30)
            return self._moveSuccess(ret, "Failed moving to position", "Success moving to position")
        except Exception:
            return Response(Constants.RESPONSE_STATUS_ERROR, "Invalid position format", {}).to_dict()

    def _handle_jog(self, parts):
        """Handle jogging requests. Supports both API-style and legacy string formats.

        Expected parts examples:
          - ['/api','v1','robot','jog','x','plus','5']
          - ['robot','jog','Z','+','5.0']
        """
        # Defensive parsing of axis / direction / step from the last three parts
        if len(parts) < 3:
            return Response(Constants.RESPONSE_STATUS_ERROR, "Invalid JOG request format", {}).to_dict()

        axis = parts[-3]
        direction_str = parts[-2]
        step_str = parts[-1]

        # Parse step as float robustly
        try:
            step = float(step_str)
        except Exception:
            step = 1.0

        # Normalize direction: accept '+', '-', 'plus', 'minus', or textual names
        dir_upper = str(direction_str).strip().lower()
        if dir_upper in ['+', 'plus', 'p', 'add']:
            direction = Direction.PLUS
        elif dir_upper in ['-', 'minus', 'm', 'sub']:
            direction = Direction.MINUS
        else:
            try:
                direction = Direction.get_by_string(direction_str)
            except Exception:
                return Response(Constants.RESPONSE_STATUS_ERROR, f"Invalid JOG direction: {direction_str}", {}).to_dict()

        # Normalize axis and get enum
        try:
            axis_enum = RobotAxis.get_by_string(axis)
        except Exception:
            return Response(Constants.RESPONSE_STATUS_ERROR, f"Invalid JOG axis: {axis}", {}).to_dict()

        ret = self.robot_service.start_jog(axis_enum, direction, step)
        return self._moveSuccess(ret, "Failed JOG", "Success JOG")

    def _handleSlotOperation(self, request,parts):
        try:
            slot_number = int(parts[-2])
            action = parts[-1]
            if action == "pickup":
                ret = self.robot_service.pickupGripper(slot_number)
            elif action == "drop":
                ret = self.robot_service.dropOffGripper(slot_number)
            else:
                raise ValueError(f"Invalid slot operation '{action}'")

            return self._moveSuccess(ret, f"Failed {action} at slot {slot_number}", f"Success {action} at slot {slot_number}")
        except Exception as e:
            return Response(Constants.RESPONSE_STATUS_ERROR, f"Invalid slot request {request}: {e}", {}).to_dict()

    def _handleSaveCalibrationPoint(self):
        # ret = self.robot_service.saveCalibrationPoint()
        return self._moveSuccess(False, "Not Implemented", "Calibration point saved")

    # === Utility ===
    def _moveSuccess(self, ret, fail_msg, success_msg):
        if ret != 0:
            return Response(Constants.RESPONSE_STATUS_ERROR, fail_msg, {}).to_dict()
        return Response(Constants.RESPONSE_STATUS_SUCCESS, success_msg, {}).to_dict()

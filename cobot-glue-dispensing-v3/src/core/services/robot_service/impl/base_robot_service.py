import threading
import time
from typing import Optional

from backend.system.utils.custom_logging import log_info_message, log_debug_message, setup_logger, LoggerContext
from backend.system.utils import robot_utils
from communication_layer.api.v1.topics import RobotTopics, VisionTopics
from core.application.interfaces.ISubscriptionModule import ISubscriptionModule
from core.application_state_management import SubscriptionManger
from core.model.robot.IRobot import IRobot
from core.services.robot_service.impl.robot_monitor.state_manager import BaseRobotServiceStateManager
from core.services.robot_service.interfaces.IRobotService import IRobotService
from core.system_state_management import ServiceState
from frontend.core.services.domain.RobotService import RobotAxis

from core.model.robot.enums.axis import Direction
from modules.shared.MessageBroker import MessageBroker

ENABLE_ROBOT_SERVICE_LOGGING = True


class CancellationToken:
    """
    Cancellation token for controlling robot operations.

    This provides a clean way to cancel robot operations without
    directly coupling to state machines.
    """

    def __init__(self):
        self._cancelled = threading.Event()
        self._reason = None
        self._timestamp = None

    def cancel(self, reason: str = "cancelled"):
        """Cancel the operation."""
        self._cancelled.set()
        self._reason = reason
        self._timestamp = time.time()

    def is_cancelled(self) -> bool:
        """Check if the operation has been cancelled."""
        return self._cancelled.is_set()

    def reset(self):
        """Reset the cancellation token."""
        self._cancelled.clear()
        self._reason = None
        self._timestamp = None

    def get_cancellation_reason(self) -> Optional[str]:
        """Get the reason for cancellation."""
        return self._reason

    def get_cancellation_timestamp(self) -> Optional[float]:
        """Get the timestamp when cancellation occurred."""
        return self._timestamp

class RobotServiceMessagePublisher:
    def __init__(self,broker,service_id):
        self.broker = broker
        self.service_id = service_id
        self.state_topic = RobotTopics.SERVICE_STATE
        self.trajectory_stop_topic = RobotTopics.TRAJECTORY_STOP
        self.trajectory_break_topic = RobotTopics.TRAJECTORY_BREAK
        self.threshold_region_topic = VisionTopics.THRESHOLD_REGION

    def publish_state(self,state):
        self.broker.publish(self.state_topic, state)

    def publish_trajectory_stop_topic(self):
        self.broker.publish(self.trajectory_stop_topic, "")

    def publish_trajectory_break_topic(self):
        self.broker.publish(self.trajectory_break_topic, {})

    def publish_threshold_region_topic(self,region):
        self.broker.publish(self.threshold_region_topic, {"region":region})

class RobotService(IRobotService):
    def __init__(self, robot:IRobot, settings_service, robot_state_manager):
        self.robot = robot
        self.service_id = "robot_service"
        self.settings_service = settings_service
        self.robot_config = self.settings_service.robot_config
        self._operation_lock = threading.Lock()
        self.enable_logging = ENABLE_ROBOT_SERVICE_LOGGING
        self.robot_state_manager = robot_state_manager
        self.broker = MessageBroker()
        self.message_publisher = RobotServiceMessagePublisher(self.broker,self.service_id)
        self.state_manager = BaseRobotServiceStateManager(ServiceState.INITIALIZING, self.message_publisher, self,self.service_id)
        self.subscription_manager = SubscriptionManger(self, self.broker,self.get_subscriptions())
        self.subscription_manager.subscribe_all()

        self.robot_state_manager.start_monitoring()

        self.tool_manager = None
        if self.enable_logging:
            self.logger = setup_logger("RobotService")
        else:
            self.logger = None
        self.logger_context = LoggerContext(enabled=self.enable_logging,
                                            logger=self.logger)

    @property
    def current_tool(self):
        return self.tool_manager.current_gripper

    def get_subscriptions(self):
        subscriptions = []
        robot_state_subscription = [self.robot_state_manager.robotStateTopic,self.state_manager.onRobotStateUpdate]
        subscriptions.append(robot_state_subscription)
        return subscriptions

    def moveToStartPosition(self, z_offset=0):
        """Move robot to start position"""
        try:
            position = self.robot_config.getHomePositionParsed()
            print(f"Position before z offset: {position}")
            # apply the z offset to account for the calibration pattern thickness
            position[2] += z_offset
            print(f"Position with z offset: {position}")
            config = self.robot_config.getHomePosConfig()

            ret = self.robot.move_cartesian(
                position=position,
                tool=self.robot_config.robot_tool,
                user=self.robot_config.robot_user,
                vel=config.velocity,
                acc=config.acceleration
            )

            print(f"Moving to start position, result: {ret}")
            self.message_publisher.publish_threshold_region_topic("pickup")
            return ret

        except Exception as e:
            print(f"Error moving to start position: {e}")
            return -1

    def pickupGripper(self, gripper_id, callback=None):
        """Delegate pickup to ToolManager"""
        success, message = self.tool_manager.pickup_gripper(gripper_id)
        if callback:
            callback(success, message)
        return success, message

    def dropOffGripper(self, gripper_id, callback=None):
        """Delegate drop off to ToolManager"""
        success, message = self.tool_manager.drop_off_gripper(gripper_id)
        if callback:
            callback(success, message)
        return success, message

    def moveToLoginPosition(self):
        ret = None
        currentPos = self.get_current_position()
        x, y, z, rx, ry, rz = currentPos

        if y > 350:
            ret = self.move_to_calibration_position()
            if ret != 0:
                return ret

            ret = self.moveToStartPosition()
            if ret != 0:
                return ret
        else:
            ret = self.moveToStartPosition()
            if ret != 0:
                return ret

        position = self.robot_config.getLoginPositionParsed()  # This already handles None case
        loginPositionConfig = self.robot_config.getLoginPosConfig()
        velocity = loginPositionConfig.velocity
        acceleration = loginPositionConfig.acceleration
        ret = self.robot.move_cartesian(position=position,
                                  tool=self.robot_config.robot_tool,
                                  user=self.robot_config.robot_user,
                                  vel=velocity,
                                  acc=acceleration)
        return ret

    def move_to_calibration_position(self,z_offset=0):
        """Move robot to calibration position"""
        try:
            position = self.robot_config.getCalibrationPositionParsed()
            # apply the z offset to account for the calibration pattern thickness
            position[2] += z_offset
            config = self.robot_config.getCalibrationPosConfig()

            ret = self.robot.move_cartesian(
                position=position,
                tool=self.robot_config.robot_tool,
                user=self.robot_config.robot_user,
                vel=config.velocity,
                acc=config.acceleration
            )

            self.message_publisher.publish_threshold_region_topic("spray")
            return ret

        except Exception as e:
            print(f"Error moving to calibration position: {e}")
            return -1

    def reload_config(self):
        self.robot_config = self.settings_service.reload_robot_config()

    def stop_motion(self)-> bool:
        """Stop robot motion safely"""
        result = False
        with self._operation_lock:
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    result = self.robot.stop_motion()
                    log_info_message(self.logger_context, message=f"Robot motion stopped, result: {result}")
                    result = True
                    break
                except Exception as e:
                    if "Request-sent" in str(e) and attempt < max_attempts - 1:
                        time.sleep(0.1)  # Wait and retry
                        continue
                    else:
                        raise
        return result

    def start_jog(self, axis, direction, step):
        step = float(step)
        # Set sign based on direction
        if direction == Direction.MINUS:
            temp_step = abs(step)
            print(f"Direction minus, step set to {temp_step}")
        else:
            temp_step = -abs(step)
            print(f"Direction plus, step set to {temp_step}")

        if axis == RobotAxis.Z:
            currentPos = self.get_current_position()
            proposedZ = currentPos[2] + temp_step
            print(f"RobotService: startJog: current Z: {currentPos[2]}, proposed Z: {proposedZ}")
            if proposedZ < self.robot_config.safety_limits.z_min:
                print(
                    f"Jog Z to {proposedZ}mm exceeds minimum limit of {self.robot_config.safety_limits.z_min}mm. Jog cancelled.")
                return -1
            if proposedZ > self.robot_config.safety_limits.z_max:
                print(
                    f"Jog Z to {proposedZ}mm exceeds maximum limit of {self.robot_config.safety_limits.z_max}mm. Jog cancelled.")
                return -1

        result = self.robot.start_jog(axis=axis,
                                      direction=direction,
                                      step=step,
                                      vel=self.robot_config.getJogConfig().velocity,
                                      acc=self.robot_config.getJogConfig().acceleration)
        print(f"RobotService: startJog: result: {result}")
        return result

    def is_within_safety_limits(self, position):
        """Check if position is within safety limits"""
        safety_config = self.robot_config.safety_limits
        pos_x, pos_y, pos_z = position[0], position[1], position[2]

        if pos_z > safety_config.z_max:
            print(f"Position Z {pos_z} exceeds maximum limit of {safety_config.z_max}")
            return False

        if pos_z < safety_config.z_min:
            print(f"Position Z {pos_z} is below minimum limit of {safety_config.z_min}")
            return False

        return True

    def move_to_position(self, position, tool, workpiece, velocity, acceleration, waitToReachPosition=False):
        """
        Moves the robot to a specified position with optional waiting.

        Args:
            position (list): Target Cartesian position
            tool (int): Tool frame ID
            workpiece (int): Workpiece frame ID
            velocity (float): Speed
            acceleration (float): Acceleration
            waitToReachPosition (bool): If True, waits for robot to reach position
        """

        # check if position is within safety limits
        result = self.is_within_safety_limits(position)
        if not result:
            return False

        ret = self.robot.move_cartesian(position, tool, workpiece, vel=velocity, acc=acceleration)

        if waitToReachPosition:  # TODO comment out when using test robot
            self._waitForRobotToReachPosition(position, 2, delay=0.1)

        # self.robot.move_liner(position, tool, workpieces, vel=velocity, acc=acceleration,blendR=20)
        return ret

    def _waitForRobotToReachPosition(self, endPoint, threshold, delay, timeout=1, cancellation_token=None):
        """Wait for robot to reach target position with state awareness"""
        start_time = time.time()
        log_info_message(self.logger_context,
                         message=f"_waitForRobotToReachPosition CALLED WITH  endPoint={endPoint},threshold={threshold},delay = {delay},timeout = {timeout}")

        while True:
            print(f"RobotService: Waiting for robot to reach position {endPoint} with threshold {threshold}mm")
            # Check cancellation token (replaces state machine dependency)
            if cancellation_token is not None and cancellation_token.is_cancelled():
                log_debug_message(self.logger_context,
                                  message=f"Operation cancelled via cancellation token: {cancellation_token.get_cancellation_reason()}")
                return False

            # Check timeout
            if time.time() - start_time > timeout:
                log_debug_message(self.logger_context,
                                  message=f"Timeout reached while waiting for robot position {endPoint}")
                return False

            # Check position
            current_position = self.get_current_position()
            if current_position is None:
                time.sleep(0.1)
                continue

            distance = robot_utils.calculate_distance_between_points(current_position, endPoint)

            if distance < threshold:
                log_debug_message(self.logger_context,
                                  message=f"Robot reached target position {endPoint} within threshold {threshold}mm")
                return True

            time.sleep(0.01)

    def add_subscription_module(self, module: "ISubscriptionModule"):
        """
        Attach a subscription module to this robot service.
        The module will register itself to the service's subscription manager.
        """
        if not self.subscription_manager:
            raise RuntimeError("No subscription manager set for this robot service")

        module.register(self.subscription_manager)
        print(f"Subscription module {module} added to robot service.")


    def get_current_velocity(self):
        """Get current robot velocity"""
        return self.robot_state_manager.velocity

    def get_current_acceleration(self):
        """Get current robot acceleration"""
        return self.robot_state_manager.acceleration

    def get_current_position(self):
        """Get current robot position"""
        return self.robot_state_manager.position
        # return self.robot.getCurrentPosition()

    def enable_robot(self):
        """Enable robot motion"""
        self.robot.enable()
        print("Robot enabled")

    def disable_robot(self):
        """Disable robot motion"""
        self.robot.disable()
        print("Robot disabled")

    def get_state(self):
        """Get current robot state"""
        return self.robot_state_manager.state

    def get_state_topic(self) -> str:
        return self.message_publisher.state_topic
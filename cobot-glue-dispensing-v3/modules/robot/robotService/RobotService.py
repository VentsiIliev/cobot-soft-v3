"""
Decoupled RobotService implementation with cancellation token support
for robust pause/resume functionality and clean operation control.
No longer dependent on external state machines.
"""

import threading
import time
from typing import Optional

from modules.shared.MessageBroker import MessageBroker
from modules.shared.shared.settings.robotConfig.robotConfigModel import RobotConfig
from modules.robot.enums.axis import Axis, Direction
from modules.robot.RobotUtils import calculate_distance_between_points
from modules.robot.robotService.RobotServiceMessagePublisher import RobotServiceMessagePublisher
from modules.robot.robotService.RobotServiceStateManager import RobotServiceStateManager
from modules.robot.robotService.RobotServiceSubscriptionManager import RobotServiceSubscriptionManager
from modules.robot.robotService.RobotStateManager import RobotStateManager
from modules.robot.robotService.enums.RobotServiceState import RobotServiceState
from src.robot_application.glue_dispensing_application.tools.Laser import Laser
from src.robot_application.glue_dispensing_application.tools.ToolChanger import ToolChanger
from src.robot_application.glue_dispensing_application.tools.VacuumPump import VacuumPump
from src.backend.system.utils.custom_logging import setup_logger, \
    LoggerContext, log_info_message, log_debug_message

ENABLE_ROBOT_SERVICE_LOGGING = True

if ENABLE_ROBOT_SERVICE_LOGGING:
    robot_service_logger = setup_logger("RobotService")
else:
    robot_service_logger = None


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

class RobotService:
    """
    RobotService implementation with cancellation token support
    for decoupled pause/resume functionality and clean operation control.
    """
    
    RX_VALUE = 180
    RY_VALUE = 0
    RZ_VALUE = 0
    
    def __init__(self, robot, settingsService):
        """Initialize the robot service"""
        self.robot_service_logger_context = LoggerContext(enabled=ENABLE_ROBOT_SERVICE_LOGGING,
                                            logger=robot_service_logger)

        # Robot and settings
        self.robot = robot
        self.robot.printSdkVersion()
        self.settingsService = settingsService
        self.robot_config: RobotConfig = self.settingsService.robot_config
        
        # Robot state monitoring
        self.robot_state_manager_cycle_time = 0.03  # 30ms cycle time
        self.robotStateManager = RobotStateManager(robot_ip=self.robot_config.robot_ip,
                                                   cycle_time=self.robot_state_manager_cycle_time)
        self.robotStateManager.start_monitoring()

        self.broker = MessageBroker()
        self.message_publisher = RobotServiceMessagePublisher(self.broker)
        self.state_manager= RobotServiceStateManager(RobotServiceState.INITIALIZING,self.message_publisher,self)
        self.subscription_manager = RobotServiceSubscriptionManager(self,self.broker)
        self.state_manager.start_state_publisher_thread()
        self.subscription_manager.subscribe_robot_state_topic()
        self.subscription_manager.subscribe_glue_process_state_topic()
        self.state_topic = self.message_publisher.state_topic

        # Tools and peripherals
        self.pump = VacuumPump()
        self.laser = Laser()
        self.toolChanger = ToolChanger()
        self.currentGripper = None
        # Thread safety
        self._operation_lock = threading.Lock()
        self._stop_thread = threading.Event()


    def _stop_robot_motion(self):
        """Stop robot motion safely"""
        with self._operation_lock:
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    result = self.robot.stopMotion()
                    log_info_message(self.robot_service_logger_context,message =f"Robot motion stopped, result: {result}")

                    break
                except Exception as e:
                    if "Request-sent" in str(e) and attempt < max_attempts - 1:
                        time.sleep(0.1)  # Wait and retry
                        continue
                    else:
                        raise
    
    def _waitForRobotToReachPosition(self, endPoint, threshold,delay, timeout=1,cancellation_token = None):
        """Wait for robot to reach target position with state awareness"""
        start_time = time.time()
        log_info_message(self.robot_service_logger_context,message=f"_waitForRobotToReachPosition CALLED WITH  endPoint={endPoint},threshold={threshold},delay = {delay},timeout = {timeout}")


        while True:
            print(f"RobotService: Waiting for robot to reach position {endPoint} with threshold {threshold}mm")
            # Check cancellation token (replaces state machine dependency)
            if cancellation_token is not None and cancellation_token.is_cancelled():
                log_debug_message(self.robot_service_logger_context,message=f"Operation cancelled via cancellation token: {cancellation_token.get_cancellation_reason()}")
                return False

            # Check timeout
            if time.time() - start_time > timeout:
                log_debug_message(self.robot_service_logger_context,message=f"Timeout reached while waiting for robot position {endPoint}")
                return False
            
            # Check position
            current_position = self.getCurrentPosition()
            if current_position is None:
                time.sleep(0.1)
                continue

            distance = calculate_distance_between_points(current_position,endPoint)
            
            if distance < threshold:
                log_debug_message(self.robot_service_logger_context,message=f"Robot reached target position {endPoint} within threshold {threshold}mm")
                return True
            
            time.sleep(0.01)

    def move_to_nesting_capture_position(self, z_offset=0):
        ret = self.moveToStartPosition(z_offset=z_offset)

        if ret != 0:
            return ret

        target_pose = self.robot_config.getHomePositionParsed()
        target_pose[2] += z_offset  # apply z_offset
        self._waitForRobotToReachPosition(target_pose, 1, 0.1)
        return  ret

    def move_to_spray_capture_position(self, z_offset=0):
        ret = self.moveToCalibrationPosition(z_offset=z_offset)

        if ret != 0:
            return ret

        target_pose = self.robot_config.getCalibrationPositionParsed()
        target_pose[2] += z_offset  # apply z_offset
        self._waitForRobotToReachPosition(target_pose, 1, 0.1)
        return ret
    # Movement methods
    def moveToCalibrationPosition(self,z_offset=0):
        """Move robot to calibration position"""
        try:
            position = self.robot_config.getCalibrationPositionParsed()
            # apply the z offset to account for the calibration pattern thickness
            position[2] += z_offset
            config = self.robot_config.getCalibrationPosConfig()
            
            ret = self.robot.moveCart(
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

    def moveToLoginPosition(self):
        ret = None
        currentPos = self.getCurrentPosition()
        x, y, z, rx, ry, rz = currentPos

        if y > 350:
            ret = self.moveToCalibrationPosition()
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
        ret = self.robot.moveCart(position=position,
                                  tool=self.robot_config.robot_tool,
                                  user=self.robot_config.robot_user,
                                  vel=velocity,
                                  acc=acceleration)
        return ret

    def moveToStartPosition(self,z_offset=0):
        """Move robot to start position"""
        try:
            position = self.robot_config.getHomePositionParsed()
            print(f"Position before z offset: {position}")
            # apply the z offset to account for the calibration pattern thickness
            position[2] += z_offset
            print(f"Position with z offset: {position}")
            config = self.robot_config.getHomePosConfig()
            
            ret = self.robot.moveCart(
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

    def get_current_velocity(self):
        """Get current robot velocity"""
        return self.robotStateManager.velocity

    def get_current_acceleration(self):
        """Get current robot acceleration"""
        return self.robotStateManager.acceleration

    def getCurrentPosition(self):
        """Get current robot position"""
        return self.robotStateManager.position
        # return self.robot.getCurrentPosition()
    
    def enableRobot(self):
        """Enable robot motion"""
        self.robot.enable()
        print("Robot enabled")
    
    def disableRobot(self):
        """Disable robot motion"""
        self.robot.disable()
        print("Robot disabled")
    
    def stopRobot(self):
        """Stop robot motion"""
        return self.robot.stopMotion()

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

    def pickupGripper(self, gripperId, callBack=None):
        """
              Picks up a gripper from the tool changer.

              Args:
                  gripperId (int): ID of the gripper to pick
                  callBack (function, optional): Optional callback after pickup

              Returns:
                  tuple: (bool, message)
              """

        # check if gripper is not already picked
        if self.currentGripper == gripperId:
            message = f"Gripper {gripperId} is already picked"
            print(message)
            return False, message

        slotId = self.toolChanger.getSlotIdByGrippedId(gripperId)
        # if not self.toolChanger.isSlotOccupied(slotId):
        #     message = f"Slot {slotId} is empty"
        #     print(message)
        #     return False, message

        self.toolChanger.setSlotAvailable(slotId)

        # ret = self.robot.moveCart([-206.239, -180.406, 726.327, 180, 0, 101], 0, 0, 30, 30)
        # print("move before pickup: ",ret)
        if gripperId == 0:
            config = self.robot_config.getSlot0PickupConfig()
            positions = self.robot_config.getSlot0PickupPointsParsed()
        elif gripperId == 1:
            config = self.robot_config.getSlot1PickupConfig()
            positions = self.robot_config.getSlot1PickupPointsParsed()
        # elif gripperId == 2:
        #     """ADD LOGIC FOR DROPPING OFF TOOL 2 -> LASER"""
        #     config = self.robot_config.getSlot2PickupConfig()
        #     positions = self.robot_config.getSlot2DropoffPointsParsed()
        elif gripperId == 4:
            """ADD LOGIC FOR DROPPING OFF TOOL 4 -> DOUBLE GRIPPER"""
            config = self.robot_config.getSlot4PickupConfig()
            positions = self.robot_config.getSlot4PickupPointsParsed()
        else:
            raise ValueError("UNSUPPORTED GRIPPER ID: ", gripperId)

        try:
            for pos in positions:
                print("Moving to position: ", pos)
                self.robot.moveL(position=pos,
                                 tool=self.robot_config.robot_tool,
                                 user=self.robot_config.robot_tool,
                                 vel=config.velocity,
                                 acc=config.acceleration,
                                 blendR=1)
        except Exception as e:
            import traceback
            traceback.print_exc()

        self.moveToStartPosition()
        self.currentGripper = gripperId
        return True, None

    def dropOffGripper(self, gripperId, callBack=None):
        """
              Drops off the currently held gripper into a specified slot.

              Args:
                  slotId (int): Target slot ID
                  callBack (function, optional): Optional callback after drop off

              Returns:
                  tuple: (bool, message)
              """
        gripperId = int(gripperId)
        slotId = self.toolChanger.getSlotIdByGrippedId(gripperId)
        # print("Drop off gripper: ", gripperId)
        if self.toolChanger.isSlotOccupied(slotId):
            message = f"Slot {slotId} is taken"
            print(message)
            return False, message


        self.toolChanger.setSlotNotAvailable(slotId)

        if gripperId == 0:
            config = self.robot_config.getSlot0DropoffConfig()
            positions = self.robot_config.getSlot0DropoffPointsParsed()
        elif gripperId == 1:
            print("RobotService.dropOffGripper: Dropping off gripper 1")
            config = self.robot_config.getSlot1DropoffConfig()
            positions = self.robot_config.getSlot1DropoffPointsParsed()
        # elif gripperId == 2:
        #     """ADD LOGIC FOR DROPPING OFF TOOL 2 -> LASER"""
        #     config = self.robot_config.getSlot2DropoffConfig()
        #     positions = self.robot_config.getSlot2DropoffPointsParsed()
        elif gripperId == 4:
            """ADD LOGIC FOR DROPPING OFF TOOL 4 -> DOUBLE GRIPPER"""
            config = self.robot_config.getSlot4DropoffConfig()
            positions = self.robot_config.getSlot4DropoffPointsParsed()
        else:
            raise ValueError("UNSUPPORTED GRIPPER ID: ", gripperId)

        for pos in positions:


            ret = self.robot.moveL(position=pos,
                             tool=self.robot_config.robot_tool,
                             user=self.robot_config.robot_user,
                             vel=config.velocity,
                             acc=config.acceleration,
                             blendR=1)
            print("move before drop off: ", ret)

        # self.moveToStartPosition()

        self.currentGripper = None
        return True, None

    def startJog(self, axis, direction, step):
        step = float(step)
        # Set sign based on direction
        if direction == Direction.MINUS:
            temp_step = abs(step)
            print(f"Direction minus, step set to {temp_step}")
        else:
            temp_step = -abs(step)
            print(f"Direction plus, step set to {temp_step}")

        if axis == Axis.Z:
            currentPos = self.getCurrentPosition()
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

        result = self.robot.startJog(axis=axis,
                                     direction=direction,
                                     step=step,
                                     vel=self.robot_config.getJogConfig().velocity,
                                     acc=self.robot_config.getJogConfig().acceleration)
        print(f"RobotService: startJog: result: {result}")
        return result

    def moveToPosition(self, position, tool, workpiece, velocity, acceleration, waitToReachPosition=False):
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


        ret = self.robot.moveCart(position, tool, workpiece, vel=velocity, acc=acceleration)

        if waitToReachPosition:  # TODO comment out when using test robot
            self._waitForRobotToReachPosition(position, 2, delay=0.1)

        # self.robot.moveL(position, tool, workpieces, vel=velocity, acc=acceleration,blendR=20)
        return ret

    def stop(self):
        """Gracefully stop the service"""
        print("Stopping NewRobotService...")
        self._stop_thread.set()
        if hasattr(self, 'robotStateManager'):
            self.robotStateManager.stop_monitoring()
        if hasattr(self, 'state_manager'):
            self.state_manager.stop_state_publisher_thread()
        print("NewRobotService stopped")

    def __del__(self):
        """Cleanup when service is destroyed"""
        try:
            self.stop()
        except:
            pass

    def loadConfig(self):
        try:
            self.robot_config = self.settingsService.load_robot_config()
            print("Robot Config reloaded in RobotService: ", self.robot_config)
            return True
        except:
            print("Failed to reload robot config in RobotService")
            return False

   

if __name__ == "__main__":
    robot_state_manager = RobotStateManager(robot_ip="192.168.58.2")
    robot_state_manager.start_thread()

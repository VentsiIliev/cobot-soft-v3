import logging
import platform
import logging
import time

from backend.system.utils.custom_logging import LoggingLevel, log_if_enabled, \
    setup_logger, LoggerContext, log_info_message, log_error_message, log_debug_message

if platform.system() == "Windows":
    from libs.fairino.windows import Robot
elif platform.system() == "Linux":
    logging.info("Linux detected")
    from libs.fairino.linux.fairino import Robot
else:
    raise Exception("Unsupported OS")

from enum import Enum
ENABLE_LOGGING = True  # Enable or disable logging
# Initialize logger if enabled
if ENABLE_LOGGING:
    robot_logger = setup_logger("RobotWrapper")
else:
    robot_logger = None

class TestRobotWrapper:
    """
       A full mock of the Fairino Robot interface.
       Implements every method used by FairinoRobot and returns safe dummy values.
       """

    def __init__(self):
        print("⚙️  TestRobot initialized (mock robot).")

    # --- Motion commands ---
    def MoveCart(self, position, tool, user, vel=100, acc=30):
        print(f"[MOCK] MoveCart -> pos={position}, tool={tool}, user={user}, vel={vel}, acc={acc}")
        return 0

    def MoveL(self, position, tool, user, vel=100, acc=30, blendR=0):
        print(f"[MOCK] MoveL -> pos={position}, tool={tool}, user={user}, vel={vel}, acc={acc}, blendR={blendR}")
        return 0

    def StartJOG(self, ref, nb, dir, vel, acc, max_dis):
        print(f"[MOCK] StartJOG -> ref={ref}, nb={nb}, dir={dir}, vel={vel}, acc={acc}, max_dis={max_dis}")
        return 0

    def StopMotion(self):
        print("[MOCK] StopMotion called")
        return 0

    def ResetAllError(self):
        print("[MOCK] ResetAllError called")
        return 0

    # --- State queries ---
    def GetActualTCPPose(self):
        # print("[MOCK] GetActualTCPPose called")
        # Returning tuple to match expected structure (status, pose)
        return (0, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def GetActualTCPCompositeSpeed(self):
        print("[MOCK] GetActualTCPCompositeSpeed called")
        return (0, [0.0])  # mimic real return: (status, [speed])

    def GetSDKVersion(self):
        print("[MOCK] GetSDKVersion called")
        return "TestRobot SDK v1.0"

    # --- Control ---
    def RobotEnable(self, flag):
        print(f"[MOCK] RobotEnable({flag}) called")
        return 0

    def SetDO(self, portId, value):
        print(f"[MOCK] SetDO -> port={portId}, value={value}")
        return 0


class FairinoRobot:
    """
      A wrapper for the real robot controller, abstracting motion and I/O operations.
      """
    def __init__(self, ip):
        """
               Initializes the robot wrapper and connects to the robot via RPC.

               Args:
                   ip (str): IP address of the robot controller.
               """
        self.ip = ip
        self.robot = Robot.RPC(self.ip)
        # self.robot = TestRobotWrapper()  # For testing purposes, replace with real robot in production
        self.logger_context = LoggerContext(logger=robot_logger, enabled=ENABLE_LOGGING)
        if self.robot is not None:
            log_info_message(self.logger_context, f"RobotWrapper initialized for robot at {self.ip}")
        else:
            log_error_message(self.logger_context, f"Failed to connect to robot at {self.ip}")
            raise ConnectionError(f"Could not connect to robot at {self.ip}")

        """overSpeedStrategy: over speed handling strategy
        0 - strategy off;
        1 - standard;
        2 - stop on error when over speeding;
        3 - adaptive speed reduction, default 0"""
        self.overSpeedStrategy = 3



    def moveCart(self,position, tool, user, vel=100, acc=30):
        """
              Moves the robot in Cartesian space.

              Args:
                  position (list): Target Cartesian position.
                  tool (int): Tool frame ID.
                  user (int): User frame ID.
                  vel (float): Velocity.
                  acc (float): Acceleration.

              Returns:
                  list: Result from robot move command.
              """
        # print position elements type

        # names = ["x", "y", "z", "rx", "ry", "rz"]
        # if position is None:
        #     print("position is None")
        # else:
        #     try:
        #         for i, name in enumerate(names):
        #             val = position[i] if i < len(position) else None
        #             print(f"{name}: value={val}, type={type(val).__name__}")
        #     except Exception as e:
        #         print(f"Error inspecting position: {e}")

        result = self.robot.MoveCart(position, tool, user, vel=vel, acc=acc)
        log_debug_message(self.logger_context, f"MoveCart to {position} with tool {tool}, user {user}, vel {vel}, acc {acc} -> result: {result}")
        return result

    def moveL(self,position, tool, user, vel, acc, blendR):
        """
              Executes a linear movement with blending.

              Args:
                  position (list): Target position.
                  tool (int): Tool frame ID.
                  user (int): User frame ID.
                  vel (float): Velocity.
                  acc (float): Acceleration.
                  blendR (float): Blend radius.

              Returns:
                  list: Result from robot linear move command.
              """

        result = self.robot.MoveL(position, tool, user, vel=vel, acc=acc, blendR=blendR)
        log_debug_message(self.logger_context, f"MoveL to {position} with tool {tool}, user {user}, vel {vel}, acc {acc}, blendR {blendR} -> result: {result}")
        return result

    def getCurrentPosition(self):
        """
              Retrieves the current TCP (tool center point) position.

              Returns:
                  list: Current robot TCP pose.
              """
        try:
            currentPose = self.robot.GetActualTCPPose()
        except Exception as e:
            log_error_message(self.logger_context, f"GetCurrentPosition failed: {e}")
            return None
        # print(f"GetCurrentPosition raw -> {currentPose}")
        # check if int
        if isinstance(currentPose, int):
            currentPose = None
        else:
            currentPose = currentPose[1]
        # log_debug_message(self.logger_context, f"GetCurrentPosition -> {currentPose}")
        return currentPose

    def getCurrentLinerSpeed(self):
        """
               Retrieves the current linear speed of the TCP.

               Returns:
                   float: TCP composite speed.
               """
        res = self.robot.GetActualTCPCompositeSpeed()
        # result = res[0]
        # compSpeed = res[1]
        # linSpeed = compSpeed[0]
        # linSpeed = res[1][0]
        # print(f"result {result}  comp Speed {compSpeed} linSpeed {linSpeed}")
        # return linSpeed
        return res


    def enable(self):
        """
               Enables the robot, allowing motion.
               """
        self.robot.RobotEnable(1)

    def disable(self):
        """
             Disables the robot, preventing motion.
             """
        self.robot.RobotEnable(0)

    def printSdkVersion(self):
        """
              Prints the current SDK version of the robot controller.
              """
        version = self.robot.GetSDKVersion()
        print(version)
        return version


    def setDigitalOutput(self, portId, value):
        """
              Sets a digital output pin on the robot.

              Args:
                  portId (int): Output port number.
                  value (int): Value to set (0 or 1).
              """
        result =  self.robot.SetDO(portId, value)
        log_debug_message(self.logger_context, f"SetDigitalOutput port {portId} to {value} -> result: {result}")
        return result

    def startJog(self,axis,direction,step,vel,acc):
        """
              Starts jogging the robot in a specified axis and direction.

              Args:
                  axis (Axis): Axis to jog.
                  direction (Direction): Jog direction (PLUS or MINUS).
                  step (float): Distance to move.
                  vel (float): Velocity of jog.
                  acc (float): Acceleration of jog.

              Returns:
                  object: Result of the StartJOG command.
              """
        axis = axis.value
        direction = direction.value

        result = self.robot.StartJOG(ref=4,nb=axis,dir=direction,vel=vel,acc=acc,max_dis=step)
        log_debug_message(self.logger_context, f"StartJog axis {axis} direction {direction} step {step} vel {vel} acc {acc} -> result: {result}")
        return result

    def stopMotion(self):
        """
               Stops all current robot motion.

               Returns:
                   object: Result of StopMotion command.
               """
        return self.robot.StopMotion()

    def resetAllErrors(self):
        """
               Resets all current error states on the robot.

               Returns:
                   object: Result of ResetAllError command.
               """
        print(f"RobotWrapper: ResetAllError called")
        return self.robot.ResetAllError()

if __name__ == "__main__":
    # robot = RobotWrapper("192.168.58.2")
    # robot.printSdkVersion()
    # current_pose = robot.getCurrentPosition()
    # print(f"Current Pose: {current_pose}")
    # # current_speed = robot.getCurrentLinerSpeed()
    # # print(f"Current Speed: {current_speed}")

# I will run minimal example
    import time
    robot = FairinoRobot("192.168.58.2")
    robot.printSdkVersion()
    time.sleep(1)
    while True:
        print(robot.getCurrentPosition())
# from tkinter import messagebox
import queue
import cv2
import numpy as np

from API.MessageBroker import MessageBroker
from API.shared.settings.robotConfig.robotConfigModel import RobotConfig
# from pl_gui.contour_editor.temp.testTransformPoints import startPosition

from GlueDispensingApplication.tools.GlueNozzleService import GlueNozzleService
from GlueDispensingApplication.robot.RobotWrapper import RobotWrapper, Axis, Direction
# from system.robot.RobotConfig import *
from GlueDispensingApplication.tools.enums import ToolID
from GlueDispensingApplication.tools.enums.ToolID import ToolID
from GlueDispensingApplication.tools.enums.Gripper import Gripper
from GlueDispensingApplication.tools.VacuumPump import VacuumPump
from GlueDispensingApplication.tools.nozzles.Tool1 import Tool1
from GlueDispensingApplication.tools.nozzles.Tool2 import Tool2
from GlueDispensingApplication.tools.nozzles.Tool3 import Tool3
from GlueDispensingApplication.tools.Laser import Laser
from GlueDispensingApplication.robot import RobotUtils
from GlueDispensingApplication.tools.ToolChanger import ToolChanger
import enum
from API.shared.Contour import Contour
from GlueDispensingApplication.SystemStatePublisherThread import SystemStatePublisherThread
import threading
import time
import math

class RobotServiceState(enum.Enum):
    INITIALIZING = "initializing"
    IDLE = "idle"
    STARTING = "starting"
    PAUSED = "paused"
    STOPPED = "stopped"
    MOVING_TO_FIRST_POINT = "moving_to_first_point"
    EXECUTING_PATH = "executing_path_state"
    TRANSITION_BETWEEN_PATHS = "transition_between_paths"
    COMPLETED = "completed"
    ERROR = "error"

class RobotState(enum.Enum):
    STATIONARY = "stationary"
    ACCELERATING = "accelerating"
    DECELERATING = "decelerating"
    MOVING = "moving"
    ERROR = "error"


class RobotStateManager:
    def __init__(self,robot_ip, controller_cycle_time=0.01, proportional_gain=0.34, speed_threshold=1, accel_threshold=0.001):
        self.robot = RobotWrapper(robot_ip)
        self.pos = None
        self.speed = 0.0
        self.accel = 0.0
        self.robotStateTopic = "robot/state"
        self.robotState = RobotState.STATIONARY  # Initial state

        self.prev_pos = None
        self.prev_time = None
        self.prev_speed = None
        self.trajectoryUpdate = False
        self._stop_event = threading.Event()

        self.following_error_gain = controller_cycle_time / proportional_gain
        self.broker = MessageBroker()

        # Thresholds for determining motion state
        self.speed_threshold = speed_threshold
        self.accel_threshold = accel_threshold

    def compute_speed(self, current_pos, previous_pos, dt):
        dx = current_pos[0] - previous_pos[0]
        dy = current_pos[1] - previous_pos[1]
        dz = current_pos[2] - previous_pos[2]
        distance = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        return distance / dt if dt > 0 else 0.0

    def update_state(self):
        """Update robot motion state based on speed and acceleration."""
        if abs(self.speed) < self.speed_threshold:
            self.robotState = RobotState.STATIONARY
        elif self.accel > self.accel_threshold:
            self.robotState = RobotState.ACCELERATING
        elif self.accel < -self.accel_threshold:
            self.robotState = RobotState.DECELERATING
        else:
            self.robotState = RobotState.MOVING
        # print("Update robot state called:")

    def fetch_position(self):
        while not self._stop_event.is_set():
            current_time = time.time()
            try:
                current_pos = self.robot.getCurrentPosition()
                # print(f"    Robot position fetched: {current_pos}")
            except Exception as e:
                # print(f"    ERROR: Failed to get robot position: {e}")
                self.robotState = RobotState.ERROR
                continue

            if current_pos == None:
                # print("    ERROR: Robot position is None")
                self.robotState = RobotState.ERROR

            self.pos = current_pos


            if self.prev_pos is not None:
                dt = current_time - self.prev_time
                self.speed = self.compute_speed(current_pos, self.prev_pos, dt)

                if self.prev_speed is not None:
                    self.accel = (self.speed - self.prev_speed) / dt

                # Determine current robot state
                self.update_state()
                self.broker.publish(self.robotStateTopic, {"state": self.robotState, "speed": self.speed, "accel": self.accel})

                if self.robotState != RobotState.STATIONARY and self.trajectoryUpdate:

                    x = current_pos[0]
                    y = current_pos[1]

                    transformed_point = self.broker.request("vision/transformToCamera", {"x": x, "y": y})
                    t_x = transformed_point[0]
                    t_y = transformed_point[1]
                    # Scale to trajectory widget dimensions (800x450)
                    t_x_scaled = int(t_x * 0.625)  # 800/1280 = 0.625
                    t_y_scaled = int(t_y * 0.625)  # 450/720 = 0.625

                    self.broker.publish("robot/trajectory/point", {"x": t_x_scaled, "y": t_y_scaled})
                    # print(f"Publishing point: ({t_x_scaled}, {t_y_scaled})")

            self.prev_pos = current_pos
            self.prev_time = current_time
            self.prev_speed = self.speed

            time.sleep(0.01)

    def start_thread(self):
        self._thread = threading.Thread(target=self.fetch_position)
        self._thread.start()

    def stop_thread(self):
        self._stop_event.set()
        self._thread.join()


class RobotService:
    """
     RobotService is a service layer to control and manage robot movements,
     tool operations, grippers, and glue dispensing for industrial automation tasks.
     """
    RX_VALUE = 180
    RY_VALUE = 0
    RZ_VALUE = 0  # TODO: Change to 0


    def __init__(self, robot, settingsService, glueNozzleService: GlueNozzleService = None):
        """
               Initializes the RobotService with robot control object and configuration services.

               Args:
                   robot: Robot controller object
                   settingsService: Settings service to fetch robot motion parameters
                   glueNozzleService (GlueNozzleService, optional): Glue nozzle control service
               """

        self.logTag = "RobotService"
        self.stateTopic = "robot-service/state"
        self.state= RobotServiceState.INITIALIZING
        self.broker = MessageBroker()
        self.statePublisherThread = SystemStatePublisherThread(self.publishState, 1,tag="RobotServiceStatePublisherThread")
        self.statePublisherThread.start()

        self.robot = robot
        self.robot.printSdkVersion()


        self.pump = VacuumPump()
        self.laser = Laser()


        # TODO: FINISH IMPLEMENTATION FOR ROBOT SETTINGS
        self.settingsService = settingsService
        self.robotSettings = self.settingsService.robot_settings
        self.robot_config: RobotConfig= self.settingsService.robot_config
        print("Robot Config in RobotService: ",self.robot_config)
        print("Robot Config Type in RobotService: ",type(self.robot_config))

        self.robotStateManager = RobotStateManager(robot_ip=self.robot_config.robot_ip)
        self.robotStateManager.start_thread()
        self.robotState = None
        self.broker.subscribe(self.robotStateManager.robotStateTopic, self.onRobotStateUpdate)

        self.glueNozzleService = glueNozzleService

        self.debugPath = []
        self.currentGripper = None
        self.toolChanger = ToolChanger()
        self.commandQue = queue.Queue()
        self._stop_thread = threading.Event()
        
        # State persistence for pause/resume functionality
        self.execution_context = {
            'paths': None,
            'spray_on': False,
            'current_path_index': 0,
            'current_point_index': 0,
            'motor_started': False,
            'generator_to_glue_delay': 0,
            'service': None,
            'glueType': None
        }

    def loadConfig(self):
        try:
            self.robot_config = self.settingsService.load_robot_config()
            print("Robot Config reloaded in RobotService: ", self.robot_config)
            return True
        except:
            print("Failed to reload robot config in RobotService")
            return False

    def onRobotStateUpdate(self,state):
        self.robotState = state['state']
        # print(f"    Robot physical state update: {self.robotState} (service state: {self.state})")

        if self.state == RobotServiceState.INITIALIZING and self.robotState == RobotState.STATIONARY:
            print("    -> Robot becoming IDLE (stationary)")
            self.state = RobotServiceState.IDLE


    def publishState(self):
        # print("Publishing state:", self.state)
        self.broker.publish(self.stateTopic,self.state)

    def getMotionParams(self):
        """
             Retrieves motion parameters from robot settings.

             Returns:
                 tuple: (velocity, tool, user, acceleration, blend radius)
             """

        robotMotionParams = (self.robot_config.global_motion_settings.global_velocity,
                             self.robot_config.robot_tool,
                             self.robot_config.robot_user,
                             self.robot_config.global_motion_settings.global_acceleration,
                             1)#blending radius

        return robotMotionParams

    def zigZag(self, contour, spacing):
        """
             Computes a zigzag path from the contour based on spacing and direction.

             Args:
                 contour (array): Input contour points
                 spacing (float): Spacing between zigzag lines
                 direction (str): Direction of zigzag (e.g., 'horizontal', 'vertical')

             Returns:
                 list: Zigzag path
             """
        path = RobotUtils.zigZag(contour, spacing)
        return path

    def moveToLoginPosition(self):
        ret = None
        currentPos = self.robot.getCurrentPosition()
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

    def moveToStartPosition(self):
        """
            Moves the robot to a predefined start position for safe initialization.
            """
        ret = None
        try:
            if not self.robot:
                # replace the tkinter messagebox with a print statement for debugging
                print("Warning: Robot not connected.")
                # messagebox.showwarning("Warning", "Robot not connected.")
                return

            position = self.robot_config.getHomePositionParsed()  # This already handles None case

            # check if position is within safety limits
            result = self.is_within_safety_limits(position)
            if not result:
                return False

            max_z_value = self.robot_config.safety_limits.z_max
            if position[2] > max_z_value:
                print(f"Error: Target Z value {position[2]} exceeds maximum limit of {max_z_value}.")
                return False

            startPositionConfig = self.robot_config.getHomePosConfig()
            velocity = startPositionConfig.velocity
            acceleration = startPositionConfig.acceleration
            ret = self.robot.moveCart(position=position,
                                      tool=self.robot_config.robot_tool,
                                      user=self.robot_config.robot_user,
                                      vel=velocity,
                                      acc=acceleration)
            # print("Moving to start: ", ret)
            return ret
        except Exception as e:
            print("Error moving to start position:", e)
            # messagebox.showerror("Error", f"Error moving to start position: {e}")
            return ret

    def moveToCalibrationPosition(self):
        """
               Moves the robot to the calibration position.
               """
        ret = None
        try:
            if not self.robot:
                print("Warning: Robot not connected.")
                # messagebox.showwarning("Warning", "Robot not connected.")
                return

            position = self.robot_config.getCalibrationPositionParsed()  # This already handles None case

            result = self.is_within_safety_limits(position)
            if not result:
                return False

            calibrationPositionConfig = self.robot_config.getCalibrationPosConfig()
            velocity = calibrationPositionConfig.velocity
            acceleration = calibrationPositionConfig.acceleration
            ret = self.robot.moveCart(position=position,
                                      tool=self.robot_config.robot_tool,
                                      user=self.robot_config.robot_user,
                                      vel=velocity,
                                      acc=acceleration)

            print("Moving to calibration result: ", ret)
            print("In moveToCalibrationPosition")

            return ret
        except Exception as e:
            print("Error moving to calibration position:", e)
            # messagebox.showerror("Error", f"Error moving to calibration position: {e}")
            return ret


    def adjustPumpSpeedWhileRobotIsMoving(
            self,
            glueSprayService,
            glue_speed_coefficient,
            motorAddress,
            endPoint,
            threshold,
            use_second_order=True
    ):
        print("RobotService.adjustPumpSpeedWhileRobotIsMoving Started")
        print("PARAMETERS")
        print(f"glueSprayService: {glueSprayService}")
        print(f"glue_speed_coefficient: {glue_speed_coefficient}")
        print(f"motorAddress: {motorAddress}")
        print(f"endPoint: {endPoint}")
        print(f"threshold: {threshold}")
        print(f"use_second_order: {use_second_order}")

        time.sleep(1)
        while True:
            currentVel = self.robotStateManager.speed
            accel = self.robotStateManager.accel
            
            # Ensure we have numeric values
            if not isinstance(currentVel, (int, float)):
                print(f"ERROR: currentVel is not numeric: {currentVel}, type: {type(currentVel)}")
                currentVel = 0.0
            if not isinstance(accel, (int, float)):
                print(f"ERROR: accel is not numeric: {accel}, type: {type(accel)}")
                accel = 0.0
            
            print(f"DEBUG: currentVel = {currentVel}, type = {type(currentVel)}")
            print(f"DEBUG: accel = {accel}, type = {type(accel)}")

            # Following error compensation (1st order)
            predicted_following_error = self.robotStateManager.following_error_gain * float(currentVel)
            print(f"DEBUG: following_error_gain = {self.robotStateManager.following_error_gain}, type = {type(self.robotStateManager.following_error_gain)}")
            print(f"DEBUG: predicted_following_error (1st order) = {predicted_following_error}, type = {type(predicted_following_error)}")

            # Optional 2nd order: account for accel lag
            if use_second_order:
                accel_compensation = (self.robotStateManager.following_error_gain * 0.5) * float(accel)
                print(f"DEBUG: accel_compensation = {accel_compensation}, type = {type(accel_compensation)}")
                predicted_following_error += accel_compensation
                print(f"DEBUG: predicted_following_error (2nd order) = {predicted_following_error}, type = {type(predicted_following_error)}")

            combined_vel = float(currentVel) + float(predicted_following_error)
            print(f"DEBUG: combined_vel = {combined_vel}, type = {type(combined_vel)}")
            adjustedPumpSpeed = float(combined_vel) * float(glue_speed_coefficient)
            glueSprayService.adjustMotorSpeed(motorAddress=motorAddress,
                                              speed=int(adjustedPumpSpeed))

            currentPos = self.robotStateManager.pos
            distance = math.sqrt(
                (currentPos[0] - endPoint[0]) ** 2 +
                (currentPos[1] - endPoint[1]) ** 2 +
                (currentPos[2] - endPoint[2]) ** 2
            )

            if distance < threshold:
                break
        print("RobotService.adjustPumpSpeedWhileRobotIsMoving Ended")

    def traceContours(self, paths, spray_on=False):
        from GlueDispensingApplication.glueSprayService.GlueSprayService import GlueSprayService
        from API.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
        from API.shared.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey
        
        # Check if this is a resume operation
        if self.state == RobotServiceState.PAUSED and self.execution_context['paths'] is not None:
            print("Resuming from paused state...")
            return self._resumeTraceContours()
        
        # New execution - initialize context
        self.execution_context = {
            'paths': paths,
            'spray_on': spray_on,
            'current_path_index': 0,
            'current_point_index': 0,
            'motor_started': False,
            'generator_to_glue_delay': 0,
            'service': None,
            'glueType': None
        }
        
        service = GlueSprayService(generatorTurnOffTimeout=10,
                                   settings=self.settingsService.glue_settings)
        
        self.execution_context['service'] = service
        self.execution_context['glueType'] = service.glueA_addresses

        try:
            print("Tracing contours with paths:", paths)
            self.changeState(RobotServiceState.STARTING)
            
            # Use execution context variables  
            current_path_index = self.execution_context['current_path_index']
            generator_to_glue_delay = self.execution_context['generator_to_glue_delay']
            paths = self.execution_context['paths']
            spray_on = self.execution_context['spray_on']
            service = self.execution_context['service']
            glueType = self.execution_context['glueType']
            
            while self.state != RobotServiceState.COMPLETED:
                print("Current State:", self.state)
                if self.state == RobotServiceState.STARTING:
                    # Unpack settings for the current path
                    path, settings = paths[current_path_index]
                    generator_to_glue_delay = float(settings.get(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value))
                    print("SEGMENT SETTINGS")
                    print(settings)
                    # Move to the first point
                    try:
                        ret = self.robot.moveCart(position=path[0],
                                                  tool=self.robot_config.robot_tool,
                                                  user=self.robot_config.robot_user,
                                                  vel=self.robot_config.global_motion_settings.global_velocity,
                                                  acc=self.robot_config.global_motion_settings.global_acceleration)

                        generator_state = service.generatorState()
                        print(f"Generator state before starting: {generator_state}")
                        if not generator_state and spray_on:
                            service.generatorOn()
                            # service.fanOn(settings.get(GlueSettingKey.FAN_SPEED.value, 100))
                            print(f"Waiting for generator_to_glue_delay {generator_to_glue_delay} ")
                            # time.sleep(generator_to_glue_delay)
                        else:
                            print("Generator already on, skipping generatorOn()")

                        if ret != 0:
                            self.changeState(RobotServiceState.ERROR)
                        else:
                            self.changeState(RobotServiceState.MOVING_TO_FIRST_POINT)
                    except:
                        service.generatorOff()
                        print("Robot could not reach start position, stopping glue dispensing")
                        return

                elif self.state == RobotServiceState.MOVING_TO_FIRST_POINT:
                    # Wait for robot to reach the first point, then transition to executing path
                    path, settings = paths[current_path_index]
                    reach_start_threshold = float(settings.get(GlueSettingKey.REACH_START_THRESHOLD.value))
                    generator_to_glue_delay = float(settings.get(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value))

                    result = self._waitForRobotToReachPosition(path[0], reach_start_threshold, 0.1,timeout=30)

                    if result is False:

                        if self.state == RobotServiceState.PAUSED:
                            continue

                        if self.state == RobotServiceState.STOPPED:
                            continue

                        self.state=RobotServiceState.COMPLETED
                    else:
                        self.state = RobotServiceState.EXECUTING_PATH


                elif self.state == RobotServiceState.EXECUTING_PATH:

                    self.robotStateManager.trajectoryUpdate = True

                    path, settings = paths[current_path_index]

                    reach_end_threshold = float(settings.get(GlueSettingKey.REACH_END_THRESHOLD.value))

                    motor_started = False

                    for i, point in enumerate(path):

                        print(f"Target point {i}: ", point)
                        if self.state == RobotServiceState.PAUSED:
                            break

                        if self.state == RobotServiceState.STOPPED:
                            break

                        ret = self.robot.moveL(position=point,

                                               tool=self.robot_config.robot_tool,

                                               user=self.robot_config.robot_user,

                                               vel=settings.get(RobotSettingKey.VELOCITY.value),

                                               acc=settings.get(RobotSettingKey.ACCELERATION.value),

                                               blendR=1)

                        print("move L command result: ", ret)
                        if ret != 0:

                            print(f"MoveL to point {point} failed with error code {ret}")

                            self.state = RobotServiceState.ERROR

                            break

                        else:

                            # Turn on motor only for the first point

                            if not motor_started:
                                print("CALLING MOTOR ON")

                                motor_started = True

                                # while self.robotStateManager.robotState == RobotState.STATIONARY:
                                #     print("Waiting for robot to start moving...")
                                #     print(f"Current robot state: {self.robotStateManager.robotState}")
                                #     time.sleep(0.01)
                                # time.sleep(float(settings.get(GlueSettingKey.TIME_BEFORE_MOTION.value, 0)))
                                if spray_on:
                                    service.motorOn(

                                        motorAddress=glueType,

                                        speed=self.settingsService.glue_settings.get_motor_speed(),

                                        ramp_steps=self.settingsService.glue_settings.get_forward_ramp_steps(),

                                        initial_ramp_speed=self.settingsService.glue_settings.get_initial_ramp_speed(),

                                        initial_ramp_speed_duration=self.settingsService.glue_settings.get_steps_reverse()

                                    )

                            # Wait for robot to reach each point
                            # self.adjustPumpSpeedWhileRobotIsMoving(glueSprayService=service,
                            #                                        glue_speed_coefficient=settings.get(GlueSettingKey.GLUE_SPEED_COEFFICIENT.value, 1),
                            #                                        motorAddress=glueType,
                            #                                        endPoint=point,
                            #                                        threshold=reach_end_threshold,
                            #                                        use_second_order=True)

                            result = self._waitForRobotToReachPosition(point, reach_end_threshold, 0.01, timeout=30)

                            if result is False:

                                if self.state == RobotServiceState.PAUSED:
                                    # Save current execution context before pausing
                                    self.execution_context['current_path_index'] = current_path_index
                                    self.execution_context['current_point_index'] = i
                                    print(f"Paused during path execution - saved context: path={current_path_index}, point={i}")
                                    continue

                                if self.state == RobotServiceState.STOPPED:
                                    continue

                                self.state = RobotServiceState.COMPLETED

                            print(f"Reached point {i}")

                    # Turn off motor ONCE after all points in path



                    if motor_started:
                        print("CALLING MOTOR OFF -> path completed")
                        if spray_on:
                            service.motorOff(motorAddress=glueType,

                                             speedReverse=self.settingsService.glue_settings.get_speed_reverse(),

                                             reverse_time=self.settingsService.glue_settings.get_steps_reverse(),

                                             ramp_steps=self.settingsService.glue_settings.get_reverse_ramp_steps())

                    if self.state == RobotServiceState.PAUSED:
                        continue  # This continues the main while loop, which will hit the PAUSED state handler
                    if self.state == RobotServiceState.STOPPED:
                        continue

                    self.state = RobotServiceState.TRANSITION_BETWEEN_PATHS


                elif self.state == RobotServiceState.TRANSITION_BETWEEN_PATHS:
                    self.robotStateManager.trajectoryUpdate = False
                    current_path_index += 1
                    if current_path_index >= len(paths):
                        self.state = RobotServiceState.COMPLETED
                        # Final cleanup after all paths
                        print(
                            f"Waiting for generator_to_glue_delay {generator_to_glue_delay} before turning off generator")
                        # time.sleep(generator_to_glue_delay)
                        if spray_on:
                            service.motorOff(motorAddress=glueType,
                                             speedReverse=self.settingsService.glue_settings.get_speed_reverse(),
                                             reverse_time=self.settingsService.glue_settings.get_steps_reverse(),
                                             ramp_steps=self.settingsService.glue_settings.get_reverse_ramp_steps())
                            service.generatorOff()

                    else:
                        self.changeState(RobotServiceState.STARTING)

                elif self.state == RobotServiceState.PAUSED:
                    print("RobotService is in PAUSED state, waiting...")
                    time.sleep(0.5)
                    continue
                elif self.state == RobotServiceState.STOPPED:
                    print("RobotService is in STOPPED state, stopping...")
                    self.state = RobotServiceState.COMPLETED

                else:
                    raise ValueError(f"Invalid state: {self.state}")



        except Exception as e:
            import traceback
            traceback.print_exc()
            service.generatorOff()

    def _resumeTraceContours(self):
        """Resume execution from paused state using stored execution context."""
        from API.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
        from API.shared.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey
        
        print("Resuming trace contours from execution context")
        print(f"Resume context: current_path_index={self.execution_context['current_path_index']}, "
              f"current_point_index={self.execution_context['current_point_index']}")
        
        # Restore execution variables from context
        paths = self.execution_context['paths']
        spray_on = self.execution_context['spray_on']
        service = self.execution_context['service']
        glueType = self.execution_context['glueType']
        current_path_index = self.execution_context['current_path_index']
        generator_to_glue_delay = self.execution_context['generator_to_glue_delay']
        
        # Change state to continue from where we left off
        self.changeState(RobotServiceState.STARTING)
        
        try:
            while self.state != RobotServiceState.COMPLETED:
                print("Current State:", self.state)
                if self.state == RobotServiceState.STARTING:
                    # Continue from current path
                    if current_path_index >= len(paths):
                        self.changeState(RobotServiceState.COMPLETED)
                        continue
                        
                    path, settings = paths[current_path_index]
                    generator_to_glue_delay = float(settings.get(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value))
                    print("RESUMING - SEGMENT SETTINGS")
                    print(settings)
                    
                    # Move to the first point of current path
                    try:
                        ret = self.robot.moveCart(position=path[0],
                                                  tool=self.robot_config.robot_tool,
                                                  user=self.robot_config.robot_user,
                                                  vel=self.robot_config.global_motion_settings.global_velocity,
                                                  acc=self.robot_config.global_motion_settings.global_acceleration)

                        generator_state = service.generatorState()
                        print(f"Generator state after resume: {generator_state}")
                        if not generator_state and spray_on:
                            service.generatorOn()
                            print(f"Generator turned on after resume, waiting {generator_to_glue_delay}s")

                        if ret != 0:
                            self.changeState(RobotServiceState.ERROR)
                        else:
                            self.changeState(RobotServiceState.MOVING_TO_FIRST_POINT)
                    except:
                        service.generatorOff()
                        print("Robot could not reach resume position, stopping glue dispensing")
                        return

                elif self.state == RobotServiceState.MOVING_TO_FIRST_POINT:
                    # Wait for robot to reach the first point, then transition to executing path
                    path, settings = paths[current_path_index]
                    reach_start_threshold = float(settings.get(GlueSettingKey.REACH_START_THRESHOLD.value))

                    result = self._waitForRobotToReachPosition(path[0], reach_start_threshold, 0.1, timeout=30)

                    if result is False:
                        if self.state == RobotServiceState.PAUSED:
                            continue
                        if self.state == RobotServiceState.STOPPED:
                            continue
                        self.changeState(RobotServiceState.COMPLETED)
                    else:
                        self.changeState(RobotServiceState.EXECUTING_PATH)

                elif self.state == RobotServiceState.EXECUTING_PATH:
                    self.robotStateManager.trajectoryUpdate = True
                    path, settings = paths[current_path_index]
                    reach_end_threshold = float(settings.get(GlueSettingKey.REACH_END_THRESHOLD.value))
                    motor_started = False

                    for i, point in enumerate(path):
                        print(f"Resume - Target point {i}: ", point)

                        ret = self.robot.moveL(position=point,
                                               tool=self.robot_config.robot_tool,
                                               user=self.robot_config.robot_user,
                                               vel=settings.get(RobotSettingKey.VELOCITY.value),
                                               acc=settings.get(RobotSettingKey.ACCELERATION.value),
                                               blendR=1)

                        print("Resume - move L command result: ", ret)
                        if ret != 0:
                            print(f"MoveL to point {point} failed with error code {ret}")
                            self.changeState(RobotServiceState.ERROR)
                            break
                        else:
                            # Turn on motor only for the first point
                            if not motor_started:
                                print("Resume - CALLING MOTOR ON")
                                motor_started = True
                                if spray_on:
                                    service.motorOn(
                                        motorAddress=glueType,
                                        speed=self.settingsService.glue_settings.get_motor_speed(),
                                        ramp_steps=self.settingsService.glue_settings.get_forward_ramp_steps(),
                                        initial_ramp_speed=self.settingsService.glue_settings.get_initial_ramp_speed(),
                                        initial_ramp_speed_duration=self.settingsService.glue_settings.get_steps_reverse()
                                    )

                            result = self._waitForRobotToReachPosition(point, reach_end_threshold, 0.01, timeout=30)

                            if result is False:
                                if self.state == RobotServiceState.PAUSED:
                                    # Save current progress before pausing
                                    self.execution_context['current_path_index'] = current_path_index
                                    self.execution_context['current_point_index'] = i
                                    continue
                                if self.state == RobotServiceState.STOPPED:
                                    continue
                                self.changeState(RobotServiceState.COMPLETED)

                            print(f"Resume - Reached point {i}")

                    # Turn off motor ONCE after all points in path
                    if motor_started:
                        print("Resume - CALLING MOTOR OFF -> path completed")
                        if spray_on:
                            service.motorOff(motorAddress=glueType,
                                             speedReverse=self.settingsService.glue_settings.get_speed_reverse(),
                                             reverse_time=self.settingsService.glue_settings.get_steps_reverse(),
                                             ramp_steps=self.settingsService.glue_settings.get_reverse_ramp_steps())

                    self.changeState(RobotServiceState.TRANSITION_BETWEEN_PATHS)

                elif self.state == RobotServiceState.TRANSITION_BETWEEN_PATHS:
                    self.robotStateManager.trajectoryUpdate = False
                    current_path_index += 1
                    self.execution_context['current_path_index'] = current_path_index  # Update context
                    
                    if current_path_index >= len(paths):
                        self.changeState(RobotServiceState.COMPLETED)
                        # Final cleanup after all paths
                        print(f"Resume - Final cleanup, turning off generator after {generator_to_glue_delay}s")
                        if spray_on:
                            service.motorOff(motorAddress=glueType,
                                             speedReverse=self.settingsService.glue_settings.get_speed_reverse(),
                                             reverse_time=self.settingsService.glue_settings.get_steps_reverse(),
                                             ramp_steps=self.settingsService.glue_settings.get_reverse_ramp_steps())
                            service.generatorOff()
                    else:
                        self.changeState(RobotServiceState.STARTING)

                elif self.state == RobotServiceState.PAUSED:
                    print("Resume - RobotService is in PAUSED state, waiting...")
                    time.sleep(0.5)
                    continue
                elif self.state == RobotServiceState.STOPPED:
                    print("Resume - RobotService is in STOPPED state, stopping...")
                    self.changeState(RobotServiceState.COMPLETED)
                else:
                    raise ValueError(f"Invalid resume state: {self.state}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            service.generatorOff()
            # Reset execution context on error
            self.execution_context['paths'] = None




    def __getTool(self, toolID):
        """
             Gets tool-specific height offset and tool instance based on ToolID.

             Args:
                 toolID (ToolID): Tool ID

             Returns:
                 tuple: (required height offset, tool instance)
             """
        if toolID == ToolID.Tool1:
            return 25, Tool1()
        elif toolID == ToolID.Tool2:
            return 25, Tool2()
        elif toolID == ToolID.Tool3:
            return 25, Tool3()
        elif toolID == ToolID.Tool0:
            return 25, None
        else:
            raise ValueError("Invalid tool ID")

    def _waitForRobotToReachPosition(self, endPoint, threshold, delay, timeout=30):
        start_time = time.time()
        result = True
        distance = None
        while True:
            print(f"    _waitForRobotToReachPosition robot service state: {self.state}, robot physical state: {self.robotState}")
            # Check for pause/stop states first and exit immediately
            if self.state == RobotServiceState.PAUSED:
                print("RobotService is in PAUSED state, exiting wait loop immediately. Distance = ", distance)
                result = False
                break

            if self.state == RobotServiceState.STOPPED:
                print("RobotService is in STOPPED state, exiting wait loop immediately. Distance = ", distance)
                result = False
                break

            # Check timeout
            if time.time() - start_time > timeout:
                print("Timeout reached while waiting for robot to reach position.")
                result = False
                break

            # Only check position if not paused/stopped
            state = self.robotStateManager.robotState
            current_position = self.robotStateManager.pos
            
            if current_position is None:
                print("Current position is None, continuing to wait...")
                time.sleep(0.1)
                continue

            distance = math.sqrt(
                (current_position[0] - endPoint[0]) ** 2 +
                (current_position[1] - endPoint[1]) ** 2 +
                (current_position[2] - endPoint[2]) ** 2
            )

            if distance < threshold:
                print(f"Position reached within threshold {threshold}mm")
                break

            # Small delay to prevent busy waiting
            time.sleep(0.01)
            
        return result

    def getCurrentPosition(self):
        """
             Gets the current Cartesian position of the robot.

             Returns:
                 list: Current robot position
             """
        return self.robot.getCurrentPosition()



    def enableRobot(self):
        """
               Enables robot motion.
               """
        self.robot.enable()
        print("Robot enabled")

    def disableRobot(self):
        """
                Disables robot motion.
                """
        self.robot.disable()
        print("Robot disabled")

    def is_within_safety_limits(self,position):
        safety_config = self.robot_config.safety_limits

        pos_x, pos_y,pos_z = position[0],position[1],position[2]

        if pos_z > safety_config.z_max:
            print(f"Position Z {pos_z} exceeds maximum limit of {safety_config.z_max}.")
            return False

        if pos_z < safety_config.z_min:
            print(f"Position Z {pos_z} is below minimum limit of {safety_config.z_min}.")
            return False

        return True

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
        if not self.toolChanger.isSlotOccupied(slotId):
            message = f"Slot {slotId} is empty"
            print(message)
            return False, message

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

    def stopRobot(self):
        result = self.robot.stopMotion()
        print("RobotService: stopRobot called, result: ", result)
        return result


    def cleanNozzle(self):
        from GlueDispensingApplication.robot.NozzleCleaner import NozzleCleaner
        cleaner = NozzleCleaner()
        try:
            ret = cleaner.clean_nozzle(self)
            return  ret
        except Exception as e:
            print("Error during nozzle cleaning:", e)
            return -1


    def pause_operation(self):
        """Pause the current robot operation or resume if already paused."""
        
        # If already paused, resume the operation
        if self.state == RobotServiceState.PAUSED:
            print("RobotService: Already paused, resuming operation")
            print(f"RobotService: Transitioning from {self.state} To resumed operation")
            return self.resume_operation()
        
        # Otherwise, pause the operation
        print(f"RobotService: Transitioning from {self.state} To {RobotServiceState.PAUSED} operation")
        self.state = RobotServiceState.PAUSED

        while self.robotStateManager.robotState != RobotState.STATIONARY:
            try:
                result = self.stopRobot()
                print("RobotService: pause_operation stop result:", result)
                break
            except Exception as e:
                print("Error stopping robot during pause:", e)

        return True, "Operation paused"

    def stop_operation(self):
        """Stop the current robot operation."""
        print("RobotService: Stopping operation")
        self.state = RobotServiceState.STOPPED


        while self.robotStateManager.robotState != RobotState.STATIONARY:
            try:
                result = self.stopRobot()
                print("RobotService: stop_operation result:", result)
                break
            except Exception as e:
                print("Error stopping robot:", e)

        return True, "Operation stopped"

    def resume_operation(self):
        """Resume operation from PAUSED state."""
        if self.state == RobotServiceState.PAUSED:
            print("RobotService: Resuming from PAUSED state")
            if self.execution_context['paths'] is not None:
                print("RobotService: Found saved execution context, resuming execution...")
                # Change state to STARTING to break out of the pause loop
                # The main execution loop in traceContours will detect this and continue
                self.changeState(RobotServiceState.STARTING)
                return True, "Operation resumed"
            else:
                print("RobotService: No execution context found, cannot resume")
                return False, "No execution context found"
        elif self.state == RobotServiceState.STOPPED:
            print("RobotService: Cannot resume from STOPPED state - operation was stopped")
            return False, "Cannot resume from STOPPED state"
        else:
            print(f"RobotService: Cannot resume from current state: {self.state}")
            return False, f"Cannot resume from state: {self.state}"

    def changeState(self, new_state):
        """
        Safely change the robot service state, respecting pause/stop conditions.
        
        Args:
            new_state (RobotServiceState): The desired new state
            
        Returns:
            bool: True if state was changed, False if blocked by pause/stop
        """
        # Don't allow state changes if currently paused or stopped (except to certain allowed states)
        if self.state in [RobotServiceState.PAUSED, RobotServiceState.STOPPED]:
            allowed_from_paused = [RobotServiceState.STARTING, RobotServiceState.COMPLETED, RobotServiceState.IDLE]
            allowed_from_stopped = [RobotServiceState.COMPLETED, RobotServiceState.IDLE]
            
            if self.state == RobotServiceState.PAUSED and new_state not in allowed_from_paused:
                print(f"State change blocked: Cannot change from PAUSED to {new_state}")
                return False
            elif self.state == RobotServiceState.STOPPED and new_state not in allowed_from_stopped:
                print(f"State change blocked: Cannot change from STOPPED to {new_state}")
                return False
        
        print(f"State change: {self.state} -> {new_state}")
        self.state = new_state
        return True

    def reset_to_idle(self):
        """Reset robot service to IDLE state."""
        print("RobotService: Resetting to IDLE state")
        self.changeState(RobotServiceState.IDLE)
        return True, "State reset to IDLE"

    def stop(self):
        """Gracefully stop the background thread."""
        self._stop_thread.set()
        print("[CommandProcessor] Stopping thread.")






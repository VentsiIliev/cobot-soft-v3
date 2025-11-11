# import threading
# import time
#
# from API.MessageBroker import MessageBroker
# from system.robot.RobotUtils import calculate_distance_between_points, calculate_velocity, \
#     calculate_acceleration
# from system.robot.FairinoRobot import FairinoRobot
# from system.robot.robotService.enums.RobotState import RobotState
#
# class RobotStateManager:
#     def __init__(self,robot_ip, cycle_time=0.03, velocity_threshold=1, acceleration_threshold=0.001):
#         self.robot = FairinoRobot(robot_ip)
#         self.pos = None
#         self.velocity = 0.0
#         self.acceleration = 0.0
#         self.robotStateTopic = "robot/state"
#         self.robotState = RobotState.STATIONARY  # Initial state
#         self._stop_event = threading.Event()
#         self.prev_pos = None
#         self.prev_time = None
#         self.prev_velocity = None
#         self.trajectoryUpdate = False
#         self.cycle_time = cycle_time
#
#         self.broker = MessageBroker()
#
#         # Thresholds for determining motion state
#         self.velocity_threshold = velocity_threshold
#         self.acceleration_threshold = acceleration_threshold
#
#     def update_state(self):
#         """Update robot motion state based on speed and acceleration."""
#         if abs(self.velocity) < self.velocity_threshold:
#             self.robotState = RobotState.STATIONARY
#         elif self.acceleration > self.acceleration_threshold:
#             self.robotState = RobotState.ACCELERATING
#         elif self.acceleration < -self.acceleration_threshold:
#             self.robotState = RobotState.DECELERATING
#         else:
#             self.robotState = RobotState.MOVING
#         # print("Update robot state called:")
#
#     def send_trajectory_point(self, current_pos):
#         x = current_pos[0]
#         y = current_pos[1]
#         transformed_point = self.broker.request("vision/transformToCamera", {"x": x, "y": y})
#         t_x = transformed_point[0]
#         t_y = transformed_point[1]
#         # Scale to trajectory widget dimensions (800x450)
#         t_x_scaled = int(t_x * 0.625)  # 800/1280 = 0.625
#         t_y_scaled = int(t_y * 0.625)  # 450/720 = 0.625
#         self.broker.publish("robot/trajectory/point", {"x": t_x_scaled, "y": t_y_scaled})
#
#     def monitor_robot(self):
#         while not self._stop_event.is_set():
#             current_time = time.time()
#             try:
#                 current_pos = self.robot.getCurrentPosition()
#             except Exception as e:
#                 print(f"    ERROR: Failed to get robot position: {e}")
#                 self.robotState = RobotState.ERROR
#                 continue
#
#             if current_pos is None:
#                 self.robotState = RobotState.ERROR
#
#             self.pos = current_pos
#
#             if self.prev_pos is not None:
#                 dt = current_time - self.prev_time
#                 self.velocity = calculate_velocity(current_pos, self.prev_pos, dt)
#
#                 if self.prev_velocity is not None:
#                     self.acceleration = calculate_acceleration(self.velocity, self.prev_velocity, dt, use_dt=False)
#
#                 # Determine current robot state
#                 self.update_state()
#                 self.broker.publish(self.robotStateTopic, {"state": self.robotState, "speed": self.velocity, "accel": self.acceleration})
#
#                 if self.robotState != RobotState.STATIONARY and self.trajectoryUpdate:
#                     self.send_trajectory_point(current_pos)
#
#                 elif self.robotState != RobotState.STATIONARY and not self.trajectoryUpdate:
#                     pass
#
#             self.prev_pos = current_pos
#             self.prev_time = current_time
#             self.prev_velocity = self.velocity
#
#             time.sleep(self.cycle_time)
#
#     def start_thread(self):
#         self._thread = threading.Thread(target=self.monitor_robot)
#         self._thread.start()
#
#     def stop_thread(self):
#         self._stop_event.set()
#         self._thread.join()
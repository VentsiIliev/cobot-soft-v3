

import threading
import time

from modules.shared.MessageBroker import MessageBroker
from src.backend.system.robot.RobotUtils import calculate_velocity, calculate_acceleration
from src.backend.system.robot.FairinoRobot import FairinoRobot
from src.backend.system.robot.robotService.enums.RobotState import RobotState


class RobotMonitor:
    """
    Continuously fetches robot position, computes velocity and acceleration,
    and reports results via a callback to the manager.
    """
    def __init__(self, robot_ip, data_callback, cycle_time=0.03):
        self.robot = FairinoRobot(robot_ip)
        self.data_callback = data_callback  # <-- sends (pos, vel, accel, timestamp)
        self.cycle_time = cycle_time
        self._stop_event = threading.Event()

        self.prev_pos = None
        self.prev_time = None
        self.prev_velocity = None

    def run(self):
        """Continuous motion data collection loop."""
        while not self._stop_event.is_set():
            current_time = time.time()
            try:
                current_pos = self.robot.getCurrentPosition()
            except Exception as e:
                print(f"ERROR: Failed to get robot position: {e}")
                self.data_callback(None, None, None, current_time, error=True)
                continue

            if current_pos is None:
                self.data_callback(None, None, None, current_time, error=True)
            else:
                velocity = 0.0
                acceleration = 0.0

                if self.prev_pos is not None:
                    dt = current_time - self.prev_time
                    velocity = calculate_velocity(current_pos, self.prev_pos, dt)
                    if self.prev_velocity is not None:
                        acceleration = calculate_acceleration(velocity, self.prev_velocity, dt, use_dt=False)

                # Send motion data back to manager
                self.data_callback(current_pos, velocity, acceleration, current_time)

                self.prev_pos = current_pos
                self.prev_time = current_time
                self.prev_velocity = velocity

            time.sleep(self.cycle_time)

    def start(self):
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()


class RobotStateManager:
    """
    Manages the robot state and communication based on motion data
    received from RobotMonitor.
    """
    def __init__(self, robot_ip, cycle_time=0.03, velocity_threshold=1, acceleration_threshold=0.001):
        self.broker = MessageBroker()
        self.robot_ip = robot_ip

        self.velocity_threshold = velocity_threshold
        self.acceleration_threshold = acceleration_threshold
        self.trajectory_update = False

        # Motion variables
        self.position = None
        self.velocity = 0.0
        self.acceleration = 0.0
        self.robotState = RobotState.STATIONARY
        self.robotStateTopic = "robot/state"

        # Attach monitor with callback
        self.monitor = RobotMonitor(robot_ip, self.on_motion_data, cycle_time)

    # ----------------------------
    # Callbacks and State Logic
    # ----------------------------

    def on_motion_data(self, pos, velocity, acceleration, timestamp, error=False):
        """Handle new motion data from RobotMonitor."""
        if error:
            self.robotState = RobotState.ERROR
            self.publish_state()
            return

        self.position = pos
        self.velocity = velocity
        self.acceleration = acceleration
        self.update_state()
        self.publish_state()

        if self.robotState != RobotState.STATIONARY and self.trajectory_update:
            self.send_trajectory_point(pos)

    def update_state(self):
        """Determine robot state based on velocity and acceleration."""
        if abs(self.velocity) < self.velocity_threshold:
            self.robotState = RobotState.STATIONARY
        elif self.acceleration > self.acceleration_threshold:
            self.robotState = RobotState.ACCELERATING
        elif self.acceleration < -self.acceleration_threshold:
            self.robotState = RobotState.DECELERATING
        else:
            self.robotState = RobotState.MOVING

    def publish_state(self):
        """Publish current robot state and motion data."""
        self.broker.publish(
            self.robotStateTopic,
            {"state": self.robotState, "speed": self.velocity, "accel": self.acceleration}
        )

    def send_trajectory_point(self, current_pos):
        x, y = current_pos[:2]
        transformed = self.broker.request("vision/transformToCamera", {"x": x, "y": y})
        t_x, t_y = transformed[0], transformed[1]

        self.broker.publish("robot/trajectory/point", {
            "x": int(t_x * 0.625),
            "y": int(t_y * 0.625)
        })

    # ----------------------------
    # Control Methods
    # ----------------------------

    def start_monitoring(self):
        self.monitor.start()

    def stop_monitoring(self):
        self.monitor.stop()

    def get_current_state(self):
        """Expose current state for external queries."""
        return {
            "position": self.position,
            "velocity": self.velocity,
            "acceleration": self.acceleration,
            "state": self.robotState
        }


import threading
import time

from modules.shared.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from src.backend.GlueDispensingApplication.robot.RobotUtils import calculate_distance_between_points
from src.backend.GlueDispensingApplication.robot.robotService.enums.RobotServiceState import RobotServiceState
from src.backend.GlueDispensingApplication.utils.custom_logging import log_debug_message
from src.backend.GlueDispensingApplication.utils.files import write_to_debug_file

# State Management Functions
def is_point_reached(currentPos, targetPoint, threshold):
    """Check if robot has reached a specific point within threshold distance"""
    distance_to_target = calculate_distance_between_points(currentPos, targetPoint)
    return distance_to_target < threshold

def check_robot_state(robotService, start_point_index, furthest_checkpoint_passed):
    """
    Check if robot is paused/stopped and return appropriate status.
    Returns: (should_exit, next_target_point)
    """
    current_state = robotService.state_machine.state
    if current_state in [RobotServiceState.PAUSED, RobotServiceState.STOPPED]:
        # Return progress - furthest_checkpoint_passed indicates the last completed point
        # Resume should be from the NEXT point after the last completed one
        last_completed_point = start_point_index + furthest_checkpoint_passed - 1 if furthest_checkpoint_passed > 0 else start_point_index
        next_target_point = start_point_index + furthest_checkpoint_passed
        
        log_debug_message(robotService.robot_service_logger_context,
            message=f"Robot state changed to {current_state}, last completed point: {last_completed_point}, should resume from point {next_target_point} (furthest_checkpoint_passed={furthest_checkpoint_passed})")
        return True, next_target_point
    
    return False, 0

def is_first_point_reached(currentPos, first_point, threshold, robotService, start_point_index, first_point_reached):
    """
    Check if robot has reached the first point.
    Returns: (first_point_reached_status, should_continue)
    """
    if not first_point_reached:
        first_point_reached = is_point_reached(currentPos, first_point, threshold)
        if first_point_reached:
            log_debug_message(robotService.robot_service_logger_context,
                message=f"First point {start_point_index} reached, starting pump speed adjustments")
            return True, True
        else:
            return False, False  # Continue waiting for first point
    
    return True, True  # First point already reached

def is_final_point_reached(currentPos, final_point, remaining_path, furthest_checkpoint_passed, threshold, robotService):
    """
    Check if robot has reached final point and passed through required checkpoints.
    Returns: True if path is complete
    """
    distance_to_final = calculate_distance_between_points(currentPos, final_point)
    final_point_threshold = threshold

    # Only exit if robot is close to final point AND has passed through second-to-last point
    if distance_to_final < final_point_threshold:
        # Ensure robot has passed through at least the second-to-last point
        if len(remaining_path) >= 2:
            second_to_last_required = len(remaining_path) - 2  # Index of second-to-last point
            if furthest_checkpoint_passed > second_to_last_required:
                log_debug_message(robotService.robot_service_logger_context,
                    message=f"Final point reached and passed through second-to-last point (checkpoint {second_to_last_required}), path complete")
                return True
            else:
                log_debug_message(robotService.robot_service_logger_context,
                    message=f"Close to final point but haven't passed second-to-last point yet (need checkpoint {second_to_last_required}, current: {furthest_checkpoint_passed})")
        else:
            log_debug_message(robotService.robot_service_logger_context,
                message="Final point reached (path has <2 points), path complete")
            return True

    return False

# Checkpoint Management Functions
def update_checkpoint_progress(currentPos, remaining_path, furthest_checkpoint_passed, start_point_index, robotService):
    """
    Update furthest checkpoint passed and log progress.
    Returns: updated furthest_checkpoint_passed value
    """
    for i in range(furthest_checkpoint_passed, len(remaining_path)):
        checkpoint = remaining_path[i]
        distance_to_checkpoint = calculate_distance_between_points(currentPos, checkpoint)

        if distance_to_checkpoint < 1:
            log_checkpoint_reached(start_point_index + i, distance_to_checkpoint, start_point_index, i + 1)
            # Robot has passed this checkpoint - set to the next point we should head toward
            furthest_checkpoint_passed = i + 1  # +1 because we've passed this point, now head to next
            log_debug_message(robotService.robot_service_logger_context,
                message=f"Passed checkpoint {start_point_index + i}, next target will be point {start_point_index + furthest_checkpoint_passed}")
    
    return furthest_checkpoint_passed

def get_current_target_checkpoint(remaining_path, furthest_checkpoint_passed):
    """Get the current target checkpoint for robot movement"""
    return remaining_path[min(furthest_checkpoint_passed, len(remaining_path) - 1)]

def log_checkpoint_reached(checkpoint_index, distance, start_point_index, furthest_checkpoint_passed):
    """Log when a checkpoint is reached"""
    message = f"Checkpoint {checkpoint_index} reached (distance: {distance:.3f} mm)\n"
    write_to_debug_file("robot_pump_values.txt", message)
    message = "\n"
    write_to_debug_file("robot_pump_values.txt", message)

# Speed Calculation Functions
def calculate_velocity_compensation(current_velocity, glue_speed_coefficient):
    """Calculate velocity-based compensation for pump speed"""
    return current_velocity * float(glue_speed_coefficient)

def calculate_acceleration_compensation(current_acceleration, glue_acceleration_coefficient):
    """Calculate acceleration-based compensation with different handling for accel/decel"""
    if current_acceleration <= 0:
        accel_compensation = float(glue_acceleration_coefficient) * float(current_acceleration)
    else:
        glue_acceleration_coefficient_temp = float(glue_acceleration_coefficient) / 2  # less compensation for deceleration
        accel_compensation = float(glue_acceleration_coefficient_temp) * float(current_acceleration)
    
    return accel_compensation

def calculate_pump_speed_adjustments(current_velocity, current_acceleration, glue_speed_coefficient, glue_acceleration_coefficient):
    """Calculate adjusted pump speed based on velocity and acceleration"""
    velocity_compensation = calculate_velocity_compensation(current_velocity, glue_speed_coefficient)
    accel_compensation = calculate_acceleration_compensation(current_acceleration, glue_acceleration_coefficient)
    
    return velocity_compensation + accel_compensation, velocity_compensation, accel_compensation

# Debug/Logging Functions
def log_debug_data(robotService, current_velocity, current_acceleration, velocity_compensation, accel_compensation, adjustedPumpSpeed, last_write_time):
    """Log comprehensive debug data to file and return updated last_write_time"""
    current_time = time.time()
    delta_time = current_time - last_write_time
    
    message = f"dt: {delta_time} Pos {robotService.getCurrentPosition()} Vel: {float(current_velocity):.3f}, Acc: {float(current_acceleration):.3f}, Vel Com: {float(velocity_compensation):.3f}, Acc Comp {accel_compensation:.3f}, Pump speed: {float(adjustedPumpSpeed):.3f}\n"
    write_to_debug_file("robot_pump_values.txt", message)
    
    return current_time

# Configuration Class
class PumpAdjustmentConfig:
    """Configuration container for pump adjustment parameters"""
    def __init__(self, glue_speed_coefficient, glue_acceleration_coefficient, threshold, motor_address, start_point_index=0):
        self.glue_speed_coefficient = glue_speed_coefficient
        self.glue_acceleration_coefficient = glue_acceleration_coefficient
        self.threshold = threshold
        self.motor_address = motor_address
        self.start_point_index = start_point_index

def adjustPumpSpeedDynamically(
        glueSprayService,
        robotService,
        glue_speed_coefficient,
        glue_acceleration_coefficient,
        motorAddress,
        path,
        threshold,
        start_point_index=0,
        ready_event=None,
        execution_context=None
):
    """
    Enhanced version that tracks robot progress through the entire path.
    Returns (success, current_point_index) for precise pause/resume handling.
    """
    print(f"adjustPumpSpeedDynamically called with start_point_index={start_point_index}")
    print(f"Path threshold: {threshold}")

    # Signal ready to main thread
    if ready_event is not None:
        ready_event.set()
        log_debug_message(robotService.robot_service_logger_context, message="Pump thread signaled ready to main thread")
        log_debug_message(robotService.robot_service_logger_context, message="Pump thread ready - signaled to main thread")

    # Initialize variables
    start_time = time.time()
    last_write_time = start_time
    remaining_path = path[start_point_index:]
    log_debug_message(robotService.robot_service_logger_context,
        f"adjustPumpSpeedWhileRobotIsMoving2: Starting with {len(remaining_path)} points, start_index={start_point_index}")

    first_point = remaining_path[0]
    final_point = remaining_path[-1]
    furthest_checkpoint_passed = 0
    first_point_reached = False

    # Main processing loop
    while True:
        # Check if robot is paused or stopped
        should_exit, next_target_point = check_robot_state(robotService, start_point_index, furthest_checkpoint_passed)
        if should_exit:
            return False, next_target_point

        # Get current position
        current_pos = robotService.getCurrentPosition()
        if current_pos is None:
            time.sleep(robotService.robot_state_manager_cycle_time)
            continue

        # Check if first point is reached
        first_point_reached, should_continue = is_first_point_reached(
            current_pos, first_point, threshold, robotService, start_point_index, first_point_reached
        )
        if not should_continue:
            time.sleep(robotService.robot_state_manager_cycle_time)
            continue

        # Check if final point is reached
        if is_final_point_reached(current_pos, final_point, remaining_path, furthest_checkpoint_passed, threshold, robotService):
            break

        # Update checkpoint progress
        furthest_checkpoint_passed = update_checkpoint_progress(
            current_pos, remaining_path, furthest_checkpoint_passed, start_point_index, robotService
        )

        # Get current robot motion data
        current_velocity = robotService.get_current_velocity()
        current_acceleration = robotService.get_current_acceleration()

        # Calculate pump speed adjustments
        adjusted_pump_speed, velocity_compensation, accel_compensation = calculate_pump_speed_adjustments(
            current_velocity, current_acceleration, glue_speed_coefficient, glue_acceleration_coefficient
        )

        # Log debug data
        last_write_time = log_debug_data(
            robotService, current_velocity, current_acceleration, 
            velocity_compensation, accel_compensation, adjusted_pump_speed, last_write_time
        )

        # Apply pump speed adjustment
        glueSprayService.adjustMotorSpeed(motorAddress=motorAddress, speed=int(adjusted_pump_speed))

    # Path completed successfully
    log_debug_message(robotService.robot_service_logger_context, message="RobotService.adjustPumpSpeedWhileRobotIsMoving2 ALL POINTS REACHED! ")
    final_progress = start_point_index + len(remaining_path) - 1
    return True, final_progress

class PumpThreadWithResult(threading.Thread):
    """Thread wrapper that stores the result from the pump adjustment function"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = None
    
    def run(self):
        try:
            self.result = self._target(*self._args, **self._kwargs)
        except Exception as e:
            self.result = (False, 0, e)

def start_dynamic_pump_speed_adjustment_thread(service,
                                               robotService,
                                               settings,
                                               glueType,
                                               path,
                                               reach_end_threshold,
                                               pump_ready_event,
                                               start_point_index=0):

    pump_thread = PumpThreadWithResult(
        target=adjustPumpSpeedDynamically,
        args=(
            service,  # glueSprayService
            robotService,  # robotService
            settings.get(GlueSettingKey.GLUE_SPEED_COEFFICIENT.value),  # glue_speed_coefficient
            settings.get(GlueSettingKey.GLUE_ACCELERATION_COEFFICIENT.value),  # glue_acceleration_coefficient
            glueType,  # motorAddress
            path,  # path (must be sequence)
            reach_end_threshold,  # threshold
            start_point_index,  # start_point_index
            pump_ready_event  # ready_event
        )
    )
    pump_thread.start()

    return pump_thread


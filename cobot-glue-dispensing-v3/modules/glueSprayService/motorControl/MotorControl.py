import time
from typing import List, Dict, Tuple
from dataclasses import dataclass

from modules.glueSprayService.motorControl.utils import split_into_16bit
from modules.modbusCommunication.ModbusController import ModbusController
from modules.glueSprayService.motorControl.errorCodes import MotorErrorCode

from src.backend.GlueDispensingApplication.utils.custom_logging import setup_logger,log_if_enabled, LoggingLevel

ENABLE_LOGGING = True
motor_control_logger = setup_logger("MotorControl")

# Motor Control Register Constants
HEALTH_CHECK_TRIGGER_REGISTER = 17
MOTOR_ERROR_COUNT_REGISTER = 20
MOTOR_ERROR_REGISTERS_START = 21

# Motor Control Configuration
DEFAULT_RAMP_STEPS = 1
DEFAULT_HEALTH_CHECK_DELAY = 3  # seconds
DEFAULT_RAMP_STEP_DELAY = 0.001  # seconds


@dataclass
class MotorState:
    """Represents the state of a motor including its health and error information."""
    
    address: int
    is_healthy: bool = False
    errors: List[int] = None
    error_count: int = 0
    modbus_errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.modbus_errors is None:
            self.modbus_errors = []
    
    def add_error(self, error_code: int) -> None:
        """Add an error code to the motor state."""
        if error_code not in self.errors:
            self.errors.append(error_code)
            self.error_count = len(self.errors)
            self.is_healthy = False
    
    def add_modbus_error(self, error: str) -> None:
        """Add a modbus error to the motor state."""
        self.modbus_errors.append(error)
        self.is_healthy = False
    
    def clear_errors(self) -> None:
        """Clear all errors and mark motor as healthy."""
        self.errors.clear()
        self.modbus_errors.clear()
        self.error_count = 0
        self.is_healthy = True
    
    def has_errors(self) -> bool:
        """Check if motor has any errors."""
        return len(self.errors) > 0 or len(self.modbus_errors) > 0
    
    def get_filtered_errors(self) -> List[int]:
        """Get errors filtered by motor address prefix."""
        motor_address_to_prefix = {
            0: 1,  # Motor 0 errors start with 1x
            2: 2,  # Motor 2 errors start with 2x
            4: 3,  # Motor 4 errors start with 3x
            6: 4   # Motor 6 errors start with 4x
        }
        
        expected_prefix = motor_address_to_prefix.get(self.address)
        if expected_prefix is None:
            return self.errors
        
        filtered = []
        for error in self.errors:
            if error == 0:
                continue
            error_prefix = error // 10
            if error_prefix == expected_prefix:
                filtered.append(error)
        
        return filtered
    
    def to_dict(self) -> Dict:
        """Convert motor state to dictionary format for backward compatibility."""
        return {
            'state': self.is_healthy,
            'errors': self.get_filtered_errors(),
            'error_count': len(self.get_filtered_errors()),
            'modbus_errors': self.modbus_errors
        }
    
    def __str__(self) -> str:
        """String representation of motor state."""
        filtered_errors = self.get_filtered_errors()
        return (f"Motor {self.address}: "
                f"Healthy={self.is_healthy}, "
                f"Error Count={len(filtered_errors)}, "
                f"Errors={filtered_errors}")


@dataclass
class AllMotorsState:
    """Represents the state of all motors."""
    
    success: bool
    motors: Dict[int, MotorState]
    sorted_errors: List[Tuple[int, int]] = None  # (error_code, motor_address)
    
    def __post_init__(self):
        if self.sorted_errors is None:
            self.sorted_errors = []
    
    def add_motor_state(self, motor_state: MotorState) -> None:
        """Add a motor state to the collection."""
        self.motors[motor_state.address] = motor_state
    
    def get_all_errors_sorted(self) -> List[Tuple[int, int]]:
        """Get all errors from all motors sorted by error code."""
        all_errors = []
        for motor_state in self.motors.values():
            filtered_errors = motor_state.get_filtered_errors()
            for error in filtered_errors:
                all_errors.append((error, motor_state.address))
        
        all_errors.sort(key=lambda x: x[0])
        self.sorted_errors = all_errors
        return all_errors
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format for backward compatibility."""
        return {
            'success': self.success,
            'motors': {addr: motor.to_dict() for addr, motor in self.motors.items()},
            'sorted_errors': self.get_all_errors_sorted()
        }



class HealthCheck:
    def __init__(self):
        pass

    def health_check_motor(self, client, motor_address: int, filter_by_motor: bool = True) -> MotorState:
        """Perform health check for a single motor and return MotorState object."""
        log_if_enabled(enabled=ENABLE_LOGGING,
                       logger=motor_control_logger,
                       message=f"Performing health check for motor {motor_address}",
                       level=LoggingLevel.INFO,
                       broadcast_to_ui=False)
        motor_state = MotorState(address=motor_address)
        
        # Reset motor (acknowledge command)
        modbus_error = client.writeRegisters(HEALTH_CHECK_TRIGGER_REGISTER, [1])
        if modbus_error is not None:
            error_msg = f"Failed to trigger health check: {modbus_error}"
            motor_state.add_modbus_error(error_msg)
            MotorControlErrorHandler.handle_modbus_error(HEALTH_CHECK_TRIGGER_REGISTER, modbus_error)
            return motor_state

        log_if_enabled(enabled=ENABLE_LOGGING,
                       logger=motor_control_logger,
                       message=f"Health check triggered, waiting for {DEFAULT_HEALTH_CHECK_DELAY} seconds",
                       level=LoggingLevel.INFO,
                       broadcast_to_ui=False)
        time.sleep(DEFAULT_HEALTH_CHECK_DELAY)

        # Check for motor-specific errors
        error_check_result, motor_errors_count = self._get_motor_errors_count(client, motor_address)
        
        if not error_check_result:
            motor_state.add_modbus_error("Failed to read motor error count")
            return motor_state

        if motor_errors_count > 0:
            raw_motor_errors = self._read_errors(client, motor_errors_count)
            if raw_motor_errors:
                # Add all non-zero errors to motor state
                for error in raw_motor_errors:
                    if error != 0:
                        motor_state.add_error(error)
                
                # Get filtered errors for this specific motor
                filtered_errors = motor_state.get_filtered_errors()
                
                if filtered_errors:
                    log_if_enabled(enabled=ENABLE_LOGGING,
                                   logger=motor_control_logger,
                                   message=f"Motor {motor_address} has errors: {filtered_errors}",
                                   level=LoggingLevel.WARNING,
                                   broadcast_to_ui=False)
                    MotorControlErrorHandler.handle_motor_errors(motor_address, filtered_errors)
                    motor_state.is_healthy = False
                else:
                    log_if_enabled(enabled=ENABLE_LOGGING,
                                   logger=motor_control_logger,
                                   message=f"Motor {motor_address} has no relevant errors",
                                   level=LoggingLevel.INFO,
                                   broadcast_to_ui=False)
                    motor_state.is_healthy = True
            else:
                motor_state.add_modbus_error("Failed to read error values")
        else:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"Motor {motor_address} has no errors",
                           level=LoggingLevel.INFO,
                           broadcast_to_ui=False)
            motor_state.is_healthy = True

        return motor_state

    def health_check_all_motors(self, client, motor_addresses: List[int]) -> AllMotorsState:
        """Perform health check for all motors efficiently."""
        all_motors_state = AllMotorsState(success=True, motors={})
        
        # Trigger health check once for all motors
        modbus_error = client.writeRegisters(HEALTH_CHECK_TRIGGER_REGISTER, [1])
        if modbus_error is not None:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"Failed to trigger health check: {modbus_error}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
            MotorControlErrorHandler.handle_modbus_error(HEALTH_CHECK_TRIGGER_REGISTER, modbus_error)
            all_motors_state.success = False
            # Create failed motor states for all motors
            for motor_address in motor_addresses:
                motor_state = MotorState(address=motor_address)
                motor_state.add_modbus_error("Failed to trigger health check")
                all_motors_state.add_motor_state(motor_state)
            return all_motors_state
        
        log_if_enabled(enabled=ENABLE_LOGGING,
                       logger=motor_control_logger,
                       message=f"Health check triggered for all motors, waiting {DEFAULT_HEALTH_CHECK_DELAY} seconds",
                       level=LoggingLevel.INFO,
                       broadcast_to_ui=False)
        time.sleep(DEFAULT_HEALTH_CHECK_DELAY)
        
        # Get global error count
        error_check_result, global_errors_count = self._get_motor_errors_count(client)
        
        if not error_check_result:
            # Communication failed - mark all motors as unhealthy
            all_motors_state.success = False
            for motor_address in motor_addresses:
                motor_state = MotorState(address=motor_address)
                motor_state.add_modbus_error("Failed to communicate with motor controller")
                all_motors_state.add_motor_state(motor_state)
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=motor_control_logger,
                               message=f"Motor {motor_address} communication failed - marked as unhealthy",
                               level=LoggingLevel.ERROR,
                               broadcast_to_ui=False)
        elif global_errors_count == 0:
            # Communication successful but no errors - set all motors to healthy state
            for motor_address in motor_addresses:
                motor_state = MotorState(address=motor_address, is_healthy=True)
                all_motors_state.add_motor_state(motor_state)
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=motor_control_logger,
                               message=f"Motor {motor_address} has no errors",
                               level=LoggingLevel.INFO,
                               broadcast_to_ui=False)
        else:
            # Read all errors once
            raw_motor_errors = self._read_errors(client, global_errors_count)
            if raw_motor_errors:
                # Filter non-zero errors
                all_motor_errors = [err for err in raw_motor_errors if err != 0]
                
                # Process each motor
                for motor_address in motor_addresses:
                    motor_state = MotorState(address=motor_address)
                    
                    # Add all errors to motor state (filtering will be done by MotorState)
                    for error in all_motor_errors:
                        motor_state.add_error(error)
                    
                    # Check if motor has relevant errors
                    filtered_errors = motor_state.get_filtered_errors()
                    
                    if filtered_errors:
                        log_if_enabled(enabled=ENABLE_LOGGING,
                                       logger=motor_control_logger,
                                       message=f"Motor {motor_address} has errors: {filtered_errors}",
                                       level=LoggingLevel.WARNING,
                                       broadcast_to_ui=False)
                        MotorControlErrorHandler.handle_motor_errors(motor_address, filtered_errors)
                        motor_state.is_healthy = False
                    else:
                        log_if_enabled(enabled=ENABLE_LOGGING,
                                       logger=motor_control_logger,
                                       message=f"Motor {motor_address} has no relevant errors",
                                       level=LoggingLevel.INFO,
                                       broadcast_to_ui=False)
                        motor_state.is_healthy = True
                    
                    all_motors_state.add_motor_state(motor_state)
            else:
                # Failed to read errors, mark all motors as failed
                all_motors_state.success = False
                for motor_address in motor_addresses:
                    motor_state = MotorState(address=motor_address)
                    motor_state.add_modbus_error("Failed to read error values")
                    all_motors_state.add_motor_state(motor_state)
        
        return all_motors_state



    def _read_errors(self, client, errors_count):
        """Read motor error values from error registers"""
        error_values, modbus_error = client.readRegisters(MOTOR_ERROR_REGISTERS_START, errors_count)

        if modbus_error is not None:
            MotorControlErrorHandler.handle_modbus_error("error_registers", modbus_error)
            return []

        if not error_values:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message="No errors read from motor",
                           level=LoggingLevel.INFO,
                           broadcast_to_ui=False)
            return []

        return error_values

    def _get_motor_errors_count(self, client, motor_address=None):
        """Read motor errors count from register 20"""
        try:
            errors_count, modbus_error = client.read(MOTOR_ERROR_COUNT_REGISTER)

            if modbus_error is not None:
                MotorControlErrorHandler.handle_modbus_error(f"{motor_address}_error_count", modbus_error)
                return False, None

            return True, errors_count

        except Exception as e:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"Exception reading motor {motor_address} errors count: {e}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
            return False, None

class MotorControlErrorHandler:
    @staticmethod
    def handle_modbus_error(motorAddress, modbus_error):
        log_if_enabled(enabled=ENABLE_LOGGING,
                       logger=motor_control_logger,
                       message="Handling Modbus error...",
                       level=LoggingLevel.WARNING,
                       broadcast_to_ui=False)
        if modbus_error is not None:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"Modbus error for motor {motorAddress} - {modbus_error.name}: {modbus_error.description()}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
        else:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"No Modbus error for motor {motorAddress}",
                           level=LoggingLevel.INFO,
                           broadcast_to_ui=False)

    @staticmethod
    def handle_motor_errors(motorAddress, errors):
        # print("Handling motor-specific errors...")
        if errors:
            # print(f"Motor {motorAddress} has the following errors:")
            for error in errors:
                try:
                    error_code = MotorErrorCode(error)
                    log_if_enabled(enabled=ENABLE_LOGGING,
                                   logger=motor_control_logger,
                                   message=f"Motor error code: {error_code.name} ({error_code.value}) - {error_code.description()}",
                                   level=LoggingLevel.WARNING,
                                   broadcast_to_ui=False)
                except ValueError:
                    log_if_enabled(enabled=ENABLE_LOGGING,
                                   logger=motor_control_logger,
                                   message=f"Unknown motor error code: {error} (not a recognized motor error)",
                                   level=LoggingLevel.WARNING,
                                   broadcast_to_ui=False)
        else:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"Motor {motorAddress} has no errors",
                           level=LoggingLevel.INFO,
                           broadcast_to_ui=False)

class MotorControl(ModbusController):
    def __init__(self,motorSlaveId=1):
        super().__init__()
        self.motorsId = motorSlaveId
        self.healthCheck = HealthCheck()
        # Connection reuse for adjustMotorSpeed
        self._adjust_client = None
        self._adjust_client_connected = False

    def adjustMotorSpeed(self, motorAddress, speed):
        speed = int(-speed)
        # print(f"adjustMotorSpeed {speed}")
        
        # Check if we have a reusable connection
        if self._adjust_client is None or not self._adjust_client_connected:
            try:
                self._adjust_client = self.getModbusClient(self.motorsId)
                self._adjust_client_connected = True
                log_if_enabled(enabled=ENABLE_LOGGING,
                              logger=motor_control_logger,
                              message="Created new adjust client connection",
                              level=LoggingLevel.INFO,
                              broadcast_to_ui=False)
            except Exception as e:
                log_if_enabled(enabled=ENABLE_LOGGING,
                              logger=motor_control_logger,
                              message=f"Failed to create adjust client: {e}",
                              level=LoggingLevel.ERROR,
                              broadcast_to_ui=False)
                return False
        
        try:
            # high16, low16 = split_into_16bit(speed)
            # high16_int, low16_int = int(high16, 16), int(low16, 16)
            result, errors = self._ramp_motor(value=speed,
                             steps=1,
                             client=self._adjust_client,
                             motorAddress=motorAddress)
            # result,errors = self._write_motor_register(self._adjust_client, motorAddress, low16_int, high16_int)
            
            if not result:
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=motor_control_logger,
                               message=f"Failed to adjust motor {motorAddress} to {speed}. Errors: {errors}",
                               level=LoggingLevel.ERROR,
                               broadcast_to_ui=False)
            else:
                # print(f"Motor {motorAddress} adjusted to speed {speed} (High16={high16_int}, Low16={low16_int})")
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=motor_control_logger,
                               message=f"Motor {motorAddress} adjusted to speed {speed})",
                               level=LoggingLevel.INFO,
                               broadcast_to_ui=False)
            
            return result
            
        except Exception as e:
            # Connection error - reset connection state and retry once
            log_if_enabled(enabled=ENABLE_LOGGING,
                          logger=motor_control_logger,
                          message=f"Connection error in adjustMotorSpeed: {e}. Resetting connection.",
                          level=LoggingLevel.WARNING,
                          broadcast_to_ui=False)
            self._adjust_client_connected = False
            self._adjust_client = None
            return False

    def closeAdjustConnection(self):
        """Manually close the adjust motor speed connection."""
        if self._adjust_client is not None and self._adjust_client_connected:
            try:
                self._adjust_client.close()
                log_if_enabled(enabled=ENABLE_LOGGING,
                              logger=motor_control_logger,
                              message="Closed adjust client connection",
                              level=LoggingLevel.INFO,
                              broadcast_to_ui=False)
            except Exception as e:
                log_if_enabled(enabled=ENABLE_LOGGING,
                              logger=motor_control_logger,
                              message=f"Error closing adjust client: {e}",
                              level=LoggingLevel.WARNING,
                              broadcast_to_ui=False)
            finally:
                self._adjust_client = None
                self._adjust_client_connected = False

    def motorOn(self, motorAddress, speed, ramp_steps, initial_ramp_speed, initial_ramp_speed_duration):
        t_total_start = time.perf_counter()
        # initialize durations
        dur_get_client = dur_ramp = dur_sleep = dur_split = dur_write = dur_close = 0.0

        speed = int(-speed)
        initial_ramp_speed = int(-initial_ramp_speed)

        log_if_enabled(enabled=ENABLE_LOGGING,
                       logger=motor_control_logger,
                       message=f"""MotorControl.motorOn called with
          motorAddress: {motorAddress}
          speed: {speed}
          ramp_steps: {ramp_steps}
          initial_ramp_speed: {initial_ramp_speed}
          initial_ramp_speed_duration: {initial_ramp_speed_duration}""",
                       level=LoggingLevel.INFO,
                       broadcast_to_ui=False)

        result = False
        try:
            t = time.perf_counter()
            client = self.getModbusClient(self.motorsId)
            dur_get_client = time.perf_counter() - t

            t = time.perf_counter()
            result, errors = self._ramp_motor(initial_ramp_speed, ramp_steps, client, motorAddress)
            dur_ramp = time.perf_counter() - t
            if not result:
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=motor_control_logger,
                               message=f"Failed to ramp motor {motorAddress}. Errors: {errors}",
                               level=LoggingLevel.ERROR,
                               broadcast_to_ui=False)
            else:
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=motor_control_logger,
                               message=f"Motor ramped to speed: {initial_ramp_speed}",
                               level=LoggingLevel.INFO,
                               broadcast_to_ui=False)

            t = time.perf_counter()
            time.sleep(initial_ramp_speed_duration)
            dur_sleep = time.perf_counter() - t

            t = time.perf_counter()
            high16, low16 = split_into_16bit(speed)
            high16_int, low16_int = int(high16, 16), int(low16, 16)
            dur_split = time.perf_counter() - t

            t = time.perf_counter()
            result, errors = self._write_motor_register(client, motorAddress, low16_int,
                                                        high16_int)
            dur_write = time.perf_counter() - t
            if not result:
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=motor_control_logger,
                               message=f"Failed to set motor {motorAddress} to {int(speed / 2)}. Errors: {errors}",
                               level=LoggingLevel.ERROR,
                               broadcast_to_ui=False)
            else:
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=motor_control_logger,
                               message=f"Motor {motorAddress} set to speed {speed} (High16={high16_int}, Low16={low16_int})",
                               level=LoggingLevel.INFO,
                               broadcast_to_ui=False)

            t = time.perf_counter()
            client.close()
            dur_close = time.perf_counter() - t

        except Exception as e:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"Error turning on motor {motorAddress}: {e}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
        finally:
            t_total_end = time.perf_counter()
            total = t_total_end - t_total_start
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"Timing breakdown (seconds): get_client={dur_get_client:.6f}, ramp={dur_ramp:.6f}, sleep={dur_sleep:.6f}, split={dur_split:.6f}, write={dur_write:.6f}, close={dur_close:.6f}, total={total:.6f}",
                           level=LoggingLevel.INFO,
                           broadcast_to_ui=False)

        return result



    def motorOff(self, motorAddress, speedReverse, reverse_time,ramp_steps):
        speedReverse = speedReverse
        log_if_enabled(enabled=ENABLE_LOGGING,
                       logger=motor_control_logger,
                       message=f"MotorControl.motorOff called with speedReverse: {speedReverse}, motorAddress: {motorAddress}, reverse_time: {reverse_time}, ramp_steps: {ramp_steps}",
                       level=LoggingLevel.INFO,
                       broadcast_to_ui=False)

        result = False
        try:
            client = self.getModbusClient(self.motorsId)

            # Initial stop - check for modbus errors
            modbus_error = client.writeRegisters(motorAddress, [0, 0])
            if modbus_error is not None:
                MotorControlErrorHandler.handle_modbus_error(motorAddress, modbus_error)
                client.close()
                return False

            result, errors = self._ramp_motor(speedReverse, ramp_steps, client, motorAddress)
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"Motor reverse time = {reverse_time} seconds",
                           level=LoggingLevel.INFO,
                           broadcast_to_ui=False)

            time.sleep(reverse_time)  # Wait for the motor to stop complete reverse movement
            
            # Final stop - check for modbus errors
            modbus_error = client.writeRegisters(motorAddress, [0, 0])
            if modbus_error is not None:
                MotorControlErrorHandler.handle_modbus_error(motorAddress, modbus_error)
                result = False
                
            client.close()

        except Exception as e:
            import traceback
            traceback.print_exc()
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"Error turning off motor {motorAddress}: {e}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
        return result



    def motorState(self, motor_address) -> MotorState:
        """Get single motor state as MotorState object."""
        try:
            client = self.getModbusClient(self.motorsId)
            motor_state = self.healthCheck.health_check_motor(client, motor_address)
            client.close()
            return motor_state
        except Exception as e:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"Exception reading motor {motor_address} state: {e}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
            error_state = MotorState(address=motor_address)
            error_state.add_modbus_error(f"Exception: {str(e)}")
            return error_state

    def getAllMotorStates(self) -> AllMotorsState:
        """Get all motor states at once using new MotorState objects.
        Reads error counts, then reads and sorts errors by error codes for all motors.
        
        Returns:
            AllMotorsState: Object containing all motor states with sorted errors
        """
        motor_addresses = [0, 2, 4, 6]
        
        try:
            client = self.getModbusClient(self.motorsId)
            all_motors_state = self.healthCheck.health_check_all_motors(client, motor_addresses)
            client.close()
            return all_motors_state
            
        except Exception as e:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"Exception in getAllMotorStates: {e}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
            # Create failed state for all motors
            failed_state = AllMotorsState(success=False, motors={})
            for motor_address in motor_addresses:
                motor_state = MotorState(address=motor_address)
                motor_state.add_modbus_error(f"Exception: {str(e)}")
                failed_state.add_motor_state(motor_state)
            return failed_state



    def _write_motor_register(self, client, motorAddress, low16_int, high16_int):
        modbus_errors = []
        motor_errors = []
        
        # Attempt to write to the motor register
        modbus_error = client.writeRegisters(motorAddress, [low16_int, high16_int])

        if modbus_error is not None:
            MotorControlErrorHandler.handle_modbus_error(motorAddress, modbus_error)
            modbus_errors.append(modbus_error)
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"Modbus Error after writing to motor {motorAddress}: {modbus_error}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
            return False, {"modbus_errors": modbus_errors, "motor_errors": motor_errors}
        
        return True, {"modbus_errors": modbus_errors, "motor_errors": motor_errors}



    def _ramp_motor(self, value, steps, client, motorAddress):
        # print("Ramping value to:", value)
        increment = int(value / steps)
        if steps == 1:
            increment = int(value)
        value = 0
        errors = []
        result = True

        # Timers
        t_start = time.perf_counter()
        dur_split_total = 0.0
        dur_write_total = 0.0
        dur_step_total = 0.0

        for i in range(steps):
            step_start = time.perf_counter()

            value = increment * (i + 1)

            t = time.perf_counter()
            high16, low16 = split_into_16bit(value)
            high16_int, low16_int = int(high16, 16), int(low16, 16)
            dur_split = time.perf_counter() - t
            dur_split_total += dur_split

            t = time.perf_counter()
            result, errors = self._write_motor_register(client, motorAddress, low16_int, high16_int)
            # time.sleep(0.02)
            dur_write = time.perf_counter() - t
            dur_write_total += dur_write

            if not result:
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=motor_control_logger,
                               message=f"Failed to write to motor register at step {i + 1}. Errors: {errors}",
                               level=LoggingLevel.ERROR,
                               broadcast_to_ui=False)
                dur_step_total += time.perf_counter() - step_start
                result = False
                break

            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=motor_control_logger,
                           message=f"Ramped to step {i + 1}/{steps}: Value={value} (High16={high16_int}, Low16={low16_int})",
                           level=LoggingLevel.INFO,
                           broadcast_to_ui=False)
            # time.sleep(DEFAULT_RAMP_STEP_DELAY)

            dur_step_total += time.perf_counter() - step_start

        total_time = time.perf_counter() - t_start
        log_if_enabled(enabled=ENABLE_LOGGING,
                       logger=motor_control_logger,
                       message=f"Ramping timing breakdown (seconds): split_total={dur_split_total:.6f}, write_total={dur_write_total:.6f}, steps_total={dur_step_total:.6f}, total={total_time:.6f}",
                       level=LoggingLevel.INFO,
                       broadcast_to_ui=False)

        return result, errors



# if __name__ == "__main__":
#     motorControl = MotorControl()
#     speedTemp = 10000
#     speedReverseTemp = 250
#
#     while True:
#         try:
#             motorAddressTemp = int(input("Enter motor address (-1/0/2/4/6 or 'exit' to quit): ").strip())
#         except ValueError:
#             print("Exiting.")
#             break
#
#         while True:
#             command = input(f"Enter command for motor {motorAddressTemp} (on/off/state/newstate/allstates/back): ").strip().lower()
#             if command == "on":
#                 motorControl.motorOn(motorAddressTemp, speedTemp,3,22000,1)
#             elif command == "off":
#                 motorControl.motorOff(motorAddressTemp, speedReverseTemp, reverse_time=0.5,ramp_steps=1)
#             elif command == "state":
#                 motorControl.motorState(motorAddressTemp)
#             elif command == "newstate":
#                 motor_state = motorControl.motorState(motorAddressTemp)
#                 print("New Motor State Object:")
#                 print(f"  {motor_state}")
#                 print(f"  Modbus Errors: {motor_state.modbus_errors}")
#             elif command == "allstates":
#                 all_motors_state = motorControl.getAllMotorStates()
#                 print("All Motor States (New Format):")
#                 print(f"Success: {all_motors_state.success}")
#                 for motor_addr, motor_state in all_motors_state.motors.items():
#                     print(f"  {motor_state}")
#                 sorted_errors = all_motors_state.get_all_errors_sorted()
#                 print(f"Sorted Errors: {sorted_errors}")
#
#             elif command == "back":
#                 break
#             else:
#                 print("Unknown command. Please enter 'on', 'off', 'state', 'newstate', 'allstates', or 'back'.")
#
#
if __name__ == "__main__":

    controller = MotorControl(1)
    # controller.motorOn(0,200,1,1000,1)
    # controller.motorOn(0,0,5,5000,1)
    controller.motorOff(0,4000,0.5,1)


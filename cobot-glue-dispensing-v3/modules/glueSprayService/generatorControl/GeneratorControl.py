from modules.glueSprayService.generatorControl.timer import Timer
from typing import List, Optional
from dataclasses import dataclass

from src.backend.GlueDispensingApplication.Statistics import Statistics
from modules.modbusCommunication.ModbusController import ModbusController
from src.backend.GlueDispensingApplication.utils.custom_logging import setup_logger,log_if_enabled, LoggingLevel

ENABLE_LOGGING = True
generator_control_logger = setup_logger("generator_control_logger")


@dataclass
class GeneratorState:
    """Represents the state of a generator including its operational status and error information."""
    
    is_on: bool = False
    is_healthy: bool = False
    error_code: Optional[int] = None
    modbus_errors: List[str] = None
    elapsed_time: Optional[float] = None  # Timer elapsed time in seconds
    
    def __post_init__(self):
        if self.modbus_errors is None:
            self.modbus_errors = []
    
    def add_modbus_error(self, error: str) -> None:
        """Add a modbus error to the generator state."""
        self.modbus_errors.append(error)
        self.is_healthy = False
    
    def set_error_code(self, error_code: int) -> None:
        """Set the generator error code."""
        self.error_code = error_code
        if error_code != 0:
            self.is_healthy = False
    
    def clear_errors(self) -> None:
        """Clear all errors and mark generator as healthy."""
        self.modbus_errors.clear()
        self.error_code = None
        self.is_healthy = True
    
    def has_errors(self) -> bool:
        """Check if generator has any errors."""
        return (self.error_code is not None and self.error_code != 0) or len(self.modbus_errors) > 0
    
    def to_dict(self) -> dict:
        """Convert generator state to dictionary format for backward compatibility."""
        return {
            'is_on': self.is_on,
            'is_healthy': self.is_healthy,
            'error_code': self.error_code,
            'modbus_errors': self.modbus_errors,
            'elapsed_time': self.elapsed_time
        }
    
    def __str__(self) -> str:
        """String representation of generator state."""
        status = "ON" if self.is_on else "OFF"
        health = "Healthy" if self.is_healthy else "Unhealthy"
        error_info = f", Error: {self.error_code}" if self.error_code else ""
        time_info = f", Elapsed: {self.elapsed_time:.1f}s" if self.elapsed_time else ""
        return f"Generator: {status}, {health}{error_info}{time_info}"

class GeneratorControl(ModbusController):


    def __init__(self, timer: Timer, generator_address=9, generator_id=1):
        super().__init__()
        self.timer = timer
        self.generator_relay_address = generator_address
        self.relaysId = generator_id

    def generatorOff(self):

        result = False
        try:
            client = self.getModbusClient(self.relaysId)
            modbus_error = client.writeRegister(self.generator_relay_address, 0)

            if modbus_error is not None:
                log_if_enabled(enabled = ENABLE_LOGGING,
                               logger=generator_control_logger,
                               message=f"Modbus error turning off generator - {modbus_error.name}: {modbus_error.description()}",
                               level=LoggingLevel.ERROR,
                               broadcast_to_ui=False)

                return False
            # print(f"Wrote 0 to register {self.generator_relay_address}")
            client.close()

            self.timer.stop()
            Statistics.incrementGeneratorOnSeconds(self.timer.elapsed_seconds or 0)

            # print("Generator OFF")
            result = True
        except Exception as e:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=generator_control_logger,
                           message=f"Error turning off generator: {e}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
        return result

    def generatorOn(self):

        result = False
        try:
            client = self.getModbusClient(self.relaysId)
            modbus_error = client.writeRegister(self.generator_relay_address, 1)
            if modbus_error is not None:
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=generator_control_logger,
                               message=f"Modbus error turning on generator - {modbus_error.name}: {modbus_error.description()}",
                               level=LoggingLevel.ERROR,
                               broadcast_to_ui=False)
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=generator_control_logger,
                               message=f"Error writing to register {self.generator_relay_address} value: {1}",
                               level=LoggingLevel.ERROR,
                               broadcast_to_ui=False)
                return False

            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=generator_control_logger,
                           message=f"Wrote 1 to register {self.generator_relay_address}",
                           level=LoggingLevel.INFO,
                           broadcast_to_ui=False)
            self.timer.start()

            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=generator_control_logger,
                           message="Generator ON",
                           level=LoggingLevel.INFO,
                           broadcast_to_ui=False)
            result = True
        except Exception as e:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=generator_control_logger,
                           message=f"Error turning on generator: {e}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
        return result

    def getGeneratorState(self) -> GeneratorState:
        """Get comprehensive generator state using new GeneratorState class."""
        generator_state = GeneratorState()
        
        try:
            client = self.getModbusClient(self.relaysId)
            
            # Read generator on/off state from register 10
            state_value, modbus_error = client.read(10)
            if modbus_error is not None:
                error_msg = f"Modbus error reading generator state - {modbus_error.name}: {modbus_error.description()}"
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=generator_control_logger,
                               message=error_msg,
                               level=LoggingLevel.ERROR,
                               broadcast_to_ui=False)
                generator_state.add_modbus_error(error_msg)
            else:
                # Generator logic: 0 = ON, 1 = OFF
                generator_state.is_on = (state_value == 0)
            
            # # Read generator error code from register 11
            # error_code, modbus_error = client.read(11)
            # if modbus_error is not None:
            #     error_msg = f"Modbus error reading generator error - {modbus_error.name}: {modbus_error.description()}"
            #     print(error_msg)
            #     generator_state.add_modbus_error(error_msg)
            # else:
            #     generator_state.set_error_code(error_code)
            #     if error_code != 0:
            #         print(f"Generator error read from register 11: {error_code}")
            #
            # Get timer elapsed time if available
            if self.timer and hasattr(self.timer, 'elapsed_seconds'):
                generator_state.elapsed_time = self.timer.elapsed_seconds
            
            # Determine overall health
            if not generator_state.has_errors():
                generator_state.is_healthy = True
            
            client.close()
            
        except Exception as e:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=generator_control_logger,
                           message=f"Exception reading generator state: {e}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
            generator_state.add_modbus_error(f"Exception: {str(e)}")
        
        return generator_state


if __name__ == "__main__":
    def timer_callback(elapsed_time):
        log_if_enabled(enabled=ENABLE_LOGGING,
                       logger=generator_control_logger,
                       message=f"Timer elapsed time: {elapsed_time} seconds",
                       level=LoggingLevel.INFO,
                       broadcast_to_ui=False)
    
    timer = Timer(timeout_minutes=1, on_timeout_callback=timer_callback)
    generator = GeneratorControl(timer)
    
    # Test new GeneratorState functionality
    log_if_enabled(enabled=ENABLE_LOGGING,
                   logger=generator_control_logger,
                   message="=== Testing GeneratorState ===",
                   level=LoggingLevel.INFO,
                   broadcast_to_ui=False)
    
    # Test getting comprehensive state
    generator_state = generator.getGeneratorState()
    log_if_enabled(enabled=ENABLE_LOGGING,
                   logger=generator_control_logger,
                   message="New Generator State Object:",
                   level=LoggingLevel.INFO,
                   broadcast_to_ui=False)
    log_if_enabled(enabled=ENABLE_LOGGING,
                   logger=generator_control_logger,
                   message=f"  {generator_state}",
                   level=LoggingLevel.INFO,
                   broadcast_to_ui=False)
    log_if_enabled(enabled=ENABLE_LOGGING,
                   logger=generator_control_logger,
                   message=f"  Dictionary: {generator_state.to_dict()}",
                   level=LoggingLevel.INFO,
                   broadcast_to_ui=False)
    
    # Interactive test
    while True:
        try:
            command = input("Enter command (on/off/state/exit): ").strip().lower()
            
            if command == "on":
                result = generator.generatorOn()
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=generator_control_logger,
                               message=f"Generator ON result: {result}",
                               level=LoggingLevel.INFO,
                               broadcast_to_ui=False)
                
            elif command == "off":
                result = generator.generatorOff()
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=generator_control_logger,
                               message=f"Generator OFF result: {result}",
                               level=LoggingLevel.INFO,
                               broadcast_to_ui=False)
                
            elif command == "state":
                generator_state = generator.getGeneratorState()
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=generator_control_logger,
                               message="Generator State:",
                               level=LoggingLevel.INFO,
                               broadcast_to_ui=False)
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=generator_control_logger,
                               message=f"  {generator_state}",
                               level=LoggingLevel.INFO,
                               broadcast_to_ui=False)
                if generator_state.modbus_errors:
                    log_if_enabled(enabled=ENABLE_LOGGING,
                                   logger=generator_control_logger,
                                   message=f"  Modbus Errors: {generator_state.modbus_errors}",
                                   level=LoggingLevel.WARNING,
                                   broadcast_to_ui=False)
                
            elif command == "exit":
                break
                
            else:
                log_if_enabled(enabled=ENABLE_LOGGING,
                               logger=generator_control_logger,
                               message="Unknown command. Use: on, off, state, exit",
                               level=LoggingLevel.WARNING,
                               broadcast_to_ui=False)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=generator_control_logger,
                           message=f"Error: {e}",
                           level=LoggingLevel.ERROR,
                           broadcast_to_ui=False)
    
    log_if_enabled(enabled=ENABLE_LOGGING,
                   logger=generator_control_logger,
                   message="Exiting generator control test.",
                   level=LoggingLevel.INFO,
                   broadcast_to_ui=False)
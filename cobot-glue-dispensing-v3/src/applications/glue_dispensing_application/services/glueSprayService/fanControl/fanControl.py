from modules.modbusCommunication.ModbusController import ModbusController
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class FanState:
    """Represents the state of a fan including its operational status and error information."""
    
    is_on: bool = False
    is_healthy: bool = False
    speed: Optional[int] = None  # Current fan speed
    speed_percentage: Optional[float] = None  # Speed as percentage (0-100)
    modbus_errors: List[str] = None
    
    def __post_init__(self):
        if self.modbus_errors is None:
            self.modbus_errors = []
    
    def add_modbus_error(self, error: str) -> None:
        """Add a modbus error to the fan state."""
        self.modbus_errors.append(error)
        self.is_healthy = False
    
    def set_speed(self, raw_speed: int, max_speed: int = 100) -> None:
        """Set the fan speed and calculate percentage."""
        self.speed = raw_speed
        self.is_on = raw_speed > 0
        
        # Calculate percentage (assuming max_speed is the maximum possible value)
        if max_speed > 0:
            self.speed_percentage = (raw_speed / max_speed) * 100
        else:
            self.speed_percentage = 0.0
        
        # Fan is healthy if we can read its speed (no modbus errors)
        if not self.modbus_errors:
            self.is_healthy = True
    
    def clear_errors(self) -> None:
        """Clear all errors and mark fan as healthy."""
        self.modbus_errors.clear()
        self.is_healthy = True
    
    def has_errors(self) -> bool:
        """Check if fan has any errors."""
        return len(self.modbus_errors) > 0
    
    def to_dict(self) -> dict:
        """Convert fan state to dictionary format for backward compatibility."""
        return {
            'is_on': self.is_on,
            'is_healthy': self.is_healthy,
            'speed': self.speed,
            'speed_percentage': self.speed_percentage,
            'modbus_errors': self.modbus_errors
        }
    
    def __str__(self) -> str:
        """String representation of fan state."""
        status = "ON" if self.is_on else "OFF"
        health = "Healthy" if self.is_healthy else "Unhealthy"
        speed_info = f", Speed: {self.speed}" if self.speed is not None else ""
        percentage_info = f" ({self.speed_percentage:.1f}%)" if self.speed_percentage is not None else ""
        return f"Fan: {status}, {health}{speed_info}{percentage_info}"


class FanControl(ModbusController):
    def __init__(self,fanSlaveId=1,fanSpeed_address=8):
        super().__init__()
        self.fanId = fanSlaveId
        self.fanSpeed_address = fanSpeed_address
    def fanOff(self):  # FAN SPEED
        try:
            client = self.getModbusClient(self.fanId)
            modbus_error = client.writeRegister(self.fanSpeed_address, 0)
            print(f"Wrote 0 to register {self.fanSpeed_address}")
            client.close()
            
            if modbus_error is not None:
                print(f"Modbus error turning off fan - {modbus_error.name}: {modbus_error.description()}")
                return False
                
            print(f"Fan OFF")
            return True
            
        except Exception as e:
            print(f"Exception turning off fan: {e}")
            return False

    def fanOn(self, value):  # FAN SPEED
        try:
            value = int(value)
            client = self.getModbusClient(self.fanId)
            # modbus_error = client.writeRegister(self.fanSpeed_address, value + 28)
            modbus_error = client.writeRegister(self.fanSpeed_address, value)
            print(f"Wrote {value} to register {self.fanSpeed_address}")
            # print(f"Wrote {value + 28} to register {self.fanSpeed_address}")
            client.close()
            
            if modbus_error is not None:
                print(f"Modbus error turning on fan - {modbus_error.name}: {modbus_error.description()}")
                return False
            else:
                print(f"No Modbus error turning on fan")
                
            print(f"Fan ON with speed {value}")
            return True
            
        except Exception as e:
            print(f"Exception turning on fan: {e}")
            return False

    def getFanState(self) -> FanState:
        """Get comprehensive fan state using new FanState class."""
        fan_state = FanState()
        
        try:
            client = self.getModbusClient(self.fanId)
            current_speed, modbus_error = client.read(self.fanSpeed_address)
            client.close()
            
            if modbus_error is not None:
                error_msg = f"Modbus error reading fan state - {modbus_error.name}: {modbus_error.description()}"
                print(error_msg)
                fan_state.add_modbus_error(error_msg)
                return fan_state

            if current_speed is None:
                error_msg = "Failed to read fan speed: No data received"
                print(error_msg)
                fan_state.add_modbus_error(error_msg)
                return fan_state

            # Set fan speed and calculate health
            fan_state.set_speed(current_speed)
            
            print(f"Fan state: {fan_state}")
            return fan_state
            
        except Exception as e:
            print(f"Exception reading fan state: {e}")
            fan_state.add_modbus_error(f"Exception: {str(e)}")
            return fan_state




if __name__ == "__main__":
    # Test new FanState functionality
    print("=== Testing FanState ===")
    
    fan = FanControl()
    
    # Test getting comprehensive state
    fan_state = fan.getFanState()
    print("New Fan State Object:")
    print(f"  {fan_state}")
    print(f"  Dictionary: {fan_state.to_dict()}")
    
    #
    
    # Interactive test
    while True:
        try:
            command = input("Enter command (on/off/state/newstate/exit): ").strip().lower()
            
            if command == "on":
                speed = input("Enter fan speed (0-100): ").strip()
                try:
                    speed_value = int(speed)
                    result = fan.fanOn(speed_value)
                    print(f"Fan ON result: {result}")
                except ValueError:
                    print("Invalid speed value. Please enter a number.")
                    
            elif command == "off":
                result = fan.fanOff()
                print(f"Fan OFF result: {result}")
                

            elif command == "newstate":
                fan_state = fan.getFanState()
                print("New Fan State:")
                print(f"  {fan_state}")
                if fan_state.modbus_errors:
                    print(f"  Modbus Errors: {fan_state.modbus_errors}")
                
            elif command == "exit":
                break
                
            else:
                print("Unknown command. Use: on, off, state, newstate, exit")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("Exiting fan control test.")
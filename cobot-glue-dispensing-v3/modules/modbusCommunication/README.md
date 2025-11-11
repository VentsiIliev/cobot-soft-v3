# modbusCommunication Module

Modbus RTU communication interface for hardware control in the cobot glue dispensing system.

## Quick Start

```python
from modbusCommunication.ModbusController import ModbusController

# Get a configured client
client = ModbusController.getModbusClient(slaveId=10)

# Write to a register
error = client.writeRegister(100, 42)

# Read from a register
value, error = client.read(100)
if error is None:
    print(f"Value: {value}")
```

## Module Files

- **ModbusClient.py** - Core Modbus RTU client with retry logic
- **ModbusController.py** - Factory for creating configured clients
- **ModbusClientSingleton.py** - Singleton pattern wrapper
- **modbus_lock.py** - Thread synchronization lock
- **MockClient.py** - Mock implementation for testing

## Key Features

- ✅ Thread-safe operations with automatic locking
- ✅ Automatic retry logic (up to 30 attempts)
- ✅ Support for reading/writing individual and multiple registers
- ✅ Coil/bit operations
- ✅ Error handling with typed exceptions
- ✅ Mock client for testing without hardware

## Documentation

For complete API reference, usage examples, and best practices, see:
[docs/modbusCommunucation.md](../../../../docs/modbusCommunucation.md)

## Common Usage Patterns

### Read/Write Single Register
```python
client = ModbusController.getModbusClient(slaveId=10)
client.writeRegister(register=100, value=42)
value, error = client.read(register=100)
```

### Read/Write Multiple Registers
```python
client.writeRegisters(start_register=100, values=[1, 2, 3, 4])
values, error = client.readRegisters(start_register=100, count=4)
```

### Singleton Pattern
```python
from modbusCommunication.ModbusClientSingleton import ModbusClientSingleton

# All components share the same instance
client = ModbusClientSingleton.get_instance(slave=10, port='/dev/ttyUSB0')
```

## Thread Safety

All operations are protected by `modbus_lock`. For multi-step atomic operations:

```python
from modbusCommunication.modbus_lock import modbus_lock

with modbus_lock:
    value1, _ = client.read(100)
    value2, _ = client.read(101)
    client.writeRegister(102, value1 + value2)
```

## Error Handling

Methods return error codes from `ModbusExceptionType` enum:

```python
value, error = client.read(100)
if error is not None:
    print(f"Error: {error.name} - {error.description()}")
else:
    print(f"Success: {value}")
```

## Configuration

Default configuration (via ModbusController):
- Port: `/dev/ttyUSB0`
- Baudrate: 115200
- Bytesize: 8
- Parity: None
- Stopbits: 1
- Timeout: 0.02s

## Testing

The module uses `MockInstrument` for development mode. See `MockClient.py` for mock implementation details.

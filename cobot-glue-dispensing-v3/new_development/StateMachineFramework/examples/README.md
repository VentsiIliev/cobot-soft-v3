# Glue Spraying Application State Machine Examples

This directory contains state machine implementations for the GlueSprayingApplication, demonstrating how to refactor the original manual state handling into a robust, maintainable state machine architecture.

## Files

### 1. `glue_spraying_state_machine.py`
**Complete Framework Implementation**

This is a comprehensive example that shows how to use the full StateMachineFramework to implement the glue spraying application states. It includes:

- **Enhanced state machine builder** with fluent API
- **Service dependency injection** for robot, vision, and glue systems
- **Precondition validation** before state transitions
- **Error handling and recovery mechanisms**
- **Performance monitoring and metrics collection**
- **Conditional transitions** for emergency conditions

**Key Features:**
- Maps all operations from the original `GlueSprayingApplication.py`
- Robust error handling with automatic recovery
- Service-oriented architecture with dependency injection
- Comprehensive validation and monitoring

**Note:** Falls back to mock implementations if the full framework isn't available, allowing the example to run independently.

### 2. `simple_glue_spraying_demo.py`
**Standalone Implementation**

This is a simplified, standalone demonstration that shows the core state machine concepts without complex framework dependencies. It includes:

- **Clear state and event definitions** using Python enums
- **State transition tables** for easy understanding
- **Precondition checking** for safe state transitions
- **Entry actions** that simulate actual operations
- **Error handling and recovery** workflows

**Key Features:**
- Self-contained implementation (no external dependencies)
- Maps all major operations from the original application:
  - `calibrateRobot()` → **ROBOT_CALIBRATION** state
  - `calibrateCamera()` → **CAMERA_CALIBRATION** state
  - `createWorkpiece()` → **WORKPIECE_CREATION** state
  - `start()` → **PROCESSING** → **SPRAYING** states
  - `measureHeight()` → **MEASURING_HEIGHT** state
- Real-time demonstration with simulated timing
- Easy to understand and modify

## Running the Examples

### Framework Implementation
```bash
python glue_spraying_state_machine.py
```

### Standalone Implementation
```bash
python simple_glue_spraying_demo.py
```

## State Diagrams

### Main Application States
```
INITIALIZING → IDLE → CALIBRATING → IDLE
                ↓         ↓
           WORKPIECE_   ROBOT_CALIBRATION
           CREATION  ↗  CAMERA_CALIBRATION
                ↓
            PREPARING → PROCESSING → FINALIZING → IDLE
                          ↓
                   MEASURING_HEIGHT
                   SPRAYING
```

### Error Handling
```
Any State → EMERGENCY_STOP → ERROR
ERROR → RETRY_OPERATION → IDLE
ERROR → RESET_SYSTEM → INITIALIZING
```

## Benefits Over Original Implementation

### 1. **Better State Management**
- Clear state definitions with explicit transitions
- Validation before state changes
- Consistent state handling across the application

### 2. **Enhanced Error Handling**
- Automatic error recovery mechanisms
- Emergency stop functionality from any state
- Error tracking and statistics

### 3. **Improved Maintainability**
- Separation of concerns (state logic vs. business logic)
- Easy to add new states and transitions
- Clear documentation of system behavior

### 4. **Better Testing**
- State transitions can be tested independently
- Mock implementations for unit testing
- Predictable system behavior

### 5. **Monitoring and Debugging**
- State transition logging
- Performance metrics collection
- Context data tracking

## Integration with Original Application

To integrate these state machines with the original `GlueSprayingApplication.py`:

1. **Replace manual state handling** with state machine events
2. **Inject actual services** instead of mock implementations
3. **Map existing methods** to state machine entry actions
4. **Add state transition events** to appropriate places in the code

### Example Integration:
```python
# Original code
self.state = GlueSprayApplicationState.IDLE

# State machine approach
self.state_machine.send_event(GlueSprayEvent.SERVICES_READY)
```

## Configuration and Customization

Both examples can be easily customized by:

- **Adding new states** for additional operations
- **Modifying transition conditions** and preconditions
- **Extending context data** for more complex operations
- **Adding timeout handling** for long-running operations
- **Implementing custom error recovery** strategies

This demonstrates how the StateMachineFramework can significantly improve the robustness and maintainability of the glue spraying application while preserving all existing functionality.
from typing import Dict, Any

from new_development.GlueSprayApplicationStateMachineAdapter.GlueSprayContext import GlueSprayContext
from new_development.GlueSprayApplicationStateMachineAdapter.GlueSprayEvent import GlueSprayEvent
from new_development.GlueSprayApplicationStateMachineAdapter.GlueSprayState import GlueSprayState

from new_development.StateMachineFramework.StateMachineFactory import StateMachineFactory
from new_development.StateMachineFramework.StateMachineBuilder import StateMachineBuilder
from new_development.StateMachineFramework.v2 import BaseStateMachine


# ============================================================================
# APPLICATION ADAPTER
# ============================================================================

class GlueSprayApplicationAdapter:
    """Adapter that integrates the generic state machine with the glue spray application"""

    def __init__(self, original_application):
        self.original_app = original_application
        self.context = GlueSprayContext(original_application)
        self.state_machine = self._create_state_machine()

        # Store original methods for delegation
        self._store_original_methods()

        # Register application-specific callbacks
        self._register_callbacks()

        # Start the state machine
        self.state_machine.start()

    def _store_original_methods(self):
        """Store references to original application methods"""
        self.original_methods = {
            'start': getattr(self.original_app, 'start', None),
            'calibrateRobot': getattr(self.original_app, 'calibrateRobot', None),
            'calibrateCamera': getattr(self.original_app, 'calibrateCamera', None),
            'createWorkpiece': getattr(self.original_app, 'createWorkpiece', None),
            'measureHeight': getattr(self.original_app, 'measureHeight', None),
            'updateToolChangerStation': getattr(self.original_app, 'updateToolChangerStation', None),
            'handleBelt': getattr(self.original_app, 'handleBelt', None),
            'testRun': getattr(self.original_app, 'testRun', None),
        }

    def _create_state_machine(self) -> BaseStateMachine:
        """Create the state machine configuration for glue spray application"""

        builder = StateMachineBuilder()

        # Define states and transitions
        (builder
         # IDLE State
         .add_state(GlueSprayState.IDLE.value)
         .add_entry_action("ensure_safe_position")
         .add_entry_action("log_entry")
         .add_transition(GlueSprayEvent.START_REQUESTED.value, GlueSprayState.EXECUTING_TRAJECTORY.value)
         .add_transition(GlueSprayEvent.CALIBRATE_ROBOT_REQUESTED.value, GlueSprayState.CALIBRATING_ROBOT.value)
         .add_transition(GlueSprayEvent.CALIBRATE_CAMERA_REQUESTED.value, GlueSprayState.CALIBRATING_CAMERA.value)
         .add_transition(GlueSprayEvent.CREATE_WORKPIECE_REQUESTED.value, GlueSprayState.CREATING_WORKPIECE.value)
         .add_transition(GlueSprayEvent.MEASURE_HEIGHT_REQUESTED.value, GlueSprayState.MEASURING_HEIGHT.value)
         .add_transition(GlueSprayEvent.UPDATE_TOOL_CHANGER_REQUESTED.value, GlueSprayState.UPDATING_TOOL_CHANGER.value)
         .add_transition(GlueSprayEvent.HANDLE_BELT_REQUESTED.value, GlueSprayState.HANDLING_BELT.value)
         .add_transition(GlueSprayEvent.TEST_RUN_REQUESTED.value, GlueSprayState.TEST_RUNNING.value)
         .done()

         # EXECUTING_TRAJECTORY State
         .add_state(GlueSprayState.EXECUTING_TRAJECTORY.value)
         .add_entry_action("log_entry")
         .set_operation("execute_trajectory")
         .set_timeout(300)  # 5 minutes
         .add_transition(GlueSprayEvent.OPERATION_COMPLETED.value, GlueSprayState.IDLE.value)
         .add_transition(GlueSprayEvent.OPERATION_FAILED.value, GlueSprayState.ERROR.value)
         .add_transition(GlueSprayEvent.PAUSE_REQUESTED.value, GlueSprayState.PAUSED.value)
         .done()

         # CALIBRATING_ROBOT State
         .add_state(GlueSprayState.CALIBRATING_ROBOT.value)
         .add_entry_action("log_entry")
         .set_operation("calibrate_robot")
         .set_timeout(120)  # 2 minutes
         .add_transition(GlueSprayEvent.OPERATION_COMPLETED.value, GlueSprayState.IDLE.value)
         .add_transition(GlueSprayEvent.OPERATION_FAILED.value, GlueSprayState.ERROR.value)
         .done()

         # CALIBRATING_CAMERA State
         .add_state(GlueSprayState.CALIBRATING_CAMERA.value)
         .add_entry_action("log_entry")
         .set_operation("calibrate_camera")
         .set_timeout(90)  # 1.5 minutes
         .add_transition(GlueSprayEvent.OPERATION_COMPLETED.value, GlueSprayState.IDLE.value)
         .add_transition(GlueSprayEvent.OPERATION_FAILED.value, GlueSprayState.ERROR.value)
         .done()

         # CREATING_WORKPIECE State
         .add_state(GlueSprayState.CREATING_WORKPIECE.value)
         .add_entry_action("log_entry")
         .set_operation("create_workpiece")
         .set_timeout(60)
         .add_transition(GlueSprayEvent.OPERATION_COMPLETED.value, GlueSprayState.IDLE.value)
         .add_transition(GlueSprayEvent.OPERATION_FAILED.value, GlueSprayState.ERROR.value)
         .done()

         # MEASURING_HEIGHT State
         .add_state(GlueSprayState.MEASURING_HEIGHT.value)
         .add_entry_action("log_entry")
         .set_operation("measure_height")
         .set_timeout(30)
         .add_transition(GlueSprayEvent.OPERATION_COMPLETED.value, GlueSprayState.IDLE.value)
         .add_transition(GlueSprayEvent.OPERATION_FAILED.value, GlueSprayState.ERROR.value)
         .done()

         # UPDATING_TOOL_CHANGER State
         .add_state(GlueSprayState.UPDATING_TOOL_CHANGER.value)
         .add_entry_action("log_entry")
         .set_operation("update_tool_changer")
         .set_timeout(45)
         .add_transition(GlueSprayEvent.OPERATION_COMPLETED.value, GlueSprayState.IDLE.value)
         .add_transition(GlueSprayEvent.OPERATION_FAILED.value, GlueSprayState.ERROR.value)
         .done()

         # HANDLING_BELT State
         .add_state(GlueSprayState.HANDLING_BELT.value)
         .add_entry_action("log_entry")
         .set_operation("handle_belt")
         .set_timeout(60)
         .add_transition(GlueSprayEvent.OPERATION_COMPLETED.value, GlueSprayState.IDLE.value)
         .add_transition(GlueSprayEvent.OPERATION_FAILED.value, GlueSprayState.ERROR.value)
         .done()

         # TEST_RUNNING State
         .add_state(GlueSprayState.TEST_RUNNING.value)
         .add_entry_action("log_entry")
         .set_operation("test_run")
         .set_timeout(180)  # 3 minutes
         .add_transition(GlueSprayEvent.OPERATION_COMPLETED.value, GlueSprayState.IDLE.value)
         .add_transition(GlueSprayEvent.OPERATION_FAILED.value, GlueSprayState.ERROR.value)
         .done()

         # ERROR State
         .add_state(GlueSprayState.ERROR.value)
         .add_entry_action("log_error")
         .add_entry_action("move_to_safe_position")
         .add_exit_action("clear_error")
         .add_transition(GlueSprayEvent.RESET_REQUESTED.value, GlueSprayState.IDLE.value)
         .done()

         # PAUSED State
         .add_state(GlueSprayState.PAUSED.value)
         .add_entry_action("log_entry")
         .add_entry_action("pause_operations")
         .add_transition(GlueSprayEvent.RESUME_REQUESTED.value, GlueSprayState.EXECUTING_TRAJECTORY.value)
         .add_transition(GlueSprayEvent.RESET_REQUESTED.value, GlueSprayState.IDLE.value)
         .done()

         # Set initial state and global transitions
         .set_initial_state(GlueSprayState.IDLE.value)
         .add_global_transition(GlueSprayEvent.ERROR_OCCURRED.value, GlueSprayState.ERROR.value)
         .add_error_recovery(GlueSprayState.EXECUTING_TRAJECTORY.value, GlueSprayState.ERROR.value)
         .add_error_recovery(GlueSprayState.CALIBRATING_ROBOT.value, GlueSprayState.ERROR.value)
         .add_error_recovery(GlueSprayState.CALIBRATING_CAMERA.value, GlueSprayState.ERROR.value)
         )

        return builder.build(self.context)

    def _register_callbacks(self):
        """Register application-specific callbacks"""

        # Operation execution callbacks
        self.context.register_callback('execute_operation', self._execute_operation)
        self.context.register_callback('process_event', self._process_event)

        # State action callbacks
        self.context.register_callback('on_entry_log_entry', self._log_state_entry)
        self.context.register_callback('on_entry_ensure_safe_position', self._ensure_safe_position)
        self.context.register_callback('on_entry_log_error', self._log_error)
        self.context.register_callback('on_entry_move_to_safe_position', self._move_to_safe_position)
        self.context.register_callback('on_entry_pause_operations', self._pause_operations)
        self.context.register_callback('on_exit_clear_error', self._clear_error)

        # Override default error handler
        self.context.register_callback('on_error', self._handle_application_error)

    def _execute_operation(self, params: Dict[str, Any]) -> Any:
        """Execute the specified operation"""
        operation_type = params.get('operation_type')
        context_data = params.get('context_data', {})

        print(f"Executing operation: {operation_type}")

        try:
            # Safety check before any operation
            if not self.context.is_safe_to_operate():
                raise Exception("System not in safe state for operation")

            # Execute the appropriate operation
            if operation_type == "execute_trajectory":
                contour_matching = context_data.get('contour_matching', True)
                return self._safe_call('start', contour_matching)

            elif operation_type == "calibrate_robot":
                return self._safe_call('calibrateRobot')

            elif operation_type == "calibrate_camera":
                return self._safe_call('calibrateCamera')

            elif operation_type == "create_workpiece":
                return self._safe_call('createWorkpiece')

            elif operation_type == "measure_height":
                return self._safe_call('measureHeight')

            elif operation_type == "update_tool_changer":
                return self._safe_call('updateToolChangerStation')

            elif operation_type == "handle_belt":
                return self._safe_call('handleBelt')

            elif operation_type == "test_run":
                return self._safe_call('testRun')

            else:
                raise ValueError(f"Unknown operation type: {operation_type}")

        except Exception as e:
            print(f"Operation {operation_type} failed: {str(e)}")
            raise

    def _safe_call(self, method_name: str, *args, **kwargs) -> Any:
        """Safely call an original application method"""
        method = self.original_methods.get(method_name)
        if not method:
            raise AttributeError(f"Method {method_name} not found in original application")

        return method(*args, **kwargs)

    def _process_event(self, params: Dict[str, Any]):
        """Process an event through the state machine"""
        event_name = params.get('event')
        event_data = params.get('data', {})
        self.state_machine.process_event(event_name, event_data)

    # Action callback implementations
    def _log_state_entry(self, params: Dict[str, Any]):
        """Log state entry"""
        state = params.get('state', 'Unknown')
        print(f"Entering state: {state}")

    def _ensure_safe_position(self, params: Dict[str, Any]):
        """Ensure robot is in safe position"""
        try:
            if hasattr(self.original_app, 'robotService') and self.original_app.robotService:
                self.original_app.robotService.moveToStartPosition()
                print("Robot moved to safe position")
        except Exception as e:
            print(f"Failed to move robot to safe position: {e}")

    def _log_error(self, params: Dict[str, Any]):
        """Log error state entry"""
        error_msg = self.context.error_message or "Unknown error"
        print(f"ERROR STATE: {error_msg}")

    def _move_to_safe_position(self, params: Dict[str, Any]):
        """Move robot to safe position on error"""
        try:
            if hasattr(self.original_app, 'robotService') and self.original_app.robotService:
                self.original_app.robotService.moveToStartPosition()
                print("Robot moved to safe position due to error")
        except Exception as e:
            print(f"Failed to move robot to safe position on error: {e}")

    def _pause_operations(self, params: Dict[str, Any]):
        """Pause current operations"""
        print("Operations paused")
        # Could implement actual pause logic here

    def _clear_error(self, params: Dict[str, Any]):
        """Clear error state"""
        self.context.error_message = ""
        print("Error state cleared")

    def _handle_application_error(self, params: Dict[str, Any]):
        """Handle application-specific errors"""
        error_msg = params.get('error', 'Unknown error')
        print(f"Application Error: {error_msg}")
        self.context.error_message = error_msg

        # Try to move robot to safe position
        self._move_to_safe_position(params)

    # ========================================================================
    # PUBLIC API - Enhanced methods that replace original application methods
    # ========================================================================

    def start(self, contourMatching: bool = True) -> tuple:
        """Enhanced start method using state machine"""
        current_state = self.state_machine.get_current_state()

        if current_state != GlueSprayState.IDLE.value:
            return False, f"Cannot start operation from state {current_state}"

        # Set operation parameters
        self.context.set_data('contour_matching', contourMatching)

        # Trigger state machine event
        self.state_machine.process_event(GlueSprayEvent.START_REQUESTED.value, {
            'contour_matching': contourMatching
        })

        return True, "Operation started via state machine"

    def calibrateRobot(self) -> tuple:
        """Enhanced robot calibration using state machine"""
        current_state = self.state_machine.get_current_state()

        if current_state != GlueSprayState.IDLE.value:
            return False, f"Cannot calibrate robot from state {current_state}", None

        self.state_machine.process_event(GlueSprayEvent.CALIBRATE_ROBOT_REQUESTED.value)
        return True, "Robot calibration started via state machine", None

    def calibrateCamera(self) -> tuple:
        """Enhanced camera calibration using state machine"""
        current_state = self.state_machine.get_current_state()

        if current_state != GlueSprayState.IDLE.value:
            return False, f"Cannot calibrate camera from state {current_state}", None

        self.state_machine.process_event(GlueSprayEvent.CALIBRATE_CAMERA_REQUESTED.value)
        return True, "Camera calibration started via state machine", None

    def createWorkpiece(self) -> tuple:
        """Enhanced workpiece creation using state machine"""
        current_state = self.state_machine.get_current_state()

        if current_state != GlueSprayState.IDLE.value:
            return False, "Cannot create workpiece from current state"

        self.state_machine.process_event(GlueSprayEvent.CREATE_WORKPIECE_REQUESTED.value)
        return True, "Workpiece creation started via state machine"

    def measureHeight(self) -> tuple:
        """Enhanced height measurement using state machine"""
        current_state = self.state_machine.get_current_state()

        if current_state != GlueSprayState.IDLE.value:
            return False, "Cannot measure height from current state"

        self.state_machine.process_event(GlueSprayEvent.MEASURE_HEIGHT_REQUESTED.value)
        return True, "Height measurement started via state machine"

    def updateToolChangerStation(self) -> tuple:
        """Enhanced tool changer update using state machine"""
        current_state = self.state_machine.get_current_state()

        if current_state != GlueSprayState.IDLE.value:
            return False, "Cannot update tool changer from current state"

        self.state_machine.process_event(GlueSprayEvent.UPDATE_TOOL_CHANGER_REQUESTED.value)
        return True, "Tool changer update started via state machine"

    def handleBelt(self) -> tuple:
        """Enhanced belt handling using state machine"""
        current_state = self.state_machine.get_current_state()

        if current_state != GlueSprayState.IDLE.value:
            return False, "Cannot handle belt from current state"

        self.state_machine.process_event(GlueSprayEvent.HANDLE_BELT_REQUESTED.value)
        return True, "Belt handling started via state machine"

    def testRun(self) -> tuple:
        """Enhanced test run using state machine"""
        current_state = self.state_machine.get_current_state()

        if current_state != GlueSprayState.IDLE.value:
            return False, "Cannot start test run from current state"

        self.state_machine.process_event(GlueSprayEvent.TEST_RUN_REQUESTED.value)
        return True, "Test run started via state machine"

    def emergency_stop(self) -> tuple:
        """Emergency stop - immediate transition to error state"""
        self.state_machine.process_event(GlueSprayEvent.ERROR_OCCURRED.value, {
            'error': 'Emergency stop activated'
        })
        return True, "Emergency stop activated"

    def reset(self) -> tuple:
        """Reset system from error state"""
        current_state = self.state_machine.get_current_state()

        if current_state != GlueSprayState.ERROR.value:
            return False, f"Cannot reset from state {current_state}"

        self.state_machine.process_event(GlueSprayEvent.RESET_REQUESTED.value)
        return True, "System reset requested"

    def pause(self) -> tuple:
        """Pause current operation"""
        current_state = self.state_machine.get_current_state()

        if current_state != GlueSprayState.EXECUTING_TRAJECTORY.value:
            return False, f"Cannot pause from state {current_state}"

        self.state_machine.process_event(GlueSprayEvent.PAUSE_REQUESTED.value)
        return True, "Operation paused"

    def resume(self) -> tuple:
        """Resume paused operation"""
        current_state = self.state_machine.get_current_state()

        if current_state != GlueSprayState.PAUSED.value:
            return False, f"Cannot resume from state {current_state}"

        self.state_machine.process_event(GlueSprayEvent.RESUME_REQUESTED.value)
        return True, "Operation resumed"

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_current_state(self) -> str:
        """Get current state"""
        return self.state_machine.get_current_state()

    def get_state_history(self) -> list:
        """Get state transition history"""
        return self.state_machine.get_history()

    def can_execute_operation(self, operation: str) -> bool:
        """Check if operation can be executed in current state"""
        current_state = self.state_machine.get_current_state()

        valid_states = {
            'start': [GlueSprayState.IDLE.value],
            'calibrate_robot': [GlueSprayState.IDLE.value],
            'calibrate_camera': [GlueSprayState.IDLE.value],
            'create_workpiece': [GlueSprayState.IDLE.value],
            'measure_height': [GlueSprayState.IDLE.value],
            'update_tool_changer': [GlueSprayState.IDLE.value],
            'handle_belt': [GlueSprayState.IDLE.value],
            'test_run': [GlueSprayState.IDLE.value],
            'emergency_stop': [state.value for state in GlueSprayState],  # Can always emergency stop
            'reset': [GlueSprayState.ERROR.value],
            'pause': [GlueSprayState.EXECUTING_TRAJECTORY.value],
            'resume': [GlueSprayState.PAUSED.value]
        }

        return current_state in valid_states.get(operation, [])

    def get_available_operations(self) -> list:
        """Get list of operations available in current state"""
        operations = ['start', 'calibrate_robot', 'calibrate_camera', 'create_workpiece',
                      'measure_height', 'update_tool_changer', 'handle_belt', 'test_run',
                      'emergency_stop', 'reset', 'pause', 'resume']

        return [op for op in operations if self.can_execute_operation(op)]

    def stop(self):
        """Stop the state machine"""
        self.state_machine.stop()

    def __getattr__(self, name):
        """Delegate unknown attributes to original application"""
        return getattr(self.original_app, name)


# ============================================================================
# INTEGRATION EXAMPLE AND USAGE
# ============================================================================

def create_enhanced_glue_spray_application(original_app):
    """
    Factory function to create an enhanced glue spray application.

    This replaces the pattern:
    app = GlueSprayingApplication(...)

    With:
    app = create_enhanced_glue_spray_application(original_app)
    """
    return GlueSprayApplicationAdapter(original_app)


# Usage example showing migration path:
"""
# BEFORE: Original application usage
original_app = GlueSprayingApplication(callback, vision, settings, glue, workpiece, robot, calib)
result = original_app.start(contourMatching=True)

# AFTER: Enhanced application with state machine
original_app = GlueSprayingApplication(callback, vision, settings, glue, workpiece, robot, calib)
enhanced_app = create_enhanced_glue_spray_application(original_app)

# All original functionality still works, but now with state machine benefits
result = enhanced_app.start(contourMatching=True)  # Uses state machine
enhanced_app.emergency_stop()  # New functionality
enhanced_app.reset()  # New functionality

# Can check what operations are available
available_ops = enhanced_app.get_available_operations()
print(f"Available operations: {available_ops}")

# Can monitor state changes
print(f"Current state: {enhanced_app.get_current_state()}")
history = enhanced_app.get_state_history()
print(f"Last 3 transitions: {history[-3:]}")
"""


# ============================================================================
# CONFIGURATION-BASED ALTERNATIVE
# ============================================================================

def create_glue_spray_from_config(original_app, config_dict: Dict[str, Any]):
    """
    Alternative approach: Create state machine from external configuration.
    This allows changing behavior without code changes.
    """

    context = GlueSprayContext(original_app)

    # Register operation callbacks
    context.register_callback('execute_operation',
                              lambda params: _execute_configured_operation(original_app, params))
    context.register_callback('process_event',
                              lambda params: None)  # Would be handled by state machine

    # Create state machine from configuration
    state_machine = StateMachineFactory.from_dict(config_dict, context)

    # Create wrapper class
    class ConfiguredGlueSprayApp:
        def __init__(self, sm, orig_app):
            self.state_machine = sm
            self.original_app = orig_app
            self.state_machine.start()

        def process_event(self, event_name: str, data: Dict[str, Any] = None):
            self.state_machine.process_event(event_name, data or {})

        def get_current_state(self):
            return self.state_machine.get_current_state()

        def __getattr__(self, name):
            return getattr(self.original_app, name)

    return ConfiguredGlueSprayApp(state_machine, original_app)


def _execute_configured_operation(original_app, params: Dict[str, Any]) -> Any:
    """Execute operation based on configuration parameters"""
    operation_type = params.get('operation_type')

    operation_map = {
        'execute_trajectory': lambda: original_app.start(params.get('contour_matching', True)),
        'calibrate_robot': lambda: original_app.calibrateRobot(),
        'calibrate_camera': lambda: original_app.calibrateCamera(),
        'create_workpiece': lambda: original_app.createWorkpiece(),
        'measure_height': lambda: original_app.measureHeight(),
        'update_tool_changer': lambda: original_app.updateToolChangerStation(),
        'handle_belt': lambda: original_app.handleBelt(),
        'test_run': lambda: original_app.testRun(),
    }

    operation = operation_map.get(operation_type)
    if operation:
        return operation()
    else:
        raise ValueError(f"Unknown operation: {operation_type}")


# Example configuration that could be loaded from JSON/YAML
GLUE_SPRAY_CONFIG = {
    "initial_state": "IDLE",
    "states": {
        "IDLE": {
            "entry_actions": ["log_entry", "ensure_safe_position"],
            "transitions": {
                "START_REQUESTED": "EXECUTING_TRAJECTORY",
                "CALIBRATE_ROBOT_REQUESTED": "CALIBRATING_ROBOT"
            }
        },
        "EXECUTING_TRAJECTORY": {
            "operation_type": "execute_trajectory",
            "timeout_seconds": 300,
            "transitions": {
                "OPERATION_COMPLETED": "IDLE",
                "OPERATION_FAILED": "ERROR"
            }
        },
        "CALIBRATING_ROBOT": {
            "operation_type": "calibrate_robot",
            "timeout_seconds": 120,
            "transitions": {
                "OPERATION_COMPLETED": "IDLE",
                "OPERATION_FAILED": "ERROR"
            }
        },
        "ERROR": {
            "entry_actions": ["log_error", "move_to_safe_position"],
            "transitions": {
                "RESET_REQUESTED": "IDLE"
            }
        }
    },
    "global_transitions": {
        "ERROR_OCCURRED": "ERROR"
    },
    "error_recovery": {
        "EXECUTING_TRAJECTORY": "ERROR",
        "CALIBRATING_ROBOT": "ERROR"
    }
}
from new_development.GlueSprayApplicationStateMachineAdapter.errorSystem.glueSprayErrorCodes.errorCodes import HardwareErrorCode, SafetyErrorCode
from new_development.GlueSprayApplicationStateMachineAdapter.recoveryStrategies.RetryRecoveryStrategy import RetryRecoveryStrategy
from new_development.GlueSprayApplicationStateMachineAdapter.recoveryStrategies.SafePositionRecoveryStrategy import \
    SafePositionRecoveryStrategy
from new_development.StateMachineFramework.errorCodesSystem.contextAndTracking.ErrorTracker import ErrorTracker
from new_development.StateMachineFramework.errorCodesSystem.errorCodes.errorCodes import OperationErrorCode, \
    ValidationErrorCode
from new_development.StateMachineFramework.errorCodesSystem.recoveryStrategies.ErrorRecoveryManager import ErrorRecoveryManager


from new_development.StateMachineFramework.v2 import *



from new_development.StateMachineFramework.errorCodesSystem.InformationRegistry.ErrorRegistry import ERROR_REGISTRY


# ============================================================================
# APPLICATION-SPECIFIC ENUMS AND EVENTS
# ============================================================================

class GlueSprayState(Enum):
    INITIALIZING = "INITIALIZING"
    IDLE = "IDLE"
    STARTED = "STARTED"
    CALIBRATING_ROBOT = "CALIBRATING_ROBOT"
    CALIBRATING_CAMERA = "CALIBRATING_CAMERA"
    MEASURING_HEIGHT = "MEASURING_HEIGHT"
    CREATING_WORKPIECE = "CREATING_WORKPIECE"
    UPDATING_TOOL_CHANGER = "UPDATING_TOOL_CHANGER"
    EXECUTING_TRAJECTORY = "EXECUTING_TRAJECTORY"
    HANDLING_BELT = "HANDLING_BELT"
    TEST_RUNNING = "TEST_RUNNING"
    ERROR = "ERROR"
    PAUSED = "PAUSED"


class GlueSprayEvent(Enum):
    # System Events
    SYSTEM_READY = "SYSTEM_READY"
    ROBOT_READY = "ROBOT_READY"
    VISION_READY = "VISION_READY"
    ERROR_OCCURRED = "ERROR_OCCURRED"
    RESET_REQUESTED = "RESET_REQUESTED"

    # Operation Events
    START_REQUESTED = "START_REQUESTED"
    CALIBRATE_ROBOT_REQUESTED = "CALIBRATE_ROBOT_REQUESTED"
    CALIBRATE_CAMERA_REQUESTED = "CALIBRATE_CAMERA_REQUESTED"
    MEASURE_HEIGHT_REQUESTED = "MEASURE_HEIGHT_REQUESTED"
    CREATE_WORKPIECE_REQUESTED = "CREATE_WORKPIECE_REQUESTED"
    UPDATE_TOOL_CHANGER_REQUESTED = "UPDATE_TOOL_CHANGER_REQUESTED"
    EXECUTE_TRAJECTORY_REQUESTED = "EXECUTE_TRAJECTORY_REQUESTED"
    HANDLE_BELT_REQUESTED = "HANDLE_BELT_REQUESTED"
    TEST_RUN_REQUESTED = "TEST_RUN_REQUESTED"

    # Completion Events
    OPERATION_COMPLETED = "OPERATION_COMPLETED"
    OPERATION_FAILED = "OPERATION_FAILED"
    PAUSE_REQUESTED = "PAUSE_REQUESTED"
    RESUME_REQUESTED = "RESUME_REQUESTED"


# ============================================================================
# APPLICATION CONTEXT
# ============================================================================

class GlueSprayContext(BaseContext):
    """Extended context for glue spray application"""

    def __init__(self, original_application):
        super().__init__()
        self.original_app = original_application
        self.current_operation = None
        self.operation_params = {}
        self.safety_checks_enabled = True

        # Initialize error management
        self.error_recovery_manager = ErrorRecoveryManager()
        self.error_tracker = ErrorTracker()
        self._setup_error_recovery()

    def _setup_error_recovery(self):
        """Setup error recovery strategies"""

        # Retry strategy for communication and temporary hardware issues
        retry_strategy = RetryRecoveryStrategy([
            HardwareErrorCode.CAMERA_CONNECTION_FAILED,
            HardwareErrorCode.IMAGE_CAPTURE_FAILED,
            HardwareErrorCode.ROBOT_MOVEMENT_FAILED,
            OperationErrorCode.OPERATION_TIMEOUT
        ], max_retries=3, delay=2.0)

        # Safe position strategy for critical hardware issues
        safe_position_strategy = SafePositionRecoveryStrategy([
            HardwareErrorCode.ROBOT_COLLISION_DETECTED,
            HardwareErrorCode.ROBOT_EMERGENCY_STOP,
            SafetyErrorCode.SAFETY_FENCE_OPEN,
            SafetyErrorCode.EMERGENCY_STOP_ACTIVATED,
            SafetyErrorCode.DANGEROUS_POSITION_DETECTED
        ])

        self.error_recovery_manager.add_strategy(retry_strategy)
        self.error_recovery_manager.add_strategy(safe_position_strategy)

    def get_robot_status(self) -> Dict[str, Any]:
        """Get current robot status with error handling"""
        try:
            if not hasattr(self.original_app, 'robotService') or not self.original_app.robotService:
                self._record_error(HardwareErrorCode.ROBOT_CONNECTION_FAILED,
                                   "Robot service not available")
                return {'connected': False, 'error': 'Robot service not available'}

            return {
                'connected': True,
                'position': 'unknown',  # Could get actual position
                'status': 'ready'
            }
        except Exception as e:
            self._record_error(HardwareErrorCode.ROBOT_CONNECTION_FAILED, str(e))
            return {'connected': False, 'error': str(e)}

    def is_safe_to_operate(self) -> bool:
        """Check if it's safe to perform operations with detailed error reporting"""
        if not self.safety_checks_enabled:
            return True

        try:
            robot_status = self.get_robot_status()
            if not robot_status.get('connected', False):
                self._record_error(ValidationErrorCode.PRECONDITION_FAILED,
                                   "Robot not connected")
                return False

            # Additional safety checks could be added here
            # e.g., safety fence status, emergency stop status, etc.

            return True

        except Exception as e:
            self._record_error(ValidationErrorCode.SAFETY_CHECK_FAILED, str(e))
            return False

    def _record_error(self, error_code: int, message: str, operation: str = None):
        """Record an error with proper context"""
        self.error_tracker.record_error(
            code=error_code,
            state=getattr(self, 'current_state', 'unknown'),
            operation=operation or self.current_operation,
            additional_data={'message': message}
        )

        # Set error message for compatibility
        self.error_message = f"[{error_code}] {message}"


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
        """Execute the specified operation with comprehensive error handling"""
        operation_type = params.get('operation_type')
        context_data = params.get('context_data', {})

        print(f"Executing operation: {operation_type}")
        self.context.current_operation = operation_type

        try:
            # Safety check before any operation
            if not self.context.is_safe_to_operate():
                raise StateMachineError(
                    code=ValidationErrorCode.SAFETY_CHECK_FAILED,
                    message="System not in safe state for operation",
                    context={'operation': operation_type}
                )

            # Execute the appropriate operation with specific error handling
            if operation_type == "execute_trajectory":
                return self._execute_trajectory(context_data)
            elif operation_type == "calibrate_robot":
                return self._execute_robot_calibration()
            elif operation_type == "calibrate_camera":
                return self._execute_camera_calibration()
            elif operation_type == "create_workpiece":
                return self._execute_workpiece_creation()
            elif operation_type == "measure_height":
                return self._execute_height_measurement()
            elif operation_type == "update_tool_changer":
                return self._execute_tool_changer_update()
            elif operation_type == "handle_belt":
                return self._execute_belt_handling()
            elif operation_type == "test_run":
                return self._execute_test_run()
            else:
                raise StateMachineError(
                    code=OperationErrorCode.OPERATION_NOT_SUPPORTED,
                    message=f"Unknown operation type: {operation_type}",
                    context={'operation': operation_type}
                )

        except StateMachineError:
            # Re-raise StateMachineError with proper error codes
            raise
        except Exception as e:
            # Convert generic exceptions to StateMachineError
            self.context._record_error(OperationErrorCode.OPERATION_FAILED, str(e), operation_type)
            raise StateMachineError(
                code=OperationErrorCode.OPERATION_FAILED,
                message=f"Operation {operation_type} failed: {str(e)}",
                context={'operation': operation_type, 'original_error': str(e)}
            )
        finally:
            self.context.current_operation = None

    def _execute_trajectory(self, context_data: Dict[str, Any]) -> Any:
        """Execute trajectory with specific error handling"""
        try:
            contour_matching = context_data.get('contour_matching', True)
            return self._safe_call('start', contour_matching)
        except Exception as e:
            if "connection" in str(e).lower():
                raise StateMachineError(HardwareErrorCode.ROBOT_CONNECTION_FAILED, str(e))
            elif "collision" in str(e).lower():
                raise StateMachineError(HardwareErrorCode.ROBOT_COLLISION_DETECTED, str(e))
            elif "position" in str(e).lower():
                raise StateMachineError(HardwareErrorCode.ROBOT_POSITION_INVALID, str(e))
            else:
                raise StateMachineError(OperationErrorCode.OPERATION_FAILED, str(e))

    def _execute_robot_calibration(self) -> Any:
        """Execute robot calibration with specific error handling"""
        try:
            return self._safe_call('calibrateRobot')
        except Exception as e:
            if "connection" in str(e).lower():
                raise StateMachineError(HardwareErrorCode.ROBOT_CONNECTION_FAILED, str(e))
            else:
                raise StateMachineError(HardwareErrorCode.ROBOT_CALIBRATION_FAILED, str(e))

    def _execute_camera_calibration(self) -> Any:
        """Execute camera calibration with specific error handling"""
        try:
            return self._safe_call('calibrateCamera')
        except Exception as e:
            if "connection" in str(e).lower():
                raise StateMachineError(HardwareErrorCode.CAMERA_CONNECTION_FAILED, str(e))
            else:
                raise StateMachineError(HardwareErrorCode.CAMERA_CALIBRATION_FAILED, str(e))

    def _execute_workpiece_creation(self) -> Any:
        """Execute workpiece creation with specific error handling"""
        try:
            return self._safe_call('createWorkpiece')
        except Exception as e:
            if "vision" in str(e).lower() or "image" in str(e).lower():
                raise StateMachineError(HardwareErrorCode.IMAGE_PROCESSING_FAILED, str(e))
            else:
                raise StateMachineError(OperationErrorCode.OPERATION_FAILED, str(e))

    def _execute_height_measurement(self) -> Any:
        """Execute height measurement with specific error handling"""
        try:
            return self._safe_call('measureHeight')
        except Exception as e:
            if "camera" in str(e).lower():
                raise StateMachineError(HardwareErrorCode.CAMERA_CONNECTION_FAILED, str(e))
            elif "vision" in str(e).lower():
                raise StateMachineError(HardwareErrorCode.VISION_ALGORITHM_FAILED, str(e))
            else:
                raise StateMachineError(OperationErrorCode.OPERATION_FAILED, str(e))

    def _execute_tool_changer_update(self) -> Any:
        """Execute tool changer update with specific error handling"""
        try:
            return self._safe_call('updateToolChangerStation')
        except Exception as e:
            if "robot" in str(e).lower():
                raise StateMachineError(HardwareErrorCode.ROBOT_MOVEMENT_FAILED, str(e))
            else:
                raise StateMachineError(OperationErrorCode.OPERATION_FAILED, str(e))

    def _execute_belt_handling(self) -> Any:
        """Execute belt handling with specific error handling"""
        try:
            return self._safe_call('handleBelt')
        except Exception as e:
            if "movement" in str(e).lower():
                raise StateMachineError(HardwareErrorCode.BELT_MOVEMENT_FAILED, str(e))
            elif "sensor" in str(e).lower():
                raise StateMachineError(HardwareErrorCode.BELT_POSITION_SENSOR_FAILED, str(e))
            elif "workpiece" in str(e).lower():
                raise StateMachineError(HardwareErrorCode.WORKPIECE_NOT_DETECTED, str(e))
            else:
                raise StateMachineError(OperationErrorCode.OPERATION_FAILED, str(e))

    def _execute_test_run(self) -> Any:
        """Execute test run with specific error handling"""
        try:
            return self._safe_call('testRun')
        except Exception as e:
            raise StateMachineError(OperationErrorCode.OPERATION_FAILED, str(e))

    def _safe_call(self, method_name: str, *args, **kwargs) -> Any:
        """Safely call an original application method with error code mapping"""
        method = self.original_methods.get(method_name)
        if not method:
            raise StateMachineError(
                code=StateMachineErrorCode.CONTEXT_CALLBACK_MISSING,
                message=f"Method {method_name} not found in original application",
                context={'method': method_name}
            )

        try:
            return method(*args, **kwargs)
        except Exception as e:
            # Map common exceptions to appropriate error codes
            error_message = str(e).lower()

            if "timeout" in error_message:
                raise StateMachineError(OperationErrorCode.OPERATION_TIMEOUT, str(e))
            elif "connection" in error_message:
                if "robot" in error_message:
                    raise StateMachineError(HardwareErrorCode.ROBOT_CONNECTION_FAILED, str(e))
                elif "camera" in error_message:
                    raise StateMachineError(HardwareErrorCode.CAMERA_CONNECTION_FAILED, str(e))
                else:
                    raise StateMachineError(HardwareErrorCode.ROBOT_CONNECTION_FAILED, str(e))
            elif "emergency" in error_message or "stop" in error_message:
                raise StateMachineError(SafetyErrorCode.EMERGENCY_STOP_ACTIVATED, str(e))
            elif "safety" in error_message:
                raise StateMachineError(ValidationErrorCode.SAFETY_CHECK_FAILED, str(e))
            else:
                # Generic operation failure
                raise StateMachineError(OperationErrorCode.OPERATION_FAILED, str(e))

    def _process_event(self, params: Dict[str, Any]):
        """Process an event through the state machine with error handling"""
        try:
            event_name = params.get('event')
            event_data = params.get('data', {})
            self.state_machine.process_event(event_name, event_data)
        except Exception as e:
            self.context._record_error(StateMachineErrorCode.EVENT_PROCESSING_FAILED, str(e))
            raise

    # Action callback implementations with error handling
    def _log_state_entry(self, params: Dict[str, Any]):
        """Log state entry"""
        state = params.get('state', 'Unknown')
        print(f"Entering state: {state}")

    def _ensure_safe_position(self, params: Dict[str, Any]):
        """Ensure robot is in safe position with error handling"""
        try:
            if hasattr(self.original_app, 'robotService') and self.original_app.robotService:
                self.original_app.robotService.moveToStartPosition()
                print("Robot moved to safe position")
            else:
                self.context._record_error(HardwareErrorCode.ROBOT_CONNECTION_FAILED,
                                           "Robot service not available")
        except Exception as e:
            self.context._record_error(HardwareErrorCode.ROBOT_MOVEMENT_FAILED, str(e))
            print(f"Failed to move robot to safe position: {e}")
            # Don't raise here as this is a safety action that should not fail state transitions

    def _log_error(self, params: Dict[str, Any]):
        """Log error state entry with error code information"""
        error_msg = self.context.error_message or "Unknown error"
        error_code = params.get('error_code', 'Unknown')
        print(f"ERROR STATE [{error_code}]: {error_msg}")

        # Log error details if available
        if hasattr(self.context, 'error_tracker'):
            recent_errors = self.context.error_tracker.get_recent_errors(1)
            if recent_errors:
                error_context = recent_errors[0]
                error_info = ERROR_REGISTRY.get_error_info(error_context.code)
                if error_info:
                    print(f"Error Info: {error_info.name}")
                    print(f"Suggested Action: {error_info.suggested_action}")

    def _move_to_safe_position(self, params: Dict[str, Any]):
        """Move robot to safe position on error with comprehensive error handling"""
        try:
            if hasattr(self.original_app, 'robotService') and self.original_app.robotService:
                self.original_app.robotService.moveToStartPosition()
                print("Robot moved to safe position due to error")
            else:
                self.context._record_error(HardwareErrorCode.ROBOT_CONNECTION_FAILED,
                                           "Robot service not available for safe position")
                print("WARNING: Cannot move robot to safe position - robot service unavailable")
        except Exception as e:
            self.context._record_error(HardwareErrorCode.ROBOT_MOVEMENT_FAILED, str(e))
            print(f"CRITICAL: Failed to move robot to safe position on error: {e}")
            # This is critical - robot may be in unsafe position

    def _pause_operations(self, params: Dict[str, Any]):
        """Pause current operations"""
        print("Operations paused")
        try:
            # Could implement actual pause logic here
            # For example, pause robot motion, stop glue flow, etc.
            pass
        except Exception as e:
            self.context._record_error(OperationErrorCode.OPERATION_FAILED, str(e))

    def _clear_error(self, params: Dict[str, Any]):
        """Clear error state"""
        self.context.error_message = ""

        # Clear active errors in error tracker
        if hasattr(self.context, 'error_tracker'):
            active_errors = self.context.error_tracker.get_active_errors()
            for error_context in active_errors:
                self.context.error_tracker.clear_error(error_context.code)

        print("Error state cleared")

    def _handle_application_error(self, params: Dict[str, Any]):
        """Handle application-specific errors with enhanced error management"""
        error_msg = params.get('error', 'Unknown error')
        error_code = params.get('error_code', OperationErrorCode.OPERATION_FAILED)

        print(f"Application Error [{error_code}]: {error_msg}")
        self.context.error_message = error_msg

        # Record in error tracker
        self.context._record_error(error_code, error_msg)

        # Try automated recovery first
        recovery_successful = self.context.error_recovery_manager.handle_error(
            error_code=error_code,
            state_machine=self.state_machine,
            state=self.state_machine.get_current_state(),
            additional_data={'error_message': error_msg}
        )

        if not recovery_successful:
            # Fallback to safe position
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
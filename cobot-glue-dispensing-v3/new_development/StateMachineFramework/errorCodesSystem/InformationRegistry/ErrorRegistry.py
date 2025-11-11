from typing import Optional, Dict, List

from new_development.GlueSprayApplicationStateMachineAdapter.errorSystem.glueSprayErrorCodes.errorCodes import HardwareErrorCode, SafetyErrorCode
from new_development.StateMachineFramework.errorCodesSystem.InformationRegistry.ErrorInfo import ErrorInfo
from new_development.StateMachineFramework.errorCodesSystem.errorCodes.errorCodes import  *



class ErrorRegistry:
    """Central registry for all error information"""

    def __init__(self):
        self._error_info: Dict[int, ErrorInfo] = {}
        self._initialize_error_registry()

    def _initialize_error_registry(self):
        """Initialize all error information"""

        # System Errors
        self._register_error(SystemErrorCode.SYSTEM_INITIALIZATION_FAILED,
                             "System Initialization Failed",
                             "The system failed to initialize properly during startup",
                             ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL,
                             "Check system configuration and dependencies",
                             recovery_possible=False, requires_restart=True)

        self._register_error(SystemErrorCode.SYSTEM_RESOURCE_EXHAUSTED,
                             "System Resource Exhausted",
                             "System has run out of available resources (memory, handles, etc.)",
                             ErrorCategory.SYSTEM, ErrorSeverity.ERROR,
                             "Free up system resources or restart application")

        # State Machine Errors
        self._register_error(StateMachineErrorCode.STATE_NOT_FOUND,
                             "State Not Found",
                             "Attempted to transition to a state that doesn't exist",
                             ErrorCategory.STATE_MACHINE, ErrorSeverity.ERROR,
                             "Check state machine configuration and state names")

        self._register_error(StateMachineErrorCode.STATE_TRANSITION_INVALID,
                             "Invalid State Transition",
                             "Attempted state transition is not allowed from current state",
                             ErrorCategory.STATE_MACHINE, ErrorSeverity.WARNING,
                             "Check current state and allowed transitions")

        self._register_error(StateMachineErrorCode.EVENT_NOT_HANDLED,
                             "Event Not Handled",
                             "Event was sent but no state could handle it",
                             ErrorCategory.STATE_MACHINE, ErrorSeverity.WARNING,
                             "Check if event is valid for current state")

        self._register_error(StateMachineErrorCode.CONFIG_PARSE_FAILED,
                             "Configuration Parse Failed",
                             "Failed to parse state machine configuration file",
                             ErrorCategory.CONFIGURATION, ErrorSeverity.CRITICAL,
                             "Check configuration file syntax and format",
                             recovery_possible=False)

        # Hardware Errors
        self._register_error(HardwareErrorCode.ROBOT_CONNECTION_FAILED,
                             "Robot Connection Failed",
                             "Failed to establish connection with robot controller",
                             ErrorCategory.HARDWARE, ErrorSeverity.CRITICAL,
                             "Check robot power, network connection, and controller status")

        self._register_error(HardwareErrorCode.ROBOT_EMERGENCY_STOP,
                             "Robot Emergency Stop",
                             "Robot emergency stop has been activated",
                             ErrorCategory.SAFETY, ErrorSeverity.FATAL,
                             "Clear emergency stop condition and reset robot",
                             requires_restart=True)

        self._register_error(HardwareErrorCode.CAMERA_CALIBRATION_FAILED,
                             "Camera Calibration Failed",
                             "Vision system camera calibration process failed",
                             ErrorCategory.HARDWARE, ErrorSeverity.ERROR,
                             "Check camera setup, lighting, and calibration targets")

        self._register_error(HardwareErrorCode.GLUE_RESERVOIR_EMPTY,
                             "Glue Reservoir Empty",
                             "Glue application system reservoir is empty",
                             ErrorCategory.HARDWARE, ErrorSeverity.WARNING,
                             "Refill glue reservoir and reset system")

        # Communication Errors
        self._register_error(CommunicationErrorCode.CONNECTION_TIMEOUT,
                             "Connection Timeout",
                             "Communication timeout while connecting to device",
                             ErrorCategory.COMMUNICATION, ErrorSeverity.ERROR,
                             "Check network connection and device availability")

        # Validation Errors
        self._register_error(ValidationErrorCode.SAFETY_CHECK_FAILED,
                             "Safety Check Failed",
                             "Pre-operation safety validation failed",
                             ErrorCategory.SAFETY, ErrorSeverity.CRITICAL,
                             "Ensure all safety conditions are met before operation")

        self._register_error(ValidationErrorCode.PARAMETER_OUT_OF_RANGE,
                             "Parameter Out of Range",
                             "Operation parameter is outside acceptable range",
                             ErrorCategory.VALIDATION, ErrorSeverity.ERROR,
                             "Check parameter values and acceptable ranges")

        # Operation Errors
        self._register_error(OperationErrorCode.OPERATION_TIMEOUT,
                             "Operation Timeout",
                             "Operation did not complete within expected time",
                             ErrorCategory.TIMEOUT, ErrorSeverity.ERROR,
                             "Check operation parameters and system performance")

        # Safety Errors
        self._register_error(SafetyErrorCode.SAFETY_FENCE_OPEN,
                             "Safety Fence Open",
                             "Safety fence is open, preventing operation",
                             ErrorCategory.SAFETY, ErrorSeverity.CRITICAL,
                             "Close safety fence before continuing operation")

    def _register_error(self, code: IntEnum, name: str, description: str,
                        category: ErrorCategory, severity: ErrorSeverity,
                        suggested_action: str, recovery_possible: bool = True,
                        requires_restart: bool = False):
        """Register an error in the registry"""
        error_info = ErrorInfo(
            code=int(code),
            name=name,
            description=description,
            category=category,
            severity=severity,
            suggested_action=suggested_action,
            recovery_possible=recovery_possible,
            requires_restart=requires_restart
        )
        self._error_info[int(code)] = error_info

    def get_error_info(self, code: int) -> Optional[ErrorInfo]:
        """Get error information by code"""
        return self._error_info.get(code)

    def get_all_errors(self) -> Dict[int, ErrorInfo]:
        """Get all registered errors"""
        return self._error_info.copy()

    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorInfo]:
        """Get all errors in a specific category"""
        return [info for info in self._error_info.values() if info.category == category]

    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorInfo]:
        """Get all errors of a specific severity"""
        return [info for info in self._error_info.values() if info.severity == severity]


# Global error registry instance
ERROR_REGISTRY = ErrorRegistry()

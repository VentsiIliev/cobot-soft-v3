# ============================================================================
# USAGE EXAMPLES
# ============================================================================
import json

from new_development.GlueSprayApplicationStateMachineAdapter.errorSystem.glueSprayErrorCodes.errorCodes import HardwareErrorCode, \
    SafetyErrorCode
from new_development.GlueSprayApplicationStateMachineAdapter.recoveryStrategies.RetryRecoveryStrategy import RetryRecoveryStrategy
from new_development.GlueSprayApplicationStateMachineAdapter.recoveryStrategies.SafePositionRecoveryStrategy import \
    SafePositionRecoveryStrategy
from new_development.StateMachineFramework.errorCodesSystem.InformationRegistry.ErrorRegistry import ERROR_REGISTRY
from new_development.StateMachineFramework.errorCodesSystem.contextAndTracking.ErrorTracker import ErrorTracker
from new_development.StateMachineFramework.errorCodesSystem.contextAndTracking.StateMachineError import StateMachineError
from new_development.StateMachineFramework.errorCodesSystem.errorCodes.errorCodes import *

from new_development.StateMachineFramework.errorCodesSystem.recoveryStrategies.ErrorRecoveryManager import ErrorRecoveryManager



def demonstrate_error_system():
    """Demonstrate the error code system"""

    print("=" * 60)
    print("ERROR CODE SYSTEM DEMONSTRATION")
    print("=" * 60)

    # 1. Basic error information lookup
    print("\n1. ERROR INFORMATION LOOKUP")
    print("-" * 30)

    error_info = ERROR_REGISTRY.get_error_info(HardwareErrorCode.ROBOT_CONNECTION_FAILED)
    if error_info:
        print(f"Code: {error_info.code}")
        print(f"Name: {error_info.name}")
        print(f"Description: {error_info.description}")
        print(f"Category: {error_info.category.value}")
        print(f"Severity: {error_info.severity.name}")
        print(f"Suggested Action: {error_info.suggested_action}")
        print(f"Recovery Possible: {error_info.recovery_possible}")

    # 2. Creating and handling errors
    print("\n2. ERROR CREATION AND HANDLING")
    print("-" * 35)

    try:
        raise StateMachineError(
            code=StateMachineErrorCode.STATE_TRANSITION_INVALID,
            context={'current_state': 'PROCESSING', 'target_state': 'INVALID'}
        )
    except StateMachineError as e:
        print(f"Caught error: {e.message}")
        print(f"Severity: {e.severity.name}")
        print(f"Category: {e.category.value}")
        print(f"Suggested Action: {e.suggested_action}")
        print(f"Error Dict: {json.dumps(e.to_dict(), indent=2)}")

    # 3. Error tracking
    print("\n3. ERROR TRACKING")
    print("-" * 20)

    tracker = ErrorTracker()

    # Record some errors
    tracker.record_error(HardwareErrorCode.ROBOT_CONNECTION_FAILED,
                         state='CALIBRATING', operation='connect_robot')
    tracker.record_error(ValidationErrorCode.SAFETY_CHECK_FAILED,
                         state='IDLE', operation='start_operation')
    tracker.record_error(HardwareErrorCode.ROBOT_EMERGENCY_STOP,
                         state='EXECUTING', operation='trajectory')

    print(f"Total errors recorded: {len(tracker.error_history)}")
    print(f"Active errors: {len(tracker.get_active_errors())}")
    print(f"Fatal errors present: {tracker.has_fatal_errors()}")

    # Show recent errors
    print("\nRecent errors:")
    for error_context in tracker.get_recent_errors(3):
        error_info = ERROR_REGISTRY.get_error_info(error_context.code)
        print(f"  - {error_info.name if error_info else 'Unknown'} in {error_context.state}")

    # 4. Error recovery
    print("\n4. ERROR RECOVERY")
    print("-" * 20)

    recovery_manager = ErrorRecoveryManager()

    # Add recovery strategies
    retry_strategy = RetryRecoveryStrategy([
        CommunicationErrorCode.CONNECTION_TIMEOUT,
        HardwareErrorCode.IMAGE_CAPTURE_FAILED
    ])

    safe_position_strategy = SafePositionRecoveryStrategy([
        HardwareErrorCode.ROBOT_COLLISION_DETECTED,
        SafetyErrorCode.EMERGENCY_STOP_ACTIVATED
    ])

    recovery_manager.add_strategy(retry_strategy)
    recovery_manager.add_strategy(safe_position_strategy)

    print("Recovery strategies configured:")
    print(f"  - Retry strategy for {len(retry_strategy.error_codes)} error codes")
    print(f"  - Safe position strategy for {len(safe_position_strategy.error_codes)} error codes")

    # 5. Error categories and analysis
    print("\n5. ERROR ANALYSIS")
    print("-" * 20)

    safety_errors = ERROR_REGISTRY.get_errors_by_category(ErrorCategory.SAFETY)
    critical_errors = ERROR_REGISTRY.get_errors_by_severity(ErrorSeverity.CRITICAL)

    print(f"Safety errors defined: {len(safety_errors)}")
    print(f"Critical errors defined: {len(critical_errors)}")

    print("\nAll error categories:")
    for category in ErrorCategory:
        count = len(ERROR_REGISTRY.get_errors_by_category(category))
        print(f"  - {category.value}: {count} errors")


if __name__ == "__main__":
    demonstrate_error_system()
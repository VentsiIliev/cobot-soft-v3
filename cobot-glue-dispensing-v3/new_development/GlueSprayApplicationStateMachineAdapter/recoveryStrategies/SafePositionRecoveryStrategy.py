from typing import List

from new_development.StateMachineFramework.errorCodesSystem.contextAndTracking.ErrorContext import ErrorContext
from new_development.StateMachineFramework.errorCodesSystem.recoveryStrategies.ErrorRecoveryStrategy import ErrorRecoveryStrategy


class SafePositionRecoveryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy that moves system to safe position"""

    def __init__(self, error_codes: List[int]):
        super().__init__(error_codes)

    def recover(self, error_context: ErrorContext, state_machine) -> bool:
        """Move to safe position"""
        try:
            # Move robot to safe position
            state_machine.context.execute_callback('move_to_safe_position', {})
            # Transition to error state
            state_machine.process_event('ERROR_OCCURRED', {
                'error_code': error_context.code,
                'recovery_strategy': 'safe_position'
            })
            return True
        except Exception as e:
            print(f"Safe position recovery failed: {e}")
            return False
from typing import List, Dict, Any

from new_development.StateMachineFramework.errorCodesSystem.contextAndTracking.ErrorTracker import ErrorTracker
from new_development.StateMachineFramework.errorCodesSystem.recoveryStrategies.ErrorRecoveryStrategy import ErrorRecoveryStrategy


class ErrorRecoveryManager:
    """Manages error recovery strategies"""

    def __init__(self):
        self.strategies: List[ErrorRecoveryStrategy] = []
        self.error_tracker = ErrorTracker()

    def add_strategy(self, strategy: ErrorRecoveryStrategy):
        """Add a recovery strategy"""
        self.strategies.append(strategy)

    def handle_error(self, error_code: int, state_machine, state: str = None,
                     operation: str = None, additional_data: Dict[str, Any] = None) -> bool:
        """Handle an error with appropriate recovery strategy"""

        # Record the error
        error_context = self.error_tracker.record_error(
            code=error_code,
            state=state,
            operation=operation,
            additional_data=additional_data
        )

        # Try recovery strategies
        for strategy in self.strategies:
            if strategy.can_handle(error_code):
                try:
                    if strategy.recover(error_context, state_machine):
                        error_context.recovery_attempted = True
                        error_context.recovery_successful = True
                        return True
                except Exception as e:
                    print(f"Recovery strategy failed: {e}")

        # No recovery possible
        error_context.recovery_attempted = True
        error_context.recovery_successful = False
        return False
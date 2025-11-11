import time
from typing import List, Dict

from new_development.StateMachineFramework.errorCodesSystem.contextAndTracking.ErrorContext import ErrorContext
from new_development.StateMachineFramework.errorCodesSystem.recoveryStrategies.ErrorRecoveryStrategy import ErrorRecoveryStrategy


class RetryRecoveryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy that retries the operation"""

    def __init__(self, error_codes: List[int], max_retries: int = 3, delay: float = 1.0):
        super().__init__(error_codes)
        self.max_retries = max_retries
        self.delay = delay
        self.retry_counts: Dict[str, int] = {}

    def recover(self, error_context: ErrorContext, state_machine) -> bool:
        """Retry the failed operation"""
        operation_key = f"{error_context.state}:{error_context.operation}"
        current_retries = self.retry_counts.get(operation_key, 0)

        if current_retries < self.max_retries:
            self.retry_counts[operation_key] = current_retries + 1
            time.sleep(self.delay)

            # Trigger retry (implementation depends on specific state machine)
            print(f"Retrying operation {error_context.operation} (attempt {current_retries + 1})")
            return True
        else:
            # Max retries exceeded
            self.retry_counts[operation_key] = 0
            return False
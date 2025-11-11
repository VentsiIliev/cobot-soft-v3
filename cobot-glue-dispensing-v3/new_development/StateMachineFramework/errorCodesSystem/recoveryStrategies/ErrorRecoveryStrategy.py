from typing import List

from new_development.StateMachineFramework.errorCodesSystem.contextAndTracking.ErrorContext import ErrorContext


class ErrorRecoveryStrategy:
    """Base class for error recovery strategies"""

    def __init__(self, error_codes: List[int]):
        self.error_codes = error_codes

    def can_handle(self, error_code: int) -> bool:
        """Check if this strategy can handle the error"""
        return error_code in self.error_codes

    def recover(self, error_context: ErrorContext, state_machine) -> bool:
        """Attempt to recover from the error"""
        raise NotImplementedError
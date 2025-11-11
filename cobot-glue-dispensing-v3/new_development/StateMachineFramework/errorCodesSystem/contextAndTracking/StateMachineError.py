from typing import Dict, Any
from new_development.StateMachineFramework.errorCodesSystem.InformationRegistry.ErrorRegistry import ERROR_REGISTRY
from new_development.StateMachineFramework.errorCodesSystem.errorCodes.errorCodes import *

class StateMachineError(Exception):
    """Enhanced exception class with error codes"""

    def __init__(self, code: int, message: str = None, context: Dict[str, Any] = None):
        self.code = code
        self.error_info = ERROR_REGISTRY.get_error_info(code)
        self.context = context or {}

        # Build message
        if message:
            self.message = message
        elif self.error_info:
            self.message = f"{self.error_info.name}: {self.error_info.description}"
        else:
            self.message = f"Unknown error code: {code}"

        super().__init__(self.message)

    @property
    def severity(self) -> ErrorSeverity:
        """Get error severity"""
        return self.error_info.severity if self.error_info else ErrorSeverity.ERROR

    @property
    def category(self) -> ErrorCategory:
        """Get error category"""
        return self.error_info.category if self.error_info else ErrorCategory.SYSTEM

    @property
    def suggested_action(self) -> str:
        """Get suggested action"""
        return self.error_info.suggested_action if self.error_info else "Contact support"

    @property
    def recovery_possible(self) -> bool:
        """Check if recovery is possible"""
        return self.error_info.recovery_possible if self.error_info else True

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization"""
        return {
            'code': self.code,
            'name': self.error_info.name if self.error_info else 'Unknown',
            'message': self.message,
            'severity': self.severity.name,
            'category': self.category.value,
            'suggested_action': self.suggested_action,
            'recovery_possible': self.recovery_possible,
            'context': self.context
        }
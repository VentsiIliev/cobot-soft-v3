from dataclasses import dataclass

from new_development.StateMachineFramework.errorCodesSystem.errorCodes.errorCodes import *


@dataclass
class ErrorInfo:
    """Complete error information"""
    code: int
    name: str
    description: str
    category: ErrorCategory
    severity: ErrorSeverity
    suggested_action: str
    recovery_possible: bool = True
    requires_restart: bool = False
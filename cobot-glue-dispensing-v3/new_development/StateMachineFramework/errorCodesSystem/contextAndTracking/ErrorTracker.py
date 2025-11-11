import time
from typing import List, Dict, Any

from new_development.StateMachineFramework.errorCodesSystem.InformationRegistry.ErrorRegistry import ERROR_REGISTRY
from new_development.StateMachineFramework.errorCodesSystem.contextAndTracking.ErrorContext import ErrorContext
from new_development.StateMachineFramework.errorCodesSystem.errorCodes.errorCodes import *


class ErrorTracker:
    """Tracks and manages error occurrences"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.error_history: List[ErrorContext] = []
        self.error_counts: Dict[int, int] = {}
        self.active_errors: Dict[int, ErrorContext] = {}

    def record_error(self, code: int, state: str = None, operation: str = None,
                     additional_data: Dict[str, Any] = None, stack_trace: str = None) -> ErrorContext:
        """Record an error occurrence"""

        error_context = ErrorContext(
            code=code,
            timestamp=time.time(),
            state=state,
            operation=operation,
            additional_data=additional_data or {},
            stack_trace=stack_trace
        )

        # Add to history
        self.error_history.append(error_context)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)

        # Update counts
        self.error_counts[code] = self.error_counts.get(code, 0) + 1

        # Track active errors (for critical/fatal errors)
        error_info = ERROR_REGISTRY.get_error_info(code)
        if error_info and error_info.severity >= ErrorSeverity.CRITICAL:
            self.active_errors[code] = error_context

        return error_context

    def clear_error(self, code: int) -> bool:
        """Clear an active error"""
        if code in self.active_errors:
            self.active_errors[code].recovery_attempted = True
            self.active_errors[code].recovery_successful = True
            del self.active_errors[code]
            return True
        return False

    def get_active_errors(self) -> List[ErrorContext]:
        """Get all currently active errors"""
        return list(self.active_errors.values())

    def get_error_count(self, code: int) -> int:
        """Get count of specific error occurrences"""
        return self.error_counts.get(code, 0)

    def get_recent_errors(self, count: int = 10) -> List[ErrorContext]:
        """Get most recent errors"""
        return self.error_history[-count:] if self.error_history else []

    def has_fatal_errors(self) -> bool:
        """Check if there are any fatal errors"""
        for error_context in self.active_errors.values():
            error_info = ERROR_REGISTRY.get_error_info(error_context.code)
            if error_info and error_info.severity == ErrorSeverity.FATAL:
                return True
        return False

    def export_error_log(self) -> List[Dict[str, Any]]:
        """Export error history for logging/analysis"""
        log_entries = []
        for error_context in self.error_history:
            error_info = ERROR_REGISTRY.get_error_info(error_context.code)
            entry = {
                'timestamp': error_context.timestamp,
                'code': error_context.code,
                'name': error_info.name if error_info else 'Unknown',
                'severity': error_info.severity.name if error_info else 'ERROR',
                'category': error_info.category.value if error_info else 'SYSTEM',
                'state': error_context.state,
                'operation': error_context.operation,
                'additional_data': error_context.additional_data,
                'recovery_attempted': error_context.recovery_attempted,
                'recovery_successful': error_context.recovery_successful
            }
            log_entries.append(entry)
        return log_entries
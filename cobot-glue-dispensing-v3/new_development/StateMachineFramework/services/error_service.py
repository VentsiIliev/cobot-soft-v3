"""
Enhanced error service integrating the existing error handling system.

This module provides a service-oriented interface to the existing error handling
components, making them compatible with the new architecture.
"""

import time
import threading
from typing import Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod

from ..core.context import BaseContext
from ..validation.validation_result import ValidationResult
from ..errorCodesSystem.contextAndTracking.ErrorTracker import ErrorTracker
from ..errorCodesSystem.recoveryStrategies.ErrorRecoveryManager import ErrorRecoveryManager
from ..errorCodesSystem.contextAndTracking.ErrorContext import ErrorContext
from ..errorCodesSystem.InformationRegistry.ErrorRegistry import ERROR_REGISTRY
from ..errorCodesSystem.errorCodes.errorCodes import ErrorSeverity


class ErrorService(ABC):
    """Abstract interface for error handling service."""
    
    @abstractmethod
    def record_error(self, error_code: int, state: str = None, 
                    operation: str = None, context: Dict[str, Any] = None) -> ErrorContext:
        """Record an error occurrence."""
        pass
    
    @abstractmethod
    def handle_error(self, error_code: int, state_machine, state: str = None,
                    operation: str = None, additional_data: Dict[str, Any] = None) -> bool:
        """Handle an error with recovery strategies."""
        pass
    
    @abstractmethod
    def clear_error(self, error_code: int) -> bool:
        """Clear an active error."""
        pass
    
    @abstractmethod
    def get_active_errors(self) -> List[ErrorContext]:
        """Get all currently active errors."""
        pass
    
    @abstractmethod
    def has_fatal_errors(self) -> bool:
        """Check if there are any fatal errors."""
        pass
    
    @abstractmethod
    def add_error_callback(self, callback: Callable[[ErrorContext], None]) -> str:
        """Add error notification callback."""
        pass
    
    @abstractmethod
    def remove_error_callback(self, callback_id: str) -> bool:
        """Remove error notification callback."""
        pass
    
    @abstractmethod
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        pass


class EnhancedErrorService(ErrorService):
    """Enhanced error service with integrated error handling."""
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize enhanced error service.
        
        Args:
            max_history: Maximum number of errors to keep in history
        """
        self._error_tracker = ErrorTracker(max_history)
        self._recovery_manager = ErrorRecoveryManager()
        self._callbacks: Dict[str, Callable[[ErrorContext], None]] = {}
        self._callback_counter = 0
        self._lock = threading.RLock()
        self._error_rate_tracker = {}  # Track error rates
        self._circuit_breaker_states = {}  # Circuit breaker for high error rates
    
    def record_error(self, error_code: int, state: str = None, 
                    operation: str = None, context: Dict[str, Any] = None) -> ErrorContext:
        """Record an error occurrence with enhanced tracking."""
        with self._lock:
            # Record the error using existing tracker
            error_context = self._error_tracker.record_error(
                code=error_code,
                state=state,
                operation=operation,
                additional_data=context
            )
            
            # Track error rates for circuit breaker pattern
            self._update_error_rate_tracking(error_code)
            
            # Notify all callbacks
            for callback in self._callbacks.values():
                try:
                    callback(error_context)
                except Exception as e:
                    print(f"Error in error callback: {e}")
            
            return error_context
    
    def handle_error(self, error_code: int, state_machine, state: str = None,
                    operation: str = None, additional_data: Dict[str, Any] = None) -> bool:
        """Handle an error with recovery strategies."""
        with self._lock:
            # Check circuit breaker
            if self._is_circuit_open(error_code):
                print(f"Circuit breaker open for error {error_code}, skipping recovery")
                return False
            
            # Use existing recovery manager
            recovery_successful = self._recovery_manager.handle_error(
                error_code=error_code,
                state_machine=state_machine,
                state=state,
                operation=operation,
                additional_data=additional_data
            )
            
            # Update circuit breaker based on recovery success
            self._update_circuit_breaker(error_code, recovery_successful)
            
            return recovery_successful
    
    def clear_error(self, error_code: int) -> bool:
        """Clear an active error."""
        with self._lock:
            return self._error_tracker.clear_error(error_code)
    
    def get_active_errors(self) -> List[ErrorContext]:
        """Get all currently active errors."""
        with self._lock:
            return self._error_tracker.get_active_errors()
    
    def has_fatal_errors(self) -> bool:
        """Check if there are any fatal errors."""
        with self._lock:
            return self._error_tracker.has_fatal_errors()
    
    def add_error_callback(self, callback: Callable[[ErrorContext], None]) -> str:
        """Add error notification callback."""
        with self._lock:
            callback_id = f"callback_{self._callback_counter}"
            self._callback_counter += 1
            self._callbacks[callback_id] = callback
            return callback_id
    
    def remove_error_callback(self, callback_id: str) -> bool:
        """Remove error notification callback."""
        with self._lock:
            if callback_id in self._callbacks:
                del self._callbacks[callback_id]
                return True
            return False
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        with self._lock:
            active_errors = self.get_active_errors()
            recent_errors = self._error_tracker.get_recent_errors(100)
            
            # Calculate error rates by severity
            severity_counts = {}
            for error_context in recent_errors:
                error_info = ERROR_REGISTRY.get_error_info(error_context.code)
                severity = error_info.severity.name if error_info else 'UNKNOWN'
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Calculate recovery success rate
            total_recovery_attempts = sum(1 for e in recent_errors if e.recovery_attempted)
            successful_recoveries = sum(1 for e in recent_errors if e.recovery_successful)
            recovery_rate = (successful_recoveries / total_recovery_attempts * 100) if total_recovery_attempts > 0 else 0
            
            return {
                'total_errors': len(self._error_tracker.error_history),
                'active_errors': len(active_errors),
                'recent_errors': len(recent_errors),
                'has_fatal_errors': self.has_fatal_errors(),
                'severity_distribution': severity_counts,
                'recovery_success_rate': recovery_rate,
                'error_rate_tracking': dict(self._error_rate_tracker),
                'circuit_breaker_states': dict(self._circuit_breaker_states),
                'registered_callbacks': len(self._callbacks)
            }
    
    def add_recovery_strategy(self, strategy):
        """Add a recovery strategy to the manager."""
        with self._lock:
            self._recovery_manager.add_strategy(strategy)
    
    def export_error_log(self) -> List[Dict[str, Any]]:
        """Export error history for analysis."""
        with self._lock:
            return self._error_tracker.export_error_log()
    
    def validate_error_handling(self, context: BaseContext) -> ValidationResult:
        """Validate current error handling state."""
        result = ValidationResult.success("Error handling validation passed")
        
        with self._lock:
            # Check for too many active errors
            active_errors = self.get_active_errors()
            if len(active_errors) > 10:
                result.add_warning(
                    "HIGH_ACTIVE_ERRORS",
                    f"High number of active errors: {len(active_errors)}"
                )
            
            # Check for fatal errors
            if self.has_fatal_errors():
                result.add_error(
                    "FATAL_ERRORS_PRESENT",
                    "Fatal errors are present in the system"
                )
            
            # Check error rates
            for error_code, rate_info in self._error_rate_tracker.items():
                if rate_info.get('rate', 0) > 10:  # More than 10 errors per minute
                    result.add_warning(
                        "HIGH_ERROR_RATE",
                        f"High error rate for error {error_code}: {rate_info['rate']} errors/min"
                    )
        
        return result
    
    def _update_error_rate_tracking(self, error_code: int) -> None:
        """Update error rate tracking for circuit breaker."""
        current_time = time.time()
        
        if error_code not in self._error_rate_tracker:
            self._error_rate_tracker[error_code] = {
                'count': 0,
                'window_start': current_time,
                'rate': 0.0
            }
        
        tracker = self._error_rate_tracker[error_code]
        tracker['count'] += 1
        
        # Calculate rate over 1-minute window
        window_duration = current_time - tracker['window_start']
        if window_duration >= 60:  # 1 minute window
            tracker['rate'] = tracker['count'] / (window_duration / 60)
            tracker['count'] = 0
            tracker['window_start'] = current_time
    
    def _is_circuit_open(self, error_code: int) -> bool:
        """Check if circuit breaker is open for this error code."""
        circuit_state = self._circuit_breaker_states.get(error_code)
        if not circuit_state:
            return False
        
        current_time = time.time()
        if circuit_state['state'] == 'open':
            # Check if we should try to close the circuit
            if current_time - circuit_state['opened_at'] > 300:  # 5 minutes
                circuit_state['state'] = 'half_open'
                return False
            return True
        
        return False
    
    def _update_circuit_breaker(self, error_code: int, recovery_successful: bool) -> None:
        """Update circuit breaker state based on recovery success."""
        if error_code not in self._circuit_breaker_states:
            self._circuit_breaker_states[error_code] = {
                'state': 'closed',
                'failure_count': 0,
                'opened_at': None
            }
        
        circuit_state = self._circuit_breaker_states[error_code]
        
        if recovery_successful:
            circuit_state['failure_count'] = 0
            if circuit_state['state'] == 'half_open':
                circuit_state['state'] = 'closed'
        else:
            circuit_state['failure_count'] += 1
            if circuit_state['failure_count'] >= 5:  # Open after 5 consecutive failures
                circuit_state['state'] = 'open'
                circuit_state['opened_at'] = time.time()


class NullErrorService(ErrorService):
    """Null implementation for testing or minimal configurations."""
    
    def record_error(self, error_code: int, state: str = None, 
                    operation: str = None, context: Dict[str, Any] = None) -> ErrorContext:
        """Record error (no-op)."""
        return ErrorContext(code=error_code, timestamp=time.time())
    
    def handle_error(self, error_code: int, state_machine, state: str = None,
                    operation: str = None, additional_data: Dict[str, Any] = None) -> bool:
        """Handle error (always fails)."""
        return False
    
    def clear_error(self, error_code: int) -> bool:
        """Clear error (always succeeds)."""
        return True
    
    def get_active_errors(self) -> List[ErrorContext]:
        """Get active errors (always empty)."""
        return []
    
    def has_fatal_errors(self) -> bool:
        """Check for fatal errors (always false)."""
        return False
    
    def add_error_callback(self, callback: Callable[[ErrorContext], None]) -> str:
        """Add callback (returns dummy ID)."""
        return "null_callback"
    
    def remove_error_callback(self, callback_id: str) -> bool:
        """Remove callback (always succeeds)."""
        return True
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get statistics (empty)."""
        return {
            'total_errors': 0,
            'active_errors': 0,
            'recent_errors': 0,
            'has_fatal_errors': False,
            'severity_distribution': {},
            'recovery_success_rate': 100.0,
            'error_rate_tracking': {},
            'circuit_breaker_states': {},
            'registered_callbacks': 0
        }
"""
Default implementations for enhanced services.

This module provides default implementations for the new service interfaces
to enable out-of-the-box functionality.
"""

import threading
import time
import json
import csv
import io
from typing import Dict, Any, Optional, List, Callable
from collections import defaultdict
import uuid

from .new_services import (
    TimerService, MetricsService, ValidationService, 
    ConfigurationService, SecurityService, NotificationService,
    StateMetrics, TransitionMetrics
)
from .error_service import ErrorService
from ..core.context import BaseContext
from ..validation.validation_result import ValidationResult


class DefaultTimerService(TimerService):
    """Default timer service using threading.Timer."""
    
    def __init__(self):
        """Initialize timer service."""
        self._timers: Dict[str, threading.Timer] = {}
        self._lock = threading.RLock()
    
    def schedule_timeout(self, state_name: str, timeout_seconds: int, 
                        callback: Callable[[], None]) -> str:
        """Schedule a timeout for a state."""
        timeout_id = f"timeout_{state_name}_{uuid.uuid4().hex[:8]}"
        
        def timeout_wrapper():
            with self._lock:
                # Remove from active timers when executed
                self._timers.pop(timeout_id, None)
            callback()
        
        timer = threading.Timer(timeout_seconds, timeout_wrapper)
        
        with self._lock:
            self._timers[timeout_id] = timer
        
        timer.start()
        return timeout_id
    
    def cancel_timeout(self, timeout_id: str) -> bool:
        """Cancel a scheduled timeout."""
        with self._lock:
            timer = self._timers.pop(timeout_id, None)
            if timer:
                timer.cancel()
                return True
            return False
    
    def schedule_event(self, event_name: str, delay_seconds: int, 
                      data: Dict[str, Any] = None) -> str:
        """Schedule a delayed event."""
        schedule_id = f"event_{event_name}_{uuid.uuid4().hex[:8]}"
        
        def event_wrapper():
            with self._lock:
                self._timers.pop(schedule_id, None)
            # Would need event service reference to emit event
            # This is a simplified implementation
        
        timer = threading.Timer(delay_seconds, event_wrapper)
        
        with self._lock:
            self._timers[schedule_id] = timer
        
        timer.start()
        return schedule_id
    
    def cancel_scheduled_event(self, schedule_id: str) -> bool:
        """Cancel a scheduled event."""
        return self.cancel_timeout(schedule_id)  # Same implementation
    
    def get_active_timers(self) -> List[Dict[str, Any]]:
        """Get information about active timers."""
        with self._lock:
            return [
                {
                    'id': timer_id,
                    'active': timer.is_alive()
                }
                for timer_id, timer in self._timers.items()
            ]


class DefaultMetricsService(MetricsService):
    """Default metrics service with in-memory storage."""
    
    def __init__(self):
        """Initialize metrics service."""
        self._state_metrics: Dict[str, StateMetrics] = {}
        self._transition_metrics: Dict[str, TransitionMetrics] = {}
        self._error_counts: Dict[int, int] = defaultdict(int)
        self._lock = threading.RLock()
        self._start_time = time.time()
    
    def record_state_entry(self, state_name: str, timestamp: Optional[float] = None) -> None:
        """Record state entry."""
        if timestamp is None:
            timestamp = time.time()
        
        with self._lock:
            if state_name not in self._state_metrics:
                self._state_metrics[state_name] = StateMetrics(state_name)
            
            metrics = self._state_metrics[state_name]
            metrics.entry_count += 1
            metrics.last_entry_time = timestamp
    
    def record_state_exit(self, state_name: str, timestamp: Optional[float] = None) -> None:
        """Record state exit."""
        if timestamp is None:
            timestamp = time.time()
        
        with self._lock:
            if state_name not in self._state_metrics:
                self._state_metrics[state_name] = StateMetrics(state_name)
            
            metrics = self._state_metrics[state_name]
            metrics.exit_count += 1
            metrics.last_exit_time = timestamp
            
            # Calculate duration if we have entry time
            if metrics.last_entry_time:
                duration = timestamp - metrics.last_entry_time
                metrics.total_duration += duration
    
    def record_transition(self, from_state: str, to_state: str, event: str, 
                         duration: Optional[float] = None) -> None:
        """Record a state transition."""
        key = f"{from_state}->{to_state}:{event}"
        
        with self._lock:
            if key not in self._transition_metrics:
                self._transition_metrics[key] = TransitionMetrics(from_state, to_state, event)
            
            metrics = self._transition_metrics[key]
            metrics.count += 1
            metrics.last_transition_time = time.time()
            
            if duration is not None:
                metrics.total_duration += duration
    
    def record_error(self, error_code: int, state: str = None, 
                    context: Dict[str, Any] = None) -> None:
        """Record an error occurrence."""
        with self._lock:
            self._error_counts[error_code] += 1
    
    def get_state_metrics(self, state_name: str) -> Optional[StateMetrics]:
        """Get metrics for a specific state."""
        with self._lock:
            return self._state_metrics.get(state_name)
    
    def get_transition_metrics(self, from_state: str, to_state: str, 
                              event: str) -> Optional[TransitionMetrics]:
        """Get metrics for a specific transition."""
        key = f"{from_state}->{to_state}:{event}"
        with self._lock:
            return self._transition_metrics.get(key)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics."""
        with self._lock:
            total_entries = sum(metrics.entry_count for metrics in self._state_metrics.values())
            total_transitions = sum(metrics.count for metrics in self._transition_metrics.values())
            total_errors = sum(self._error_counts.values())
            
            return {
                'collection_start_time': self._start_time,
                'collection_duration': time.time() - self._start_time,
                'total_state_entries': total_entries,
                'total_transitions': total_transitions,
                'total_errors': total_errors,
                'states_tracked': len(self._state_metrics),
                'transitions_tracked': len(self._transition_metrics),
                'error_codes_seen': len(self._error_counts),
                'state_metrics': {name: {
                    'entry_count': metrics.entry_count,
                    'exit_count': metrics.exit_count,
                    'average_duration': metrics.average_duration,
                    'is_active': metrics.is_currently_active
                } for name, metrics in self._state_metrics.items()},
                'error_distribution': dict(self._error_counts)
            }
    
    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        with self._lock:
            self._state_metrics.clear()
            self._transition_metrics.clear()
            self._error_counts.clear()
            self._start_time = time.time()
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        summary = self.get_metrics_summary()
        
        if format.lower() == "json":
            return json.dumps(summary, indent=2)
        elif format.lower() == "csv":
            # Export state metrics as CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['State', 'Entries', 'Exits', 'Average Duration', 'Is Active'])
            
            # Write state data
            for name, metrics in summary['state_metrics'].items():
                writer.writerow([
                    name,
                    metrics['entry_count'],
                    metrics['exit_count'],
                    metrics['average_duration'],
                    metrics['is_active']
                ])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")


class DefaultValidationService(ValidationService):
    """Default validation service with configurable rules."""
    
    def __init__(self):
        """Initialize validation service."""
        self._global_validators: List[Callable[[BaseContext], ValidationResult]] = []
        self._state_validators: Dict[str, List[Callable[[BaseContext], ValidationResult]]] = defaultdict(list)
        self._transition_validators: Dict[str, List[Callable[[BaseContext], ValidationResult]]] = defaultdict(list)
        self._lock = threading.RLock()
    
    def validate_transition(self, from_state: str, to_state: str, 
                           event: str, context: BaseContext) -> ValidationResult:
        """Validate if transition is allowed."""
        result = ValidationResult.success("Transition validation passed")
        
        # Run global validators
        with self._lock:
            for validator in self._global_validators:
                try:
                    validator_result = validator(context)
                    result.merge(validator_result)
                except Exception as e:
                    result.add_error("VALIDATOR_EXCEPTION", f"Validator failed: {str(e)}")
            
            # Run transition-specific validators
            transition_key = f"{from_state}->{to_state}:{event}"
            for validator in self._transition_validators.get(transition_key, []):
                try:
                    validator_result = validator(context)
                    result.merge(validator_result)
                except Exception as e:
                    result.add_error("VALIDATOR_EXCEPTION", f"Transition validator failed: {str(e)}")
        
        return result
    
    def validate_state_entry(self, state_name: str, context: BaseContext) -> ValidationResult:
        """Validate state entry conditions."""
        result = ValidationResult.success("State entry validation passed")
        
        with self._lock:
            # Run global validators
            for validator in self._global_validators:
                try:
                    validator_result = validator(context)
                    result.merge(validator_result)
                except Exception as e:
                    result.add_error("VALIDATOR_EXCEPTION", f"Validator failed: {str(e)}")
            
            # Run state-specific validators
            for validator in self._state_validators.get(state_name, []):
                try:
                    validator_result = validator(context)
                    result.merge(validator_result)
                except Exception as e:
                    result.add_error("VALIDATOR_EXCEPTION", f"State validator failed: {str(e)}")
        
        return result
    
    def validate_state_exit(self, state_name: str, context: BaseContext) -> ValidationResult:
        """Validate state exit conditions."""
        # Same as entry validation for now
        return self.validate_state_entry(state_name, context)
    
    def add_global_validator(self, validator: Callable[[BaseContext], ValidationResult]) -> None:
        """Add a global validation rule."""
        with self._lock:
            self._global_validators.append(validator)
    
    def add_state_validator(self, state_name: str, 
                           validator: Callable[[BaseContext], ValidationResult]) -> None:
        """Add a state-specific validation rule."""
        with self._lock:
            self._state_validators[state_name].append(validator)
    
    def add_transition_validator(self, from_state: str, to_state: str, event: str,
                                validator: Callable[[BaseContext], ValidationResult]) -> None:
        """Add a transition-specific validation rule."""
        transition_key = f"{from_state}->{to_state}:{event}"
        with self._lock:
            self._transition_validators[transition_key].append(validator)


class DefaultConfigurationService(ConfigurationService):
    """Default configuration service with in-memory storage."""
    
    def __init__(self):
        """Initialize configuration service."""
        self._configurations: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def save_configuration(self, config: Dict[str, Any], name: str) -> bool:
        """Save configuration with a name."""
        try:
            with self._lock:
                self._configurations[name] = dict(config)
            return True
        except Exception:
            return False
    
    def load_configuration(self, name: str) -> Optional[Dict[str, Any]]:
        """Load configuration by name."""
        with self._lock:
            config = self._configurations.get(name)
            return dict(config) if config else None
    
    def list_configurations(self) -> List[str]:
        """List available configuration names."""
        with self._lock:
            return list(self._configurations.keys())
    
    def delete_configuration(self, name: str) -> bool:
        """Delete configuration by name."""
        with self._lock:
            if name in self._configurations:
                del self._configurations[name]
                return True
            return False
    
    def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate a configuration."""
        result = ValidationResult.success("Configuration is valid")
        
        # Basic validation
        if 'initial_state' not in config:
            result.add_error("MISSING_INITIAL_STATE", "Configuration must have initial_state")
        
        if 'states' not in config:
            result.add_error("MISSING_STATES", "Configuration must have states")
        elif not isinstance(config['states'], dict):
            result.add_error("INVALID_STATES", "States must be a dictionary")
        
        return result


class DefaultSecurityService(SecurityService):
    """Default security service with basic role-based authorization."""
    
    def __init__(self):
        """Initialize security service."""
        self._role_permissions: Dict[str, List[str]] = {
            'admin': ['*'],  # Admin can do anything
            'operator': ['transition:*', 'operation:view'],
            'viewer': ['operation:view']
        }
        self._security_log: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
    
    def authorize_transition(self, from_state: str, to_state: str, 
                           user_context: Dict[str, Any]) -> bool:
        """Authorize a state transition for a user."""
        user_role = user_context.get('role', 'viewer')
        permissions = self._role_permissions.get(user_role, [])
        
        # Check if user has global permission or specific transition permission
        return ('*' in permissions or 
                'transition:*' in permissions or 
                f'transition:{from_state}->{to_state}' in permissions)
    
    def authorize_operation(self, operation: str, state: str,
                           user_context: Dict[str, Any]) -> bool:
        """Authorize an operation in a specific state."""
        user_role = user_context.get('role', 'viewer')
        permissions = self._role_permissions.get(user_role, [])
        
        return ('*' in permissions or 
                f'operation:{operation}' in permissions or
                f'operation:*' in permissions)
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log a security-related event."""
        with self._lock:
            self._security_log.append({
                'timestamp': time.time(),
                'event_type': event_type,
                'details': details
            })
    
    def get_user_permissions(self, user_context: Dict[str, Any]) -> List[str]:
        """Get user permissions."""
        user_role = user_context.get('role', 'viewer')
        return self._role_permissions.get(user_role, [])


class DefaultNotificationService(NotificationService):
    """Default notification service with callback-based notifications."""
    
    def __init__(self):
        """Initialize notification service."""
        self._state_change_subscribers: Dict[str, Callable[[str, str], None]] = {}
        self._error_subscribers: Dict[str, Callable[[int, str, Dict[str, Any]], None]] = {}
        self._lock = threading.RLock()
    
    def send_notification(self, message: str, level: str = "info", 
                         recipients: List[str] = None) -> bool:
        """Send notification."""
        # Simple console notification
        print(f"[{level.upper()}] {message}")
        return True
    
    def subscribe_to_state_changes(self, callback: Callable[[str, str], None]) -> str:
        """Subscribe to state change notifications."""
        subscription_id = f"state_sub_{uuid.uuid4().hex[:8]}"
        with self._lock:
            self._state_change_subscribers[subscription_id] = callback
        return subscription_id
    
    def subscribe_to_errors(self, callback: Callable[[int, str, Dict[str, Any]], None]) -> str:
        """Subscribe to error notifications."""
        subscription_id = f"error_sub_{uuid.uuid4().hex[:8]}"
        with self._lock:
            self._error_subscribers[subscription_id] = callback
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from notifications."""
        with self._lock:
            removed = False
            if subscription_id in self._state_change_subscribers:
                del self._state_change_subscribers[subscription_id]
                removed = True
            if subscription_id in self._error_subscribers:
                del self._error_subscribers[subscription_id]
                removed = True
            return removed
    
    def notify_state_change(self, from_state: str, to_state: str) -> None:
        """Notify all subscribers of state change."""
        with self._lock:
            for callback in self._state_change_subscribers.values():
                try:
                    callback(from_state, to_state)
                except Exception as e:
                    print(f"Error in state change notification: {e}")
    
    def notify_error(self, error_code: int, state: str, context: Dict[str, Any]) -> None:
        """Notify all subscribers of error."""
        with self._lock:
            for callback in self._error_subscribers.values():
                try:
                    callback(error_code, state, context)
                except Exception as e:
                    print(f"Error in error notification: {e}")


# Service factory for easy creation
class ServiceFactory:
    """Factory for creating default service implementations."""
    
    @staticmethod
    def create_default_services() -> Dict[type, Any]:
        """Create all default service implementations."""
        from .error_service import EnhancedErrorService
        return {
            TimerService: DefaultTimerService(),
            MetricsService: DefaultMetricsService(),
            ValidationService: DefaultValidationService(),
            ConfigurationService: DefaultConfigurationService(),
            SecurityService: DefaultSecurityService(),
            NotificationService: DefaultNotificationService(),
            ErrorService: EnhancedErrorService()
        }
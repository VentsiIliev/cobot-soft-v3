"""
New service interfaces for enhanced state machine functionality.

This module provides additional service interfaces for timers, metrics,
validation, and other advanced features.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field
import time
from ..core.context import BaseContext
from ..validation.validation_result import ValidationResult


class TimerService(ABC):
    """Service for managing state timeouts and scheduled events."""
    
    @abstractmethod
    def schedule_timeout(self, state_name: str, timeout_seconds: int, 
                        callback: Callable[[], None]) -> str:
        """
        Schedule a timeout for a state.
        
        Args:
            state_name: Name of the state
            timeout_seconds: Timeout duration in seconds
            callback: Callback to execute on timeout
            
        Returns:
            Timeout ID for cancellation
        """
        pass
    
    @abstractmethod
    def cancel_timeout(self, timeout_id: str) -> bool:
        """
        Cancel a scheduled timeout.
        
        Args:
            timeout_id: ID of timeout to cancel
            
        Returns:
            True if timeout was found and cancelled
        """
        pass
    
    @abstractmethod
    def schedule_event(self, event_name: str, delay_seconds: int, 
                      data: Dict[str, Any] = None) -> str:
        """
        Schedule a delayed event.
        
        Args:
            event_name: Name of event to emit
            delay_seconds: Delay before emitting event
            data: Optional event data
            
        Returns:
            Schedule ID for cancellation
        """
        pass
    
    @abstractmethod
    def cancel_scheduled_event(self, schedule_id: str) -> bool:
        """
        Cancel a scheduled event.
        
        Args:
            schedule_id: ID of scheduled event
            
        Returns:
            True if event was found and cancelled
        """
        pass
    
    @abstractmethod
    def get_active_timers(self) -> List[Dict[str, Any]]:
        """
        Get information about active timers.
        
        Returns:
            List of active timer information
        """
        pass


@dataclass
class StateMetrics:
    """Metrics for a specific state."""
    state_name: str
    entry_count: int = 0
    exit_count: int = 0
    total_duration: float = 0.0
    error_count: int = 0
    last_entry_time: Optional[float] = None
    last_exit_time: Optional[float] = None
    
    @property
    def average_duration(self) -> float:
        """Calculate average duration per entry."""
        if self.entry_count > 0:
            return self.total_duration / self.entry_count
        return 0.0
    
    @property
    def is_currently_active(self) -> bool:
        """Check if state is currently active."""
        return (self.last_entry_time is not None and 
                (self.last_exit_time is None or self.last_entry_time > self.last_exit_time))


@dataclass 
class TransitionMetrics:
    """Metrics for state transitions."""
    from_state: str
    to_state: str
    event: str
    count: int = 0
    total_duration: float = 0.0
    last_transition_time: Optional[float] = None
    
    @property
    def average_duration(self) -> float:
        """Calculate average transition duration."""
        if self.count > 0:
            return self.total_duration / self.count
        return 0.0


class MetricsService(ABC):
    """Service for collecting state machine metrics."""
    
    @abstractmethod
    def record_state_entry(self, state_name: str, timestamp: Optional[float] = None) -> None:
        """
        Record state entry.
        
        Args:
            state_name: Name of state entered
            timestamp: Optional timestamp (uses current time if None)
        """
        pass
    
    @abstractmethod
    def record_state_exit(self, state_name: str, timestamp: Optional[float] = None) -> None:
        """
        Record state exit.
        
        Args:
            state_name: Name of state exited
            timestamp: Optional timestamp (uses current time if None)
        """
        pass
    
    @abstractmethod
    def record_transition(self, from_state: str, to_state: str, event: str, 
                         duration: Optional[float] = None) -> None:
        """
        Record a state transition.
        
        Args:
            from_state: Source state
            to_state: Target state
            event: Event that triggered transition
            duration: Optional transition duration
        """
        pass
    
    @abstractmethod
    def record_error(self, error_code: int, state: str = None, 
                    context: Dict[str, Any] = None) -> None:
        """
        Record an error occurrence.
        
        Args:
            error_code: Error code
            state: State where error occurred
            context: Additional error context
        """
        pass
    
    @abstractmethod
    def get_state_metrics(self, state_name: str) -> Optional[StateMetrics]:
        """
        Get metrics for a specific state.
        
        Args:
            state_name: Name of state
            
        Returns:
            State metrics or None if not found
        """
        pass
    
    @abstractmethod
    def get_transition_metrics(self, from_state: str, to_state: str, 
                              event: str) -> Optional[TransitionMetrics]:
        """
        Get metrics for a specific transition.
        
        Args:
            from_state: Source state
            to_state: Target state
            event: Event name
            
        Returns:
            Transition metrics or None if not found
        """
        pass
    
    @abstractmethod
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of collected metrics.
        
        Returns:
            Dictionary containing metrics summary
        """
        pass
    
    @abstractmethod
    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        pass
    
    @abstractmethod
    def export_metrics(self, format: str = "json") -> str:
        """
        Export metrics in specified format.
        
        Args:
            format: Export format ("json", "csv", etc.)
            
        Returns:
            Exported metrics as string
        """
        pass


class ValidationService(ABC):
    """Service for validating state machine operations."""
    
    @abstractmethod
    def validate_transition(self, from_state: str, to_state: str, 
                           event: str, context: BaseContext) -> ValidationResult:
        """
        Validate if transition is allowed.
        
        Args:
            from_state: Source state
            to_state: Target state
            event: Event triggering transition
            context: State machine context
            
        Returns:
            Validation result
        """
        pass
    
    @abstractmethod
    def validate_state_entry(self, state_name: str, context: BaseContext) -> ValidationResult:
        """
        Validate state entry conditions.
        
        Args:
            state_name: Name of state to enter
            context: State machine context
            
        Returns:
            Validation result
        """
        pass
    
    @abstractmethod
    def validate_state_exit(self, state_name: str, context: BaseContext) -> ValidationResult:
        """
        Validate state exit conditions.
        
        Args:
            state_name: Name of state to exit
            context: State machine context
            
        Returns:
            Validation result
        """
        pass
    
    @abstractmethod
    def add_global_validator(self, validator: Callable[[BaseContext], ValidationResult]) -> None:
        """
        Add a global validation rule.
        
        Args:
            validator: Validation function
        """
        pass
    
    @abstractmethod
    def add_state_validator(self, state_name: str, 
                           validator: Callable[[BaseContext], ValidationResult]) -> None:
        """
        Add a state-specific validation rule.
        
        Args:
            state_name: State name
            validator: Validation function
        """
        pass
    
    @abstractmethod
    def add_transition_validator(self, from_state: str, to_state: str, event: str,
                                validator: Callable[[BaseContext], ValidationResult]) -> None:
        """
        Add a transition-specific validation rule.
        
        Args:
            from_state: Source state
            to_state: Target state
            event: Event name
            validator: Validation function
        """
        pass


class ConfigurationService(ABC):
    """Service for managing state machine configuration."""
    
    @abstractmethod
    def save_configuration(self, config: Dict[str, Any], name: str) -> bool:
        """
        Save configuration with a name.
        
        Args:
            config: Configuration dictionary
            name: Configuration name
            
        Returns:
            True if saved successfully
        """
        pass
    
    @abstractmethod
    def load_configuration(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load configuration by name.
        
        Args:
            name: Configuration name
            
        Returns:
            Configuration dictionary or None if not found
        """
        pass
    
    @abstractmethod
    def list_configurations(self) -> List[str]:
        """
        List available configuration names.
        
        Returns:
            List of configuration names
        """
        pass
    
    @abstractmethod
    def delete_configuration(self, name: str) -> bool:
        """
        Delete configuration by name.
        
        Args:
            name: Configuration name
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Validate a configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Validation result
        """
        pass


class SecurityService(ABC):
    """Service for state machine security and access control."""
    
    @abstractmethod
    def authorize_transition(self, from_state: str, to_state: str, 
                           user_context: Dict[str, Any]) -> bool:
        """
        Authorize a state transition for a user.
        
        Args:
            from_state: Source state
            to_state: Target state
            user_context: User authentication/authorization context
            
        Returns:
            True if transition is authorized
        """
        pass
    
    @abstractmethod
    def authorize_operation(self, operation: str, state: str,
                           user_context: Dict[str, Any]) -> bool:
        """
        Authorize an operation in a specific state.
        
        Args:
            operation: Operation name
            state: Current state
            user_context: User context
            
        Returns:
            True if operation is authorized
        """
        pass
    
    @abstractmethod
    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log a security-related event.
        
        Args:
            event_type: Type of security event
            details: Event details
        """
        pass
    
    @abstractmethod
    def get_user_permissions(self, user_context: Dict[str, Any]) -> List[str]:
        """
        Get user permissions.
        
        Args:
            user_context: User context
            
        Returns:
            List of user permissions
        """
        pass


class NotificationService(ABC):
    """Service for sending notifications about state machine events."""
    
    @abstractmethod
    def send_notification(self, message: str, level: str = "info", 
                         recipients: List[str] = None) -> bool:
        """
        Send notification.
        
        Args:
            message: Notification message
            level: Notification level (info, warning, error, critical)
            recipients: Optional list of recipients
            
        Returns:
            True if notification was sent successfully
        """
        pass
    
    @abstractmethod
    def subscribe_to_state_changes(self, callback: Callable[[str, str], None]) -> str:
        """
        Subscribe to state change notifications.
        
        Args:
            callback: Callback function (from_state, to_state)
            
        Returns:
            Subscription ID
        """
        pass
    
    @abstractmethod
    def subscribe_to_errors(self, callback: Callable[[int, str, Dict[str, Any]], None]) -> str:
        """
        Subscribe to error notifications.
        
        Args:
            callback: Callback function (error_code, state, context)
            
        Returns:
            Subscription ID
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from notifications.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            True if unsubscribed successfully
        """
        pass
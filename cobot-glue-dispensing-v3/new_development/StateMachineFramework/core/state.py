"""
State implementations for the state machine framework.

This module provides the base state classes and their implementations
with enhanced validation and operation support.
"""

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from ..ServiceInterfaces import ActionService, LoggingService
from .context import BaseContext
from .events import BaseEvent


@dataclass
class StateConfig:
    """
    Configuration for a single state.

    Attributes:
        name (str): Name of the state.
        entry_actions (List[str]): Actions to execute on entry.
        exit_actions (List[str]): Actions to execute on exit.
        transitions (Dict[str, str]): Event-to-state transition mapping.
        operation_type (Optional[str]): Type of operation associated with the state.
        timeout_seconds (Optional[int]): Timeout for the state in seconds.
        retry_count (int): Number of retries allowed for the state.
        preconditions (List[Callable]): Conditions that must be met before entering.
        postconditions (List[Callable]): Conditions that must be met before exiting.
        guard_conditions (Dict[str, Callable]): Event-specific guard conditions.
        metadata (Dict[str, Any]): Additional state metadata.
    """
    name: str
    entry_actions: List[str] = field(default_factory=list)
    exit_actions: List[str] = field(default_factory=list)
    transitions: Dict[str, str] = field(default_factory=dict)
    operation_type: Optional[str] = None
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    preconditions: List[Callable[[BaseContext], bool]] = field(default_factory=list)
    postconditions: List[Callable[[BaseContext], bool]] = field(default_factory=list)
    guard_conditions: Dict[str, Callable[[BaseContext], bool]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseState(ABC):
    """Base class for all states with enhanced validation and lifecycle support."""

    def __init__(self, name: str):
        """
        Initialize state.
        
        Args:
            name: State name
        """
        self.name = name
        self.entry_actions: List[str] = []
        self.exit_actions: List[str] = []
        self.transitions: Dict[str, str] = {}
        self._entry_time: Optional[float] = None
        self._operation_thread: Optional[threading.Thread] = None
        self._metrics = {
            'entry_count': 0,
            'exit_count': 0,
            'total_time': 0.0,
            'error_count': 0
        }

    def enter(self, context: BaseContext) -> bool:
        """
        Called when entering the state.
        
        Args:
            context: State machine context
            
        Returns:
            True if entry was successful
        """
        self._entry_time = time.time()
        self._metrics['entry_count'] += 1
        
        try:
            # Validate preconditions
            if not self._validate_preconditions(context):
                self._metrics['error_count'] += 1
                return False
            
            # Execute entry actions
            if context.has_service(ActionService):
                action_service = context.get_service(ActionService)
                for action in self.entry_actions:
                    try:
                        action_service.execute_entry_action(action, self.name, context.copy_data())
                    except Exception as e:
                        self._handle_action_error(context, action, 'entry', e)
                        self._metrics['error_count'] += 1
                        return False
            
            # State-specific entry logic
            return self._on_enter(context)
            
        except Exception as e:
            self._handle_unexpected_error(context, 'enter', e)
            self._metrics['error_count'] += 1
            return False

    def exit(self, context: BaseContext) -> bool:
        """
        Called when exiting the state.
        
        Args:
            context: State machine context
            
        Returns:
            True if exit was successful
        """
        try:
            # Validate postconditions
            if not self._validate_postconditions(context):
                self._metrics['error_count'] += 1
                return False
            
            # State-specific exit logic
            if not self._on_exit(context):
                return False
            
            # Execute exit actions
            if context.has_service(ActionService):
                action_service = context.get_service(ActionService)
                for action in self.exit_actions:
                    try:
                        action_service.execute_exit_action(action, self.name, context.copy_data())
                    except Exception as e:
                        self._handle_action_error(context, action, 'exit', e)
                        self._metrics['error_count'] += 1
                        return False
            
            # Update metrics
            if self._entry_time:
                self._metrics['total_time'] += time.time() - self._entry_time
                self._entry_time = None
            self._metrics['exit_count'] += 1
            
            return True
            
        except Exception as e:
            self._handle_unexpected_error(context, 'exit', e)
            self._metrics['error_count'] += 1
            return False

    def _on_enter(self, context: BaseContext) -> bool:
        """
        Override for state-specific entry logic.
        
        Args:
            context: State machine context
            
        Returns:
            True if successful
        """
        return True

    def _on_exit(self, context: BaseContext) -> bool:
        """
        Override for state-specific exit logic.
        
        Args:
            context: State machine context
            
        Returns:
            True if successful
        """
        return True

    def _validate_preconditions(self, context: BaseContext) -> bool:
        """
        Validate state preconditions.
        
        Args:
            context: State machine context
            
        Returns:
            True if all preconditions pass
        """
        # Override in subclasses that have preconditions
        return True

    def _validate_postconditions(self, context: BaseContext) -> bool:
        """
        Validate state postconditions.
        
        Args:
            context: State machine context
            
        Returns:
            True if all postconditions pass
        """
        # Override in subclasses that have postconditions
        return True

    def can_transition(self, event: BaseEvent, context: BaseContext) -> bool:
        """
        Check if transition is allowed for given event.
        
        Args:
            event: Event triggering transition
            context: State machine context
            
        Returns:
            True if transition is allowed
        """
        if event.name not in self.transitions:
            return False
        
        # Check guard conditions
        return self._check_guard_conditions(event.name, context)

    def _check_guard_conditions(self, event_name: str, context: BaseContext) -> bool:
        """
        Check guard conditions for event.
        
        Args:
            event_name: Name of event
            context: State machine context
            
        Returns:
            True if guard conditions pass
        """
        # Override in subclasses that have guard conditions
        return True

    def handle_event(self, event: BaseEvent, context: BaseContext) -> Optional[str]:
        """
        Handle event and return target state.
        
        Args:
            event: Event to handle
            context: State machine context
            
        Returns:
            Target state name if transition should occur, None otherwise
        """
        if not self.can_transition(event, context):
            return None
        
        return self.transitions.get(event.name)

    def _handle_action_error(self, context: BaseContext, action: str, phase: str, error: Exception):
        """Handle action execution errors."""
        error_msg = f"Action {action} failed in {phase} phase: {str(error)}"
        if context.has_service(LoggingService):
            logging_service = context.get_service(LoggingService)
            logging_service.log_error(error_msg, self.name, {'action': action, 'phase': phase})

    def _handle_unexpected_error(self, context: BaseContext, operation: str, error: Exception):
        """Handle unexpected errors."""
        error_msg = f"Unexpected error in {operation}: {str(error)}"
        if context.has_service(LoggingService):
            logging_service = context.get_service(LoggingService)
            logging_service.log_error(error_msg, self.name, {'operation': operation, 'error_type': type(error).__name__})

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get state metrics.
        
        Returns:
            Dictionary of state metrics
        """
        metrics = dict(self._metrics)
        if self._metrics['entry_count'] > 0:
            metrics['average_time'] = self._metrics['total_time'] / self._metrics['entry_count']
        else:
            metrics['average_time'] = 0.0
        
        if self._entry_time:
            metrics['current_duration'] = time.time() - self._entry_time
        else:
            metrics['current_duration'] = 0.0
            
        return metrics

    def reset_metrics(self) -> None:
        """Reset state metrics."""
        self._metrics = {
            'entry_count': 0,
            'exit_count': 0,
            'total_time': 0.0,
            'error_count': 0
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"BaseState(name='{self.name}', transitions={list(self.transitions.keys())})"


class ConfigurableState(BaseState):
    """State that can be configured via StateConfig with enhanced validation."""

    def __init__(self, config: StateConfig):
        """
        Initialize configurable state.
        
        Args:
            config: State configuration
        """
        super().__init__(config.name)
        self.config = config
        self.entry_actions = config.entry_actions
        self.exit_actions = config.exit_actions
        self.transitions = config.transitions
        self.operation_type = config.operation_type
        self.timeout_seconds = config.timeout_seconds
        self.retry_count = config.retry_count
        self.preconditions = config.preconditions
        self.postconditions = config.postconditions
        self.guard_conditions = config.guard_conditions
        self.metadata = config.metadata

    def _validate_preconditions(self, context: BaseContext) -> bool:
        """Validate all configured preconditions."""
        for condition in self.preconditions:
            try:
                if not condition(context):
                    return False
            except Exception as e:
                self._handle_unexpected_error(context, 'precondition_check', e)
                return False
        return True

    def _validate_postconditions(self, context: BaseContext) -> bool:
        """Validate all configured postconditions."""
        for condition in self.postconditions:
            try:
                if not condition(context):
                    return False
            except Exception as e:
                self._handle_unexpected_error(context, 'postcondition_check', e)
                return False
        return True

    def _check_guard_conditions(self, event_name: str, context: BaseContext) -> bool:
        """Check configured guard conditions for event."""
        if event_name in self.guard_conditions:
            try:
                return self.guard_conditions[event_name](context)
            except Exception as e:
                self._handle_unexpected_error(context, 'guard_condition_check', e)
                return False
        return True

    def add_precondition(self, condition: Callable[[BaseContext], bool]) -> None:
        """
        Add a precondition to the state.
        
        Args:
            condition: Condition function
        """
        self.preconditions.append(condition)

    def add_postcondition(self, condition: Callable[[BaseContext], bool]) -> None:
        """
        Add a postcondition to the state.
        
        Args:
            condition: Condition function
        """
        self.postconditions.append(condition)

    def add_guard_condition(self, event_name: str, condition: Callable[[BaseContext], bool]) -> None:
        """
        Add a guard condition for an event.
        
        Args:
            event_name: Event name
            condition: Guard condition function
        """
        self.guard_conditions[event_name] = condition


class OperationState(BaseState):
    """State that executes an operation asynchronously with enhanced error handling."""

    def __init__(self, name: str, operation_type: str, 
                 success_event: str = "OPERATION_COMPLETED",
                 error_event: str = "OPERATION_FAILED",
                 timeout_seconds: Optional[int] = None):
        """
        Initialize operation state.
        
        Args:
            name: State name
            operation_type: Type of operation to execute
            success_event: Event to emit on success
            error_event: Event to emit on error
            timeout_seconds: Operation timeout
        """
        super().__init__(name)
        self.operation_type = operation_type
        self.success_event = success_event
        self.error_event = error_event
        self.timeout_seconds = timeout_seconds
        self._operation_result = None
        self._operation_error = None

    def _on_enter(self, context: BaseContext) -> bool:
        """Start operation in background thread."""
        if not context.has_callback('execute_operation'):
            self._handle_unexpected_error(context, 'enter', 
                                        Exception("execute_operation callback not registered"))
            return False

        def execute_operation():
            try:
                result = context.execute_callback('execute_operation', {
                    'operation_type': self.operation_type,
                    'state': self.name,
                    'context_data': context.copy_data(),
                    'timeout_seconds': self.timeout_seconds
                })

                self._operation_result = result
                context.operation_result = result
                
                # Emit success event
                if context.has_callback('process_event'):
                    context.execute_callback('process_event', {
                        'event': self.success_event,
                        'data': {'result': result, 'operation_type': self.operation_type}
                    })

            except Exception as e:
                self._operation_error = str(e)
                context.error_message = str(e)
                
                # Emit error event
                if context.has_callback('process_event'):
                    context.execute_callback('process_event', {
                        'event': self.error_event,
                        'data': {'error': str(e), 'operation_type': self.operation_type}
                    })

        self._operation_thread = threading.Thread(target=execute_operation, daemon=True)
        self._operation_thread.start()
        return True

    def _on_exit(self, context: BaseContext) -> bool:
        """Wait for operation to complete before exiting."""
        if self._operation_thread and self._operation_thread.is_alive():
            # Give operation some time to complete
            self._operation_thread.join(timeout=1.0)
            
            if self._operation_thread.is_alive():
                # Operation still running, but we need to exit
                # This is acceptable for daemon threads
                pass
        
        return True

    def get_operation_status(self) -> Dict[str, Any]:
        """
        Get operation status.
        
        Returns:
            Dictionary with operation status information
        """
        is_running = self._operation_thread and self._operation_thread.is_alive()
        
        return {
            'operation_type': self.operation_type,
            'is_running': is_running,
            'result': self._operation_result,
            'error': self._operation_error,
            'thread_alive': is_running
        }


class TimedState(ConfigurableState):
    """State with automatic timeout handling."""
    
    def __init__(self, config: StateConfig, timeout_event: str = "TIMEOUT"):
        """
        Initialize timed state.
        
        Args:
            config: State configuration
            timeout_event: Event to emit on timeout
        """
        super().__init__(config)
        self.timeout_event = timeout_event
        self._timeout_timer: Optional[threading.Timer] = None

    def _on_enter(self, context: BaseContext) -> bool:
        """Start timeout timer on entry."""
        result = super()._on_enter(context)
        
        if result and self.timeout_seconds:
            def on_timeout():
                if context.has_callback('process_event'):
                    context.execute_callback('process_event', {
                        'event': self.timeout_event,
                        'data': {'state': self.name, 'timeout_seconds': self.timeout_seconds}
                    })
            
            self._timeout_timer = threading.Timer(self.timeout_seconds, on_timeout)
            self._timeout_timer.start()
        
        return result

    def _on_exit(self, context: BaseContext) -> bool:
        """Cancel timeout timer on exit."""
        if self._timeout_timer:
            self._timeout_timer.cancel()
            self._timeout_timer = None
        
        return super()._on_exit(context)
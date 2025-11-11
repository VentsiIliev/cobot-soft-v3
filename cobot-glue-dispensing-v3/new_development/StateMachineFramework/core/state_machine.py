"""
Enhanced state machine implementation with integrated error handling and validation.

This module provides the main state machine class with support for async processing,
comprehensive error handling, performance metrics, and validation.
"""

import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Type, Callable
import weakref

from .context import BaseContext
from .events import BaseEvent, GenericEvent, PriorityEvent, EventQueue, EventPriority
from .state import BaseState, StateConfig
from .performance import PerformanceManager, PerformanceProfiler, PerformanceOptimizer
from ..services.enhanced_container import EnhancedServiceContainer
from ..services.new_services import (
    TimerService, MetricsService, ValidationService, 
    NotificationService, SecurityService
)
from ..services.error_service import ErrorService
from ..ServiceInterfaces import LoggingService, EventService, ActionService
from ..errorCodesSystem.recoveryStrategies.ErrorRecoveryManager import ErrorRecoveryManager
from ..errorCodesSystem.errorCodes.errorCodes import StateMachineErrorCode, SystemErrorCode
from ..validation.validation_result import ValidationResult


@dataclass
class StateMachineConfig:
    """
    Complete state machine configuration with enhanced features.

    Attributes:
        initial_state (str): Name of the initial state.
        states (Dict[str, StateConfig]): Mapping of state names to configurations.
        global_transitions (Dict[str, str]): Global event-to-state transitions.
        error_recovery (Dict[str, str]): Error recovery transitions.
        timeouts (Dict[str, int]): Optional timeouts for states.
        max_event_queue_size (int): Maximum event queue size.
        enable_metrics (bool): Whether to collect metrics.
        enable_validation (bool): Whether to enable validation.
        thread_pool_size (int): Thread pool size for async operations.
        metadata (Dict[str, Any]): Additional configuration metadata.
    """
    initial_state: str
    states: Dict[str, StateConfig]
    global_transitions: Dict[str, str] = field(default_factory=dict)
    error_recovery: Dict[str, str] = field(default_factory=dict)
    timeouts: Dict[str, int] = field(default_factory=dict)
    max_event_queue_size: int = 1000
    enable_metrics: bool = True
    enable_validation: bool = True
    thread_pool_size: int = 4
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedStateMachine:
    """Enhanced state machine with comprehensive features and error handling."""

    def __init__(self, config: StateMachineConfig, context: Optional[BaseContext] = None):
        """
        Initialize enhanced state machine.
        
        Args:
            config: State machine configuration
            context: Optional context (will create default if None)
        """
        self.config = config
        self.context = context or BaseContext()
        
        # Core state management
        self.current_state: Optional[BaseState] = None
        self.current_state_name: Optional[str] = None
        self.states: Dict[str, BaseState] = {}
        
        # Event processing
        self.event_queue = EventQueue(config.max_event_queue_size)
        self.running = False
        self.paused = False
        
        # Threading
        self.event_thread: Optional[threading.Thread] = None
        self.executor = ThreadPoolExecutor(max_workers=config.thread_pool_size, 
                                         thread_name_prefix="StateMachine")
        
        # History and metrics
        self.history: List[Dict[str, Any]] = []
        self._history_lock = threading.RLock()
        self._performance_metrics = {
            'events_processed': 0,
            'state_changes': 0,
            'errors_handled': 0,
            'start_time': None,
            'total_runtime': 0.0,
            'average_event_processing_time': 0.0
        }
        
        # Error handling - keeping legacy manager for backward compatibility
        self.error_manager = ErrorRecoveryManager()
        self._setup_default_error_recovery()
        
        # Enhanced error handling through service
        if not self.context.has_service(ErrorService):
            from ..services.error_service import EnhancedErrorService
            enhanced_error_service = EnhancedErrorService()
            self.context.services.register_singleton(
                ErrorService,
                enhanced_error_service,
                metadata={"type": "enhanced", "component": "error_handling"}
            )
        
        # Performance management
        self.performance_manager = PerformanceManager()
        
        # Add performance optimizations
        self._setup_performance_optimizations()
        
        # Validation cache
        self._validation_cache: Dict[str, ValidationResult] = {}
        self._cache_lock = threading.RLock()
        
        # Weak references to track resources
        self._cleanup_handlers: List[Callable[[], None]] = []
        
        # Initialize components
        self._initialize_states()
        self._setup_default_services()
        self._setup_callbacks()
        
    def _setup_performance_optimizations(self) -> None:
        """Setup performance optimizations."""
        # Create optimized thread pool if enabled
        if self.config.thread_pool_size > 0:
            self.executor = self.performance_manager.optimizer.create_optimized_thread_pool(
                max_workers=self.config.thread_pool_size
            )
        
        # Setup caching for expensive operations
        if hasattr(self, '_validate_transition_cached'):
            # Already cached
            pass
        else:
            # Cache validation results for better performance
            self._validate_transition_cached = self.performance_manager.optimizer.create_lru_cache(
                maxsize=256
            )(self._validate_transition_internal)
        
        # Add performance monitoring callback
        self.performance_manager.add_performance_callback(self._performance_callback)
        
    def _performance_callback(self, performance_data: Dict[str, Any]) -> None:
        """Handle performance monitoring data."""
        # Log performance issues if any
        resource_data = performance_data.get('resources', {})
        memory_data = resource_data.get('memory', {})
        
        if memory_data.get('current_mb', 0) > 500:  # More than 500MB
            self._log_info(f"High memory usage detected: {memory_data.get('current_mb', 0):.1f}MB")
        
        # Check for performance degradation
        profiler_data = performance_data.get('profiler', {})
        operations = profiler_data.get('operations', {})
        
        for operation, stats in operations.items():
            if stats.get('average_time', 0) > 0.1:  # More than 100ms
                self._log_info(f"Slow operation detected: {operation} averaging {stats['average_time']*1000:.1f}ms")
    
    def _validate_transition_internal(self, from_state: str, to_state: str, event: str) -> ValidationResult:
        """Internal validation method for caching."""
        # This would contain the actual validation logic
        # For now, return success to maintain compatibility
        return ValidationResult.success("Transition validation passed")

    def _initialize_states(self) -> None:
        """Initialize states from configuration."""
        for name, state_config in self.config.states.items():
            if hasattr(self, '_create_state') and callable(getattr(self, '_create_state')):
                # Allow custom state creation
                state_obj = self._create_state(name, state_config)
            else:
                # Create default state based on configuration
                from .state import ConfigurableState, OperationState, TimedState
                
                if state_config.operation_type:
                    if state_config.timeout_seconds:
                        # Create timed operation state
                        base_config = StateConfig(
                            name=name,
                            entry_actions=state_config.entry_actions,
                            exit_actions=state_config.exit_actions,
                            transitions=state_config.transitions,
                            timeout_seconds=state_config.timeout_seconds,
                            preconditions=state_config.preconditions,
                            postconditions=state_config.postconditions,
                            guard_conditions=state_config.guard_conditions
                        )
                        state_obj = TimedState(base_config)
                        # Add operation capability
                        state_obj.operation_type = state_config.operation_type
                    else:
                        state_obj = OperationState(
                            name, 
                            state_config.operation_type,
                            timeout_seconds=state_config.timeout_seconds
                        )
                else:
                    if state_config.timeout_seconds:
                        state_obj = TimedState(state_config)
                    else:
                        state_obj = ConfigurableState(state_config)
            
            self.states[name] = state_obj

    def _setup_default_services(self) -> None:
        """Setup default services if not provided."""
        from ..services.default_implementations import DefaultTimerService, DefaultMetricsService
        
        # Import legacy services for backward compatibility
        try:
            from ..defaultServices import DefaultLoggingService, StateMachineEventService, DefaultActionService
        except ImportError:
            # Define minimal compatible services if defaultServices is removed
            from ..ServiceInterfaces import LoggingService, EventService, ActionService
            
            class DefaultLoggingService(LoggingService):
                def log_state_change(self, from_state: str, to_state: str, data: Dict[str, Any]) -> None:
                    print(f"State change: {from_state} -> {to_state}")
                def log_error(self, message: str, state: str, data: Dict[str, Any]) -> None:
                    print(f"Error in {state}: {message}")
                    
            class DefaultActionService(ActionService):
                def execute_action(self, action_name: str, context: 'BaseContext') -> Any:
                    return f"Executed {action_name}"
                    
            class StateMachineEventService(EventService):
                def __init__(self, state_machine):
                    self.state_machine = state_machine
                def emit_event(self, event_name: str, data: Dict[str, Any]) -> bool:
                    return True
        
        # Ensure we have an enhanced service container
        if not isinstance(self.context.services, EnhancedServiceContainer):
            # Migrate to enhanced container
            enhanced_container = EnhancedServiceContainer()
            
            # Copy existing services if any
            if hasattr(self.context.services, '_singletons'):
                for service_type, instance in self.context.services._singletons.items():
                    enhanced_container.register_singleton(service_type, instance)
            
            self.context.services = enhanced_container
        
        # Register default services if not present
        if not self.context.has_service(LoggingService):
            self.context.services.register_singleton(
                LoggingService,
                DefaultLoggingService(),
                metadata={"type": "default", "component": "logging"}
            )
        
        if not self.context.has_service(ActionService):
            self.context.services.register_singleton(
                ActionService,
                DefaultActionService(),
                metadata={"type": "default", "component": "actions"}
            )
        
        if not self.context.has_service(EventService):
            self.context.services.register_singleton(
                EventService,
                StateMachineEventService(self),
                metadata={"type": "state_machine", "component": "events"}
            )

    def _setup_callbacks(self) -> None:
        """Setup required callbacks in context."""
        self.context.register_callback('process_event', self._process_event_callback)
        
        # Register cleanup handler
        def cleanup():
            self.stop()
            self.executor.shutdown(wait=False)
        
        self._cleanup_handlers.append(cleanup)

    def _setup_default_error_recovery(self) -> None:
        """Setup default error recovery strategies."""
        from ..errorCodesSystem.recoveryStrategies.ErrorRecoveryStrategy import ErrorRecoveryStrategy
        from ..errorCodesSystem.contextAndTracking.ErrorContext import ErrorContext
        
        class RetryRecoveryStrategy(ErrorRecoveryStrategy):
            def can_handle(self, error_code: int) -> bool:
                transient_errors = [
                    StateMachineErrorCode.STATE_ENTRY_FAILED,
                    StateMachineErrorCode.EVENT_PROCESSING_FAILED,
                    SystemErrorCode.RESOURCE_LOCK_TIMEOUT
                ]
                return error_code in transient_errors
            
            def recover(self, error_context: ErrorContext, state_machine) -> bool:
                retry_count = error_context.additional_data.get('retry_count', 0)
                max_retries = error_context.additional_data.get('max_retries', 3)
                
                if retry_count < max_retries:
                    error_context.additional_data['retry_count'] = retry_count + 1
                    return True
                return False
        
        class SafeStateRecoveryStrategy(ErrorRecoveryStrategy):
            def can_handle(self, error_code: int) -> bool:
                critical_errors = [
                    StateMachineErrorCode.STATE_TRANSITION_INVALID,
                    StateMachineErrorCode.CONTEXT_CALLBACK_FAILED
                ]
                return error_code in critical_errors
            
            def recover(self, error_context: ErrorContext, state_machine) -> bool:
                safe_state = state_machine.config.error_recovery.get(
                    error_context.state, 
                    "ERROR_STATE"
                )
                if safe_state in state_machine.states:
                    return state_machine.transition_to(safe_state)
                return False
        
        self.error_manager.add_strategy(RetryRecoveryStrategy())
        self.error_manager.add_strategy(SafeStateRecoveryStrategy())

    def start(self) -> bool:
        """
        Start the state machine.
        
        Returns:
            True if started successfully
        """
        if self.running:
            return True
        
        try:
            # Validate configuration
            if self.config.enable_validation:
                validation_result = self._validate_configuration()
                if not validation_result.success:
                    self._log_error(f"Configuration validation failed: {validation_result.message}")
                    return False
            
            # Initialize metrics
            self._performance_metrics['start_time'] = time.time()
            
            # Start performance monitoring
            self.performance_manager.start_monitoring()
            
            # Set initial state
            if not self._transition_to_initial_state():
                return False
            
            # Start event processing
            self.running = True
            self.event_thread = threading.Thread(target=self._event_loop, daemon=True)
            self.event_thread.start()
            
            self._log_info("State machine started successfully")
            return True
            
        except Exception as e:
            self._log_error(f"Failed to start state machine: {str(e)}")
            return False

    def stop(self, timeout: float = 5.0) -> bool:
        """
        Stop the state machine.
        
        Args:
            timeout: Maximum time to wait for shutdown
            
        Returns:
            True if stopped successfully
        """
        if not self.running:
            return True
        
        try:
            self.running = False
            
            # Wait for event thread to complete
            if self.event_thread and self.event_thread.is_alive():
                self.event_thread.join(timeout=timeout)
            
            # Stop performance monitoring
            self.performance_manager.stop_monitoring()
            
            # Exit current state
            if self.current_state:
                self.current_state.exit(self.context)
            
            # Update metrics
            if self._performance_metrics['start_time']:
                self._performance_metrics['total_runtime'] = (
                    time.time() - self._performance_metrics['start_time']
                )
            
            self._log_info("State machine stopped")
            return True
            
        except Exception as e:
            self._log_error(f"Error stopping state machine: {str(e)}")
            return False

    def pause(self) -> None:
        """Pause event processing."""
        self.paused = True

    def resume(self) -> None:
        """Resume event processing."""
        self.paused = False

    def process_event(self, event_name: str, data: Dict[str, Any] = None, 
                     priority: int = EventPriority.NORMAL) -> bool:
        """
        Process an event.
        
        Args:
            event_name: Name of event
            data: Optional event data
            priority: Event priority
            
        Returns:
            True if event was queued successfully
        """
        try:
            priority_event = PriorityEvent(
                priority=priority,
                timestamp=time.time(),
                event_name=event_name,
                data=data or {}
            )
            
            return self.event_queue.enqueue(priority_event)
            
        except Exception as e:
            self._log_error(f"Failed to process event {event_name}: {str(e)}")
            return False

    def transition_to(self, target_state: str, event_data: Dict[str, Any] = None) -> bool:
        """
        Transition to a target state.
        
        Args:
            target_state: Name of target state
            event_data: Optional event data
            
        Returns:
            True if transition was successful
        """
        if target_state not in self.states:
            self._log_error(f"Target state '{target_state}' not found")
            return False
        
        try:
            # Validate transition if validation is enabled
            if self.config.enable_validation and self.context.has_service(ValidationService):
                validation_service = self.context.get_service(ValidationService)
                validation_result = validation_service.validate_transition(
                    self.current_state_name or "",
                    target_state,
                    "",  # No specific event for direct transitions
                    self.context
                )
                
                if not validation_result.success:
                    self._log_error(f"Transition validation failed: {validation_result.message}")
                    return False
            
            old_state = self.current_state
            old_state_name = self.current_state_name
            new_state = self.states[target_state]
            
            # Exit current state
            if old_state and not old_state.exit(self.context):
                self._log_error(f"Failed to exit state '{old_state_name}'")
                return False
            
            # Enter new state
            if not new_state.enter(self.context):
                self._log_error(f"Failed to enter state '{target_state}'")
                # Try to re-enter old state
                if old_state:
                    old_state.enter(self.context)
                return False
            
            # Update current state
            self.current_state = new_state
            self.current_state_name = target_state
            
            # Record history
            self._record_transition(old_state_name, target_state, "", event_data)
            
            # Record metrics
            if self.config.enable_metrics and self.context.has_service(MetricsService):
                metrics_service = self.context.get_service(MetricsService)
                metrics_service.record_transition(old_state_name or "", target_state, "")
            
            # Update performance metrics
            self._performance_metrics['state_changes'] += 1
            
            self._log_info(f"Transitioned from '{old_state_name}' to '{target_state}'")
            return True
            
        except Exception as e:
            self._log_error(f"Transition failed: {str(e)}")
            
            # Record error and attempt recovery
            error_code = StateMachineErrorCode.STATE_TRANSITION_INVALID
            self._handle_error(error_code, target_state, {'error': str(e), 'event_data': event_data})
            return False

    def get_current_state(self) -> Optional[str]:
        """Get current state name."""
        return self.current_state_name

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get state transition history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of history entries
        """
        with self._history_lock:
            if limit is None:
                return list(self.history)
            return list(self.history[-limit:])

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        metrics = dict(self._performance_metrics)
        
        # Calculate derived metrics
        if metrics['start_time']:
            current_runtime = time.time() - metrics['start_time']
            metrics['current_runtime'] = current_runtime
            
            if metrics['events_processed'] > 0:
                metrics['events_per_second'] = metrics['events_processed'] / current_runtime
            else:
                metrics['events_per_second'] = 0.0
        
        # Add queue metrics
        metrics['queue_size'] = self.event_queue.size()
        metrics['dropped_events'] = self.event_queue.get_dropped_count()
        
        # Add state metrics if available
        if self.current_state:
            metrics['current_state_metrics'] = self.current_state.get_metrics()
        
        return metrics

    def can_handle_event(self, event_name: str) -> bool:
        """
        Check if event can be handled in current state.
        
        Args:
            event_name: Event name
            
        Returns:
            True if event can be handled
        """
        # Check global transitions
        if event_name in self.config.global_transitions:
            return True
        
        # Check current state transitions
        if self.current_state and hasattr(self.current_state, 'transitions'):
            return event_name in self.current_state.transitions
        
        return False

    def _event_loop(self) -> None:
        """Main event processing loop."""
        while self.running:
            try:
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                event = self.event_queue.dequeue()
                if event:
                    start_time = time.time()
                    self._handle_priority_event(event)
                    
                    # Update performance metrics
                    processing_time = time.time() - start_time
                    self._update_processing_metrics(processing_time)
                else:
                    time.sleep(0.01)  # Short sleep when no events
                    
            except Exception as e:
                self._log_error(f"Error in event loop: {str(e)}")
                self._performance_metrics['errors_handled'] += 1

    def _handle_priority_event(self, priority_event: PriorityEvent) -> None:
        """Handle a priority event."""
        event = GenericEvent(priority_event.event_name, priority_event.data)
        
        try:
            # Validate event if validation is enabled
            if self.config.enable_validation:
                validation_result = self._validate_event(event)
                if not validation_result.success:
                    self._log_error(f"Event validation failed: {validation_result.message}")
                    return
            
            # Check for global transitions first
            target_state = self.config.global_transitions.get(event.name)
            
            # If no global transition, check current state
            if not target_state and self.current_state:
                target_state = self.current_state.handle_event(event, self.context)
            
            # Execute transition if target found
            if target_state:
                self.transition_to(target_state, event.data)
            
            # Execute callback if provided
            if priority_event.callback:
                priority_event.callback()
            
            # Update metrics
            self._performance_metrics['events_processed'] += 1
            
        except Exception as e:
            self._log_error(f"Error handling event '{event.name}': {str(e)}")
            error_code = StateMachineErrorCode.EVENT_PROCESSING_FAILED
            self._handle_error(error_code, self.current_state_name, 
                             {'event': event.name, 'error': str(e)})

    def _process_event_callback(self, params: Dict[str, Any]) -> None:
        """Callback for processing events from context."""
        event_name = params.get('event', '')
        data = params.get('data', {})
        priority = params.get('priority', EventPriority.NORMAL)
        
        self.process_event(event_name, data, priority)

    def _transition_to_initial_state(self) -> bool:
        """Transition to the initial state."""
        if self.config.initial_state not in self.states:
            self._log_error(f"Initial state '{self.config.initial_state}' not found")
            return False
        
        initial_state = self.states[self.config.initial_state]
        
        if not initial_state.enter(self.context):
            self._log_error(f"Failed to enter initial state '{self.config.initial_state}'")
            return False
        
        self.current_state = initial_state
        self.current_state_name = self.config.initial_state
        
        self._record_transition(None, self.config.initial_state, "INIT", {})
        return True

    def _validate_configuration(self) -> ValidationResult:
        """Validate state machine configuration."""
        result = ValidationResult.success("Configuration is valid")
        
        # Check initial state exists
        if self.config.initial_state not in self.config.states:
            result.add_error(
                "MISSING_INITIAL_STATE",
                f"Initial state '{self.config.initial_state}' not defined in states"
            )
        
        # Check all transition targets exist
        for state_name, state_config in self.config.states.items():
            for event, target in state_config.transitions.items():
                if target not in self.config.states:
                    result.add_error(
                        "INVALID_TRANSITION_TARGET",
                        f"State '{state_name}' transitions to undefined state '{target}' on event '{event}'"
                    )
        
        # Check global transition targets exist
        for event, target in self.config.global_transitions.items():
            if target not in self.config.states:
                result.add_error(
                    "INVALID_GLOBAL_TRANSITION",
                    f"Global transition for event '{event}' targets undefined state '{target}'"
                )
        
        return result

    def _validate_event(self, event: BaseEvent) -> ValidationResult:
        """Validate an event."""
        # Simple validation - can be extended
        if not event.name:
            return ValidationResult.error("EMPTY_EVENT_NAME", "Event name cannot be empty")
        
        return ValidationResult.success()

    def _record_transition(self, from_state: Optional[str], to_state: str, 
                          event: str, data: Dict[str, Any]) -> None:
        """Record a state transition in history."""
        entry = {
            'from_state': from_state,
            'to_state': to_state,
            'event': event,
            'data': data or {},
            'timestamp': time.time(),
            'success': True
        }
        
        with self._history_lock:
            self.history.append(entry)
            
            # Limit history size
            if len(self.history) > 1000:
                self.history = self.history[-500:]  # Keep last 500 entries

    def _handle_error(self, error_code: int, state: Optional[str], 
                     additional_data: Dict[str, Any]) -> None:
        """Handle an error with recovery attempts using both legacy and enhanced error handling."""
        try:
            recovered = False
            
            # Use enhanced error service if available
            if self.context.has_service(ErrorService):
                error_service = self.context.get_service(ErrorService)
                
                # Record the error
                error_service.record_error(
                    error_code=error_code,
                    state=state,
                    operation=additional_data.get('operation'),
                    context=additional_data
                )
                
                # Attempt recovery
                recovered = error_service.handle_error(
                    error_code=error_code,
                    state_machine=self,
                    state=state,
                    additional_data=additional_data
                )
            
            # Fallback to legacy error manager if enhanced service fails
            if not recovered:
                recovered = self.error_manager.handle_error(
                    error_code=error_code,
                    state_machine=self,
                    state=state,
                    additional_data=additional_data
                )
            
            if not recovered:
                self._log_error(f"Failed to recover from error {error_code} in state {state}")
                
                # Transition to error state if available
                error_state = self.config.error_recovery.get(state or "", "ERROR_STATE")
                if error_state in self.states and error_state != self.current_state_name:
                    self.transition_to(error_state)
            
            self._performance_metrics['errors_handled'] += 1
            
        except Exception as e:
            self._log_error(f"Error in error handling: {str(e)}")

    def _update_processing_metrics(self, processing_time: float) -> None:
        """Update event processing metrics."""
        count = self._performance_metrics['events_processed']
        current_avg = self._performance_metrics['average_event_processing_time']
        
        if count > 0:
            new_avg = ((current_avg * (count - 1)) + processing_time) / count
            self._performance_metrics['average_event_processing_time'] = new_avg
        else:
            self._performance_metrics['average_event_processing_time'] = processing_time

    def _log_info(self, message: str) -> None:
        """Log info message."""
        if self.context.has_service(LoggingService):
            logging_service = self.context.get_service(LoggingService)
            logging_service.log_state_change(None, self.current_state_name, {'message': message})

    def _log_error(self, message: str) -> None:
        """Log error message."""
        if self.context.has_service(LoggingService):
            logging_service = self.context.get_service(LoggingService)
            logging_service.log_error(message, self.current_state_name, {})
    
    # Error service integration methods
    
    def get_active_errors(self) -> List:
        """Get all currently active errors."""
        if self.context.has_service(ErrorService):
            error_service = self.context.get_service(ErrorService)
            return error_service.get_active_errors()
        return []
    
    def has_fatal_errors(self) -> bool:
        """Check if there are any fatal errors."""
        if self.context.has_service(ErrorService):
            error_service = self.context.get_service(ErrorService)
            return error_service.has_fatal_errors()
        return False
    
    def clear_error(self, error_code: int) -> bool:
        """Clear an active error."""
        if self.context.has_service(ErrorService):
            error_service = self.context.get_service(ErrorService)
            return error_service.clear_error(error_code)
        return False
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        if self.context.has_service(ErrorService):
            error_service = self.context.get_service(ErrorService)
            return error_service.get_error_statistics()
        return {}
    
    def add_error_callback(self, callback: Callable) -> str:
        """Add error notification callback."""
        if self.context.has_service(ErrorService):
            error_service = self.context.get_service(ErrorService)
            return error_service.add_error_callback(callback)
        return ""
    
    def remove_error_callback(self, callback_id: str) -> bool:
        """Remove error notification callback."""
        if self.context.has_service(ErrorService):
            error_service = self.context.get_service(ErrorService)
            return error_service.remove_error_callback(callback_id)
        return False
    
    def validate_error_handling(self) -> ValidationResult:
        """Validate current error handling state."""
        if self.context.has_service(ErrorService):
            error_service = self.context.get_service(ErrorService)
            return error_service.validate_error_handling(self.context)
        return ValidationResult.success("Error service not available")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        
        # Run cleanup handlers
        for handler in self._cleanup_handlers:
            try:
                handler()
            except Exception:
                pass

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.stop()
            self.executor.shutdown(wait=False)
        except Exception:
            pass
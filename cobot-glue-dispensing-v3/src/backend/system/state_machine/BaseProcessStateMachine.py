"""
Base Process State Machine

This module provides the base implementation for all process state machines
in robot applications. It implements the ProcessStateMachineInterface and
provides common functionality that can be shared across different applications.
"""

import threading
import time
from collections import defaultdict, deque
from enum import Enum
from typing import Dict, Set, List, Callable, Any, Optional, Union

from modules.shared.MessageBroker import MessageBroker
from backend.system.utils.custom_logging import log_debug_message, log_info_message, log_error_message, \
    LoggerContext
from .ProcessMessageTopics import ProcessStateTopics, ProcessControlTopics, MessageFormats
from .ProcessStateMachineInterface import ProcessStateMachineInterface, StateTransition, StateHandler
from .ProcessStateType import ProcessStateType, ProcessStateMetadata


class BaseProcessStateMachine(ProcessStateMachineInterface):
    """
    Base implementation of the ProcessStateMachineInterface.
    
    This class provides common state machine functionality that can be inherited
    by application-specific state machines. It handles:
    - State transitions with validation
    - State handlers (on_enter, on_exit)
    - MessageBroker integration
    - Transition history
    - Thread-safe operations
    - Logging and debugging
    """
    
    def __init__(self, initial_state: Enum, application_type: str, context: Any = None, broker: MessageBroker = None):
        """
        Initialize the base process state machine.
        
        Args:
            initial_state: The initial state of the process
            application_type: Application type identifier ("glue", "paint", "pick_place")
            context: Optional context object (e.g., robot service, settings)
            broker: Message broker for state change notifications
        """
        self._current_state = initial_state
        self._application_type = application_type
        self._context = context
        self._broker = broker or MessageBroker()
        
        # Thread safety
        self._state_lock = threading.RLock()
        
        # State management
        self._transition_rules: Dict[Enum, Set[Enum]] = {}
        self._state_handlers: Dict[Enum, Dict[str, List[StateHandler]]] = defaultdict(lambda: defaultdict(list))
        
        # History and statistics
        self._transition_history: deque = deque(maxlen=1000)  # Keep last 1000 transitions
        self._state_statistics: Dict[Enum, Dict[str, Any]] = defaultdict(lambda: {
            "enter_count": 0,
            "total_time": 0.0,
            "last_enter_time": None,
            "last_exit_time": None
        })
        
        # State machine metadata
        self._creation_time = time.time()
        self._last_transition_time = time.time()
        self._state_enter_time = time.time()
        
        # Control flags
        self._is_running = True
        self._paused_from_state = None
        
        # Logging
        self._logger_context = LoggerContext(f"{application_type.title()}ProcessStateMachine")
        
        # Initialize MessageBroker subscriptions
        self._setup_message_subscriptions()
        
        log_info_message(
            self._logger_context,
            f"Process state machine initialized: {application_type}, initial state: {initial_state}"
        )
    
    # === CORE INTERFACE IMPLEMENTATION ===
    
    @property
    def current_state(self) -> Enum:
        """Get the current state (thread-safe)."""
        with self._state_lock:
            return self._current_state
    
    @property
    def application_type(self) -> str:
        """Get the application type identifier."""
        return self._application_type
    
    def can_transition(self, to_state: Enum) -> bool:
        """
        Check if a transition to the specified state is allowed.
        
        Args:
            to_state: The target state
            
        Returns:
            bool: True if transition is allowed, False otherwise
        """
        with self._state_lock:
            current = self._current_state
            
            # Check if target state is in allowed transitions
            if current in self._transition_rules:
                return to_state in self._transition_rules[current]
            
            # If no specific rules defined, allow transition
            # (Subclasses should override this behavior if needed)
            return True
    
    def transition(self, to_state: Enum, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Attempt to transition to a new state.
        
        Args:
            to_state: The target state
            context: Optional context data for the transition
            
        Returns:
            bool: True if transition was successful, False otherwise
        """
        with self._state_lock:
            old_state = self._current_state
            transition_context = context or {}
            
            # Validate transition
            if not self.can_transition(to_state):
                log_debug_message(
                    self._logger_context,
                    f"Invalid transition blocked: {old_state} -> {to_state}"
                )
                return False
            
            # Additional validation (can be overridden by subclasses)
            if not self.validate_transition_context(old_state, to_state, transition_context):
                log_debug_message(
                    self._logger_context,
                    f"Transition context validation failed: {old_state} -> {to_state}"
                )
                return False
            
            log_info_message(
                self._logger_context,
                f"State transition: {old_state} -> {to_state}"
            )
            
            # Record transition timing
            now = time.time()
            if self._state_enter_time:
                time_in_state = now - self._state_enter_time
                self._state_statistics[old_state]["total_time"] += time_in_state
                self._state_statistics[old_state]["last_exit_time"] = now
            
            # Execute transition
            try:
                # Call exit handlers for old state
                self._execute_state_handlers(old_state, "on_exit", transition_context)
                
                # Change state
                self._current_state = to_state
                self._last_transition_time = now
                self._state_enter_time = now
                
                # Update statistics
                self._state_statistics[to_state]["enter_count"] += 1
                self._state_statistics[to_state]["last_enter_time"] = now
                
                # Record transition
                transition_record = StateTransition(old_state, to_state, now, transition_context)
                self._transition_history.append(transition_record)
                
                # Call enter handlers for new state
                self._execute_state_handlers(to_state, "on_enter", transition_context)
                
                # Publish state change
                self.publish_state_change(old_state, to_state, transition_context)
                
                return True
                
            except Exception as e:
                log_error_message(
                    self._logger_context,
                    f"Error during state transition {old_state} -> {to_state}: {e}"
                )
                # Revert state change if handlers failed
                self._current_state = old_state
                return False
    
    def get_valid_transitions(self) -> Set[Enum]:
        """
        Get all valid transitions from the current state.
        
        Returns:
            Set[Enum]: Set of valid target states
        """
        with self._state_lock:
            return self._transition_rules.get(self._current_state, set())
    
    def register_state_handler(self, state: Enum, handler_type: str, handler: Callable, priority: int = 0):
        """
        Register a handler for state entry/exit events.
        
        Args:
            state: The state to register the handler for
            handler_type: Type of handler ("on_enter", "on_exit")
            handler: The handler function
            priority: Handler priority (higher priority handlers run first)
        """
        if handler_type not in ["on_enter", "on_exit"]:
            raise ValueError(f"Invalid handler type: {handler_type}")
        
        handler_obj = StateHandler(state, handler_type, handler, priority)
        
        with self._state_lock:
            self._state_handlers[state][handler_type].append(handler_obj)
            # Sort handlers by priority (higher priority first)
            self._state_handlers[state][handler_type].sort(key=lambda h: h.priority, reverse=True)
        
        log_debug_message(
            self._logger_context,
            f"Registered {handler_type} handler for state {state} with priority {priority}"
        )
    
    def get_transition_history(self) -> List[StateTransition]:
        """
        Get the history of state transitions.
        
        Returns:
            list: List of transition records with timestamps
        """
        with self._state_lock:
            return list(self._transition_history)
    
    def reset(self, initial_state: Optional[Enum] = None):
        """
        Reset the state machine to its initial state or specified state.
        
        Args:
            initial_state: Optional state to reset to (uses original if not provided)
        """
        with self._state_lock:
            if initial_state is None:
                # Use the first state from transition history as the original initial state
                if self._transition_history:
                    initial_state = self._transition_history[0].from_state
                else:
                    initial_state = self._current_state
            
            old_state = self._current_state
            
            # Reset state without validation or handlers
            self._current_state = initial_state
            self._state_enter_time = time.time()
            
            # Clear statistics and history
            self._state_statistics.clear()
            self._transition_history.clear()
            
            # Reset control flags
            self._paused_from_state = None
            
            log_info_message(
                self._logger_context,
                f"State machine reset: {old_state} -> {initial_state}"
            )
            
            # Publish reset event
            self.publish_state_change(old_state, initial_state, {"reset": True})
    
    # === MESSAGE BROKER INTEGRATION ===
    
    def publish_state_change(self, old_state: Enum, new_state: Enum, context: Optional[Dict[str, Any]] = None):
        """
        Publish state change notification via MessageBroker.
        
        Args:
            old_state: The previous state
            new_state: The new state
            context: Optional context data
        """
        try:
            # Publish to application-specific state topic
            app_state_topic = ProcessStateTopics.get_app_state_topic(self._application_type)
            state_message = MessageFormats.process_state_message(
                self._application_type,
                str(old_state),
                str(new_state),
                context
            )
            self._broker.publish(app_state_topic, state_message)
            
            # Publish to general state change topic
            general_message = {
                **state_message,
                "state_machine_id": id(self),
                "timestamp": time.time()
            }
            self._broker.publish(ProcessStateTopics.STATE_CHANGED, general_message)
            
        except Exception as e:
            log_error_message(
                self._logger_context,
                f"Error publishing state change: {e}"
            )
    
    def subscribe_to_control_messages(self):
        """
        Subscribe to control messages that can trigger state changes.
        """
        # Subscribe to general process control messages
        self._broker.subscribe(ProcessControlTopics.PAUSE_PROCESS, self._handle_pause_message)
        self._broker.subscribe(ProcessControlTopics.RESUME_PROCESS, self._handle_resume_message)
        self._broker.subscribe(ProcessControlTopics.STOP_PROCESS, self._handle_stop_message)
        self._broker.subscribe(ProcessControlTopics.RESET_PROCESS, self._handle_reset_message)
        
        # Subscribe to application-specific control messages
        app_pause = ProcessControlTopics.get_app_specific_topic(ProcessControlTopics.PAUSE_PROCESS, self._application_type)
        app_resume = ProcessControlTopics.get_app_specific_topic(ProcessControlTopics.RESUME_PROCESS, self._application_type)
        app_stop = ProcessControlTopics.get_app_specific_topic(ProcessControlTopics.STOP_PROCESS, self._application_type)
        app_reset = ProcessControlTopics.get_app_specific_topic(ProcessControlTopics.RESET_PROCESS, self._application_type)
        
        self._broker.subscribe(app_pause, self._handle_pause_message)
        self._broker.subscribe(app_resume, self._handle_resume_message)
        self._broker.subscribe(app_stop, self._handle_stop_message)
        self._broker.subscribe(app_reset, self._handle_reset_message)
        
        log_debug_message(
            self._logger_context,
            "Subscribed to process control messages"
        )
    
    # === INTERNAL METHODS ===
    
    def _setup_message_subscriptions(self):
        """Set up MessageBroker subscriptions."""
        if self._broker:
            self.subscribe_to_control_messages()
    
    def _execute_state_handlers(self, state: Enum, handler_type: str, context: Dict[str, Any]):
        """
        Execute state handlers for a given state and handler type.
        
        Args:
            state: The state
            handler_type: Type of handler ("on_enter", "on_exit")
            context: Handler context
        """
        handlers = self._state_handlers.get(state, {}).get(handler_type, [])
        
        for handler_obj in handlers:
            try:
                # Call handler with context
                handler_obj.handler(context)
            except Exception as e:
                log_error_message(
                    self._logger_context,
                    f"Error in {handler_type} handler for state {state}: {e}"
                )
    
    def _handle_pause_message(self, message: Dict[str, Any]):
        """Handle pause message from MessageBroker."""
        # Check if message is for this application or general
        if self._should_handle_message(message):
            current = self.current_state
            if ProcessStateMetadata.is_interruptible(current) if hasattr(current, 'name') else True:
                self._paused_from_state = current
                self.transition(ProcessStateType.PAUSED, {"paused_from": str(current)})
    
    def _handle_resume_message(self, message: Dict[str, Any]):
        """Handle resume message from MessageBroker."""
        if self._should_handle_message(message):
            if self.current_state == ProcessStateType.PAUSED and self._paused_from_state:
                self.transition(self._paused_from_state, {"resumed_to": str(self._paused_from_state)})
                self._paused_from_state = None
    
    def _handle_stop_message(self, message: Dict[str, Any]):
        """Handle stop message from MessageBroker."""
        if self._should_handle_message(message):
            self.transition(ProcessStateType.STOPPED, {"stop_reason": "external_command"})
    
    def _handle_reset_message(self, message: Dict[str, Any]):
        """Handle reset message from MessageBroker."""
        if self._should_handle_message(message):
            self.reset()
    
    def _should_handle_message(self, message: Dict[str, Any]) -> bool:
        """
        Check if this state machine should handle the given message.
        
        Args:
            message: The message to check
            
        Returns:
            bool: True if should handle, False otherwise
        """
        # Handle all general messages
        app_type = message.get("app_type")
        if not app_type:
            return True
        
        # Handle application-specific messages
        return app_type == self._application_type
    
    # === EXTENDED FUNCTIONALITY ===
    
    def set_transition_rules(self, rules: Dict[Enum, Set[Enum]]):
        """
        Set the transition rules for this state machine.
        
        Args:
            rules: Dictionary mapping states to their valid transition targets
        """
        with self._state_lock:
            self._transition_rules = rules.copy()
        
        log_debug_message(
            self._logger_context,
            f"Transition rules updated: {len(rules)} states defined"
        )
    
    def add_transition_rule(self, from_state: Enum, to_states: Union[Enum, Set[Enum]]):
        """
        Add a transition rule.
        
        Args:
            from_state: The source state
            to_states: Valid target state(s)
        """
        if isinstance(to_states, Enum):
            to_states = {to_states}
        
        with self._state_lock:
            if from_state not in self._transition_rules:
                self._transition_rules[from_state] = set()
            self._transition_rules[from_state].update(to_states)
    
    def remove_transition_rule(self, from_state: Enum, to_state: Enum):
        """
        Remove a specific transition rule.
        
        Args:
            from_state: The source state
            to_state: The target state to remove
        """
        with self._state_lock:
            if from_state in self._transition_rules:
                self._transition_rules[from_state].discard(to_state)
    
    def get_state_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about state machine usage.
        
        Returns:
            Dict[str, Any]: Statistics like time in each state, transition counts, etc.
        """
        with self._state_lock:
            # Calculate current state time
            current_state = self._current_state
            current_time = time.time()
            if self._state_enter_time and current_state in self._state_statistics:
                current_duration = current_time - self._state_enter_time
                total_time = self._state_statistics[current_state]["total_time"] + current_duration
            else:
                total_time = 0
            
            stats = {
                "creation_time": self._creation_time,
                "uptime": current_time - self._creation_time,
                "current_state": str(current_state),
                "current_state_duration": current_time - (self._state_enter_time or current_time),
                "total_transitions": len(self._transition_history),
                "states": {}
            }
            
            for state, state_stats in self._state_statistics.items():
                stats["states"][str(state)] = {
                    **state_stats,
                    "total_time": total_time if state == current_state else state_stats["total_time"]
                }
            
            return stats
    
    def get_state_metadata(self, state: Enum) -> Dict[str, Any]:
        """
        Get metadata about a specific state.
        
        Args:
            state: The state to get metadata for
            
        Returns:
            Dict[str, Any]: Metadata about the state
        """
        metadata = {
            "state": str(state),
            "description": getattr(state, 'description', 'No description'),
            "category": "unknown",
            "is_active": False,
            "is_terminal": False,
            "is_error": False,
            "is_interruptible": False,
        }
        
        # Add ProcessStateType metadata if available
        if hasattr(ProcessStateMetadata, 'get_description'):
            try:
                metadata.update({
                    "description": ProcessStateMetadata.get_description(state),
                    "category": str(ProcessStateMetadata.get_category(state)),
                    "is_active": ProcessStateMetadata.is_active(state),
                    "is_terminal": ProcessStateMetadata.is_terminal(state),
                    "is_error": ProcessStateMetadata.is_error_state(state),
                    "is_interruptible": ProcessStateMetadata.is_interruptible(state),
                })
            except:
                pass  # State might not be a ProcessStateType
        
        return metadata
    
    # === CONVENIENCE METHODS ===
    
    def is_active(self) -> bool:
        """Check if the state machine is in an active state."""
        current = self.current_state
        return ProcessStateMetadata.is_active(current) if hasattr(current, 'name') else True
    
    def is_error_state(self) -> bool:
        """Check if the state machine is in an error state."""
        current = self.current_state
        return ProcessStateMetadata.is_error_state(current) if hasattr(current, 'name') else False
    
    def is_terminal_state(self) -> bool:
        """Check if the state machine is in a terminal state."""
        current = self.current_state
        return ProcessStateMetadata.is_terminal(current) if hasattr(current, 'name') else False
    
    def get_uptime(self) -> float:
        """Get the uptime of the state machine in seconds."""
        return time.time() - self._creation_time
    
    def get_current_state_duration(self) -> float:
        """Get the time spent in the current state in seconds."""
        if self._state_enter_time:
            return time.time() - self._state_enter_time
        return 0.0
    
    def __str__(self):
        """String representation of the state machine."""
        return f"{self._application_type.title()}ProcessStateMachine(current_state={self._current_state})"
    
    def __repr__(self):
        """Detailed string representation of the state machine."""
        return (f"{self.__class__.__name__}("
                f"app_type='{self._application_type}', "
                f"current_state={self._current_state}, "
                f"uptime={self.get_uptime():.1f}s)")
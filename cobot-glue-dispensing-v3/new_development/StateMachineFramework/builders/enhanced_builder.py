"""
Enhanced state machine builder with validation and advanced features.

This module provides an enhanced builder pattern with comprehensive validation,
conditional transitions, and advanced configuration options.
"""

from typing import Dict, Optional, List, Callable, Any
from dataclasses import dataclass, field

from ..core.state import StateConfig
from ..core.state_machine import StateMachineConfig, EnhancedStateMachine
from ..core.context import BaseContext
from ..validation.validation_result import ValidationResult


@dataclass
class ConditionalTransition:
    """Represents a conditional state transition."""
    condition: Callable[[BaseContext], bool]
    target_state: str
    priority: int = 0  # Higher priority conditions checked first
    description: str = ""
    
    def __post_init__(self):
        if not self.description:
            self.description = f"Condition -> {self.target_state}"


class EnhancedStateMachineBuilder:
    """Enhanced builder for fluent state machine configuration with validation."""

    def __init__(self):
        """Initialize the enhanced builder."""
        self.states: Dict[str, StateConfig] = {}
        self.initial_state: Optional[str] = None
        self.global_transitions: Dict[str, str] = {}
        self.error_recovery: Dict[str, str] = {}
        self.timeouts: Dict[str, int] = {}
        
        # Enhanced features
        self.validators: List[Callable[[StateMachineConfig], ValidationResult]] = []
        self.conditional_transitions: Dict[str, List[ConditionalTransition]] = {}
        self.guard_conditions: Dict[str, Callable[[BaseContext], bool]] = {}
        self.metadata: Dict[str, Any] = {}
        
        # Configuration options
        self.max_event_queue_size: int = 1000
        self.enable_metrics: bool = True
        self.enable_validation: bool = True
        self.thread_pool_size: int = 4

    def add_state(self, name: str) -> 'EnhancedStateBuilder':
        """
        Add a new state to the builder.

        Args:
            name: State name

        Returns:
            Enhanced state builder for configuring the state
        """
        config = StateConfig(name=name)
        self.states[name] = config
        return EnhancedStateBuilder(self, config)

    def set_initial_state(self, state_name: str) -> 'EnhancedStateMachineBuilder':
        """
        Set the initial state.

        Args:
            state_name: Name of initial state

        Returns:
            Self for chaining
        """
        self.initial_state = state_name
        return self

    def add_global_transition(self, event: str, target_state: str) -> 'EnhancedStateMachineBuilder':
        """
        Add a global transition available from any state.

        Args:
            event: Event name
            target_state: Target state name

        Returns:
            Self for chaining
        """
        self.global_transitions[event] = target_state
        return self

    def add_error_recovery(self, from_state: str, to_state: str) -> 'EnhancedStateMachineBuilder':
        """
        Add error recovery transition.

        Args:
            from_state: State to recover from
            to_state: State to recover to

        Returns:
            Self for chaining
        """
        self.error_recovery[from_state] = to_state
        return self

    def add_validator(self, validator: Callable[[StateMachineConfig], ValidationResult]) -> 'EnhancedStateMachineBuilder':
        """
        Add configuration validator.

        Args:
            validator: Validation function

        Returns:
            Self for chaining
        """
        self.validators.append(validator)
        return self

    def add_conditional_transition(self, from_state: str, event: str, 
                                  conditions: List[ConditionalTransition]) -> 'EnhancedStateMachineBuilder':
        """
        Add conditional transition based on context data.

        Args:
            from_state: Source state
            event: Event name
            conditions: List of conditional transitions

        Returns:
            Self for chaining
        """
        key = f"{from_state}:{event}"
        if key not in self.conditional_transitions:
            self.conditional_transitions[key] = []
        self.conditional_transitions[key].extend(conditions)
        return self

    def add_guard_condition(self, state_name: str, 
                           condition: Callable[[BaseContext], bool]) -> 'EnhancedStateMachineBuilder':
        """
        Add guard condition for state entry.

        Args:
            state_name: State name
            condition: Guard condition function

        Returns:
            Self for chaining
        """
        self.guard_conditions[state_name] = condition
        return self

    def set_metadata(self, key: str, value: Any) -> 'EnhancedStateMachineBuilder':
        """
        Set metadata value.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Self for chaining
        """
        self.metadata[key] = value
        return self

    def configure_performance(self, max_queue_size: int = None, 
                            thread_pool_size: int = None,
                            enable_metrics: bool = None,
                            enable_validation: bool = None) -> 'EnhancedStateMachineBuilder':
        """
        Configure performance options.

        Args:
            max_queue_size: Maximum event queue size
            thread_pool_size: Thread pool size
            enable_metrics: Enable metrics collection
            enable_validation: Enable validation

        Returns:
            Self for chaining
        """
        if max_queue_size is not None:
            self.max_event_queue_size = max_queue_size
        if thread_pool_size is not None:
            self.thread_pool_size = thread_pool_size
        if enable_metrics is not None:
            self.enable_metrics = enable_metrics
        if enable_validation is not None:
            self.enable_validation = enable_validation
        return self

    def validate_configuration(self) -> ValidationResult:
        """
        Validate the complete configuration.

        Returns:
            Validation result
        """
        config = self._build_config()
        
        # Run all custom validators
        for validator in self.validators:
            result = validator(config)
            if not result.success:
                return result

        # Run built-in validations
        return self._run_builtin_validations(config)

    def _run_builtin_validations(self, config: StateMachineConfig) -> ValidationResult:
        """Run built-in configuration validations."""
        result = ValidationResult.success("Configuration is valid")

        # Check initial state exists
        if config.initial_state not in config.states:
            result.add_error(
                "MISSING_INITIAL_STATE",
                f"Initial state '{config.initial_state}' not defined"
            )

        # Check all transition targets exist
        for state_name, state_config in config.states.items():
            for event, target in state_config.transitions.items():
                if target not in config.states:
                    result.add_error(
                        "INVALID_TRANSITION_TARGET",
                        f"State '{state_name}' transitions to undefined state '{target}' on event '{event}'"
                    )

        # Check global transition targets exist
        for event, target in config.global_transitions.items():
            if target not in config.states:
                result.add_error(
                    "INVALID_GLOBAL_TRANSITION",
                    f"Global transition for event '{event}' targets undefined state '{target}'"
                )

        # Check for unreachable states
        reachable = {config.initial_state}
        changed = True
        while changed:
            changed = False
            for state_name, state_config in config.states.items():
                if state_name in reachable:
                    for target in state_config.transitions.values():
                        if target not in reachable:
                            reachable.add(target)
                            changed = True
            
            # Also check global transitions
            for target in config.global_transitions.values():
                if target not in reachable:
                    reachable.add(target)
                    changed = True

        unreachable = set(config.states.keys()) - reachable
        if unreachable:
            result.add_warning(
                "UNREACHABLE_STATES",
                f"Unreachable states detected: {unreachable}"
            )

        # Check for circular dependencies in error recovery
        def has_circular_recovery(state: str, visited: set) -> bool:
            if state in visited:
                return True
            if state not in config.error_recovery:
                return False
            
            visited.add(state)
            return has_circular_recovery(config.error_recovery[state], visited)

        for state in config.error_recovery:
            if has_circular_recovery(state, set()):
                result.add_error(
                    "CIRCULAR_ERROR_RECOVERY",
                    f"Circular error recovery detected starting from state '{state}'"
                )

        return result

    def build(self, context: Optional[BaseContext] = None) -> EnhancedStateMachine:
        """
        Build the enhanced state machine.

        Args:
            context: Optional context (will create default if None)

        Returns:
            Enhanced state machine instance

        Raises:
            ValueError: If configuration validation fails
        """
        # Validate configuration
        validation_result = self.validate_configuration()
        if not validation_result.success:
            error_details = "\n".join([str(error) for error in validation_result.errors])
            raise ValueError(f"Configuration validation failed:\n{error_details}")

        # Build configuration
        config = self._build_config()
        
        # Apply conditional transitions and guard conditions to states
        self._apply_advanced_features()

        # Create and return state machine
        return EnhancedStateMachine(config, context)

    def _build_config(self) -> StateMachineConfig:
        """Build StateMachineConfig from current settings."""
        if not self.initial_state:
            raise ValueError("Initial state must be set")

        return StateMachineConfig(
            initial_state=self.initial_state,
            states=self.states,
            global_transitions=self.global_transitions,
            error_recovery=self.error_recovery,
            timeouts=self.timeouts,
            max_event_queue_size=self.max_event_queue_size,
            enable_metrics=self.enable_metrics,
            enable_validation=self.enable_validation,
            thread_pool_size=self.thread_pool_size,
            metadata=self.metadata
        )

    def _apply_advanced_features(self) -> None:
        """Apply conditional transitions and guard conditions to states."""
        # Apply guard conditions
        for state_name, condition in self.guard_conditions.items():
            if state_name in self.states:
                state_config = self.states[state_name]
                # Add guard condition as precondition
                state_config.preconditions.append(condition)

        # Apply conditional transitions (would need custom state implementation)
        # This is a placeholder for more advanced conditional logic
        pass


class EnhancedStateBuilder:
    """Enhanced builder for individual state configuration."""

    def __init__(self, parent: EnhancedStateMachineBuilder, config: StateConfig):
        """
        Initialize state builder.

        Args:
            parent: Parent state machine builder
            config: State configuration
        """
        self.parent = parent
        self.config = config

    def add_entry_action(self, action: str) -> 'EnhancedStateBuilder':
        """Add entry action."""
        self.config.entry_actions.append(action)
        return self

    def add_exit_action(self, action: str) -> 'EnhancedStateBuilder':
        """Add exit action."""
        self.config.exit_actions.append(action)
        return self

    def add_transition(self, event: str, target_state: str) -> 'EnhancedStateBuilder':
        """Add transition."""
        self.config.transitions[event] = target_state
        return self

    def set_operation(self, operation_type: str) -> 'EnhancedStateBuilder':
        """Set operation type."""
        self.config.operation_type = operation_type
        return self

    def set_timeout(self, seconds: int) -> 'EnhancedStateBuilder':
        """Set timeout."""
        self.config.timeout_seconds = seconds
        return self

    def add_precondition(self, condition: Callable[[BaseContext], bool],
                        description: str = "") -> 'EnhancedStateBuilder':
        """
        Add precondition for state entry.

        Args:
            condition: Condition function
            description: Optional description

        Returns:
            Self for chaining
        """
        self.config.preconditions.append(condition)
        if description:
            self.config.metadata.setdefault('precondition_descriptions', []).append(description)
        return self

    def add_postcondition(self, condition: Callable[[BaseContext], bool],
                         description: str = "") -> 'EnhancedStateBuilder':
        """
        Add postcondition for state exit.

        Args:
            condition: Condition function
            description: Optional description

        Returns:
            Self for chaining
        """
        self.config.postconditions.append(condition)
        if description:
            self.config.metadata.setdefault('postcondition_descriptions', []).append(description)
        return self

    def add_guard_condition(self, event: str, condition: Callable[[BaseContext], bool],
                           description: str = "") -> 'EnhancedStateBuilder':
        """
        Add guard condition for specific event.

        Args:
            event: Event name
            condition: Guard condition function
            description: Optional description

        Returns:
            Self for chaining
        """
        self.config.guard_conditions[event] = condition
        if description:
            self.config.metadata.setdefault('guard_descriptions', {})[event] = description
        return self

    def set_metadata(self, key: str, value: Any) -> 'EnhancedStateBuilder':
        """
        Set state metadata.

        Args:
            key: Metadata key
            value: Metadata value

        Returns:
            Self for chaining
        """
        self.config.metadata[key] = value
        return self

    def add_conditional_transition(self, event: str, 
                                  conditions: List[ConditionalTransition]) -> 'EnhancedStateBuilder':
        """
        Add conditional transitions for an event.

        Args:
            event: Event name
            conditions: List of conditional transitions

        Returns:
            Self for chaining
        """
        self.parent.add_conditional_transition(self.config.name, event, conditions)
        return self

    def done(self) -> EnhancedStateMachineBuilder:
        """Return to parent builder."""
        return self.parent


# Predefined validators
class CommonValidators:
    """Common validation functions for state machine configurations."""

    @staticmethod
    def no_orphaned_states(config: StateMachineConfig) -> ValidationResult:
        """Validate that no states are orphaned (unreachable)."""
        reachable = {config.initial_state}
        changed = True
        
        while changed:
            changed = False
            for state_name, state_config in config.states.items():
                if state_name in reachable:
                    for target in state_config.transitions.values():
                        if target not in reachable:
                            reachable.add(target)
                            changed = True
            
            # Check global transitions
            for target in config.global_transitions.values():
                if target not in reachable:
                    reachable.add(target)
                    changed = True

        unreachable = set(config.states.keys()) - reachable
        if unreachable:
            return ValidationResult.error(
                "ORPHANED_STATES",
                f"Orphaned states found: {unreachable}"
            )
        
        return ValidationResult.success()

    @staticmethod
    def required_error_state(config: StateMachineConfig) -> ValidationResult:
        """Validate that an ERROR_STATE exists."""
        if "ERROR_STATE" not in config.states:
            return ValidationResult.error(
                "MISSING_ERROR_STATE",
                "Configuration should include an ERROR_STATE for error handling"
            )
        return ValidationResult.success()

    @staticmethod
    def all_states_have_exit_transitions(config: StateMachineConfig) -> ValidationResult:
        """Validate that all states have at least one exit transition."""
        result = ValidationResult.success()
        
        for state_name, state_config in config.states.items():
            if not state_config.transitions and state_name not in config.global_transitions:
                result.add_warning(
                    "NO_EXIT_TRANSITIONS",
                    f"State '{state_name}' has no exit transitions",
                    field="transitions"
                )
        
        return result

    @staticmethod
    def timeout_states_have_timeout_transitions(config: StateMachineConfig) -> ValidationResult:
        """Validate that states with timeouts have timeout event transitions."""
        result = ValidationResult.success()
        
        for state_name, state_config in config.states.items():
            if state_config.timeout_seconds and "TIMEOUT" not in state_config.transitions:
                if "TIMEOUT" not in config.global_transitions:
                    result.add_warning(
                        "TIMEOUT_WITHOUT_TRANSITION",
                        f"State '{state_name}' has timeout but no TIMEOUT transition",
                        field="transitions"
                    )
        
        return result
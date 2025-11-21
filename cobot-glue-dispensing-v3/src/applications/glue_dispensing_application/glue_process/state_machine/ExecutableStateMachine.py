from abc import ABC
from enum import Enum
from typing import Dict, Callable, TypeVar, Generic, Optional
import time

from applications.glue_dispensing_application.glue_process.ExecutionContext import Context
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import \
    GlueProcessTransitionRules, GlueProcessState
from modules.shared.MessageBroker import MessageBroker
from backend.system.utils.custom_logging import log_if_enabled, LoggingLevel, setup_logger

TState = TypeVar("TState")  # Generic state type

ENABLE_STATE_MACHINE_LOGGING = True
state_machine_logger = setup_logger("ExecutableStateMachine") if ENABLE_STATE_MACHINE_LOGGING else None

# ---------------------- State Class ----------------------
class State(ABC):
    def __init__(
        self,
        state: Enum,
        handler: Callable[[Context], None],
        on_enter: Optional[Callable[[Context], None]] = None,
        on_exit: Optional[Callable[[Context], None]] = None,
    ):
        self.state = state
        self.handler = handler
        self.on_enter = on_enter
        self.on_exit = on_exit

    def execute(self, context: Context):
        if self.handler:
            self.handler(context)

# ---------------------- State Registry ----------------------
class StateRegistry:
    """Registry for managing State objects."""

    def __init__(self):
        self.registry: Dict[Enum, State] = {}

    def register_state(self, state: State):
        self.registry[state.state] = state

    def get(self, state_enum: Enum) -> Optional[State]:
        return self.registry.get(state_enum)

# ------------------ Executable State Machine ------------------
class ExecutableStateMachine(Generic[TState]):
    """
    Generic state machine fully integrated with StateRegistry.
    """

    def __init__(
        self,
        initial_state: TState,
        transition_rules: Dict[TState, set],
        state_registry: StateRegistry,
        broker: Optional[MessageBroker] = None,
        context: Optional[Context] = None
    ):
        self.current_state: TState = initial_state
        self.transition_rules = transition_rules
        self.state_registry = state_registry
        self.broker: MessageBroker = broker or MessageBroker()
        self.context: Context = context or Context()
        self._stop_requested = False

        log_if_enabled(
            ENABLE_STATE_MACHINE_LOGGING,
            state_machine_logger,
            LoggingLevel.INFO,
            f"ExecutableStateMachine initialized with state: {self.current_state}"
        )

    # ------------------ Properties ------------------
    @property
    def state(self) -> TState:
        return self.current_state

    # ------------------ Transition Logic ------------------
    def can_transition(self, to_state: TState) -> bool:
        return to_state in self.transition_rules.get(self.current_state, set())

    def transition(self, to_state: TState):
        """Perform transition and call exit/enter handlers with context"""
        if not self.can_transition(to_state):
            self.on_invalid_transition_attempt(to_state)
            return False

        old_state = self.current_state
        self._call_handler(old_state, "on_exit")
        self.current_state = to_state
        self._call_handler(to_state, "on_enter")
        self.on_transition_success(to_state)
        return True

    def _call_handler(self, state: TState, handler_type: str):
        """Call a handler if defined, passing context"""
        state_obj = self.state_registry.get(state)
        if not state_obj:
            return

        handler = getattr(state_obj, handler_type, None)
        if handler:
            try:
                handler(self.context)
            except Exception as e:
                log_if_enabled(
                    ENABLE_STATE_MACHINE_LOGGING,
                    state_machine_logger,
                    f"Error in {state}.{handler_type}: {e}",
                    LoggingLevel.ERROR
                )

    # ------------------ Hooks ------------------
    def on_transition_success(self, new_state: TState):
        self.broker.publish("STATE_MACHINE_STATE", new_state)

    def on_invalid_transition_attempt(self, attempted_state: TState):
        log_if_enabled(
            ENABLE_STATE_MACHINE_LOGGING,
            state_machine_logger,
            LoggingLevel.WARNING,
            f"Invalid transition attempt: {self.current_state} -> {attempted_state}"
        )

    # ------------------ Execution Loop ------------------
    def start_execution(self, delay: float = 0.1):
        """Start execution loop that calls 'execute' for current state"""
        self._stop_requested = False
        while not self._stop_requested:
            state_obj = self.state_registry.get(self.current_state)
            if state_obj:
                try:
                    state_obj.execute(self.context)
                except Exception as e:
                    log_if_enabled(
                        ENABLE_STATE_MACHINE_LOGGING,
                        state_machine_logger,
                        LoggingLevel.ERROR,
                        f"Error executing state {self.current_state}: {e}"
                    )
            time.sleep(delay)

    def stop_execution(self):
        """Stop the execution loop"""
        self._stop_requested = True


from typing import Optional, Dict, Set

# ------------------ State Machine Builder ------------------
class ExecutableStateMachineBuilder(Generic[TState]):
    """
    Builder for ExecutableStateMachine using StateRegistry.
    """

    def __init__(self):
        self._initial_state: Optional[TState] = None
        self._transition_rules: Dict[TState, Set[TState]] = {}
        self._registry: Optional[StateRegistry] = None
        self._broker: Optional[MessageBroker] = None
        self._context: Optional[Context] = None

    def with_initial_state(self, initial_state: TState):
        self._initial_state = initial_state
        return self

    def with_transition_rules(self, transition_rules: Dict[TState, Set[TState]]):
        self._transition_rules = transition_rules
        return self

    def with_state_registry(self, registry: StateRegistry):
        self._registry = registry
        return self

    def with_message_broker(self, broker: MessageBroker):
        self._broker = broker
        return self

    def with_context(self, context: Context):
        self._context = context
        return self

    def build(self) -> ExecutableStateMachine[TState]:
        if not self._initial_state:
            raise ValueError("Initial state must be set")
        if not self._registry:
            raise ValueError("StateRegistry must be set")
        return ExecutableStateMachine(
            initial_state=self._initial_state,
            transition_rules=self._transition_rules,
            state_registry=self._registry,
            broker=self._broker,
            context=self._context
        )

# ------------------ Example Usage ------------------
if __name__ == "__main__":
    def make_mock_handler(name):
        """Returns a mock execute function for a state that uses context"""

        def handler(ctx: Context):
            if not hasattr(ctx, "counter"):
                ctx.counter = 0
            ctx.counter += 1
            print(f"[{name}] Executing state logic... (counter={ctx.counter})")
            time.sleep(0.5)

            # Auto-transition to next valid state
            possible_transitions = transition_rules.get(current_state_machine.state, [])
            next_state = next(
                (s for s in possible_transitions if s not in [GlueProcessState.ERROR, GlueProcessState.PAUSED]),
                None
            )
            if next_state:
                current_state_machine.transition(next_state)

        return handler

    # Transition rules
    transition_rules = GlueProcessTransitionRules.get_glue_transition_rules()

    # Create StateRegistry and register states
    registry = StateRegistry()
    for state_enum in GlueProcessState:
        state = State(
            state_enum,
            handler=make_mock_handler(state_enum.name),
            on_enter=lambda ctx, s=state_enum: print(f"Entered {s.name}"),
            on_exit=lambda ctx, s=state_enum: print(f"Exited {s.name}")
        )
        registry.register_state(state)

    # Build the state machine using the builder
    current_state_machine = (
        ExecutableStateMachineBuilder()
        .with_initial_state(GlueProcessState.INITIALIZING)
        .with_transition_rules(GlueProcessTransitionRules.get_glue_transition_rules())
        .with_state_registry(registry)
        .build()
    )

    current_state_machine.transition(GlueProcessState.IDLE)
    current_state_machine.transition(GlueProcessState.STARTING)

    # Start execution loop
    try:
        current_state_machine.start_execution(delay=0.2)
    except KeyboardInterrupt:
        print("Execution stopped by user")
        current_state_machine.stop_execution()

from dataclasses import dataclass
from typing import Dict, Callable, TypeVar, Generic, Set, Optional
import time

from applications.glue_dispensing_application.glue_process.ExecutionContext import Context
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import \
    GlueProcessTransitionRules, GlueProcessState
from modules.shared.MessageBroker import MessageBroker
from backend.system.utils.custom_logging import log_if_enabled, LoggingLevel, setup_logger

TState = TypeVar("TState")  # Generic state type

ENABLE_STATE_MACHINE_LOGGING = True
state_machine_logger = setup_logger("ExecutableStateMachine") if ENABLE_STATE_MACHINE_LOGGING else None



class ExecutableStateMachine(Generic[TState]):
    """
    Generic state machine that can also execute state logic.

    Attributes:
        initial_state: Starting state
        transition_rules: Dict[TState, Set[TState]] - allowed transitions
        state_handlers: Dict[TState, Dict[str, Callable]] - 'on_enter', 'on_exit', 'execute'
        broker: Optional MessageBroker for state publishing
    """

    def __init__(
        self,
        initial_state: TState,
        transition_rules: Dict[TState, Set[TState]],
        state_handlers: Optional[Dict[TState, Dict[str, Callable]]] = None,
        broker: Optional[MessageBroker] = None,
        context: Context = None
    ):
        self.current_state: TState = initial_state
        self.transition_rules = transition_rules
        self.state_handlers = state_handlers or {}
        self.broker: MessageBroker = broker or MessageBroker()
        self._stop_requested = False
        self.context = context or Context()

        log_if_enabled(
            ENABLE_STATE_MACHINE_LOGGING,
            state_machine_logger,
            LoggingLevel.INFO,
            f"ExecutableStateMachine initialized with state: {self.current_state}"
        )

    @property
    def state(self) -> TState:
        return self.current_state

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
        handler = self.state_handlers.get(state, {}).get(handler_type)
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

    # Hooks
    def on_transition_success(self, new_state: TState):
        self.broker.publish("STATE_MACHINE_STATE", new_state)

    def on_invalid_transition_attempt(self, attempted_state: TState):
        log_if_enabled(
            ENABLE_STATE_MACHINE_LOGGING,
            state_machine_logger,
            LoggingLevel.WARNING,
            f"Invalid transition attempt: {self.current_state} -> {attempted_state}"
        )

    # ---------------- Execution Loop ----------------
    def start_execution(self, delay: float = 0.1):
        """Start execution loop that calls 'execute' for current state"""
        self._stop_requested = False
        while not self._stop_requested:
            current_state = self.current_state
            execute_handler = self.state_handlers.get(current_state, {}).get("execute")

            if execute_handler:
                try:
                    # Pass the context object to the execute handler
                    execute_handler(self.context)
                except Exception as e:
                    log_if_enabled(
                        ENABLE_STATE_MACHINE_LOGGING,
                        state_machine_logger,
                        LoggingLevel.ERROR,
                        f"Error executing state {current_state}: {e}"
                    )
            time.sleep(delay)

    def stop_execution(self):
        """Stop the execution loop"""
        self._stop_requested = True

if __name__ == "__main__":

    def make_mock_handler(name):
        """Returns a mock execute function for a state that uses context"""

        def handler(ctx: Context):
            # Example: increment a counter in the context
            if not hasattr(ctx, "counter"):
                ctx.counter = 0
            ctx.counter += 1

            print(f"[{name}] Executing state logic... (counter={ctx.counter})")
            time.sleep(0.5)  # simulate work

            # Automatically transition to next valid state if possible
            possible_transitions = transition_rules.get(current_state_machine.state, [])
            next_state = next(
                (s for s in possible_transitions if s not in [GlueProcessState.ERROR, GlueProcessState.PAUSED]),
                None
            )
            if next_state:
                current_state_machine.transition(next_state)

        return handler


    transition_rules = GlueProcessTransitionRules.get_glue_transition_rules()

    # 1️⃣ Create mock handlers for all states
    state_handlers = {
        state: {"execute": make_mock_handler(state.name)}
        for state in GlueProcessState
    }

    # 2️⃣ Initialize the generic executable state machine
    current_state_machine = ExecutableStateMachine(
        initial_state=GlueProcessState.INITIALIZING,
        transition_rules=transition_rules,
        state_handlers=state_handlers
    )

    # 3️⃣ Simulate normal workflow
    current_state_machine.transition(GlueProcessState.IDLE)
    current_state_machine.transition(GlueProcessState.STARTING)

    # 4️⃣ Start the execution loop
    try:
        current_state_machine.start_execution(delay=0.2)
    except KeyboardInterrupt:
        print("Execution stopped by user")
        current_state_machine.stop_execution()
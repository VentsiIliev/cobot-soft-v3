from typing import Dict, Callable

from backend.system.utils.custom_logging import log_if_enabled, LoggingLevel, \
    log_calls_with_timestamp_decorator, setup_logger
from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import \
    GlueProcessTransitionRules, GlueProcessState
from communication_layer.api.v1.topics import GlueTopics
from modules.shared.MessageBroker import MessageBroker

ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING = True
if ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING:
    robot_service_state_machine_logger = setup_logger("RobotStateMachine")
else:
    robot_service_state_machine_logger = None

class GlueProcessStateMachine:
    """State machine for managing robot service states and transitions"""

    def __init__(self, initial_state: GlueProcessState):
        self.current_state = initial_state

        self.transition_rules = GlueProcessTransitionRules.get_glue_transition_rules()
        self.state_handlers = self._define_state_handlers()
        # self._state_lock = threading.Lock()
        self.broker = MessageBroker()
        log_if_enabled(enabled=ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING, logger=robot_service_state_machine_logger,
                       message="GlueProcessStateMachine initialized", level=LoggingLevel.INFO)
    log_calls_with_timestamp_decorator(logger=robot_service_state_machine_logger, enabled=False)


    def _define_state_handlers(self) -> Dict[GlueProcessState, Dict[str, Callable]]:
        """Define entry/exit handlers for states"""
        return {
            GlueProcessState.PAUSED: {
                'on_enter': self._on_enter_paused,
                'on_exit': self._on_exit_paused
            },
            GlueProcessState.STOPPED: {
                'on_enter': self._on_enter_stopped,
            },
            GlueProcessState.COMPLETED: {
                'on_enter': self._on_enter_completed,
            }
        }

    def _on_enter_paused(self, context: dict = None):
        """Called when entering PAUSED state"""


    def _on_exit_paused(self, context: dict = None):
        """Called when exiting PAUSED state"""

        # start glue dispensing if it was active before pause

        log_if_enabled(enabled=ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING,
                       logger=robot_service_state_machine_logger,
                       message="StateMachine: Exiting PAUSED state", level=LoggingLevel.DEBUG)

    def _on_enter_stopped(self, context: dict = None):
        """Called when entering STOPPED state"""
        log_if_enabled(enabled=ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING,
                       logger=robot_service_state_machine_logger,
                       message="StateMachine: Entering STOPPED state", level=LoggingLevel.DEBUG)


    def _on_enter_completed(self, context: dict = None):
        """Called when entering COMPLETED state"""
        log_if_enabled(enabled=ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING,
                       logger=robot_service_state_machine_logger,
                       message="StateMachine: Entering COMPLETED state", level=LoggingLevel.DEBUG)
    def can_transition(self, to_state: GlueProcessState) -> bool:
        """Check if transition is allowed"""
        # with self._state_lock:
        return to_state in self.transition_rules.get(self.current_state, set())

    def transition(self, to_state: GlueProcessState, context: dict = None) -> bool:
        """Attempt to transition to new state"""
        # with self._state_lock:
        if not self.can_transition(to_state):
            log_if_enabled(enabled=ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING,
                           logger=robot_service_state_machine_logger,
                           message=f"StateMachine: Invalid transition blocked: {self.current_state} -> {to_state}",
                           level=LoggingLevel.DEBUG)

            return False

        log_if_enabled(enabled=ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING,
                       logger=robot_service_state_machine_logger,
                       message=f"StateMachine: State transition: {self.current_state} -> {to_state}",
                       level=LoggingLevel.DEBUG)
        old_state = self.current_state
        self.current_state = to_state
        self.broker.publish(GlueTopics.PROCESS_STATE, self.current_state)

        # Call exit handler for old state
        self._call_handler(old_state, 'on_exit', context)

        # Call entry handler for new state
        self._call_handler(to_state, 'on_enter', context)

        return True

    def _call_handler(self, state: GlueProcessState, handler_type: str, context: dict):
        """Call state handler if it exists"""
        try:
            handler = self.state_handlers.get(state, {}).get(handler_type)
            if handler:
                handler(context)
        except Exception as e:
            log_if_enabled(enabled=ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING,
                           logger=robot_service_state_machine_logger,
                           message=f"Error in state handler {state}.{handler_type}: {e}",
                           level=LoggingLevel.ERROR)

    @property
    def state(self) -> GlueProcessState:
        """Get current state (thread-safe)"""
        # with self._state_lock:
        return self.current_state
from typing import Dict, Set, Callable

from modules.shared.MessageBroker import MessageBroker
from modules.robot.robotService.enums.RobotServiceState import RobotServiceState
from backend.system.utils.custom_logging import log_if_enabled, LoggingLevel, \
    log_calls_with_timestamp_decorator, setup_logger

ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING = True
if ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING:
    robot_service_state_machine_logger = setup_logger("RobotStateMachine")
else:
    robot_service_state_machine_logger = None

class GlueProcessStateMachine:
    """State machine for managing robot service states and transitions"""

    def __init__(self, initial_state: RobotServiceState, robot_service):
        self.current_state = initial_state
        self.robot_service = robot_service
        self.transition_rules = self._define_transition_rules()
        self.state_handlers = self._define_state_handlers()
        # self._state_lock = threading.Lock()
        self.broker = MessageBroker()
        log_if_enabled(enabled=ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING, logger=robot_service_state_machine_logger,
                       message="RobotStateMachine initialized", level=LoggingLevel.INFO)

    log_calls_with_timestamp_decorator(logger=robot_service_state_machine_logger, enabled=False)

    def _define_transition_rules(self) -> Dict[RobotServiceState, Set[RobotServiceState]]:
        """Define valid state transitions"""
        return {
            RobotServiceState.INITIALIZING: {
                RobotServiceState.IDLE,
                RobotServiceState.ERROR
            },

            RobotServiceState.IDLE: {
                RobotServiceState.STARTING,
                RobotServiceState.ERROR,
            },

            RobotServiceState.STARTING: {
                RobotServiceState.MOVING_TO_FIRST_POINT,
                RobotServiceState.EXECUTING_PATH,
                RobotServiceState.COMPLETED,
                RobotServiceState.PAUSED,
                RobotServiceState.STOPPED,
                RobotServiceState.ERROR,
            },

            RobotServiceState.MOVING_TO_FIRST_POINT: {
                RobotServiceState.EXECUTING_PATH,
                RobotServiceState.PAUSED,
                RobotServiceState.STOPPED,
                RobotServiceState.COMPLETED,
                RobotServiceState.ERROR,
            },

            # 🆕 Extended execution chain
            RobotServiceState.EXECUTING_PATH: {
                RobotServiceState.PUMP_INITIAL_BOOST,
                RobotServiceState.TRANSITION_BETWEEN_PATHS,
                RobotServiceState.PAUSED,
                RobotServiceState.STOPPED,
                RobotServiceState.COMPLETED,
                RobotServiceState.ERROR,
            },

            # 🆕 New intermediate state: PUMP_INITIAL_BOOST
            RobotServiceState.PUMP_INITIAL_BOOST: {
                RobotServiceState.STARTING_PUMP_ADJUSTMENT_THREAD,
                RobotServiceState.PAUSED,
                RobotServiceState.STOPPED,
                RobotServiceState.ERROR,
            },

            # 🆕 New intermediate state: STARTING_PUMP_ADJUSTMENT_THREAD
            RobotServiceState.STARTING_PUMP_ADJUSTMENT_THREAD: {
                RobotServiceState.SENDING_PATH_POINTS,
                RobotServiceState.PAUSED,
                RobotServiceState.STOPPED,
                RobotServiceState.ERROR,
            },

            # 🆕 New intermediate state: SENDING_PATH_POINTS
            RobotServiceState.SENDING_PATH_POINTS: {
                RobotServiceState.WAIT_FOR_PATH_COMPLETION,
                RobotServiceState.PAUSED,
                RobotServiceState.STOPPED,
                RobotServiceState.ERROR,
            },

            # 🆕 New intermediate state: WAIT_FOR_PATH_COMPLETION
            RobotServiceState.WAIT_FOR_PATH_COMPLETION: {
                RobotServiceState.TRANSITION_BETWEEN_PATHS,
                RobotServiceState.COMPLETED,
                RobotServiceState.PAUSED,
                RobotServiceState.STOPPED,
                RobotServiceState.ERROR,
            },

            RobotServiceState.TRANSITION_BETWEEN_PATHS: {
                RobotServiceState.STARTING,  # Start next path
                RobotServiceState.COMPLETED,  # No more paths
                RobotServiceState.PAUSED,
                RobotServiceState.STOPPED,
                RobotServiceState.ERROR,
            },

            RobotServiceState.PAUSED: {
                RobotServiceState.STARTING,  # Resume execution
                RobotServiceState.STOPPED,  # Stop from pause
                RobotServiceState.COMPLETED,  # Complete from pause
                RobotServiceState.IDLE,  # Reset to idle
                RobotServiceState.ERROR,
            },

            RobotServiceState.STOPPED: {
                RobotServiceState.COMPLETED,  # Complete after stop
                RobotServiceState.IDLE,  # Reset to idle
                RobotServiceState.ERROR,
            },

            RobotServiceState.COMPLETED: {
                RobotServiceState.IDLE,  # Ready for next operation
                RobotServiceState.ERROR,
            },

            RobotServiceState.ERROR: {
                RobotServiceState.IDLE,  # Recovery
                RobotServiceState.INITIALIZING,  # Full reset
            },
        }

    def _define_state_handlers(self) -> Dict[RobotServiceState, Dict[str, Callable]]:
        """Define entry/exit handlers for states"""
        return {
            RobotServiceState.PAUSED: {
                'on_enter': self._on_enter_paused,
                'on_exit': self._on_exit_paused
            },
            RobotServiceState.STOPPED: {
                'on_enter': self._on_enter_stopped,
            },
            RobotServiceState.COMPLETED: {
                'on_enter': self._on_enter_completed,
            }
        }

    def _on_enter_paused(self, context: dict = None):
        """Called when entering PAUSED state"""

        # Stop robot motion
        try:
            self.robot_service._stop_robot_motion()

            # stop glue dispensing if active

        except Exception as e:
            log_if_enabled(enabled=ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING,
                           logger=robot_service_state_machine_logger,
                           message=f"Error stopping robot on pause: {e}", level=LoggingLevel.ERROR)

    def _on_exit_paused(self, context: dict = None):
        """Called when exiting PAUSED state"""

        # start glue dispensing if it was active before pause

        log_if_enabled(enabled=ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING,
                       logger=robot_service_state_machine_logger,
                       message="StateMachine: Exiting PAUSED state", level=LoggingLevel.DEBUG)

    def _on_enter_stopped(self, context: dict = None):
        """Called when entering STOPPED state"""

        # Stop Glue dispensing if active
        # Stop robot motion
        try:
            self.robot_service._stop_robot_motion()
        except Exception as e:
            log_if_enabled(enabled=ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING,
                           logger=robot_service_state_machine_logger,
                           message=f"Error stopping robot: {e}", level=LoggingLevel.ERROR)

    def _on_enter_completed(self, context: dict = None):
        """Called when entering COMPLETED state"""

        # # Clean up glue systems
        # # stop glue dispensing if active
        # if hasattr(self.robot_service, 'execution_context') and self.robot_service.execution_context.service:
        #     try:
        #         self.robot_service.execution_context.service.generatorOff()
        #     except Exception as e:
        #         log_if_enabled(enabled=ENABLE_ROBOT_SERVICE_STATE_MACHINE_LOGGING,
        #                        logger=robot_service_state_machine_logger,
        #                        message=f"Error turning off generator: {e}", level=LoggingLevel.ERROR)

    def can_transition(self, to_state: RobotServiceState) -> bool:
        """Check if transition is allowed"""
        # with self._state_lock:
        return to_state in self.transition_rules.get(self.current_state, set())

    def transition(self, to_state: RobotServiceState, context: dict = None) -> bool:
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
        self.broker.publish("glue-process/state",self.current_state)

        # Call exit handler for old state
        self._call_handler(old_state, 'on_exit', context)

        # Call entry handler for new state
        self._call_handler(to_state, 'on_enter', context)

        return True

    def _call_handler(self, state: RobotServiceState, handler_type: str, context: dict):
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
    def state(self) -> RobotServiceState:
        """Get current state (thread-safe)"""
        # with self._state_lock:
        return self.current_state
"""
Glue Process States

This module defines the states specific to the glue dispensing application.
These states extend the base ProcessStateType with glue-specific operations
and workflow steps.
"""

from enum import Enum, auto
from typing import Dict, Set



class GlueProcessState(Enum):
    """
    States specific to the glue dispensing process.
    
    These states represent the complete workflow for glue dispensing operations,
    from initialization through completion. They inherit the base process patterns
    but add glue-specific operations.
    """

    INITIALIZING = auto()
    IDLE = auto()
    MOVING_TO_FIRST_POINT = auto()
    WAIT_FOR_PATH_COMPLETION = auto()
    STARTING = auto()
    PREPARING_PATH = auto()
    MOVING_TO_START_POINT = auto()
    WAITING_FOR_START_REACH = auto()
    EXECUTING_PATH = auto()
    STARTING_PUMP = auto()
    SENDING_PATH_POINTS = auto()
    WAITING_PATH_COMPLETION = auto()
    STOPPING_PUMP = auto()
    TRANSITION_BETWEEN_PATHS = auto()
    PATH_CLEANUP = auto()
    PATH_INCREMENT = auto()
    COMPLETED = auto()
    ERROR = auto()
    STOPPED = auto()
    PAUSED = auto()
    STARTING_PUMP_ADJUSTMENT_THREAD = auto()
    PUMP_INITIAL_BOOST = auto()





class GlueProcessTransitionRules:
    """
    Transition rules specific to the glue dispensing process.
    
    These rules define the valid state transitions for glue dispensing operations.
    """
    
    @staticmethod
    def get_glue_transition_rules() -> Dict[GlueProcessState, Set[GlueProcessState]]:
        """
        Get the complete transition rules for glue dispensing operations.
        
        Returns:
            Dict mapping glue process states to their valid transition targets
        """
        return {
            GlueProcessState.INITIALIZING: {
                GlueProcessState.IDLE,
                GlueProcessState.ERROR
            },

            GlueProcessState.IDLE: {
                GlueProcessState.STARTING,
                GlueProcessState.ERROR,
            },

            GlueProcessState.STARTING: {
                GlueProcessState.MOVING_TO_FIRST_POINT,
                GlueProcessState.EXECUTING_PATH,
                GlueProcessState.COMPLETED,
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPED,
                GlueProcessState.ERROR,
            },

            GlueProcessState.MOVING_TO_FIRST_POINT: {
                GlueProcessState.EXECUTING_PATH,
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPED,
                GlueProcessState.COMPLETED,
                GlueProcessState.ERROR,
            },

            # 🆕 Extended execution chain
            GlueProcessState.EXECUTING_PATH: {
                GlueProcessState.PUMP_INITIAL_BOOST,
                GlueProcessState.TRANSITION_BETWEEN_PATHS,
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPED,
                GlueProcessState.COMPLETED,
                GlueProcessState.ERROR,
            },

            # 🆕 New intermediate state: PUMP_INITIAL_BOOST
            GlueProcessState.PUMP_INITIAL_BOOST: {
                GlueProcessState.STARTING_PUMP_ADJUSTMENT_THREAD,
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPED,
                GlueProcessState.ERROR,
            },

            # 🆕 New intermediate state: STARTING_PUMP_ADJUSTMENT_THREAD
            GlueProcessState.STARTING_PUMP_ADJUSTMENT_THREAD: {
                GlueProcessState.SENDING_PATH_POINTS,
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPED,
                GlueProcessState.ERROR,
            },

            # 🆕 New intermediate state: SENDING_PATH_POINTS
            GlueProcessState.SENDING_PATH_POINTS: {
                GlueProcessState.WAIT_FOR_PATH_COMPLETION,
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPED,
                GlueProcessState.ERROR,
            },

            # 🆕 New intermediate state: WAIT_FOR_PATH_COMPLETION
            GlueProcessState.WAIT_FOR_PATH_COMPLETION: {
                GlueProcessState.TRANSITION_BETWEEN_PATHS,
                GlueProcessState.COMPLETED,
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPED,
                GlueProcessState.ERROR,
            },

            GlueProcessState.TRANSITION_BETWEEN_PATHS: {
                GlueProcessState.STARTING,  # Start next path
                GlueProcessState.COMPLETED,  # No more paths
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPED,
                GlueProcessState.ERROR,
            },

            GlueProcessState.PAUSED: {
                GlueProcessState.STARTING,  # Resume execution
                GlueProcessState.STOPPED,  # Stop from pause
                GlueProcessState.COMPLETED,  # Complete from pause
                GlueProcessState.IDLE,  # Reset to idle
                GlueProcessState.ERROR,
            },

            GlueProcessState.STOPPED: {
                GlueProcessState.COMPLETED,  # Complete after stop
                GlueProcessState.IDLE,  # Reset to idle
                GlueProcessState.ERROR,
            },

            GlueProcessState.COMPLETED: {
                GlueProcessState.IDLE,  # Ready for next operation
                GlueProcessState.ERROR,
            },

            GlueProcessState.ERROR: {
                GlueProcessState.IDLE,  # Recovery
                GlueProcessState.INITIALIZING,  # Full reset
            },
        }


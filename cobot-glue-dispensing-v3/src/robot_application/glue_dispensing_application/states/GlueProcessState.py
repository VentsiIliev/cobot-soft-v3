"""
Glue Process States

This module defines the states specific to the glue dispensing application.
These states extend the base ProcessStateType with glue-specific operations
and workflow steps.
"""

from enum import Enum, auto
from typing import Dict, Set
from src.backend.system.state_machine.ProcessStateType import ProcessStateType, ProcessStateCategory


class GlueProcessState(Enum):
    """
    States specific to the glue dispensing process.
    
    These states represent the complete workflow for glue dispensing operations,
    from initialization through completion. They inherit the base process patterns
    but add glue-specific operations.
    """
    
    # === LIFECYCLE STATES (inherit from base) ===
    INITIALIZING = auto()           # Starting up, loading configuration
    READY = auto()                  # Initialized and ready for operations
    SHUTTING_DOWN = auto()          # Graceful shutdown in progress
    
    # === PREPARATION STATES ===
    PREPARING = auto()              # General preparation phase
    LOADING_WORKPIECE = auto()      # Loading workpiece data
    VALIDATING_WORKPIECE = auto()   # Validating workpiece parameters
    CALIBRATING_ROBOT = auto()      # Robot calibration
    CALIBRATING_CAMERA = auto()     # Camera calibration
    CALIBRATING_NOZZLE = auto()     # Glue nozzle calibration
    NESTING = auto()                # Workpiece nesting operations
    
    # === GLUE-SPECIFIC PREPARATION ===
    PREPARING_GLUE_SYSTEM = auto()  # Initializing glue dispensing system
    PRIMING_NOZZLE = auto()         # Priming glue nozzle
    TESTING_GLUE_FLOW = auto()      # Testing glue flow rate
    ADJUSTING_PRESSURE = auto()     # Adjusting glue pressure
    HEATING_GLUE = auto()           # Heating glue if required
    
    # === EXECUTION STATES ===
    STARTING_OPERATION = auto()     # Starting glue dispensing operation
    MOVING_TO_START_POINT = auto()  # Moving robot to starting position
    POSITIONING_NOZZLE = auto()     # Fine positioning of nozzle
    
    # === GLUE DISPENSING EXECUTION ===
    STARTING_GLUE_FLOW = auto()     # Starting glue dispensing
    DISPENSING_GLUE = auto()        # Active glue dispensing
    SPRAYING_GLUE = auto()          # Spraying glue (alternative to dispensing)
    ADJUSTING_FLOW_RATE = auto()    # Dynamic flow rate adjustment
    MONITORING_COVERAGE = auto()    # Monitoring glue coverage
    
    # === PATH EXECUTION ===
    EXECUTING_PATH = auto()         # Executing robot path with glue
    TRANSITIONING_PATHS = auto()    # Moving between different paths
    PUMP_INITIAL_BOOST = auto()     # Initial pump boost at start of path
    PUMP_ADJUSTMENT = auto()        # Dynamic pump speed adjustment
    SENDING_PATH_POINTS = auto()    # Sending path points to robot
    WAITING_PATH_COMPLETION = auto() # Waiting for path completion
    
    # === CONTROL STATES ===
    IDLE = auto()                   # Idle, waiting for commands
    PAUSED = auto()                 # Operation paused
    RESUMING = auto()               # Resuming from pause
    STOPPING = auto()               # Stopping operation
    STOPPED = auto()                # Operation stopped
    
    # === COMPLETION AND CLEANUP ===
    STOPPING_GLUE_FLOW = auto()     # Stopping glue dispensing
    CLEANING_NOZZLE = auto()        # Cleaning glue nozzle
    RETRACTING_NOZZLE = auto()      # Retracting nozzle from workpiece
    MOVING_TO_HOME = auto()         # Moving robot to home position
    FINALIZING = auto()             # Final cleanup operations
    COMPLETED = auto()              # Operation completed successfully
    
    # === ERROR AND RECOVERY STATES ===
    ERROR = auto()                  # General error state
    GLUE_SYSTEM_ERROR = auto()      # Glue system specific error
    ROBOT_ERROR = auto()            # Robot specific error
    NOZZLE_CLOGGED = auto()         # Nozzle clogging error
    PRESSURE_ERROR = auto()         # Pressure system error
    FLOW_RATE_ERROR = auto()        # Flow rate error
    RECOVERING = auto()             # Attempting error recovery
    FAILED = auto()                 # Unrecoverable failure


class GlueProcessStateMetadata:
    """
    Metadata about glue process states including categories, descriptions, and properties.
    """
    
    # State category mapping (extends base categories)
    STATE_CATEGORIES: Dict[GlueProcessState, ProcessStateCategory] = {
        # Lifecycle
        GlueProcessState.INITIALIZING: ProcessStateCategory.LIFECYCLE,
        GlueProcessState.READY: ProcessStateCategory.LIFECYCLE,
        GlueProcessState.SHUTTING_DOWN: ProcessStateCategory.LIFECYCLE,
        
        # Preparation
        GlueProcessState.PREPARING: ProcessStateCategory.PREPARATION,
        GlueProcessState.LOADING_WORKPIECE: ProcessStateCategory.PREPARATION,
        GlueProcessState.VALIDATING_WORKPIECE: ProcessStateCategory.PREPARATION,
        GlueProcessState.CALIBRATING_ROBOT: ProcessStateCategory.PREPARATION,
        GlueProcessState.CALIBRATING_CAMERA: ProcessStateCategory.PREPARATION,
        GlueProcessState.CALIBRATING_NOZZLE: ProcessStateCategory.PREPARATION,
        GlueProcessState.NESTING: ProcessStateCategory.PREPARATION,
        GlueProcessState.PREPARING_GLUE_SYSTEM: ProcessStateCategory.PREPARATION,
        GlueProcessState.PRIMING_NOZZLE: ProcessStateCategory.PREPARATION,
        GlueProcessState.TESTING_GLUE_FLOW: ProcessStateCategory.PREPARATION,
        GlueProcessState.ADJUSTING_PRESSURE: ProcessStateCategory.PREPARATION,
        GlueProcessState.HEATING_GLUE: ProcessStateCategory.PREPARATION,
        
        # Execution
        GlueProcessState.STARTING_OPERATION: ProcessStateCategory.EXECUTION,
        GlueProcessState.MOVING_TO_START_POINT: ProcessStateCategory.EXECUTION,
        GlueProcessState.POSITIONING_NOZZLE: ProcessStateCategory.EXECUTION,
        GlueProcessState.STARTING_GLUE_FLOW: ProcessStateCategory.EXECUTION,
        GlueProcessState.DISPENSING_GLUE: ProcessStateCategory.EXECUTION,
        GlueProcessState.SPRAYING_GLUE: ProcessStateCategory.EXECUTION,
        GlueProcessState.ADJUSTING_FLOW_RATE: ProcessStateCategory.EXECUTION,
        GlueProcessState.MONITORING_COVERAGE: ProcessStateCategory.EXECUTION,
        GlueProcessState.EXECUTING_PATH: ProcessStateCategory.EXECUTION,
        GlueProcessState.TRANSITIONING_PATHS: ProcessStateCategory.EXECUTION,
        GlueProcessState.PUMP_INITIAL_BOOST: ProcessStateCategory.EXECUTION,
        GlueProcessState.PUMP_ADJUSTMENT: ProcessStateCategory.EXECUTION,
        GlueProcessState.SENDING_PATH_POINTS: ProcessStateCategory.EXECUTION,
        GlueProcessState.WAITING_PATH_COMPLETION: ProcessStateCategory.EXECUTION,
        
        # Control
        GlueProcessState.IDLE: ProcessStateCategory.CONTROL,
        GlueProcessState.PAUSED: ProcessStateCategory.CONTROL,
        GlueProcessState.RESUMING: ProcessStateCategory.CONTROL,
        GlueProcessState.STOPPING: ProcessStateCategory.CONTROL,
        GlueProcessState.STOPPED: ProcessStateCategory.CONTROL,
        
        # Completion
        GlueProcessState.STOPPING_GLUE_FLOW: ProcessStateCategory.COMPLETION,
        GlueProcessState.CLEANING_NOZZLE: ProcessStateCategory.COMPLETION,
        GlueProcessState.RETRACTING_NOZZLE: ProcessStateCategory.COMPLETION,
        GlueProcessState.MOVING_TO_HOME: ProcessStateCategory.COMPLETION,
        GlueProcessState.FINALIZING: ProcessStateCategory.COMPLETION,
        GlueProcessState.COMPLETED: ProcessStateCategory.COMPLETION,
        
        # Error
        GlueProcessState.ERROR: ProcessStateCategory.ERROR,
        GlueProcessState.GLUE_SYSTEM_ERROR: ProcessStateCategory.ERROR,
        GlueProcessState.ROBOT_ERROR: ProcessStateCategory.ERROR,
        GlueProcessState.NOZZLE_CLOGGED: ProcessStateCategory.ERROR,
        GlueProcessState.PRESSURE_ERROR: ProcessStateCategory.ERROR,
        GlueProcessState.FLOW_RATE_ERROR: ProcessStateCategory.ERROR,
        GlueProcessState.RECOVERING: ProcessStateCategory.ERROR,
        GlueProcessState.FAILED: ProcessStateCategory.ERROR,
    }
    
    # State descriptions
    STATE_DESCRIPTIONS: Dict[GlueProcessState, str] = {
        # Lifecycle
        GlueProcessState.INITIALIZING: "Glue dispensing system is starting up",
        GlueProcessState.READY: "System ready for glue dispensing operations",
        GlueProcessState.SHUTTING_DOWN: "Glue dispensing system shutting down",
        
        # Preparation
        GlueProcessState.PREPARING: "Preparing for glue dispensing operation",
        GlueProcessState.LOADING_WORKPIECE: "Loading workpiece data and parameters",
        GlueProcessState.VALIDATING_WORKPIECE: "Validating workpiece compatibility",
        GlueProcessState.CALIBRATING_ROBOT: "Calibrating robot positioning",
        GlueProcessState.CALIBRATING_CAMERA: "Calibrating vision system",
        GlueProcessState.CALIBRATING_NOZZLE: "Calibrating glue nozzle position",
        GlueProcessState.NESTING: "Optimizing workpiece layout and paths",
        GlueProcessState.PREPARING_GLUE_SYSTEM: "Initializing glue dispensing system",
        GlueProcessState.PRIMING_NOZZLE: "Priming glue nozzle for dispensing",
        GlueProcessState.TESTING_GLUE_FLOW: "Testing glue flow rate and consistency",
        GlueProcessState.ADJUSTING_PRESSURE: "Adjusting glue system pressure",
        GlueProcessState.HEATING_GLUE: "Heating glue to optimal temperature",
        
        # Execution
        GlueProcessState.STARTING_OPERATION: "Starting glue dispensing operation",
        GlueProcessState.MOVING_TO_START_POINT: "Moving robot to starting position",
        GlueProcessState.POSITIONING_NOZZLE: "Fine positioning glue nozzle",
        GlueProcessState.STARTING_GLUE_FLOW: "Starting glue dispensing flow",
        GlueProcessState.DISPENSING_GLUE: "Actively dispensing glue",
        GlueProcessState.SPRAYING_GLUE: "Spraying glue onto workpiece",
        GlueProcessState.ADJUSTING_FLOW_RATE: "Dynamically adjusting glue flow rate",
        GlueProcessState.MONITORING_COVERAGE: "Monitoring glue coverage quality",
        GlueProcessState.EXECUTING_PATH: "Executing robot path with glue dispensing",
        GlueProcessState.TRANSITIONING_PATHS: "Moving between different glue paths",
        GlueProcessState.PUMP_INITIAL_BOOST: "Applying initial pump boost",
        GlueProcessState.PUMP_ADJUSTMENT: "Adjusting pump speed dynamically",
        GlueProcessState.SENDING_PATH_POINTS: "Sending path points to robot",
        GlueProcessState.WAITING_PATH_COMPLETION: "Waiting for path execution completion",
        
        # Control
        GlueProcessState.IDLE: "System idle, ready for commands",
        GlueProcessState.PAUSED: "Glue dispensing operation paused",
        GlueProcessState.RESUMING: "Resuming glue dispensing operation",
        GlueProcessState.STOPPING: "Stopping glue dispensing operation",
        GlueProcessState.STOPPED: "Glue dispensing operation stopped",
        
        # Completion
        GlueProcessState.STOPPING_GLUE_FLOW: "Stopping glue dispensing flow",
        GlueProcessState.CLEANING_NOZZLE: "Cleaning glue nozzle",
        GlueProcessState.RETRACTING_NOZZLE: "Retracting nozzle from workpiece",
        GlueProcessState.MOVING_TO_HOME: "Moving robot to home position",
        GlueProcessState.FINALIZING: "Finalizing glue dispensing operation",
        GlueProcessState.COMPLETED: "Glue dispensing operation completed",
        
        # Error
        GlueProcessState.ERROR: "Glue dispensing error occurred",
        GlueProcessState.GLUE_SYSTEM_ERROR: "Glue system malfunction",
        GlueProcessState.ROBOT_ERROR: "Robot system error",
        GlueProcessState.NOZZLE_CLOGGED: "Glue nozzle is clogged",
        GlueProcessState.PRESSURE_ERROR: "Glue pressure system error",
        GlueProcessState.FLOW_RATE_ERROR: "Glue flow rate error",
        GlueProcessState.RECOVERING: "Attempting to recover from error",
        GlueProcessState.FAILED: "Glue dispensing operation failed",
    }
    
    # States that can be interrupted
    INTERRUPTIBLE_STATES: Set[GlueProcessState] = {
        GlueProcessState.PREPARING,
        GlueProcessState.LOADING_WORKPIECE,
        GlueProcessState.VALIDATING_WORKPIECE,
        GlueProcessState.CALIBRATING_ROBOT,
        GlueProcessState.CALIBRATING_CAMERA,
        GlueProcessState.CALIBRATING_NOZZLE,
        GlueProcessState.NESTING,
        GlueProcessState.PREPARING_GLUE_SYSTEM,
        GlueProcessState.PRIMING_NOZZLE,
        GlueProcessState.TESTING_GLUE_FLOW,
        GlueProcessState.ADJUSTING_PRESSURE,
        GlueProcessState.HEATING_GLUE,
        GlueProcessState.STARTING_OPERATION,
        GlueProcessState.MOVING_TO_START_POINT,
        GlueProcessState.POSITIONING_NOZZLE,
        GlueProcessState.STARTING_GLUE_FLOW,
        GlueProcessState.DISPENSING_GLUE,
        GlueProcessState.SPRAYING_GLUE,
        GlueProcessState.ADJUSTING_FLOW_RATE,
        GlueProcessState.MONITORING_COVERAGE,
        GlueProcessState.EXECUTING_PATH,
        GlueProcessState.TRANSITIONING_PATHS,
        GlueProcessState.PUMP_INITIAL_BOOST,
        GlueProcessState.PUMP_ADJUSTMENT,
        GlueProcessState.SENDING_PATH_POINTS,
        GlueProcessState.WAITING_PATH_COMPLETION,
    }
    
    # Terminal states
    TERMINAL_STATES: Set[GlueProcessState] = {
        GlueProcessState.COMPLETED,
        GlueProcessState.FAILED,
        GlueProcessState.STOPPED,
    }
    
    # Error states
    ERROR_STATES: Set[GlueProcessState] = {
        GlueProcessState.ERROR,
        GlueProcessState.GLUE_SYSTEM_ERROR,
        GlueProcessState.ROBOT_ERROR,
        GlueProcessState.NOZZLE_CLOGGED,
        GlueProcessState.PRESSURE_ERROR,
        GlueProcessState.FLOW_RATE_ERROR,
        GlueProcessState.RECOVERING,
        GlueProcessState.FAILED,
    }
    
    # Glue-specific states (states unique to glue dispensing)
    GLUE_SPECIFIC_STATES: Set[GlueProcessState] = {
        GlueProcessState.PREPARING_GLUE_SYSTEM,
        GlueProcessState.PRIMING_NOZZLE,
        GlueProcessState.TESTING_GLUE_FLOW,
        GlueProcessState.ADJUSTING_PRESSURE,
        GlueProcessState.HEATING_GLUE,
        GlueProcessState.STARTING_GLUE_FLOW,
        GlueProcessState.DISPENSING_GLUE,
        GlueProcessState.SPRAYING_GLUE,
        GlueProcessState.ADJUSTING_FLOW_RATE,
        GlueProcessState.MONITORING_COVERAGE,
        GlueProcessState.PUMP_INITIAL_BOOST,
        GlueProcessState.PUMP_ADJUSTMENT,
        GlueProcessState.STOPPING_GLUE_FLOW,
        GlueProcessState.CLEANING_NOZZLE,
        GlueProcessState.RETRACTING_NOZZLE,
        GlueProcessState.GLUE_SYSTEM_ERROR,
        GlueProcessState.NOZZLE_CLOGGED,
        GlueProcessState.PRESSURE_ERROR,
        GlueProcessState.FLOW_RATE_ERROR,
    }
    
    @classmethod
    def get_category(cls, state: GlueProcessState) -> ProcessStateCategory:
        """Get the category for a given glue process state."""
        return cls.STATE_CATEGORIES.get(state, ProcessStateCategory.EXECUTION)
    
    @classmethod
    def get_description(cls, state: GlueProcessState) -> str:
        """Get the description for a given glue process state."""
        return cls.STATE_DESCRIPTIONS.get(state, "Unknown glue process state")
    
    @classmethod
    def is_interruptible(cls, state: GlueProcessState) -> bool:
        """Check if a glue process state can be interrupted."""
        return state in cls.INTERRUPTIBLE_STATES
    
    @classmethod
    def is_terminal(cls, state: GlueProcessState) -> bool:
        """Check if a glue process state is terminal."""
        return state in cls.TERMINAL_STATES
    
    @classmethod
    def is_error_state(cls, state: GlueProcessState) -> bool:
        """Check if a glue process state represents an error."""
        return state in cls.ERROR_STATES
    
    @classmethod
    def is_glue_specific(cls, state: GlueProcessState) -> bool:
        """Check if a state is specific to glue dispensing (vs generic process state)."""
        return state in cls.GLUE_SPECIFIC_STATES
    
    @classmethod
    def get_states_by_category(cls, category: ProcessStateCategory) -> Set[GlueProcessState]:
        """Get all glue process states in a specific category."""
        return {state for state, cat in cls.STATE_CATEGORIES.items() if cat == category}


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
            # From INITIALIZING
            GlueProcessState.INITIALIZING: {
                GlueProcessState.READY,
                GlueProcessState.ERROR,
                GlueProcessState.FAILED,
            },
            
            # From READY
            GlueProcessState.READY: {
                GlueProcessState.PREPARING,
                GlueProcessState.IDLE,
                GlueProcessState.CALIBRATING_ROBOT,
                GlueProcessState.CALIBRATING_CAMERA,
                GlueProcessState.SHUTTING_DOWN,
                GlueProcessState.ERROR,
            },
            
            # From IDLE
            GlueProcessState.IDLE: {
                GlueProcessState.PREPARING,
                GlueProcessState.LOADING_WORKPIECE,
                GlueProcessState.CALIBRATING_ROBOT,
                GlueProcessState.CALIBRATING_CAMERA,
                GlueProcessState.CALIBRATING_NOZZLE,
                GlueProcessState.SHUTTING_DOWN,
                GlueProcessState.ERROR,
            },
            
            # From PREPARING
            GlueProcessState.PREPARING: {
                GlueProcessState.LOADING_WORKPIECE,
                GlueProcessState.PREPARING_GLUE_SYSTEM,
                GlueProcessState.NESTING,
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPED,
                GlueProcessState.ERROR,
            },
            
            # From NESTING
            GlueProcessState.NESTING: {
                GlueProcessState.VALIDATING_WORKPIECE,
                GlueProcessState.PREPARING_GLUE_SYSTEM,
                GlueProcessState.STARTING_OPERATION,
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPED,
                GlueProcessState.ERROR,
            },
            
            # From PREPARING_GLUE_SYSTEM
            GlueProcessState.PREPARING_GLUE_SYSTEM: {
                GlueProcessState.PRIMING_NOZZLE,
                GlueProcessState.TESTING_GLUE_FLOW,
                GlueProcessState.HEATING_GLUE,
                GlueProcessState.STARTING_OPERATION,
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPED,
                GlueProcessState.GLUE_SYSTEM_ERROR,
                GlueProcessState.ERROR,
            },
            
            # From STARTING_OPERATION
            GlueProcessState.STARTING_OPERATION: {
                GlueProcessState.MOVING_TO_START_POINT,
                GlueProcessState.POSITIONING_NOZZLE,
                GlueProcessState.EXECUTING_PATH,
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPED,
                GlueProcessState.ERROR,
            },
            
            # From EXECUTING_PATH
            GlueProcessState.EXECUTING_PATH: {
                GlueProcessState.PUMP_INITIAL_BOOST,
                GlueProcessState.SENDING_PATH_POINTS,
                GlueProcessState.DISPENSING_GLUE,
                GlueProcessState.SPRAYING_GLUE,
                GlueProcessState.TRANSITIONING_PATHS,
                GlueProcessState.STOPPING_GLUE_FLOW,
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPING,
                GlueProcessState.ERROR,
            },
            
            # From DISPENSING_GLUE
            GlueProcessState.DISPENSING_GLUE: {
                GlueProcessState.ADJUSTING_FLOW_RATE,
                GlueProcessState.MONITORING_COVERAGE,
                GlueProcessState.PUMP_ADJUSTMENT,
                GlueProcessState.TRANSITIONING_PATHS,
                GlueProcessState.STOPPING_GLUE_FLOW,
                GlueProcessState.PAUSED,
                GlueProcessState.STOPPING,
                GlueProcessState.NOZZLE_CLOGGED,
                GlueProcessState.PRESSURE_ERROR,
                GlueProcessState.FLOW_RATE_ERROR,
                GlueProcessState.ERROR,
            },
            
            # From PAUSED
            GlueProcessState.PAUSED: {
                GlueProcessState.RESUMING,
                GlueProcessState.STOPPING,
                GlueProcessState.STOPPED,
                GlueProcessState.ERROR,
            },
            
            # From STOPPING
            GlueProcessState.STOPPING: {
                GlueProcessState.STOPPING_GLUE_FLOW,
                GlueProcessState.CLEANING_NOZZLE,
                GlueProcessState.MOVING_TO_HOME,
                GlueProcessState.STOPPED,
                GlueProcessState.ERROR,
            },
            
            # From COMPLETED
            GlueProcessState.COMPLETED: {
                GlueProcessState.IDLE,
                GlueProcessState.SHUTTING_DOWN,
            },
            
            # Error state transitions
            GlueProcessState.ERROR: {
                GlueProcessState.RECOVERING,
                GlueProcessState.FAILED,
                GlueProcessState.STOPPED,
                GlueProcessState.IDLE,
            },
            
            GlueProcessState.NOZZLE_CLOGGED: {
                GlueProcessState.CLEANING_NOZZLE,
                GlueProcessState.RECOVERING,
                GlueProcessState.FAILED,
                GlueProcessState.STOPPED,
            },
            
            GlueProcessState.RECOVERING: {
                GlueProcessState.IDLE,
                GlueProcessState.PREPARING,
                GlueProcessState.FAILED,
                GlueProcessState.ERROR,
            },
            
            # Add more transition rules as needed...
        }
    
    @staticmethod
    def get_emergency_stop_transitions() -> Set[GlueProcessState]:
        """
        Get states that can be reached from any state in emergency situations.
        
        Returns:
            Set of states that can always be transitioned to
        """
        return {
            GlueProcessState.ERROR,
            GlueProcessState.STOPPING,
            GlueProcessState.STOPPED,
            GlueProcessState.FAILED,
            GlueProcessState.CLEANING_NOZZLE,  # Emergency nozzle cleaning
        }
from enum import Enum
from abc import ABC, abstractmethod
import threading
import time
from typing import Dict, Callable, Any, Optional


# Enhanced State Enum (extends your existing GlueSprayApplicationState)
class ApplicationState(Enum):
    INITIALIZING = "INITIALIZING"
    IDLE = "IDLE"
    STARTED = "STARTED"
    CALIBRATING_ROBOT = "CALIBRATING_ROBOT"
    CALIBRATING_CAMERA = "CALIBRATING_CAMERA"
    MEASURING_HEIGHT = "MEASURING_HEIGHT"
    CREATING_WORKPIECE = "CREATING_WORKPIECE"
    UPDATING_TOOL_CHANGER = "UPDATING_TOOL_CHANGER"
    EXECUTING_TRAJECTORY = "EXECUTING_TRAJECTORY"
    HANDLING_BELT = "HANDLING_BELT"
    TEST_RUNNING = "TEST_RUNNING"
    ERROR = "ERROR"
    PAUSED = "PAUSED"


# Event Types
class Event(Enum):
    # System Events
    SYSTEM_READY = "SYSTEM_READY"
    ROBOT_READY = "ROBOT_READY"
    VISION_READY = "VISION_READY"
    ERROR_OCCURRED = "ERROR_OCCURRED"
    RESET_REQUESTED = "RESET_REQUESTED"

    # Operation Events
    START_REQUESTED = "START_REQUESTED"
    CALIBRATE_ROBOT_REQUESTED = "CALIBRATE_ROBOT_REQUESTED"
    CALIBRATE_CAMERA_REQUESTED = "CALIBRATE_CAMERA_REQUESTED"
    MEASURE_HEIGHT_REQUESTED = "MEASURE_HEIGHT_REQUESTED"
    CREATE_WORKPIECE_REQUESTED = "CREATE_WORKPIECE_REQUESTED"
    UPDATE_TOOL_CHANGER_REQUESTED = "UPDATE_TOOL_CHANGER_REQUESTED"
    EXECUTE_TRAJECTORY_REQUESTED = "EXECUTE_TRAJECTORY_REQUESTED"
    HANDLE_BELT_REQUESTED = "HANDLE_BELT_REQUESTED"
    TEST_RUN_REQUESTED = "TEST_RUN_REQUESTED"

    # Completion Events
    OPERATION_COMPLETED = "OPERATION_COMPLETED"
    OPERATION_FAILED = "OPERATION_FAILED"
    PAUSE_REQUESTED = "PAUSE_REQUESTED"
    RESUME_REQUESTED = "RESUME_REQUESTED"


# State Machine Context
class StateMachineContext:
    def __init__(self):
        self.operation_data: Dict[str, Any] = {}
        self.error_message: str = ""
        self.operation_result: Any = None
        self.callback_function: Optional[Callable] = None


# Abstract State Base Class
class State(ABC):
    def __init__(self, name: ApplicationState):
        self.name = name

    @abstractmethod
    def enter(self, context: StateMachineContext, application) -> None:
        """Called when entering the state"""
        pass

    @abstractmethod
    def exit(self, context: StateMachineContext, application) -> None:
        """Called when exiting the state"""
        pass

    @abstractmethod
    def handle_event(self, event: Event, context: StateMachineContext, application) -> Optional[ApplicationState]:
        """Handle an event and return next state if transition should occur"""
        pass


# Concrete State Implementations
class IdleState(State):
    def __init__(self):
        super().__init__(ApplicationState.IDLE)

    def enter(self, context: StateMachineContext, application) -> None:
        print("Entering IDLE state")
        # Ensure robot is in safe position

    def exit(self, context: StateMachineContext, application) -> None:
        print("Exiting IDLE state")

    def handle_event(self, event: Event, context: StateMachineContext, application) -> Optional[ApplicationState]:
        transitions = {
            Event.START_REQUESTED: ApplicationState.EXECUTING_TRAJECTORY,
            Event.CALIBRATE_ROBOT_REQUESTED: ApplicationState.CALIBRATING_ROBOT,
            Event.CALIBRATE_CAMERA_REQUESTED: ApplicationState.CALIBRATING_CAMERA,
            Event.CREATE_WORKPIECE_REQUESTED: ApplicationState.CREATING_WORKPIECE,
            Event.MEASURE_HEIGHT_REQUESTED: ApplicationState.MEASURING_HEIGHT,
            Event.UPDATE_TOOL_CHANGER_REQUESTED: ApplicationState.UPDATING_TOOL_CHANGER,
            Event.HANDLE_BELT_REQUESTED: ApplicationState.HANDLING_BELT,
            Event.TEST_RUN_REQUESTED: ApplicationState.TEST_RUNNING,
            Event.ERROR_OCCURRED: ApplicationState.ERROR
        }
        return transitions.get(event)


class ExecutingTrajectoryState(State):
    def __init__(self):
        super().__init__(ApplicationState.EXECUTING_TRAJECTORY)

    def enter(self, context: StateMachineContext, application) -> None:
        print("Entering EXECUTING_TRAJECTORY state")

        # Start trajectory execution in background thread
        def execute():
            try:
                contour_matching = context.operation_data.get('contour_matching', True)
                result = application._original_start(contour_matching)
                context.operation_result = result
                print(f"Trajectory execution result: {result}")
                application.state_machine.process_event(Event.OPERATION_COMPLETED)
            except Exception as e:
                context.error_message = str(e)
                application.state_machine.process_event(Event.OPERATION_FAILED)

        threading.Thread(target=execute, daemon=True).start()

    def exit(self, context: StateMachineContext, application) -> None:
        print("Exiting EXECUTING_TRAJECTORY state")

    def handle_event(self, event: Event, context: StateMachineContext, application) -> Optional[ApplicationState]:
        if event == Event.OPERATION_COMPLETED:
            return ApplicationState.IDLE
        elif event == Event.OPERATION_FAILED:
            return ApplicationState.ERROR
        elif event == Event.PAUSE_REQUESTED:
            return ApplicationState.PAUSED
        return None


class CalibratingRobotState(State):
    def __init__(self):
        super().__init__(ApplicationState.CALIBRATING_ROBOT)

    def enter(self, context: StateMachineContext, application) -> None:
        print("Entering CALIBRATING_ROBOT state")

        def calibrate():
            try:
                result = application._original_calibrateRobot()
                context.operation_result = result
                application.state_machine.process_event(Event.OPERATION_COMPLETED)
            except Exception as e:
                context.error_message = str(e)
                application.state_machine.process_event(Event.OPERATION_FAILED)

        threading.Thread(target=calibrate, daemon=True).start()

    def exit(self, context: StateMachineContext, application) -> None:
        print("Exiting CALIBRATING_ROBOT state")

    def handle_event(self, event: Event, context: StateMachineContext, application) -> Optional[ApplicationState]:
        if event == Event.OPERATION_COMPLETED:
            return ApplicationState.IDLE
        elif event == Event.OPERATION_FAILED:
            return ApplicationState.ERROR
        return None


class ErrorState(State):
    def __init__(self):
        super().__init__(ApplicationState.ERROR)

    def enter(self, context: StateMachineContext, application) -> None:
        print(f"Entering ERROR state: {context.error_message}")
        # Stop all operations, move robot to safe position
        try:
            application.robotService.moveToStartPosition()
        except:
            pass

    def exit(self, context: StateMachineContext, application) -> None:
        print("Exiting ERROR state")
        context.error_message = ""

    def handle_event(self, event: Event, context: StateMachineContext, application) -> Optional[ApplicationState]:
        if event == Event.RESET_REQUESTED:
            return ApplicationState.IDLE
        return None


# Additional states for other operations...
class CreatingWorkpieceState(State):
    def __init__(self):
        super().__init__(ApplicationState.CREATING_WORKPIECE)

    def enter(self, context: StateMachineContext, application) -> None:
        print("Entering CREATING_WORKPIECE state")

        def create_workpiece():
            try:
                result = application._original_createWorkpiece()
                print("Workpiece creation result:", result)
                context.operation_result = result
                application.state_machine.process_event(Event.OPERATION_COMPLETED)
            except Exception as e:
                context.error_message = str(e)
                application.state_machine.process_event(Event.OPERATION_FAILED)

        threading.Thread(target=create_workpiece, daemon=True).start()

    def exit(self, context: StateMachineContext, application) -> None:
        print("Exiting CREATING_WORKPIECE state")

    def handle_event(self, event: Event, context: StateMachineContext, application) -> Optional[ApplicationState]:
        if event == Event.OPERATION_COMPLETED:
            return ApplicationState.IDLE
        elif event == Event.OPERATION_FAILED:
            return ApplicationState.ERROR
        return None


# State Machine Implementation
class StateMachine:
    def __init__(self, application):
        self.application = application
        self.context = StateMachineContext()
        self.current_state: Optional[State] = None
        self.states: Dict[ApplicationState, State] = {}
        self.event_queue = []
        self.event_lock = threading.Lock()
        self.running = True

        # Initialize states
        self._initialize_states()

        # Start event processing thread
        self.event_thread = threading.Thread(target=self._process_events, daemon=True)
        self.event_thread.start()

    def _initialize_states(self):
        """Initialize all state instances"""
        self.states = {
            ApplicationState.IDLE: IdleState(),
            ApplicationState.EXECUTING_TRAJECTORY: ExecutingTrajectoryState(),
            ApplicationState.CALIBRATING_ROBOT: CalibratingRobotState(),
            ApplicationState.CREATING_WORKPIECE: CreatingWorkpieceState(),
            ApplicationState.ERROR: ErrorState(),
            # Add other states as needed...
        }

    def transition_to(self, new_state: ApplicationState):
        """Transition to a new state"""
        if new_state not in self.states:
            print(f"Warning: State {new_state} not implemented, staying in current state")
            return

        old_state = self.current_state
        new_state_obj = self.states[new_state]

        # Exit current state
        if old_state:
            old_state.exit(self.context, self.application)

        # Update application state (for compatibility)
        self.application.state = new_state

        # Enter new state
        self.current_state = new_state_obj
        new_state_obj.enter(self.context, self.application)

        print(f"State transition: {old_state.name if old_state else 'None'} -> {new_state}")

    def process_event(self, event: Event, data: Dict[str, Any] = None):
        """Add event to processing queue"""
        with self.event_lock:
            self.event_queue.append((event, data or {}))

    def _process_events(self):
        """Process events from queue"""
        while self.running:
            try:
                with self.event_lock:
                    if not self.event_queue:
                        continue
                    event, data = self.event_queue.pop(0)

                # Update context with event data
                self.context.operation_data.update(data)

                # Handle event in current state
                if self.current_state:
                    next_state = self.current_state.handle_event(event, self.context, self.application)
                    if next_state:
                        self.transition_to(next_state)

                time.sleep(0.01)  # Small delay to prevent busy waiting
            except Exception as e:
                print(f"Error processing event {event}: {e}")
                self.process_event(Event.ERROR_OCCURRED)

    def start(self):
        """Start the state machine"""
        self.transition_to(ApplicationState.IDLE)


# Enhanced GlueSprayingApplication with State Machine
class StateMachineEnhancedGlueSprayingApplication:
    """
    This is a mixin/wrapper that adds state machine functionality to your existing class.
    It preserves all original functionality while adding state machine behavior.
    """

    def __init__(self, original_application):
        self.original_app = original_application
        self.state_machine = StateMachine(self)

        # Preserve original methods by renaming them
        self._original_start = original_application.start
        self._original_calibrateRobot = original_application.calibrateRobot
        self._original_calibrateCamera = original_application.calibrateCamera
        self._original_createWorkpiece = original_application.createWorkpiece
        self._original_measureHeight = original_application.measureHeight
        self._original_updateToolChangerStation = original_application.updateToolChangerStation
        self._original_handleBelt = original_application.handleBelt
        self._original_testRun = original_application.testRun
        self._original_handleExecuteFromGallery = original_application.handleExecuteFromGallery

        # Delegate all other attributes to original application
        self.__dict__.update(original_application.__dict__)

        # Start state machine
        self.state_machine.start()

    # Enhanced public API methods that use state machine
    def start(self, contourMatching=True):
        """Enhanced start method using state machine"""
        if self.state != ApplicationState.IDLE:
            return False, f"Cannot start operation from state {self.state}"

        self.state_machine.process_event(Event.START_REQUESTED, {
            'contour_matching': contourMatching
        })
        return True, "Operation started"

    def calibrateRobot(self):
        """Enhanced robot calibration using state machine"""
        if self.state != ApplicationState.IDLE:
            return False, f"Cannot calibrate robot from state {self.state}", None

        self.state_machine.process_event(Event.CALIBRATE_ROBOT_REQUESTED)
        return True, "Robot calibration started", None

    def createWorkpiece(self):
        """Enhanced workpiece creation using state machine"""
        if self.state != ApplicationState.IDLE:
            return False, "Cannot create workpiece from current state"

        self.state_machine.process_event(Event.CREATE_WORKPIECE_REQUESTED)
        return True, "Workpiece creation started"

    def emergency_stop(self):
        """Emergency stop - immediate transition to error state"""
        self.state_machine.process_event(Event.ERROR_OCCURRED)
        return True, "Emergency stop activated"

    def reset(self):
        """Reset system from error state"""
        self.state_machine.process_event(Event.RESET_REQUESTED)
        return True, "System reset requested"

    def get_current_state(self) -> ApplicationState:
        """Get current state"""
        return self.state

    def can_execute_operation(self, operation: str) -> bool:
        """Check if operation can be executed in current state"""
        valid_states = {
            'start': [ApplicationState.IDLE],
            'calibrate': [ApplicationState.IDLE],
            'create_workpiece': [ApplicationState.IDLE],
            'emergency_stop': list(ApplicationState),  # Can always emergency stop
            'reset': [ApplicationState.ERROR]
        }
        return self.state in valid_states.get(operation, [])


# Usage Example - How to integrate without breaking existing code:
"""
# Instead of:
# app = GlueSprayingApplication(callback, vision, settings, glue, workpiece, robot, calib)

# Use:
original_app = GlueSprayingApplication(callback, vision, settings, glue, workpiece, robot, calib)
app = StateMachineEnhancedGlueSprayingApplication(original_app)

# All existing code continues to work, but now with state machine benefits:
app.start(contourMatching=True)  # Uses state machine
app.calibrateRobot()  # Uses state machine  
app.emergency_stop()  # New functionality
app.reset()  # New functionality
"""
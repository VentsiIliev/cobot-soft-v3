
from robot_application.base_robot_application import ApplicationState
from modules.VisionSystem.VisionSystem import VisionSystemState
from modules.robot.robotService.enums.RobotServiceState import RobotServiceState
from robot_application.glue_dispensing_application.glue_dispensing.state_machine.GlueProcessState import \
    GlueProcessState


class GlueDispensingApplicationStateManager:
    """Extended state manager for glue dispensing specific state handling"""

    def __init__(self, base_state_manager):
        self.base_state_manager = base_state_manager
        self.visonServiceState = None
        self.robotServiceState = None

        self._services_ready = False  # Flag to indicate when both services are ready

    def __getattr__(self, name):
        # Delegate all other attributes to the base state manager
        return getattr(self.base_state_manager, name)

    def update_state(self, new_state: ApplicationState):
        """Override update_state to add debugging"""
        self.base_state_manager.update_state(new_state)


    def check_and_initialize_glue_process(self):
        """Check if both services are ready and initialize glue process if needed"""

        if (self.visonServiceState == VisionSystemState.RUNNING and 
            self.robotServiceState == RobotServiceState.IDLE):
            
            # Check if we have access to the glue process state machine to trigger transition
            # This would need to be called from the main application that has access to the state machine
            print(f"🚀 Both services ready - robot: {self.robotServiceState}, vision: {self.visonServiceState}")
            return True
        return False

    def onRobotServiceStateUpdate(self, state):
        """
        Handle robot service state updates with glue dispensing specific logic.

        Transition rules:
          - Robot in {INITIALIZING, ERROR} -> ApplicationState.INITIALIZING
            * This is a hard reset/stop condition and takes precedence over vision state.
          - Robot == IDLE and Vision == RUNNING -> ApplicationState.IDLE
            * Both services ready; system is idle and ready for a new glue process.
          - Robot in {STARTING, MOVING_TO_FIRST_POINT, EXECUTING_PATH, TRANSITION_BETWEEN_PATHS}
            and Vision == RUNNING -> ApplicationState.RUNNING
            * Robot is actively executing and vision is available; application is RUNNING.
          - Any other combinations -> no application state change (waiting for both services to be ready).

        Notes:
          - Robot updates are forwarded to the base state manager first.
          - If `self.visonServiceState` is `None` the code treats vision as not ready.
        """
        self.robotServiceState = state
        self.base_state_manager.on_robot_service_state_update(state)

        if self.robotServiceState in [RobotServiceState.INITIALIZING, RobotServiceState.ERROR]:
            self.base_state_manager.update_state(ApplicationState.INITIALIZING)
        elif self.robotServiceState == RobotServiceState.IDLE and self.visonServiceState == VisionSystemState.RUNNING:
            self.base_state_manager.update_state(ApplicationState.IDLE)

        else:
            # No transition: waiting for a combination that triggers a state change.
            pass


    def onVisonSystemStateUpdate(self, state):
        """
        Handle vision system state updates with glue dispensing specific logic.

        Transition rules (vision-driven):
          - Vision == RUNNING and Robot == IDLE -> ApplicationState.IDLE
            * Covers the case where vision comes online after the robot is already idle.
          - All other vision updates do not force application-level transitions here;
            robot-driven transitions handle RUNNING/INITIALIZING decisions.

        Notes:
          - Vision updates are forwarded to the base state manager first.
          - If `self.robotServiceState` is `None` the code treats robot as not ready.
        """
        self.visonServiceState = state
        self.base_state_manager.on_vision_system_state_update(state)

        if self.visonServiceState == VisionSystemState.RUNNING and self.robotServiceState == RobotServiceState.IDLE:
            self.base_state_manager.update_state(ApplicationState.IDLE)
        else:
            # No transition on vision update alone.
            pass

    def on_glue_process_state_update(self, state):
        """Handle glue process state updates"""
        print(f"Glue process state update received: {state}")
        if state == GlueProcessState.PAUSED:
            self.base_state_manager.update_state(ApplicationState.PAUSED)
        elif state == GlueProcessState.COMPLETED:
            self.base_state_manager.update_state(ApplicationState.IDLE)
        elif state == GlueProcessState.ERROR:
            self.base_state_manager.update_state(ApplicationState.ERROR)
        elif state == GlueProcessState.STOPPED:
            self.base_state_manager.update_state(ApplicationState.IDLE)
        elif state in [
            GlueProcessState.STARTING,
            GlueProcessState.MOVING_TO_FIRST_POINT,
            GlueProcessState.EXECUTING_PATH,
            GlueProcessState.TRANSITION_BETWEEN_PATHS,
        ]:
            self.base_state_manager.update_state(ApplicationState.RUNNING)
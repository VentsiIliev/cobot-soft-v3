from modules.VisionSystem.VisionSystem import VisionSystemState
from src.backend.robot_application.base_robot_application import ApplicationState
from src.backend.system.robot.robotService.enums.RobotServiceState import RobotServiceState


class GlueDispensingApplicationStateManager:
    """Extended state manager for glue dispensing specific state handling"""

    def __init__(self, base_state_manager):
        self.base_state_manager = base_state_manager
        self.visonServiceState = None
        self.robotServiceState = None

    def __getattr__(self, name):
        # Delegate all other attributes to the base state manager
        return getattr(self.base_state_manager, name)

    def onRobotServiceStateUpdate(self, state):
        """Handle robot service state updates with glue dispensing specific logic"""
        # print(f"[GlueDispensingStateManager] Robot service state: {state}, Vision state: {self.visonServiceState}")
        self.robotServiceState = state
        self.base_state_manager.on_robot_service_state_update(state)

        # Map robot service states to application states
        if self.robotServiceState in [RobotServiceState.INITIALIZING, RobotServiceState.ERROR]:
            # print(f"[GlueDispensingStateManager] Setting app state to INITIALIZING")
            self.base_state_manager.update_state(ApplicationState.INITIALIZING)
        elif self.robotServiceState == RobotServiceState.IDLE and self.visonServiceState == VisionSystemState.RUNNING:
            # print(f"[GlueDispensingStateManager] Both services ready - Setting app state to IDLE")
            self.base_state_manager.update_state(ApplicationState.IDLE)
        elif self.robotServiceState in [RobotServiceState.STARTING, RobotServiceState.MOVING_TO_FIRST_POINT,
                                        RobotServiceState.EXECUTING_PATH,
                                        RobotServiceState.TRANSITION_BETWEEN_PATHS] and self.visonServiceState == VisionSystemState.RUNNING:
            # print(f"[GlueDispensingStateManager] Robot active and vision ready - Setting app state to RUNNING")
            self.base_state_manager.update_state(ApplicationState.RUNNING)
        else:
            pass
            # print(f"[GlueDispensingStateManager] Staying in current state - waiting for both services to be ready")

    def onVisonSystemStateUpdate(self, state):
        """Handle vision system state updates with glue dispensing specific logic"""
        # print(f"[GlueDispensingStateManager] Vision system state: {state}, Robot state: {self.robotServiceState}")
        self.visonServiceState = state
        self.base_state_manager.on_vision_system_state_update(state)

        if self.visonServiceState == VisionSystemState.RUNNING and self.robotServiceState == RobotServiceState.IDLE:
            # print(f"[GlueDispensingStateManager] Both services ready (via vision update) - Setting app state to IDLE")
            self.base_state_manager.update_state(ApplicationState.IDLE)
        else:
            # print(f"[GlueDispensingStateManager] Vision update - staying in current state")
            pass

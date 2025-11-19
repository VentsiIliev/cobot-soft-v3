from core.services.robot_service.impl.robot_monitor.state_manager import BaseRobotServiceStateManager


class GlueRobotServiceStateManager(BaseRobotServiceStateManager):
    def __init__(self, initial_state, message_publisher, robot_service):
        super().__init__(initial_state, message_publisher, robot_service)

    def on_glue_process_state_update(self, state):
        print(f"Glue process state update received: {state}")
        self.update_state(state)
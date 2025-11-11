from src.backend.system.SystemStatePublisherThread import SystemStatePublisherThread
from src.backend.system.robot.robotService.enums.RobotServiceState import RobotServiceState
from src.backend.system.robot.robotService.enums.RobotState import RobotState


class RobotServiceStateManager:
    def __init__(self,initial_state,message_publisher,robot_service):
        self.state = initial_state
        self.robot_service = robot_service
        self.message_publisher = message_publisher
        self.system_state_publisher = None
        self._last_state = None

    def update_state(self,new_state):
        if self.state != new_state:
            self.state = new_state
            self.publish_state()
            # NOTE: Do not force the state's authoritative machine here.
            # The RobotStateMachine is the single source of truth for transitions.
            # Removing the unconditional transition to IDLE fixes cases where
            # published glue-process state updates (e.g. PAUSED/STARTING during resume)
            # immediately forced the machine back to IDLE and prevented resume.

    def publish_state(self):
        try:
            if True:
                self.message_publisher.publish_state(self.state)
                self._last_state = self.state
        except Exception as e:
            import traceback
            traceback.print_exc()

    def start_state_publisher_thread(self):
        self.system_state_publisher = SystemStatePublisherThread(publish_state_func=self.publish_state, interval=0.1)
        self.system_state_publisher.start()

    def stop_state_publisher_thread(self):
        if self.system_state_publisher:
            self.system_state_publisher.stop()
            self.system_state_publisher.join()

    def onRobotStateUpdate(self, state):
        """Handle robot physical state updates"""
        robotState = state['state']

        # Transition to IDLE when robot becomes stationary and ready
        if (self.robot_service.state_machine.state == RobotServiceState.INITIALIZING and
                robotState == RobotState.STATIONARY):
            # Update manager internal state and publish
            self.update_state(RobotServiceState.IDLE)
            # Explicitly transition the authoritative state machine to IDLE
            try:
                self.robot_service.state_machine.transition(RobotServiceState.IDLE)
            except Exception:
                # Don't crash on transition errors; just log if available
                print("RobotServiceStateManager: Failed to transition state machine to IDLE")

    def on_glue_process_state_update(self,state):
        print(f"Glue process state update received: {state}")
        self.update_state(state)

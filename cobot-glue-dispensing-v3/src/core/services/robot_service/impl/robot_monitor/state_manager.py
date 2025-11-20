from backend.system.SystemStatePublisherThread import SystemStatePublisherThread
from core.services.robot_service.enums.RobotState import RobotState
from core.system_state_management import ServiceStateMessage, ServiceState


class BaseRobotServiceStateManager:
    def __init__(self,initial_state,message_publisher,robot_service,service_id):
        self.state = initial_state
        self.service_id = service_id
        self.robot_service = robot_service
        self.message_publisher = message_publisher
        self.system_state_publisher = None
        self._last_state = None

    def update_state(self,new_state):
        if self.state != new_state:
            self.state = new_state

            # NOTE: Do not force the state's authoritative machine here.
            # The RobotStateMachine is the single source of truth for transitions.
            # Removing the unconditional transition to IDLE fixes cases where
            # published glue-process state updates (e.g. PAUSED/STARTING during resume)
            # immediately forced the machine back to IDLE and prevented resume.

    def publish_state(self):
        try:
            if True:
                state = ServiceStateMessage(id=self.service_id, state=self.state).to_dict()
                # print(f"Publishing robot service state: {state}")
                self.message_publisher.publish_state(state)
                self._last_state = self.state
        except Exception as e:
            print(f"RobotServiceStateManager: Error publishing state: {e}")
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
        if self.state == ServiceState.INITIALIZING and robotState == RobotState.STATIONARY:
            # Update manager internal state and publish
            # print(f"Received robot state update: {robotState}, transitioning to IDLE")
            self.update_state(ServiceState.IDLE)
            self.publish_state()
            # print("[RobotServiceStateManager] -> Transitioned to IDLE state")

    def on_glue_process_state_update(self,state):
        print(f"Glue process state update received: {state}")
        self.update_state(state)



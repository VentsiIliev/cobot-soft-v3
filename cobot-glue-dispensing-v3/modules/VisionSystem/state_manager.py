from modules.shared.MessageBroker import MessageBroker
from backend.system.SystemStatePublisherThread import SystemStatePublisherThread
from backend.system.utils.custom_logging import log_if_enabled, LoggingLevel


class StateManager:
    def __init__(self,initial_state,message_publisher,log_enabled,logger):
        self.state = initial_state
        self.message_publisher = message_publisher
        self.log_enabled = log_enabled
        self.logger = logger
        self.system_state_publisher = None
        self._last_state = None


    def update_state(self,new_state):
        if self.state != new_state:
            self.state = new_state
            self.publishState()

    def publishState(self):
        # print(f"    VisionSystem: Publishing state:", self.state)
        try:
            if True:
                # print(f"    VisionSystem: State changed from {self._last_state} to {self.state}")
                self.message_publisher.publish_state(self.state)
                self._last_state = self.state
        except Exception as e:
            log_if_enabled(enabled=self.log_enabled,
                           logger=self.logger,
                           level=LoggingLevel.ERROR,
                           message=f"VisionSystem: Error publishing state: {e}",
                           broadcast_to_ui=False)
            import traceback
            traceback.print_exc()

    def start_state_publisher_thread(self):
        self.system_state_publisher = SystemStatePublisherThread(publish_state_func=self.publishState, interval=0.1)
        self.system_state_publisher.start()
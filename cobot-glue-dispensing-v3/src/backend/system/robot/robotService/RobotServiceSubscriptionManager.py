
class RobotServiceSubscriptionManager:
    def __init__(self,robot_service,broker):
        self.robot_service = robot_service
        self.broker = broker
        self.glue_process_state_topic = "glue-process/state"
        self.subscriptions = {}

    def subscribe_all(self):
        self.subscribe_robot_state_topic()
        self.subscribe_glue_process_state_topic()

    def subscribe_robot_state_topic(self):
        self.broker.subscribe(self.robot_service.robotStateManager.robotStateTopic, self.robot_service.state_manager.onRobotStateUpdate)
        self.subscriptions[self.robot_service.robotStateManager.robotStateTopic] = self.robot_service.state_manager.onRobotStateUpdate

    def unsubscribe_robot_state_topic(self):
        self.broker.unsubscribe(self.robot_service.robotStateManager.robotStateTopic, self.robot_service.state_manager.onRobotStateUpdate)
        if self.robot_service.robotStateManager.robotStateTopic in self.subscriptions:
            del self.subscriptions[self.robot_service.robotStateManager.robotStateTopic]


    def subscribe_glue_process_state_topic(self):
        self.broker.subscribe(self.glue_process_state_topic, self.robot_service.state_manager.on_glue_process_state_update)
        self.subscriptions[self.glue_process_state_topic] = self.robot_service.state_manager.on_glue_process_state_update
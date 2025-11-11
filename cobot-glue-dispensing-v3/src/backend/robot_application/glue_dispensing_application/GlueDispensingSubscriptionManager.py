from modules.shared.v1.topics import GlueTopics


class GlueDispensingSubscriptionManager:
    """Extended subscription manager for glue dispensing specific subscriptions"""

    def __init__(self, glue_application, base_subscription_manager):
        self.glue_application = glue_application
        self.base_subscription_manager = base_subscription_manager
        self.broker = base_subscription_manager.broker
        self.glue_specific_subscriptions = {}

    def __getattr__(self, name):
        # Delegate all other attributes to the base subscription manager
        return getattr(self.base_subscription_manager, name)

    def subscribe_all(self):
        # Subscribe to robot and vision topics with glue-specific callbacks
        self.subscribe_robot_service_topics()
        self.subscribe_vision_topics()
        # Add glue-specific subscriptions
        self.subscribe_mode_change()

    def subscribe_robot_service_topics(self):
        """Subscribe to robot service topics with glue-specific callback"""
        topic = self.glue_application.robotService.state_topic
        callback = self.glue_application.state_manager.onRobotServiceStateUpdate
        self.broker.subscribe(topic, callback)
        self.base_subscription_manager.subscriptions[topic] = callback
        print(f"Subscribed to robot service topic: {topic} with callback: {callback}")

    def subscribe_vision_topics(self):
        """Subscribe to vision service topics with glue-specific callback"""
        topic = self.glue_application.visionService.stateTopic
        callback = self.glue_application.state_manager.onVisonSystemStateUpdate
        self.broker.subscribe(topic, callback)
        self.base_subscription_manager.subscriptions[topic] = callback
        print(f"Subscribed to vision service topic: {topic} with callback: {callback}")

    def subscribe_mode_change(self):
        topic = GlueTopics.MODE_CHANGE
        callback = self.glue_application.changeMode
        self.broker.subscribe(topic, callback)
        self.glue_specific_subscriptions[topic] = callback

    def unsubscribe_all(self):
        # Unsubscribe glue-specific topics
        for topic, callback in self.glue_specific_subscriptions.items():
            self.broker.unsubscribe(topic, callback)
        self.glue_specific_subscriptions.clear()

        # Call base unsubscribe
        self.base_subscription_manager.unsubscribe_all()
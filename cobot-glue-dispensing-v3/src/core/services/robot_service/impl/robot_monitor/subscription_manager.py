# core/services/robot_service/impl/robot_monitor/subscription_manager.py
from frontend.core.services.domain import RobotService


class BaseSubscriptionManager:
    def __init__(self, robot_service: RobotService, broker):
        self.robot_service = robot_service
        self.broker = broker
        self.subscriptions = {}
        self.modules = []   # ← NEW: registered subscription modules

    # ----------------------------
    # Module support
    # ----------------------------
    def load_modules(self, modules):
        """Load subscription modules (plugins)"""
        for module in modules:
            module.register(self)
            self.modules.append(module)

    # ----------------------------
    # Core robot subscriptions
    # ----------------------------
    def subscribe_all(self):
        """Subscribe the base robot topics + all loaded modules."""
        self.subscribe_robot_state_topic()

    def subscribe_robot_state_topic(self):
        topic = self.robot_service.robot_state_manager.robotStateTopic
        callback = self.robot_service.state_manager.onRobotStateUpdate
        self._add_subscription(topic, callback)

    # ----------------------------
    # Internal subscription handling
    # ----------------------------
    def _add_subscription(self, topic, callback):
        self.broker.subscribe(topic, callback)
        self.subscriptions[topic] = callback

    def _remove_subscription(self, topic):
        if topic in self.subscriptions:
            self.broker.unsubscribe(topic, self.subscriptions[topic])
            del self.subscriptions[topic]

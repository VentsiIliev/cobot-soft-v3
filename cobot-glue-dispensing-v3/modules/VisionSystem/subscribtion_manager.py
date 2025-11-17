from modules.shared.MessageBroker import MessageBroker
from modules.shared.v1.topics import VisionTopics

class SubscriptionManager:

    def __init__(self,vision_system):
        self.vision_system = vision_system
        self.broker= MessageBroker()
        self.subscriptions = {}

    def subscribe_to_threshold_update(self):
        self.broker.subscribe(VisionTopics.THRESHOLD_REGION, self.vision_system.on_threshold_update)
        self.subscriptions[VisionTopics.THRESHOLD_REGION] = self.vision_system.on_threshold_update

    def subscribe_to_auto_brightness_toggle(self):
        # self.broker.subscribe(VisionTopics.BRIGHTNESS_REGION, self.vision_system.brightnessManager.on_brighteness_toggle)
        self.subscriptions[VisionTopics.AUTO_BRIGHTNESS] = self.vision_system.brightnessManager.on_brighteness_toggle

    def subscribe_all(self):
        self.subscribe_to_threshold_update()
        self.subscribe_to_auto_brightness_toggle()
from modules.shared.MessageBroker import MessageBroker


class SubscriptionManager:

    def __init__(self,vision_system):
        self.vision_system = vision_system
        self.broker= MessageBroker()
        self.subscriptions = {}

    def subscribe_to_threshold_update(self):
        self.broker.subscribe("vision-system/threshold", self.vision_system.on_threshold_update)
        self.subscriptions["vision-system/threshold"] = self.vision_system.on_threshold_update

    def subscribe_to_auto_brightness_toggle(self):
        self.broker.subscribe("vison-auto-brightness", self.vision_system.brightnessManager.on_brighteness_toggle)
        self.subscriptions["vison-auto-brightness"] = self.vision_system.brightnessManager.on_brighteness_toggle

    def subscribe_all(self):
        self.subscribe_to_threshold_update()
        self.subscribe_to_auto_brightness_toggle()
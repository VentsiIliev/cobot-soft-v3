from modules.shared.MessageBroker import MessageBroker
from typing import List, Tuple, Callable


class DashboardMessageManager:
    def __init__(self):
        self.broker = MessageBroker()
        self.subscriptions: List[Tuple[str, Callable]] = []

    def subscribe_glue_meter(self, meter, index: int) -> None:
        """Subscribe a glue meter to its message topics"""
        value_callback = meter.updateWidgets
        state_callback = meter.updateState

        value_topic = f"GlueMeter_{index}/VALUE"
        state_topic = f"GlueMeter_{index}/STATE"

        self.broker.subscribe(value_topic, value_callback)
        self.broker.subscribe(state_topic, state_callback)

        self.subscriptions.extend([
            (value_topic, value_callback),
            (state_topic, state_callback)
        ])

    def subscribe_trajectory_widget(self, trajectory_widget) -> None:
        """Subscribe trajectory widget to robot updates"""
        image_callback = trajectory_widget.set_image
        point_callback = trajectory_widget.update
        break_callback = lambda message: trajectory_widget.break_trajectory()
        disable_drawing_callback = trajectory_widget.disable_drawing
        enable_drawing_callback = trajectory_widget.enable_drawing

        disable_drawing_subscription = lambda message: self.on_disable_drawing(disable_drawing_callback,image_callback)
        enable_drawing_subscription = lambda message: self.on_enable_drawing(enable_drawing_callback,image_callback)
        self.broker.subscribe("robot/trajectory/updateImage", image_callback)
        self.broker.subscribe("vision-system/latest_image", image_callback)
        self.broker.subscribe("robot/trajectory/point", point_callback)
        self.broker.subscribe("robot/trajectory/break", break_callback)
        self.broker.subscribe("robot/trajectory/stop", disable_drawing_subscription)
        self.broker.subscribe("robot/trajectory/start",enable_drawing_subscription)

        self.subscriptions.extend([
            ("robot/trajectory/updateImage", image_callback),
            ("robot/trajectory/point", point_callback),
            ("robot/trajectory/break", break_callback),
            ("robot/trajectory/stop", disable_drawing_subscription),
            ("robot/trajectory/start", enable_drawing_subscription),
            ("vision-system/latest_image", image_callback)
        ])



    def on_enable_drawing(self,enable_drawing_callback,vision_update_callback):
        print("Enabling drawing and unsubscribing from vision updates")
         # Unsubscribe from vision updates to prevent interference
        if ("vision-system/latest_image", vision_update_callback) in self.subscriptions:
            self.broker.unsubscribe("vision-system/latest_image", vision_update_callback)
            print("Unsubscribed from vision-system/latest_image")
            self.subscriptions.remove(("vision-system/latest_image", vision_update_callback))
        else:
            print("No existing subscription to vision-system/latest_image found")

        enable_drawing_callback("")


    def on_disable_drawing(self,disable_drawing_callback,vision_update_callback):
        if ("vision-system/latest_image", vision_update_callback) not in self.subscriptions:
            self.broker.subscribe("vision-system/latest_image", vision_update_callback)
            self.subscriptions.append(("vision-system/latest_image", vision_update_callback))
        else:
            print("Already subscribed to vision-system/latest_image")

        disable_drawing_callback("")

    def publish_mode_change(self,mode):
        """Publish mode change to the broker"""
        self.broker.publish("glue-spray-app/mode", mode)

    def subscribe_card_container(self, card_container) -> None:
        """Subscribe card container to glue type changes"""
        # callback = card_container.selectCardByGlueType
        # self.broker.subscribe("glueType", callback)
        # self.subscriptions.append(("glueType", callback))
        pass
    def cleanup(self) -> None:
        """Unsubscribe from all topics"""
        for topic, callback in self.subscriptions:
            self.broker.unsubscribe(topic, callback)
        self.subscriptions.clear()
from modules.shared.v1.topics import VisionTopics, RobotTopics


class GlueDispensingMessagePublisher:
    """Extended message publisher for glue dispensing specific messages"""

    def __init__(self, base_publisher):
        self.base_publisher = base_publisher
        self.broker = base_publisher.broker
        self.brightness_region_topic = VisionTopics.BRIGHTNESS_REGION
        self.robot_trajectory_image_topic = RobotTopics.TRAJECTORY_UPDATE_IMAGE
        self.trajectory_start_topic = RobotTopics.TRAJECTORY_START

    def __getattr__(self, name):
        # Delegate all other attributes to the base publisher
        return getattr(self.base_publisher, name)

    def publish_brightness_region(self, region):
        self.broker.publish(self.brightness_region_topic, {"region": region})

    def publish_trajectory_image(self, image):
        self.broker.publish(self.robot_trajectory_image_topic, {"image": image})

    def publish_trajectory_start(self):
        self.broker.publish(self.trajectory_start_topic, "")



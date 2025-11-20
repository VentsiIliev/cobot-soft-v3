from communication_layer.api.v1.topics import VisionTopics
from modules.shared.MessageBroker import MessageBroker
class MessagePublisher:
    def __init__(self):
        self.broker= MessageBroker()
        self.latest_image_topic = VisionTopics.LATEST_IMAGE
        self.calibration_image_captured_topic = VisionTopics.CALIBRATION_IMAGE_CAPTURED
        self.thresh_image_topic = VisionTopics.THRESHOLD_IMAGE
        self.stateTopic = VisionTopics.SERVICE_STATE
        self.topic = VisionTopics.CALIBRATION_FEEDBACK

    def publish_latest_image(self,image):
        self.broker.publish(self.latest_image_topic, {"image": image})

    def publish_calibration_image_captured(self,calibration_images):
        self.broker.publish(self.calibration_image_captured_topic, calibration_images)

    def publish_thresh_image(self,thresh_image):
        self.broker.publish(self.thresh_image_topic, thresh_image)

    def publish_state(self,state):
        # print("[VisionMessagePublisher] Publishing vision service state:", state)
        self.broker.publish(self.stateTopic, state)

    def publish_calibration_feedback(self,feedback):
        self.broker.publish(self.topic, feedback)
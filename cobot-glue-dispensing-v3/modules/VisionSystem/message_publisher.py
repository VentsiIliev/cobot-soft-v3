from modules.shared.MessageBroker import MessageBroker

class MessagePublisher:
    def __init__(self):
        self.broker= MessageBroker()
        self.latest_image_topic = "vision-system/latest_image"
        self.calibration_image_captured_topic = "vision-system/calibration_image_captured"
        self.thresh_image_topic = "vision-system/thresh_image"
        self.stateTopic = "vision-system/state"
        self.topic = "vision-system/calibration-feedback"

    def publish_latest_image(self,image):
        self.broker.publish(self.latest_image_topic, {"image": image})

    def publish_calibration_image_captured(self,calibration_images):
        self.broker.publish(self.calibration_image_captured_topic, calibration_images)

    def publish_thresh_image(self,thresh_image):
        self.broker.publish(self.thresh_image_topic, thresh_image)

    def publish_state(self,state):
        self.broker.publish(self.stateTopic, state)

    def publish_calibration_feedback(self,feedback):
        self.broker.publish(self.topic, feedback)
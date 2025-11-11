from modules.shared.v1.topics import RobotTopics, VisionTopics

class RobotServiceMessagePublisher:
    def __init__(self,broker):
        self.broker = broker
        self.state_topic = RobotTopics.SERVICE_STATE
        self.trajectory_stop_topic = RobotTopics.TRAJECTORY_STOP
        self.trajectory_break_topic = RobotTopics.TRAJECTORY_BREAK
        self.threshold_region_topic = VisionTopics.THRESHOLD_REGION
    def publish_state(self,state):
        # print(f"Publishing Robot Service State: {state}")
        self.broker.publish(self.state_topic, state)

    def publish_trajectory_stop_topic(self):
        self.broker.publish(self.trajectory_stop_topic, "")

    def publish_trajectory_break_topic(self):
        self.broker.publish(self.trajectory_break_topic, {})

    def publish_threshold_region_topic(self,region):
        self.broker.publish(self.threshold_region_topic, {"region":region})
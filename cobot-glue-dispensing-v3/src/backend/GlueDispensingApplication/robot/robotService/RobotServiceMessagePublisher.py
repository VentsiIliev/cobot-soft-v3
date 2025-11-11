class RobotServiceMessagePublisher:
    def __init__(self,broker):
        self.broker = broker
        self.state_topic = "robot-service/state"
        self.trajectory_stop_topic = "robot/trajectory/stop"
        self.trajectory_break_topic = "robot/trajectory/break"
        self.threshold_region_topic = "vision-system/threshold"
    def publish_state(self,state):
        # print(f"Publishing Robot Service State: {state}")
        self.broker.publish(self.state_topic, state)

    def publish_trajectory_stop_topic(self):
        self.broker.publish(self.trajectory_stop_topic, "")

    def publish_trajectory_break_topic(self):
        self.broker.publish(self.trajectory_break_topic, {})

    def publish_threshold_region_topic(self,region):
        self.broker.publish(self.threshold_region_topic, {"region":region})
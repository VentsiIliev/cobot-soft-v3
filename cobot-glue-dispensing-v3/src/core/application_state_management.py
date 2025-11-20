from backend.system.SystemStatePublisherThread import SystemStatePublisherThread
from core.application.interfaces.ISubscriptionModule import ISubscriptionModule


class SubscriptionManger:
    def __init__(self, owner, broker, subscriptions):
        self.owner = owner
        self.broker = broker
        # Convert list of tuples to dictionary for easier lookup
        if isinstance(subscriptions, list):
            self.subscriptions = {}
            self._initial_subscriptions = subscriptions
        else:
            self.subscriptions = subscriptions
            self._initial_subscriptions = []
        self.modules = []

    def subscribe_all(self):
        """Subscribe all loaded modules."""
        # First subscribe to initial subscriptions from constructor
        for subscription in self._initial_subscriptions:
            topic = subscription[0]
            callback = subscription[1]
            print(f"Subscribing to topic: {topic} with callback: {callback}")
            self._add_subscription(topic, callback)

    def load_modules(self, modules: list[ISubscriptionModule]):
        for module in modules:
            module.register(self)
            self.modules.append(module)

    def _add_subscription(self, topic: str, callback):
        self.broker.subscribe(topic, callback)
        self.subscriptions[topic] = callback

    def _remove_subscription(self, topic):
        if topic in self.subscriptions:
            self.broker.unsubscribe(topic, self.subscriptions[topic])
            del self.subscriptions[topic]


from enum import auto, Enum

from communication_layer.api.v1.topics import VisionTopics, RobotTopics, SystemTopics


class ApplicationState(Enum):
    """Base application states that all robot applications should support"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    PAUSED = "paused"
    STOPPED = "stopped"
    STARTED = "started"
    ERROR = "error"
    CALIBRATING = "calibrating"


class ProcessState(Enum):
    INITIALIZING = auto()
    IDLE = auto()
    STARTING = auto()
    STOPPED = auto()
    PAUSED = auto()
    COMPLETED = auto()
    ERROR = auto()


class ApplicationMessagePublisher:
    """Extended message publisher for glue dispensing specific messages"""

    def __init__(self, broker):
        self.broker=broker
        self.brightness_region_topic = VisionTopics.BRIGHTNESS_REGION
        self.robot_trajectory_image_topic = RobotTopics.TRAJECTORY_UPDATE_IMAGE
        self.trajectory_start_topic = RobotTopics.TRAJECTORY_START


    def publish_state(self, state):
        self.broker.publish(topic=SystemTopics.APPLICATION_STATE, message=state)

    def publish_brightness_region(self, region):
        self.broker.publish(self.brightness_region_topic, {"region": region})

    def publish_trajectory_image(self, image):
        self.broker.publish(self.robot_trajectory_image_topic, {"image": image})

    def publish_trajectory_start(self):
        self.broker.publish(self.trajectory_start_topic, "")

class ApplicationStateManager:
    """Extended state manager for glue dispensing specific state handling"""

    def __init__(self, message_publisher: ApplicationMessagePublisher):
        self.message_publisher = message_publisher
        self.current_state = ApplicationState.INITIALIZING
        self._services_ready = False  # Flag to indicate when both services are ready
        self.state_publisher = None

    def update_state(self, state):
        """Update the application state"""
        print(f"ApplicationStateManager: Updating state to {state}")
        self.current_state = state
        self.publish_state()

    def publish_state(self):
        """Publish the current state (no arguments needed - used by publisher thread)"""
        print(f"ApplicationStateManager: Publishing state {self.current_state}")
        self.message_publisher.publish_state(self.current_state)

    def __map_process_to_application_state(self, process_state):
        """Map GlueProcessState to ApplicationState"""
        if process_state == ProcessState.PAUSED:
            return ApplicationState.PAUSED
        elif process_state == ProcessState.COMPLETED:
            return ApplicationState.IDLE
        elif process_state == ProcessState.ERROR:
            return ApplicationState.ERROR
        elif process_state == ProcessState.STOPPED:
            return ApplicationState.IDLE
        else:
            return ApplicationState.STARTED

    def on_process_state_update(self, state):
        """Handle glue process state updates"""
        print(f"Glue process state update received: {state}")
        # check if state is GluePrecessState and map to ApplicationState
        if not isinstance(state, ProcessState):
            raise ValueError(f"Invalid state type: {type(state)}. Expected GlueProcessState.")
        self.update_state(self.__map_process_to_application_state(state))

    def start_state_publisher_thread(self):
        if self.state_publisher is None:
            self.state_publisher = SystemStatePublisherThread(publish_state_func=self.publish_state, interval=0.1)
            self.state_publisher.start()

    def stop_state_publisher_thread(self):
        if self.state_publisher:
            self.state_publisher.stop()
            self.state_publisher.join()
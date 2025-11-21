from enum import auto, Enum
from backend.system.SystemStatePublisherThread import SystemStatePublisherThread
from core.application.interfaces.ISubscriptionModule import ISubscriptionModule
from core.operation_state_management import OperationState
from core.system_state_management import SystemState
from communication_layer.api.v1.topics import VisionTopics, RobotTopics, SystemTopics



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



class ApplicationState(Enum):
    """Base application states that all robot applications should support"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    PAUSED = "paused"
    STOPPED = "stopped"
    STARTED = "started"
    ERROR = "error"
    CALIBRATING = "calibrating"

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

    def __init__(self, message_publisher: ApplicationMessagePublisher):
        self.state_publisher = None
        self.message_publisher = message_publisher
        self.current_state = ApplicationState.INITIALIZING

        self.system_state = SystemState.UNKNOWN
        self.process_state = OperationState.INITIALIZING


    def publish_state(self):
        self.message_publisher.publish_state(self.current_state)

    # ----------------------------
    # Update Events (System / Operation)
    # ----------------------------
    def on_system_state_update(self, message):
        """message is like {'state': SystemState.XYZ}"""
        if isinstance(message, dict) and "state" in message:
            self.system_state = message["state"]
        else:
            self.system_state = message  # already raw enum

        print(f"[ApplicationStateManager] Received system state → {self.system_state}")
        self._update_application_state()

    def on_operation_state_update(self, state: OperationState):
        if not isinstance(state, OperationState):
            raise ValueError("Expected OperationState")
        self.process_state = state
        self._update_application_state()

    # ----------------------------
    # Aggregation Logic
    # ----------------------------
    def _recompute_application_state(self) -> ApplicationState:
        print("\n[ApplicationStateManager] --- Recomputing Application State ---")
        print(f"[ApplicationStateManager] SystemState:     {self.system_state}")
        print(f"[ApplicationStateManager] OperationState:  {self.process_state}")

        # 1. Any error -> application is ERROR
        if self.system_state == SystemState.ERROR:
            print("[ApplicationStateManager] Rule: SYSTEM ERROR → ApplicationState.ERROR")
            return ApplicationState.ERROR

        if self.process_state == OperationState.ERROR:
            print("[ApplicationStateManager] Rule: OPERATION ERROR → ApplicationState.ERROR")
            return ApplicationState.ERROR

        # 2. Services not ready yet
        if self.system_state in [SystemState.INITIALIZING, SystemState.UNKNOWN]:
            print("[ApplicationStateManager] Rule: System not ready → ApplicationState.INITIALIZING")
            return ApplicationState.INITIALIZING

        # 3. Active operation rules
        if self.process_state == OperationState.PAUSED:
            print("[ApplicationStateManager] Rule: OPERATION PAUSED → ApplicationState.PAUSED")
            return ApplicationState.PAUSED

        # Treat INITIALIZING as IDLE (operation not running yet)
        if self.process_state == OperationState.INITIALIZING:
            print("[ApplicationStateManager] Rule: OPERATION INITIALIZING → ApplicationState.IDLE")
            return ApplicationState.IDLE

        if self.process_state in [OperationState.COMPLETED, OperationState.STOPPED]:
            print("[ApplicationStateManager] Rule: COMPLETED/STOPPED → ApplicationState.IDLE")
            return ApplicationState.IDLE

        if self.process_state == OperationState.IDLE:
            print("[ApplicationStateManager] Rule: OPERATION IDLE → ApplicationState.IDLE")
            return ApplicationState.IDLE

        # Default: considered “running”
        print("[ApplicationStateManager] Rule: Default → ApplicationState.STARTED")
        return ApplicationState.STARTED

    def _update_application_state(self):
        new_state = self._recompute_application_state()
        if new_state != self.current_state:
            print(f"[ApplicationStateManager] Application state → {new_state}")
            self.current_state = new_state
            self.publish_state()

    def start_state_publisher_thread(self):
        if self.state_publisher is None:
            self.state_publisher = SystemStatePublisherThread(publish_state_func=self.publish_state, interval=0.1)
            self.state_publisher.start()

    def stop_state_publisher_thread(self):
        if self.state_publisher:
            self.state_publisher.stop()
            self.state_publisher.join()
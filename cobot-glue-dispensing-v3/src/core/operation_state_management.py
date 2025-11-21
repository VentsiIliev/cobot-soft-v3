from abc import abstractmethod, ABC
from enum import Enum, auto

from communication_layer.api.v1.topics import SystemTopics
from modules.VisionSystem.message_publisher import MessagePublisher
from modules.shared.MessageBroker import MessageBroker


class OperationState(Enum):
    INITIALIZING = auto()
    IDLE = auto()
    STARTING = auto()
    STOPPED = auto()
    PAUSED = auto()
    COMPLETED = auto()
    ERROR = auto()

class OperationStatePublisher:
    def __init__(self,broker:MessageBroker):
        self.broker=broker
        self.topic = SystemTopics.OPERATION_STATE
    def publish(self,state: OperationState):
        self.broker.publish(self.topic,state)

class IOperation(ABC):

    def __init__(self):
        self.__publisher = None

    def set_state_publisher(self, publisher:OperationStatePublisher):
        self.__publisher = publisher

    def __publish_state(self, state):
        print(f"IOperation: Publishing state {state}")
        if self.__publisher:
            self.__publisher.publish(state)
        else:
            print("IOperation: No publisher set, cannot publish state")

    # Public interface with state publishing
    def start(self,*args, **kwargs):
        print(f"IOperation: Starting operation with args: {args}, kwargs: {kwargs}")
        self.__publish_state(OperationState.STARTING)
        self._do_start(*args, **kwargs)

    def stop(self,*args, **kwargs):
        self.__publish_state(OperationState.STOPPED)
        self._do_stop(*args, **kwargs)

    def pause(self,*args, **kwargs):
        self.__publish_state(OperationState.PAUSED)
        self._do_pause(*args, **kwargs)

    def resume(self,*args, **kwargs):
        self.__publish_state(OperationState.STARTING)
        self._do_resume(*args, **kwargs)

    # Template methods that subclasses implement
    @abstractmethod
    def _do_start(self,*args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def _do_stop(self,*args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def _do_pause(self,*args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def _do_resume(self,*args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")
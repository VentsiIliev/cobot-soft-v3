from abc import abstractmethod, ABC
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Any

from communication_layer.api.v1.topics import SystemTopics
from modules.shared.MessageBroker import MessageBroker


class OperationState(Enum):
    INITIALIZING = auto()
    IDLE = auto()
    STARTING = auto()
    STOPPED = auto()
    PAUSED = auto()
    COMPLETED = auto()
    ERROR = auto()

@dataclass
class OperationResult:
    """Standard structure for operation results"""
    success: bool
    message: str = ""
    data: Dict[str, Any] = None
    error: str = ""

    def to_dict(self):
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data if self.data is not None else {},
            "error": self.error if self.error is not None else ""
        }

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
    def start(self,*args, **kwargs) -> OperationResult:
        print(f"IOperation: Starting operation with args: {args}, kwargs: {kwargs}")
        self.__publish_state(OperationState.STARTING)
        try:
            self._do_start(*args, **kwargs)
            return OperationResult(success=True, message="Operation started successfully")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.__publish_state(OperationState.ERROR)
            return OperationResult(success=False, message="Operation failed to start", error=str(e))

    def stop(self,*args, **kwargs) -> OperationResult:
        try:
            self.__publish_state(OperationState.STOPPED)
            self._do_stop(*args, **kwargs)
            return OperationResult(success=True, message="Operation stopped successfully")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.__publish_state(OperationState.ERROR)
            return OperationResult(success=False, message="Operation failed to stop", error=str(e))

    def pause(self,*args, **kwargs)-> OperationResult:
        try:
            self.__publish_state(OperationState.PAUSED)
            self._do_pause(*args, **kwargs)
            return OperationResult(success=True, message="Operation paused successfully")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.__publish_state(OperationState.ERROR)
            return OperationResult(success=False, message="Operation failed to pause", error=str(e))

    def resume(self,*args, **kwargs)-> OperationResult:
        try:
            self.__publish_state(OperationState.STARTING)
            self._do_resume(*args, **kwargs)
            return OperationResult(success=True, message="Operation resumed successfully")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.__publish_state(OperationState.ERROR)
            return OperationResult(success=False, message="Operation failed to resume", error=str(e))

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


class BaseOperation(IOperation):

    def _do_start(self,*args, **kwargs):
        print("BaseOperation: Default start implementation")

    def _do_stop(self,*args, **kwargs):
        print("BaseOperation: Default stop implementation")

    def _do_pause(self,*args, **kwargs):
        print("BaseOperation: Default pause implementation")

    def _do_resume(self,*args, **kwargs):
        print("BaseOperation: Default resume implementation")
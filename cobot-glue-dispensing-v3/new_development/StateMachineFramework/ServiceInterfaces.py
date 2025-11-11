from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class OperationService(ABC):
    """Service for executing operations"""

    @abstractmethod
    def execute_operation(self, operation_type: str, state: str, context_data: Dict[str, Any]) -> Any:
        """Execute an operation and return the result"""
        pass


class EventService(ABC):
    """Service for processing events"""

    @abstractmethod
    def process_event(self, event_name: str, data: Dict[str, Any]) -> None:
        """Process an event with associated data"""
        pass


class LoggingService(ABC):
    """Service for logging state machine activities"""

    @abstractmethod
    def log_state_change(self, from_state: Optional[str], to_state: str, event_data: Dict[str, Any]) -> None:
        """Log a state transition"""
        pass

    @abstractmethod
    def log_error(self, error_message: str, state: Optional[str], context: Dict[str, Any]) -> None:
        """Log an error"""
        pass


class ActionService(ABC):
    """Service for executing state entry/exit actions"""

    @abstractmethod
    def execute_entry_action(self, action: str, state: str, context: Dict[str, Any]) -> None:
        """Execute a state entry action"""
        pass

    @abstractmethod
    def execute_exit_action(self, action: str, state: str, context: Dict[str, Any]) -> None:
        """Execute a state exit action"""
        pass


from typing import TypeVar, Type, Dict, Any

T = TypeVar('T')


class ServiceContainer:
    """Dependency injection container for managing services"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}

    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """Register a singleton service instance"""
        self._singletons[service_type] = instance

    def register_transient(self, service_type: Type[T], factory: callable) -> None:
        """Register a transient service factory"""
        self._services[service_type] = factory

    def get_service(self, service_type: Type[T]) -> T:
        """Get a service instance"""
        # Check singletons first
        if service_type in self._singletons:
            return self._singletons[service_type]

        # Check transient services
        if service_type in self._services:
            return self._services[service_type]()

        raise ValueError(f"Service {service_type.__name__} not registered")

    def has_service(self, service_type: Type[T]) -> bool:
        """Check if a service is registered"""
        return service_type in self._singletons or service_type in self._services
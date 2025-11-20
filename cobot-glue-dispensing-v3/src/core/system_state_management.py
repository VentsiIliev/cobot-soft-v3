from dataclasses import dataclass
from enum import Enum
from typing import Callable
from backend.system.SystemStatePublisherThread import SystemStatePublisherThread
from backend.system.utils import PathResolver


# -----------------------------
# Enums
# -----------------------------

class ServiceRegistry:
    def __init__(self,on_register_callback: Callable = None):
        self.registry = {}
        self.on_register_callback = on_register_callback

    def register_service(self, name: str, topic: str,initial_state: 'ServiceState'):
        self.registry[name] = {
            "topic": topic,
            "initial_state": initial_state
        }

        if self.on_register_callback is not None:
            self.on_register_callback()

    def get_service_info(self, name: str):
        return self.registry.get(name, None)

    def unregister_service(self, name: str):
        if name in self.registry:
            del self.registry[name]

    def get_registered_services(self):
        return list(self.registry.keys())

class ServiceState(Enum):
    """Canonical states for individual services."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    PAUSED = "paused"
    STOPPED = "stopped"
    STARTED = "started"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class ServiceStateMessage:
    id: str
    state: ServiceState

    def to_dict(self):
        return {
            "id": self.id,
            "state": self.state.value
        }

class SystemState(Enum):
    """Aggregated system-wide state."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    PAUSED = "paused"
    STOPPED = "stopped"
    STARTED = "started"
    ERROR = "error"
    UNKNOWN = "unknown"

# -----------------------------
# System state priority
# -----------------------------
SYSTEM_STATE_PRIORITY = {
    SystemState.ERROR: 4,
    SystemState.STOPPED: 3,
    SystemState.PAUSED: 2,
    SystemState.STARTED: 1,
    SystemState.IDLE: 0,
    SystemState.INITIALIZING: -1,
    SystemState.UNKNOWN: -2,
}

# -----------------------------
# SystemStateManager
# -----------------------------
class SystemStateManager:
    def __init__(self, system_state_priority,broker,service_registry: ServiceRegistry):
        self.system_state_priority = system_state_priority
        self.service_registry = service_registry
        self.service_registry.on_register_callback = self.__refresh_registered_services
        self.service_states: dict[str, ServiceState] = {}  # service_name -> ServiceState
        self.system_state: SystemState = SystemState.UNKNOWN
        self.subscribers: list[Callable] = []
        self.broker=broker
        self.system_state_publisher = None
        self.__register_all_services()

    def __register_all_services(self):
        for service_name, info in self.service_registry.registry.items():
            topic = info["topic"]
            initial_state = info["initial_state"]
            self.__register_service(service_name, topic, initial_state)

    def __refresh_registered_services(self):
        """Refresh the registered services from the service registry."""
        self.service_states.clear()
        self.__register_all_services()

    def __register_service(self, name: str, topic: str, initial_state: ServiceState = ServiceState.UNKNOWN):
        """Register service and subscribe to its state topic."""
        print(f"[SystemStateManager] Registering service '{name}' with initial state {initial_state} on topic '{topic}'")
        self.service_states[name] = initial_state
        # Subscribe to broker topic


        self.broker.subscribe(topic, self.update_service_state)

        self._recompute_system_state()

    def __convert_state_str_to_enum(self,state_str: str) -> ServiceState:
        try:
            return ServiceState(state_str)
        except ValueError:
            raise ValueError(f"Invalid state value: {state_str}")

    def update_service_state(self,message: dict):
        name = message.get("id")
        state_str = message.get("state")
        state = self.__convert_state_str_to_enum(state_str)
        if name not in self.service_states:
            raise ValueError(f"Receoved INVALID MESSAGE {message} Service '{name}' not registered")
        if not isinstance(state, ServiceState):
            raise TypeError(f"Receoved INVALID MESSAGE {message}  State must be ServiceState Enum, got {type(state).__name__}: {state}")
        # print(f"[SystemStateManager.update_service_state] Updating '{name}' to {state}")
        # print(f"[SystemStateManager] Service '{name}' state updated to {state}")
        # only recompute if state has changed
        self.service_states[name] = state
        self._recompute_system_state()

    def _recompute_system_state(self):
        def map_service_to_system(s: ServiceState) -> SystemState:
            mapping = {
                ServiceState.ERROR: SystemState.ERROR,
                ServiceState.PAUSED: SystemState.PAUSED,
                ServiceState.STOPPED: SystemState.STOPPED,
                ServiceState.STARTED: SystemState.STARTED,
                ServiceState.IDLE: SystemState.IDLE,
                ServiceState.INITIALIZING: SystemState.INITIALIZING,
                ServiceState.UNKNOWN: SystemState.UNKNOWN,
            }
            return mapping.get(s, SystemState.UNKNOWN)

        system_states = [map_service_to_system(s) for s in self.service_states.values()]
        new_system_state = min(system_states, key=lambda s: self.system_state_priority[s])

        if new_system_state != self.system_state:
            self.system_state = new_system_state

    def publish_state(self):
        print(f"publishing system state: {self.system_state}")
        # print all registered services and their states
        for service_name, state in self.service_states.items():
            print(f" - Service '{service_name}': {state}")
        self.broker.publish("system/state", {"state": self.system_state})

    def start_state_publisher_thread(self):
        """Start the state publisher thread"""
        if self.system_state_publisher is None:
            self.system_state_publisher = SystemStatePublisherThread(self.publish_state)
            self.system_state_publisher.start()

# -----------------------------
# Example usage
# -----------------------------




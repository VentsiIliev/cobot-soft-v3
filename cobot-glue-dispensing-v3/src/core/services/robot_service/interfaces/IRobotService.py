from abc import ABC, abstractmethod
from typing import List

from core.application.interfaces.ISubscriptionModule import ISubscriptionModule
from core.model.robot.enums.axis import Direction, RobotAxis

class IRobotService(ABC):
    """Interface for all robot service implementations."""

    @abstractmethod
    def move_to_position(self, position: List[float], tool: int, workpiece: int,
                         velocity: float, acceleration: float,
                         wait_to_reach: bool = False) -> bool: ...

    @abstractmethod
    def start_jog(self, axis: RobotAxis, direction: Direction, step: float) -> int: ...

    @abstractmethod
    def stop_motion(self) -> bool: ...

    @abstractmethod
    def get_current_position(self) -> List[float]: ...

    @abstractmethod
    def get_current_velocity(self) -> float: ...

    @abstractmethod
    def get_current_acceleration(self) -> float: ...

    @abstractmethod
    def enable_robot(self) -> None: ...

    @abstractmethod
    def disable_robot(self) -> None: ...

    @abstractmethod
    def get_state(self) -> str: ...

    @abstractmethod
    def get_state_topic(self) -> str: ...



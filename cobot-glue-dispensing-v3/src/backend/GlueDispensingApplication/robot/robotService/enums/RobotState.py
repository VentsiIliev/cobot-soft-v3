from enum import Enum


class RobotState(Enum):
    """Physical robot motion states"""
    STATIONARY = "stationary"
    ACCELERATING = "accelerating"
    DECELERATING = "decelerating"
    MOVING = "moving"
    ERROR = "error"

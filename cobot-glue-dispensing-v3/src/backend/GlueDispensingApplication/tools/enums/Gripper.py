from enum import Enum

class Gripper(Enum):
    """
    Enum representing the available types of grippers in the system.

    Attributes:
        SINGLE (str): Represents a single gripper configuration.
        MOCK (str): Represents a mock gripper setup (used for testing or simulation).
        MOCK2 (str): Represents a second variant of a mock gripper.
        MOCK3 (str): Represents a third variant of a mock gripper.
        DOUBLE (str): Represents a double gripper configuration.
    """

    BELT = "0"
    SINGLE = "1"
    DOUBLE = "4"
    MOCK3 = "3"
    MOCK4 = "2"

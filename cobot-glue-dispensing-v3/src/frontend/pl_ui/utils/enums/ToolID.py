from enum import Enum


class ToolID(Enum):
    Tool0 = "0"
    Tool1 = "1"
    Tool2 = "2"
    Tool3 = "3"

    def __str__(self):
        """String representation of the enum value."""
        return self.value

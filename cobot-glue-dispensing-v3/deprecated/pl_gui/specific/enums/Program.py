from enum import Enum


class Program(Enum):
    TRACE = "Trace"
    ZIGZAG = "ZigZag"


    def __str__(self):
        """String representation of the enum value."""
        return self.value
from enum import Enum

class Program(Enum):
    """
    Enum representing different program execution patterns for glue dispensing or motion paths.

    Attributes:
        TRACE (str): Represents a tracing program, typically following a continuous path or contour.
        ZIGZAG (str): Represents a zigzag program pattern, often used for filling or covering an area.
    """

    TRACE = "Trace"
    ZIGZAG = "ZigZag"

    def __str__(self):
        """Return the string value of the enum."""
        return self.value

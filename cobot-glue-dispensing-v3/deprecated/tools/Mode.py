from enum import Enum
"""

    NOTE: This enum is currently not in use in the application. It is defined
    for future extensibility or configuration purposes.
    """

class Mode(Enum):
    """
    Enum representing different operating modes for glue dispensing.


    Attributes:
        CONSTANT_FREQ (int): Dispensing occurs at a constant frequency.
        CONSTANT_DIST (int): Dispensing occurs at constant spatial intervals.
        PRINTER (int): Simulates printer-like behavior, potentially for grid or raster patterns.
        SINGLE_DROPS (int): Dispenses individual drops, typically for precision or spot gluing.
    """
    CONSTANT_FREQ = 1
    CONSTANT_DIST = 2
    PRINTER = 3
    SINGLE_DROPS = 4

    def getValue(self):
        return self.value
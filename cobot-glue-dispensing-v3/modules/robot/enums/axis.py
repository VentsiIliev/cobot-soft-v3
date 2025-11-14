from enum import Enum


class Axis(Enum):
    """
    Enum representing robot movement axes.
    """
    X = 1
    Y = 2
    Z = 3
    RX = 4
    RY = 5
    RZ = 6

    def __str__(self):
        return self.name

    @staticmethod
    def get_by_string(name):
        """
        Retrieve an Axis enum value by its string representation.

        Args:
            name (str): The string representation of the axis.

        Returns:
            Axis: The corresponding Axis enum value.

        Raises:
            ValueError: If the string does not match any Axis enum.
        """
        try:
            return Axis[name.upper()]
        except KeyError:
            raise ValueError(f"Invalid axis name: {name}")

class Direction(Enum):
    """
       Enum representing movement directions along an axis.
       """
    MINUS = -1
    PLUS = 1

    def __str__(self):
        return self.name

    @staticmethod
    def get_by_string(name):
        try:
            return Direction[name.upper()]
        except KeyError:
            raise ValueError(f"Invalid Direction name: {name}")
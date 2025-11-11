from enum import Enum

class ToolID(Enum):
    """
    Enum representing identifiers for different robot tools.

    Attributes:
        Tool0 (str): Represents Tool ID 0, typically the default or primary tool.
        Tool1 (str): Represents Tool ID 1, used when a second tool is configured.
        Tool2 (str): Represents Tool ID 2, used for additional tooling configurations.
        Tool3 (str): Represents Tool ID 3, for specialized or less common tools.
    """

    Tool0 = "0"
    Tool1 = "1"
    Tool2 = "2"
    Tool3 = "3"
    Tool4 = "4"

    def __str__(self):
        """Return the string value of the enum."""
        return self.value

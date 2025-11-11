class Tool1:
    """
    Class representing Tool1, a specific tool used for dispensing operations.

    This tool is characterized by its offsets relative to the main tooltip or suction cup,
    as well as a required spraying height for proper operation.

    Attributes:
        xOffset (float): The offset in the x-direction from the main tooltip/suction cup.
        yOffset (float): The offset in the y-direction from the main tooltip/suction cup.
        zOffset (float): The offset in the z-direction from the main tooltip/suction cup.
        requiredSprayingHeight (float): The required height for spraying to occur effectively.
    """

    def __init__(self):
        """
        Initializes the Tool1 object with default offset values and required spraying height.

        The offsets represent the positioning adjustments relative to the main tooltip/suction cup.
        The requiredSprayingHeight ensures that the tool operates at the correct height for dispensing.
        """
        self.xOffset = -54  # y offset from the main tooltip/suction cup
        self.yOffset = -4  # x offset from the main tooltip/suction cup
        self.zOffset = -1.289  # z offset from the main tooltip/suction cup
        self.requiredSprayingHeight = 25  # Required spraying height for effective operation

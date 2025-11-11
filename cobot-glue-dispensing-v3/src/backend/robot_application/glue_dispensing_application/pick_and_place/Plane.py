class Plane:
    """
       Represents the 2D nesting area where workpieces are placed.

       This class defines the boundaries, spacing, and current state of the nesting grid.
       It is used to control how and where contours (representing workpieces) are positioned
       within a defined rectangular workspace. It also tracks the layout state across multiple
       rows and detects when the area is full.

       Attributes:
           xMin (int): The minimum x-coordinate (left boundary) of the nesting area.
           xMax (int): The maximum x-coordinate (right boundary) of the nesting area.
           yMax (int): The maximum y-coordinate (top boundary) of the nesting area.
           yMin (int): The minimum y-coordinate (bottom boundary) of the nesting area.
           spacing (int): The horizontal space to leave between adjacent workpieces.
           xOffset (int): The current horizontal offset used to determine the x-position of the next workpieces.
           yOffset (int): The current vertical offset used to determine the y-position of the current row.
           tallestContour (float): The height of the tallest workpieces in the current row, used for row spacing.
           rowCount (int): Tracks the number of completed rows.
           isFull (bool): Indicates whether the nesting area is full and cannot fit more workpieces.

       Usage:
           The Plane instance is passed to the `nestingNew()` function, which uses it to calculate placement
           coordinates for each workpiece. It automatically updates x and y offsets, checks for boundary overflows,
           and transitions to new rows when needed. If the next row cannot be placed within the vertical boundary
           (`yMin`), `isFull` is set to True to signal that no further nesting is possible.

       Example:
           plane = Plane()
           result, message = robotService.nestingNew(workpieces, callback, plane=plane)
       """
    def __init__(self):
        """
        TOP LEFT -> x = -348.07 Y= 803.743
        TOP RIGHT -> x = 490.103 Y = 673.587
        BOTTOM RIGHT -> x = 369.597 Y = 202.095
        BOTTOM LEFT -> x = -424.101 Y = 284.279
        """
        self.xMin = -450      # Left boundary of the nesting area (in mm or unit)
        self.xMax = 350       # Right boundary of the nesting area
        self.yMax = 700       # Top boundary of the nesting area
        self.yMin = 300       # Bottom boundary of the nesting area
        self.spacing = 30     # Horizontal spacing between workpieces
        self.xOffset = 0      # Horizontal offset for placing the next workpieces
        self.yOffset = 0      # Vertical offset for the current row
        self.tallestContour = 0  # Height of the tallest workpieces in the current row
        self.rowCount = 0        # Number of completed rows
        self.isFull = False      # Flag indicating if nesting area is full

"""
Description:
    This module defines the data model for a workpieces used in the glue dispensing system.
    It includes a field enumeration for standardized keys and abstract/base class definitions
    for workpieces data structures.

    These abstractions help manage serialization, validation, and structural consistency
    across various components of the application.
"""

from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from modules.shared.shared.interfaces.JsonSerializable import JsonSerializable


class WorkpieceField(Enum):
    """
       Enum representing standardized keys for workpieces fields.

       Used for consistency in shared communication and internal data structures.
       """
    WORKPIECE_ID = "workpieceId"
    NAME = "name"
    DESCRIPTION = "description"
    TOOL_ID = "toolId"
    GRIPPER_ID = "gripperId"
    GLUE_TYPE = "glueType"
    PROGRAM = "program"
    MATERIAL = "material"
    CONTOUR = "contour"
    OFFSET = "offset"
    HEIGHT = "height"
    SPRAY_PATTERN = "sprayPattern"
    CONTOUR_AREA = "contourArea"
    NOZZLES = "nozzles"
    GLUE_QTY = "glue_qty"
    SPRAY_WIDTH = "spray_width"
    PICKUP_POINT = "pickup_point"

    def getAsLabel(self):
        """
               Returns a user-friendly label version of the enum name.
               Example: CONTOUR_AREA → "Contour area"
               """
        return self.name.capitalize().replace("_", " ")

    def lower(self):
        """
               Returns the enum value in lowercase.
               Useful for JSON key consistency.
               """
        return self.value.lower()

class AbstractWorkpiece(ABC):
    """
    Abstract base class for workpieces objects.

    Enforces implementation of equality logic and provides a validation
    mechanism for mandatory fields.
    """
    def __init__(self, workpieceId, contour):
        """
               Initializes an abstract workpieces with a required ID.

               Args:
                   workpieceId (str): Unique identifier for the workpieces.
                   contour: Geometric representation of the workpieces boundary.
               """
        if not workpieceId:
            raise ValueError("Workpiece ID must be provided")
        self.workpieceId = workpieceId

    @abstractmethod

    def __eq__(self, other):
        """
                Abstract method to compare two workpieces.
                Must be implemented by subclasses.
                """
        pass


class BaseWorkpiece(AbstractWorkpiece):
    """
        Base implementation of a workpieces.

        Only equality comparison is implemented here, based on the workpieces ID.
        """
    def __init__(self, workpieceId, contour):
        """
               Initializes a base workpieces.

               Args:
                   workpieceId (str): Unique identifier for the workpieces.
                   contour: Geometric boundary data for the workpieces.
               """
        super().__init__(workpieceId, contour)

    def __eq__(self, other):
        """
              Checks equality based on workpieces ID.

              Returns:
                  bool: True if IDs match, otherwise False.
              """
        return self.workpieceId == other.workpieceId

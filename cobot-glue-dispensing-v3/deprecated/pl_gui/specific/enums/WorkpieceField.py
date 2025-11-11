from enum import Enum

class WorkpieceField(Enum):
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

    def getAsLabel(self):
        return self.name.capitalize().replace("_", " ")

    def lower(self):
        return self.value.lower()
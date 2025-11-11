from enum import Enum
class RobotSettingKey(Enum):
    IP_ADDRESS = "IP"
    VELOCITY = "Velocity"
    ACCELERATION = "Acceleration"
    TOOL = "Tool"
    USER = "User"

    def getAsLabel(self):
        return self.value + ":"
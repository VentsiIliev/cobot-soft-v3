
from modules.shared.core.settings.BaseSettings import Settings
from modules.shared.core.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey
class RobotSettings(Settings):
    def __init__(self, data: dict = None):
        super().__init__()
        # Initialize default robot settings using the Enum
        self.set_value(RobotSettingKey.IP_ADDRESS.value, "192.168.58.2")
        self.set_value(RobotSettingKey.VELOCITY.value, 100)
        self.set_value(RobotSettingKey.ACCELERATION.value, 100)
        self.set_value(RobotSettingKey.TOOL.value, 0)
        self.set_value(RobotSettingKey.USER.value, 0)

        # Update settings with provided data
        if data:
            for key, value in data.items():
                self.set_value(key, value)

    def get_robot_ip(self):
        return self.get_value(RobotSettingKey.IP_ADDRESS.value)

    def set_robot_ip(self, value):
        self.set_value(RobotSettingKey.IP_ADDRESS.value, value)

    def get_robot_velocity(self):
        return self.get_value(RobotSettingKey.VELOCITY.value)

    def set_robot_velocity(self, value):
        self.set_value(RobotSettingKey.VELOCITY.value, value)

    def get_robot_acceleration(self):
        return self.get_value(RobotSettingKey.ACCELERATION.value)

    def set_robot_acceleration(self, value):
        self.set_value(RobotSettingKey.ACCELERATION.value, value)

    def get_robot_tool(self):
        return self.get_value(RobotSettingKey.TOOL.value)

    def set_robot_tool(self, value):
        self.set_value(RobotSettingKey.TOOL.value, value)

    def get_robot_user(self):
        return self.get_value(RobotSettingKey.USER.value)

    def set_robot_user(self, value):
        self.set_value(RobotSettingKey.USER.value, value)

    def __str__(self):
        return (
            f"RobotSettings:\n"
            f"  IP Address: {self.get_robot_ip()}\n"
            f"  Velocity: {self.get_robot_velocity()}\n"
            f"  Acceleration: {self.get_robot_acceleration()}\n"
            f"  Tool: {self.get_robot_tool()}\n"
            f"  User: {self.get_robot_user()}"
        )


from modules.shared.shared.settings.BaseSettings import Settings
from modules.shared.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from robot_application.glue_dispensing_application.tools.GlueCell import GlueType


class GlueSettings(Settings):
    def __init__(self, data: dict = None):
        super().__init__()

        self.set_value(GlueSettingKey.SPRAY_WIDTH.value, 5)
        self.set_value(GlueSettingKey.SPRAYING_HEIGHT.value, 10)
        self.set_value(GlueSettingKey.FAN_SPEED.value, 50)
        self.set_value(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value, 1)
        self.set_value(GlueSettingKey.MOTOR_SPEED.value, 10000)
        self.set_value(GlueSettingKey.REVERSE_DURATION.value, 1)
        self.set_value(GlueSettingKey.SPEED_REVERSE.value, 1000)
        self.set_value(GlueSettingKey.RZ_ANGLE.value, 0)
        self.set_value(GlueSettingKey.GLUE_TYPE.value, GlueType.TypeA.value)
        self.set_value(GlueSettingKey.GENERATOR_TIMEOUT.value,5.0)
        self.set_value(GlueSettingKey.TIME_BEFORE_MOTION.value,1.0)
        self.set_value(GlueSettingKey.TIME_BEFORE_STOP.value, 1)
        self.set_value(GlueSettingKey.REACH_START_THRESHOLD.value, 1)
        self.set_value(GlueSettingKey.REACH_END_THRESHOLD.value, 1)
        self.set_value(GlueSettingKey.INITIAL_RAMP_SPEED.value, 5000)
        self.set_value(GlueSettingKey.FORWARD_RAMP_STEPS.value, 1)
        self.set_value(GlueSettingKey.REVERSE_RAMP_STEPS.value, 1)
        self.set_value(GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value, 1)
        self.set_value(GlueSettingKey.SPRAY_ON.value, True)

        # Update settings with provided data
        if data:
            for key, value in data.items():
                self.set_value(key, value)

    def set_spray_width(self, sprayWidth):
        """Set the spray width."""
        self.set_value(GlueSettingKey.SPRAY_WIDTH.value, sprayWidth)

    def get_spray_width(self):
        """Get the spray width."""
        return self.get_value(GlueSettingKey.SPRAY_WIDTH.value)

    def set_spraying_height(self, sprayingHeight):
        """Set the spraying height."""
        self.set_value(GlueSettingKey.SPRAYING_HEIGHT.value, sprayingHeight)

    def get_spraying_height(self):
        """Get the spraying height."""
        return self.get_value(GlueSettingKey.SPRAYING_HEIGHT.value)

    def set_fan_speed(self, fanSpeed):
        """Set the fan speed."""
        self.set_value(GlueSettingKey.FAN_SPEED.value, fanSpeed)

    def get_fan_speed(self):
        """Get the fan speed."""
        return self.get_value(GlueSettingKey.FAN_SPEED.value)

    def set_time_between_generator_and_glue(self, timeBetweenGeneratorAndGlue):
        """Set the time between generator and glue."""
        self.set_value(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value, timeBetweenGeneratorAndGlue)

    def get_time_between_generator_and_glue(self):
        """Get the time between generator and glue."""
        return self.get_value(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value)

    def set_motor_speed(self, motorSpeed):
        """Set the motor speed."""
        self.set_value(GlueSettingKey.MOTOR_SPEED.value, motorSpeed)

    def get_motor_speed(self):
        """Get the motor speed."""
        return self.get_value(GlueSettingKey.MOTOR_SPEED.value)

    def set_steps_reverse(self, stepsReverse):
        """Set the steps in reverse."""
        self.set_value(GlueSettingKey.REVERSE_DURATION.value, stepsReverse)

    def get_steps_reverse(self):
        """Get the steps in reverse."""
        return self.get_value(GlueSettingKey.REVERSE_DURATION.value)

    def set_speed_reverse(self, speedReverse):
        """Set the speed in reverse."""
        self.set_value(GlueSettingKey.SPEED_REVERSE.value, speedReverse)

    def get_speed_reverse(self):
        """Get the speed in reverse."""
        return self.get_value(GlueSettingKey.SPEED_REVERSE.value)

    def set_rz_angle(self, rzAngle):
        """Set the RZ angle."""
        self.set_value(GlueSettingKey.RZ_ANGLE.value, rzAngle)

    def get_rz_angle(self):
        """Get the RZ angle."""
        return self.get_value(GlueSettingKey.RZ_ANGLE.value)


    def set_glue_type(self, glueType):
        """Set the glue type."""
        self.set_value(GlueSettingKey.GLUE_TYPE.value, glueType)


    def get_glue_type(self):
        """Get the glue type."""
        return self.get_value(GlueSettingKey.GLUE_TYPE.value)


    def set_generator_timeout(self, timeout):
        """Set the generator timeout."""
        self.set_value(GlueSettingKey.GENERATOR_TIMEOUT.value, timeout)

    def get_generator_timeout(self):
        """Get the generator timeout."""
        return self.get_value(GlueSettingKey.GENERATOR_TIMEOUT.value)

    def set_time_before_motion(self, timeBeforeMotion):
        """Set the time before motion."""
        self.set_value(GlueSettingKey.TIME_BEFORE_MOTION.value, timeBeforeMotion)

    def get_time_before_motion(self):
        """Get the time before motion."""
        return self.get_value(GlueSettingKey.TIME_BEFORE_MOTION.value)

    def get_reach_position_threshold(self):
        """Get the threshold for reaching a position."""
        return self.get_value(GlueSettingKey.REACH_START_THRESHOLD.value)

    def set_reach_position_threshold(self, threshold):
        """Set the threshold for reaching a position."""
        self.set_value(GlueSettingKey.REACH_START_THRESHOLD.value, threshold)

    def get_reach_end_threshold(self):
        """Get the threshold for reaching the end position."""
        return self.get_value(GlueSettingKey.REACH_END_THRESHOLD.value)
    def set_reach_end_threshold(self, threshold):
        """Set the threshold for reaching the end position."""
        self.set_value(GlueSettingKey.REACH_END_THRESHOLD.value, threshold)

    def get_time_before_stop(self):
        """Get the time before stopping."""
        return self.get_value(GlueSettingKey.TIME_BEFORE_STOP.value)
    def set_time_before_stop(self, timeBeforeStop):
        """Set the time before stopping."""
        self.set_value(GlueSettingKey.TIME_BEFORE_STOP.value, timeBeforeStop)

    def get_initial_ramp_speed(self):
        """Get the initial ramp speed."""
        return self.get_value(GlueSettingKey.INITIAL_RAMP_SPEED.value)

    def set_initial_ramp_speed(self, speed):
        """Set the initial ramp speed."""
        self.set_value(GlueSettingKey.INITIAL_RAMP_SPEED.value, speed)

    def get_forward_ramp_steps(self):
        """Get the number of forward ramp steps."""
        return self.get_value(GlueSettingKey.FORWARD_RAMP_STEPS.value)

    def set_forward_ramp_steps(self, steps):
        """Set the number of forward ramp steps."""
        self.set_value(GlueSettingKey.FORWARD_RAMP_STEPS.value, steps)

    def get_reverse_ramp_steps(self):
        """Get the number of reverse ramp steps."""
        return self.get_value(GlueSettingKey.REVERSE_RAMP_STEPS.value)

    def set_reverse_ramp_steps(self, steps):
        """Set the number of reverse ramp steps."""
        self.set_value(GlueSettingKey.REVERSE_RAMP_STEPS.value, steps)

    def get_initial_ramp_speed_duration(self):
        """Get the duration of the initial ramp speed."""
        return self.get_value(GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value)

    def set_initial_ramp_speed_duration(self, duration):
        """Set the duration of the initial ramp speed."""
        self.set_value(GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value, duration)

    def get_spray_on(self):
        """Get the spray on/off setting."""
        return self.get_value(GlueSettingKey.SPRAY_ON.value)

    def set_spray_on(self, spray_on):
        """Set the spray on/off setting."""
        self.set_value(GlueSettingKey.SPRAY_ON.value, spray_on)



    def display_settings(self):
        """Display all settings."""
        settings = self.get_all_settings()
        for key, value in settings.items():
            print(f"{key}: {value}")


    def __str__(self):
        return (
            f"GlueSettings:\n"
            f"  Spray Width: {self.get_spray_width()}\n"
            f"  Spraying Height: {self.get_spraying_height()}\n"
            f"  Fan Speed: {self.get_fan_speed()}\n"
            f"  Time Between Generator and Glue: {self.get_time_between_generator_and_glue()}\n"
            f"  Motor Speed: {self.get_motor_speed()}\n"
            f"  Steps Reverse: {self.get_steps_reverse()}\n"
            f"  Speed Reverse: {self.get_speed_reverse()}\n"
            f"  RZ Angle: {self.get_rz_angle()}\n"
            f"  Glue Type: {self.get_glue_type()}\n"
            f"  Generator Timeout: {self.get_generator_timeout()}\n"
            f"  Time Before Motion: {self.get_time_before_motion()}\n"
            f"  Reach Position Threshold: {self.get_reach_position_threshold()}\n"
            f"  Spray On: {self.get_spray_on()}\n"
        )

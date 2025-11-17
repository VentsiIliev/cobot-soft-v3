from enum import Enum


class GlueSettingKey(Enum):
    SPRAY_WIDTH = "Spray Width"
    SPRAYING_HEIGHT = "Spraying Height"
    FAN_SPEED = "Fan Speed"
    TIME_BETWEEN_GENERATOR_AND_GLUE = "Generator-Glue Delay"
    MOTOR_SPEED = "Pump Speed"
    REVERSE_DURATION = "Pump Reverse Time"
    SPEED_REVERSE = "Pump Speed Reverse"
    RZ_ANGLE = "RZ Angle"
    GLUE_TYPE = "Glue Type"
    GENERATOR_TIMEOUT = "Generator Timeout"
    TIME_BEFORE_MOTION = "Time Before Motion"
    TIME_BEFORE_STOP = "Time Before Stop"
    REACH_START_THRESHOLD = "Reach Start Threshold"
    REACH_END_THRESHOLD = "Reach End Threshold"
    GLUE_SPEED_COEFFICIENT = "Glue Speed Coefficient"
    GLUE_ACCELERATION_COEFFICIENT = "Glue Acceleration Coefficient"

    INITIAL_RAMP_SPEED = "Initial Ramp Speed"
    FORWARD_RAMP_STEPS = "Forward Ramp Steps"
    REVERSE_RAMP_STEPS = "Reverse Ramp Steps"
    INITIAL_RAMP_SPEED_DURATION = "Initial Ramp Speed Duration"

    SPRAY_ON = "Spray On"

    def getAsLabel(self):
        return self.value + ":"
from enum import Enum, IntEnum
from typing import Dict, Any, Optional, List
import time
from dataclasses import dataclass
import json


# ============================================================================
# ERROR CODE DEFINITIONS
# ============================================================================


class HardwareErrorCode(IntEnum):
    """Hardware-related error codes (3000-3999)"""
    # Robot Errors (3000-3099)
    ROBOT_CONNECTION_FAILED = 3001
    ROBOT_CALIBRATION_FAILED = 3002
    ROBOT_MOVEMENT_FAILED = 3003
    ROBOT_POSITION_INVALID = 3004
    ROBOT_EMERGENCY_STOP = 3005
    ROBOT_SERVO_ERROR = 3006
    ROBOT_COLLISION_DETECTED = 3007

    # Vision System Errors (3100-3199)
    CAMERA_CONNECTION_FAILED = 3101
    CAMERA_CALIBRATION_FAILED = 3102
    IMAGE_CAPTURE_FAILED = 3103
    IMAGE_PROCESSING_FAILED = 3104
    VISION_ALGORITHM_FAILED = 3105

    # Glue System Errors (3200-3299)
    GLUE_PUMP_FAILED = 3201
    GLUE_PRESSURE_INVALID = 3202
    GLUE_TEMPERATURE_INVALID = 3203
    GLUE_FLOW_RATE_INVALID = 3204
    GLUE_RESERVOIR_EMPTY = 3205

    # Conveyor/Belt Errors (3300-3399)
    BELT_MOVEMENT_FAILED = 3301
    BELT_POSITION_SENSOR_FAILED = 3302
    BELT_SPEED_INVALID = 3303
    WORKPIECE_NOT_DETECTED = 3304





class SafetyErrorCode(IntEnum):
    """Safety-related error codes (7000-7999)"""
    SAFETY_FENCE_OPEN = 7001
    EMERGENCY_STOP_ACTIVATED = 7002
    SAFETY_LIGHT_CURTAIN_BROKEN = 7003
    OPERATOR_PRESENCE_DETECTED = 7004
    SAFETY_SYSTEM_MALFUNCTION = 7005
    DANGEROUS_POSITION_DETECTED = 7006
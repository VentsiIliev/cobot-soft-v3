from dataclasses import dataclass, field
from typing import Dict, List, Optional


def get_default_config():
    """Get default configuration data"""
    movement_groups = {
        "LOGIN_POS": MovementGroup(
            position="[59.118, -334, 721.66, 180, 0, -90]",
            velocity=0,
            acceleration=0
        ),
        "HOME_POS": MovementGroup(
            position="[-232.343, -93.902, 819.846, 180, 0, 90]",
            velocity=0,
            acceleration=0
        ),
        "CALIBRATION_POS": MovementGroup(
            position="[-25.4, 370.001, 819.846, 180, 0, 0]",
            velocity=0,
            acceleration=0
        ),
        "JOG": MovementGroup(
            velocity=20,
            acceleration=100
        ),
        "NOZZLE CLEAN": MovementGroup(
            velocity=30,
            acceleration=30,
            points=[
                "[-165.037, -300.705, 298.201, 180, 0, 90]",
                "[-165.037, -431.735, 298.201, 180, 0, 90]",
                "[-165.037, -400, 298.201, 180, 0, 90]"
            ]
        ),
        "TOOL CHANGER": MovementGroup(
            velocity=100,
            acceleration=30,
            points=[]
        ),
        "SLOT 0 PICKUP": MovementGroup(
            points=[
                "[-98.555, -224.46, 300, 180, 0, 90]",
                "[-98.555, -224.46, 181.11, 180, 0, 90]",
                "[-98.555, -190.696, 181.11, 180, 0, 90]",
                "[-98.555, -190.696, 300, 180, 0, 90]"
            ]
        ),
        "SLOT 0 DROPOFF": MovementGroup(
            points=[
                "[-98.555, -190.696, 300, 180, 0, 90]",
                "[-98.555, -190.696, 181.11, 180, 0, 90]",
                "[-98.555, -224.46, 181.11, 180, 0, 90]",
                "[-98.555, -224.46, 300, 180, 0, 90]"
            ]
        ),
        "SLOT 1 PICKUP": MovementGroup(
            points=[
                "[-247.871, -221.213, 300, 180, 0, 90]",
                "[-247.871, -221.213, 180.278, 180, 0, 90]",
                "[-247.871, -150, 180.278, 180, 0, 90]"
            ]
        ),
        "SLOT 1 DROPOFF": MovementGroup(
            points=[
                "[-247.871, -150, 180.278, 180, 0, 90]",
                "[-247.871, -221.213, 180.278, 180, 0, 90]",
                "[-247.871, -221.213, 300, 180, 0, 90]"
            ]
        ),
        "SLOT 4 PICKUP": MovementGroup(
            points=[
                "[-441.328, -280.786, 300, -180, 0, 90]",
                "[-441.328, -280.786, 184.912, -180, 0, 90]",
                "[-441.328, -201.309, 184.912, -180, 0, 90]"
            ]
        ),
        "SLOT 4 DROPOFF": MovementGroup(
            points=[
                "[-441.328, -201.309, 184.912, -180, 0, 90]",
                "[-441.328, -280.786, 184.912, -180, 0, 90]",
                "[-441.328, -280.786, 300, -180, 0, 90]"
            ]
        )
    }

    return RobotConfig(
        robot_ip="192.168.58.2",
        robot_tool=0,
        robot_user=0,
        tcp_x_offset=0.0,
        tcp_y_offset=0.0,
        tcp_x_step_distance=50.0,
        tcp_x_step_offset=0.1,
        tcp_y_step_distance=50.0,
        tcp_y_step_offset=0.1,
        movement_groups=movement_groups,
        safety_limits=SafetyLimits(),
        global_motion_settings=GlobalMotionSettings()
    )

@dataclass
class MovementGroup:
    """Data class representing a movement group configuration"""
    velocity: int = 0
    acceleration: int = 0
    position: Optional[str] = None
    points: List[str] = field(default_factory=list)
    iterations: int = 1

    @classmethod
    def from_dict(cls, data: Dict) -> 'MovementGroup':
        """Create MovementGroup from dictionary data"""
        return cls(
            velocity=data.get("velocity", 0),
            acceleration=data.get("acceleration", 0),
            position=data.get("position"),
            points=data.get("points", []),
            iterations=data.get("iterations", 1)
        )

    def to_dict(self) -> Dict:
        """Convert MovementGroup to dictionary"""
        result = {
            "velocity": self.velocity,
            "acceleration": self.acceleration,
            "iterations": self.iterations
        }
        if self.position:
            result["position"] = self.position
        if self.points:
            result["points"] = self.points
        return result
    
    def parse_position(self) -> Optional[List[float]]:
        """Parse position string into list of floats"""
        if not self.position:
            return None
        
        try:
            # Remove brackets and split by comma
            position_str = self.position.strip("[]")
            values = [float(x.strip()) for x in position_str.split(",")]
            return values
        except (ValueError, AttributeError):
            return None
    
    def parse_points(self) -> List[List[float]]:
        """Parse all trajectory points into lists of floats"""
        parsed_points = []
        for point in self.points:
            try:
                # Remove brackets and split by comma
                point_str = point.strip("[]")
                values = [float(x.strip()) for x in point_str.split(",")]
                parsed_points.append(values)
            except (ValueError, AttributeError):
                continue
        return parsed_points


@dataclass
class SafetyLimits:
    """Data class representing robot safety limits"""
    x_min: int = -500
    x_max: int = 500
    y_min: int = -500
    y_max: int = 500
    z_min: int = 100
    z_max: int = 800
    rx_min: int = 170
    rx_max: int = 190
    ry_min: int = -10
    ry_max: int = 10
    rz_min: int = -180
    rz_max: int = 180

    @classmethod
    def from_dict(cls, data: Dict) -> 'SafetyLimits':
        """Create SafetyLimits from dictionary data"""
        return cls(
            x_min=data.get("x_min", -500),
            x_max=data.get("x_max", 500),
            y_min=data.get("y_min", -500),
            y_max=data.get("y_max", 500),
            z_min=data.get("z_min", 100),
            z_max=data.get("z_max", 800),
            rx_min=data.get("rx_min", 170),
            rx_max=data.get("rx_max", 190),
            ry_min=data.get("ry_min", -10),
            ry_max=data.get("ry_max", 10),
            rz_min=data.get("rz_min", -180),
            rz_max=data.get("rz_max", 180)
        )

    def to_dict(self) -> Dict:
        """Convert SafetyLimits to dictionary"""
        return {
            "x_min": self.x_min,
            "x_max": self.x_max,
            "y_min": self.y_min,
            "y_max": self.y_max,
            "z_min": self.z_min,
            "z_max": self.z_max,
            "rx_min": self.rx_min,
            "rx_max": self.rx_max,
            "ry_min": self.ry_min,
            "ry_max": self.ry_max,
            "rz_min": self.rz_min,
            "rz_max": self.rz_max
        }


@dataclass
class GlobalMotionSettings:
    """Data class representing global motion settings"""
    global_velocity: int = 100
    global_acceleration: int = 100
    emergency_decel: int = 500
    max_jog_step: int = 50

    @classmethod
    def from_dict(cls, data: Dict) -> 'GlobalMotionSettings':
        """Create GlobalMotionSettings from dictionary data"""
        return cls(
            global_velocity=data.get("global_velocity", 100),
            global_acceleration=data.get("global_acceleration", 100),
            emergency_decel=data.get("emergency_decel", 500),
            max_jog_step=data.get("max_jog_step", 50)
        )

    def to_dict(self) -> Dict:
        """Convert GlobalMotionSettings to dictionary"""
        return {
            "global_velocity": self.global_velocity,
            "global_acceleration": self.global_acceleration,
            "emergency_decel": self.emergency_decel,
            "max_jog_step": self.max_jog_step
        }
from dataclasses import dataclass, asdict

@dataclass
class OffsetDirectionMap:
    """Represents direction-following states for TCP offset correction"""
    pos_x: bool = True
    neg_x: bool = True
    pos_y: bool = True
    neg_y: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> 'OffsetDirectionMap':
        """Create an OffsetDirectionMap from a dict"""
        return cls(
            pos_x=data.get("+X", True),
            neg_x=data.get("-X", True),
            pos_y=data.get("+Y", True),
            neg_y=data.get("-Y", True)
        )

    def to_dict(self) -> dict:
        """Convert OffsetDirectionMap to dict for JSON"""
        return {
            "+X": self.pos_x,
            "-X": self.neg_x,
            "+Y": self.pos_y,
            "-Y": self.neg_y
        }


@dataclass
class RobotConfig:
    """Data class representing the complete robot configuration"""
    robot_ip: str = "192.168.58.2"
    robot_tool: int = 0
    robot_user: int = 0
    tcp_x_offset: float = 0.0
    tcp_y_offset: float = 0.0

    # New dynamic offset fields
    tcp_x_step_distance: float = 50.0
    tcp_x_step_offset: float = 0.1
    tcp_y_step_distance: float = 50.0
    tcp_y_step_offset: float = 0.1
    offset_direction_map: OffsetDirectionMap = field(default_factory=OffsetDirectionMap)

    movement_groups: Dict[str, MovementGroup] = field(default_factory=dict)
    safety_limits: SafetyLimits = field(default_factory=SafetyLimits)
    global_motion_settings: GlobalMotionSettings = field(default_factory=GlobalMotionSettings)

    @classmethod
    def from_dict(cls, data: Dict) -> 'RobotConfig':
        """Create RobotConfig from dictionary data"""
        movement_groups = {}
        for group_name, group_data in data.get("MOVEMENT_GROUPS", {}).items():
            movement_groups[group_name] = MovementGroup.from_dict(group_data)

        safety_limits = SafetyLimits.from_dict(data.get("SAFETY_LIMITS", {}))
        global_motion_settings = GlobalMotionSettings.from_dict(data.get("GLOBAL_MOTION_SETTINGS", {}))
        # Create OffsetDirectionMap from the dictionary (with default values if missing)
        offset_direction_map = OffsetDirectionMap.from_dict(data.get("OFFSET_DIRECTION_MAP", {}))
        return cls(
            robot_ip=data.get("ROBOT_IP", "192.168.58.2"),
            robot_tool=data.get("ROBOT_TOOL", 0),
            robot_user=data.get("ROBOT_USER", 0),
            tcp_x_offset=data.get("TCP_X_OFFSET", 0.0), # base offset x
            tcp_y_offset=data.get("TCP_Y_OFFSET", 0.0), # base offset y
            tcp_x_step_distance=data.get("TCP_X_STEP_DISTANCE", 50.0), # this will be removed in future
            tcp_x_step_offset=data.get("TCP_X_STEP_OFFSET", 0.1), # step/coeff per mm x
            tcp_y_step_distance=data.get("TCP_Y_STEP_DISTANCE", 50.0), # this will be removed in future
            tcp_y_step_offset=data.get("TCP_Y_STEP_OFFSET", 0.1), # step/coeff per mm y
            offset_direction_map=offset_direction_map,
            movement_groups=movement_groups,
            safety_limits=safety_limits,
            global_motion_settings=global_motion_settings
        )

    def to_dict(self) -> Dict:
        """Convert RobotConfig to dictionary for JSON serialization"""
        return {
            "ROBOT_IP": self.robot_ip,
            "ROBOT_TOOL": self.robot_tool,
            "ROBOT_USER": self.robot_user,
            "TCP_X_OFFSET": self.tcp_x_offset,
            "TCP_Y_OFFSET": self.tcp_y_offset,
            "TCP_X_STEP_DISTANCE": self.tcp_x_step_distance,
            "TCP_X_STEP_OFFSET": self.tcp_x_step_offset,
            "TCP_Y_STEP_DISTANCE": self.tcp_y_step_distance,
            "TCP_Y_STEP_OFFSET": self.tcp_y_step_offset,
            "OFFSET_DIRECTION_MAP": self.offset_direction_map.to_dict(),
            "MOVEMENT_GROUPS": {name: group.to_dict() for name, group in self.movement_groups.items()},
            "SAFETY_LIMITS": self.safety_limits.to_dict(),
            "GLOBAL_MOTION_SETTINGS": self.global_motion_settings.to_dict()
        }

    def __str__(self):
        import json
        return json.dumps(self.to_dict(), indent=4)
    
    # Convenience methods for accessing specific movement groups
    
    def getLoginPosConfig(self) -> Optional[MovementGroup]:
        """Get LOGIN_POS movement group configuration"""
        return self.movement_groups.get("LOGIN_POS")
    
    def getHomePosConfig(self) -> Optional[MovementGroup]:
        """Get HOME_POS movement group configuration"""
        return self.movement_groups.get("HOME_POS")
    
    def getCalibrationPosConfig(self) -> Optional[MovementGroup]:
        """Get CALIBRATION_POS movement group configuration"""
        return self.movement_groups.get("CALIBRATION_POS")
    
    def getJogConfig(self) -> Optional[MovementGroup]:
        """Get JOG movement group configuration"""
        return self.movement_groups.get("JOG")
    
    def getNozzleCleanConfig(self) -> Optional[MovementGroup]:
        """Get NOZZLE CLEAN movement group configuration"""
        return self.movement_groups.get("NOZZLE CLEAN")
    
    def getToolChangerConfig(self) -> Optional[MovementGroup]:
        """Get TOOL CHANGER movement group configuration"""
        return self.movement_groups.get("TOOL CHANGER")
    
    def getSlot0PickupConfig(self) -> Optional[MovementGroup]:
        """Get SLOT 0 PICKUP movement group configuration"""
        return self.movement_groups.get("SLOT 0 PICKUP")
    
    def getSlot0DropoffConfig(self) -> Optional[MovementGroup]:
        """Get SLOT 0 DROPOFF movement group configuration"""
        return self.movement_groups.get("SLOT 0 DROPOFF")
    
    def getSlot1PickupConfig(self) -> Optional[MovementGroup]:
        """Get SLOT 1 PICKUP movement group configuration"""
        return self.movement_groups.get("SLOT 1 PICKUP")
    
    def getSlot1DropoffConfig(self) -> Optional[MovementGroup]:
        """Get SLOT 1 DROPOFF movement group configuration"""
        return self.movement_groups.get("SLOT 1 DROPOFF")
    
    def getSlot4PickupConfig(self) -> Optional[MovementGroup]:
        """Get SLOT 4 PICKUP movement group configuration"""
        return self.movement_groups.get("SLOT 4 PICKUP")
    
    def getSlot4DropoffConfig(self) -> Optional[MovementGroup]:
        """Get SLOT 4 DROPOFF movement group configuration"""
        return self.movement_groups.get("SLOT 4 DROPOFF")
    
    # Helper methods for position strings (single positions)
    
    def getLoginPosition(self) -> Optional[str]:
        """Get LOGIN_POS position string"""
        config = self.getLoginPosConfig()
        return config.position if config else None
    
    def getHomePosition(self) -> Optional[str]:
        """Get HOME_POS position string"""
        config = self.getHomePosConfig()
        return config.position if config else None
    
    def getCalibrationPosition(self) -> Optional[str]:
        """Get CALIBRATION_POS position string"""
        config = self.getCalibrationPosConfig()
        return config.position if config else None
    
    # Helper methods for trajectory points (multi-point positions)
    
    def getNozzleCleanPoints(self) -> List[str]:
        """Get NOZZLE CLEAN trajectory points"""
        config = self.getNozzleCleanConfig()
        return config.points if config else []
    
    def getSlot0PickupPoints(self) -> List[str]:
        """Get SLOT 0 PICKUP trajectory points"""
        config = self.getSlot0PickupConfig()
        return config.points if config else []
    
    def getSlot0DropoffPoints(self) -> List[str]:
        """Get SLOT 0 DROPOFF trajectory points"""
        config = self.getSlot0DropoffConfig()
        return config.points if config else []
    
    def getSlot1PickupPoints(self) -> List[str]:
        """Get SLOT 1 PICKUP trajectory points"""
        config = self.getSlot1PickupConfig()
        return config.points if config else []
    
    def getSlot1DropoffPoints(self) -> List[str]:
        """Get SLOT 1 DROPOFF trajectory points"""
        config = self.getSlot1DropoffConfig()
        return config.points if config else []
    
    def getSlot4PickupPoints(self) -> List[str]:
        """Get SLOT 4 PICKUP trajectory points"""
        config = self.getSlot4PickupConfig()
        return config.points if config else []
    
    def getSlot4DropoffPoints(self) -> List[str]:
        """Get SLOT 4 DROPOFF trajectory points"""
        config = self.getSlot4DropoffConfig()
        return config.points if config else []
    
    def getToolChangerPoints(self) -> List[str]:
        """Get TOOL CHANGER trajectory points"""
        config = self.getToolChangerConfig()
        return config.points if config else []
    
    # Helper methods for parsed positions (returns lists of floats ready for robot)
    
    def getLoginPositionParsed(self) -> Optional[List[float]]:
        """Get LOGIN_POS position as parsed list of floats"""
        config = self.getLoginPosConfig()
        return config.parse_position() if config else None
    
    def getHomePositionParsed(self) -> Optional[List[float]]:
        """Get HOME_POS position as parsed list of floats"""
        config = self.getHomePosConfig()
        return config.parse_position() if config else None
    
    def getCalibrationPositionParsed(self) -> Optional[List[float]]:
        """Get CALIBRATION_POS position as parsed list of floats"""
        config = self.getCalibrationPosConfig()
        return config.parse_position() if config else None
    
    def getNozzleCleanPointsParsed(self) -> List[List[float]]:
        """Get NOZZLE CLEAN trajectory points as parsed lists of floats"""
        config = self.getNozzleCleanConfig()
        return config.parse_points() if config else []
    
    def getSlot0PickupPointsParsed(self) -> List[List[float]]:
        """Get SLOT 0 PICKUP trajectory points as parsed lists of floats"""
        config = self.getSlot0PickupConfig()
        return config.parse_points() if config else []
    
    def getSlot0DropoffPointsParsed(self) -> List[List[float]]:
        """Get SLOT 0 DROPOFF trajectory points as parsed lists of floats"""
        config = self.getSlot0DropoffConfig()
        return config.parse_points() if config else []
    
    def getSlot1PickupPointsParsed(self) -> List[List[float]]:
        """Get SLOT 1 PICKUP trajectory points as parsed lists of floats"""
        config = self.getSlot1PickupConfig()
        return config.parse_points() if config else []
    
    def getSlot1DropoffPointsParsed(self) -> List[List[float]]:
        """Get SLOT 1 DROPOFF trajectory points as parsed lists of floats"""
        config = self.getSlot1DropoffConfig()
        return config.parse_points() if config else []
    
    def getSlot4PickupPointsParsed(self) -> List[List[float]]:
        """Get SLOT 4 PICKUP trajectory points as parsed lists of floats"""
        config = self.getSlot4PickupConfig()
        return config.parse_points() if config else []
    
    def getSlot4DropoffPointsParsed(self) -> List[List[float]]:
        """Get SLOT 4 DROPOFF trajectory points as parsed lists of floats"""
        config = self.getSlot4DropoffConfig()
        return config.parse_points() if config else []
    
    def getToolChangerPointsParsed(self) -> List[List[float]]:
        """Get TOOL CHANGER trajectory points as parsed lists of floats"""
        config = self.getToolChangerConfig()
        return config.parse_points() if config else []
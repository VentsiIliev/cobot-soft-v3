"""
Robot Application Interface

This module defines the standard interface that all robot applications must implement.
It provides a contract for operation control, calibration, workpiece handling, and configuration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from enum import Enum

from core.base_robot_application import ApplicationType


class OperationMode(Enum):
    """Available operation modes for robot applications"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SEMI_AUTOMATIC = "semi_automatic"
    TEST = "test"
    DEMO = "demo"


class CalibrationStatus(Enum):
    """Calibration status indicators"""
    NOT_CALIBRATED = "not_calibrated"
    IN_PROGRESS = "in_progress"
    CALIBRATED = "calibrated"
    FAILED = "failed"
    EXPIRED = "expired"


class WorkpieceProcessingResult(Enum):
    """Results of workpiece processing operations"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    ERROR = "error"


class RobotApplicationInterface(ABC):
    """
    Standard interface that all robot applications must implement.
    
    This interface defines the contract for:
    - Operation control (start, stop, pause, resume)
    - Calibration management (robot, camera, tools)
    - Workpiece handling and processing
    - Configuration and settings management
    - Status monitoring and reporting
    """
    
    # ========== Core Operation Control ==========
    
    @abstractmethod
    def start(self, mode: OperationMode = OperationMode.AUTOMATIC, **kwargs) -> Dict[str, Any]:
        """
        Start the robot application operation.
        
        Args:
            mode: Operation mode (automatic, manual, etc.)
            **kwargs: Additional application-specific parameters
            
        Returns:
            Dict containing operation result and status
        """
        pass
    
    @abstractmethod
    def stop(self, emergency: bool = False) -> Dict[str, Any]:
        """
        Stop the robot application operation.
        
        Args:
            emergency: Whether this is an emergency stop
            
        Returns:
            Dict containing operation result
        """
        pass
    
    @abstractmethod
    def pause(self) -> Dict[str, Any]:
        """
        Pause the robot application operation.
        
        Returns:
            Dict containing operation result
        """
        pass
    
    @abstractmethod
    def resume(self) -> Dict[str, Any]:
        """
        Resume the robot application operation.
        
        Returns:
            Dict containing operation result
        """
        pass
    
    @abstractmethod
    def reset(self) -> Dict[str, Any]:
        """
        Reset the robot application to initial state.
        
        Returns:
            Dict containing operation result
        """
        pass
    
    # ========== Calibration Management ==========
    
    @abstractmethod
    def calibrate_robot(self) -> Dict[str, Any]:
        """
        Calibrate the robot coordinate system.
        

        Returns:
            Dict containing calibration result and status
        """
        pass
    
    @abstractmethod
    def calibrate_camera(self) -> Dict[str, Any]:
        """
        Calibrate the camera system.
        

        Returns:
            Dict containing calibration result and status
        """
        pass

    
    # ========== Workpiece Handling ==========
    
    @abstractmethod
    def load_workpiece(self, workpiece_id: str) -> Dict[str, Any]:
        """
        Load a workpiece for processing.
        
        Args:
            workpiece_id: Unique identifier of the workpiece
            
        Returns:
            Dict containing load result and workpiece info
        """
        pass
    
    @abstractmethod
    def process_workpiece(self, workpiece_id: str, **parameters) -> Dict[str, Any]:
        """
        Process a workpiece with the robot application.
        
        Args:
            workpiece_id: Unique identifier of the workpiece
            **parameters: Application-specific processing parameters
            
        Returns:
            Dict containing processing result and statistics
        """
        pass


    # ========== Tool and Hardware Control ==========
    
    @abstractmethod
    def clean_tool(self, tool_id: str) -> Dict[str, Any]:
        """
        Clean a specific tool (e.g., nozzle cleaning).
        
        Args:
            tool_id: Identifier of the tool to clean
            
        Returns:
            Dict containing cleaning result
        """
        pass
    

    @abstractmethod
    def home_robot(self) -> Dict[str, Any]:
        """
        Move robot to home position.
        
        Returns:
            Dict containing operation result
        """
        pass

# ========== Helper Data Classes ==========

class ApplicationInfo:
    """Information about a robot application"""
    
    def __init__(self, 
                 app_type: ApplicationType, 
                 name: str, 
                 version: str,
                 description: str,
                 supported_operations: List[str],
                 supported_tools: List[str],
                 supported_workpieces: List[str]):
        self.app_type = app_type
        self.name = name
        self.version = version
        self.description = description
        self.supported_operations = supported_operations
        self.supported_tools = supported_tools
        self.supported_workpieces = supported_workpieces
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "type": self.app_type.value,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "supported_operations": self.supported_operations,
            "supported_tools": self.supported_tools,
            "supported_workpieces": self.supported_workpieces
        }


class OperationResult:
    """Standardized operation result"""
    
    def __init__(self, 
                 success: bool, 
                 message: str, 
                 data: Dict[str, Any] = None,
                 warnings: List[str] = None,
                 errors: List[str] = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.warnings = warnings or []
        self.errors = errors or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "warnings": self.warnings,
            "errors": self.errors
        }
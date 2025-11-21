"""
Robot Application Interface

This module defines the standard interface that all robot applications must implement.
It provides a contract for operation control, calibration, workpiece handling, and configuration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from enum import Enum

from core.base_robot_application import ApplicationType
from core.operation_state_management import OperationResult


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
    def start(self, **kwargs) -> OperationResult:
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
    def stop(self, emergency: bool = False) -> OperationResult:
        """
        Stop the robot application operation.
        
        Args:
            emergency: Whether this is an emergency stop
            
        Returns:
            Dict containing operation result
        """
        pass

    @abstractmethod
    def pause(self) -> OperationResult:
        """
        Pause the robot application operation.
        
        Returns:
            Dict containing operation result
        """
        pass
    
    @abstractmethod
    def resume(self) -> OperationResult:
        """
        Resume the robot application operation.
        
        Returns:
            Dict containing operation result
        """
        pass
    
    @abstractmethod
    def reset(self) -> OperationResult:
        """
        Reset the robot application to initial state.
        
        Returns:
            Dict containing operation result
        """
        pass
    
    # ========== Calibration Management ==========
    
    @abstractmethod
    def calibrate_robot(self) -> OperationResult:
        """
        Calibrate the robot coordinate system.
        

        Returns:
            Dict containing calibration result and status
        """
        pass
    
    @abstractmethod
    def calibrate_camera(self) -> OperationResult:
        """
        Calibrate the camera system.
        

        Returns:
            Dict containing calibration result and status
        """
        pass


    # ========== Tool and Hardware Control ==========

    @abstractmethod
    def home_robot(self) -> OperationResult:
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

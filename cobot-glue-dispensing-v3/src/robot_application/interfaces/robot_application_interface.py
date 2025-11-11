"""
Robot Application Interface

This module defines the standard interface that all robot applications must implement.
It provides a contract for operation control, calibration, workpiece handling, and configuration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum

from src.robot_application.base_robot_application import ApplicationType, ApplicationState


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
    

    
    @abstractmethod
    def get_calibration_status(self) -> Dict[str, CalibrationStatus]:
        """
        Get current calibration status for all components.
        
        Returns:
            Dict mapping component names to their calibration status
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
    
    @abstractmethod
    def validate_workpiece(self, workpiece_id: str) -> Dict[str, Any]:
        """
        Validate that a workpiece can be processed by this application.
        
        Args:
            workpiece_id: Unique identifier of the workpiece
            
        Returns:
            Dict containing validation result and any issues found
        """
        pass
    
    @abstractmethod
    def get_workpiece_requirements(self) -> Dict[str, Any]:
        """
        Get requirements for workpieces that can be processed by this application.
        
        Returns:
            Dict containing workpiece requirements specification
        """
        pass
    
    # ========== Configuration Management ==========
    
    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get current application configuration.
        
        Returns:
            Dict containing all configuration parameters
        """
        pass
    
    @abstractmethod
    def update_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update application configuration.
        
        Args:
            config: Configuration parameters to update
            
        Returns:
            Dict containing update result and validation errors if any
        """
        pass
    
    @abstractmethod
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate current application configuration.
        
        Returns:
            Dict containing validation result and any issues found
        """
        pass
    
    @abstractmethod
    def get_default_configuration(self) -> Dict[str, Any]:
        """
        Get default configuration for this application.
        
        Returns:
            Dict containing default configuration parameters
        """
        pass
    
    # ========== Status and Monitoring ==========
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive application status.
        
        Returns:
            Dict containing current status of all components
        """
        pass
    
    @abstractmethod
    def get_operation_statistics(self) -> Dict[str, Any]:
        """
        Get operation statistics and performance metrics.
        
        Returns:
            Dict containing statistics like cycle time, success rate, etc.
        """
        pass
    
    @abstractmethod
    def get_health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all application components.
        
        Returns:
            Dict containing health status of all components
        """
        pass
    
    @abstractmethod
    def get_error_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent error log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of error log entries
        """
        pass
    
    # ========== Application-Specific Information ==========
    
    @abstractmethod
    def get_application_type(self) -> ApplicationType:
        """Get the type of this application"""
        pass
    
    @abstractmethod
    def get_application_name(self) -> str:
        """Get the human-readable name of this application"""
        pass
    
    @abstractmethod
    def get_application_version(self) -> str:
        """Get the version of this application"""
        pass
    
    @abstractmethod
    def get_supported_operations(self) -> List[str]:
        """
        Get list of operations supported by this application.
        
        Returns:
            List of operation names
        """
        pass
    
    @abstractmethod
    def get_supported_tools(self) -> List[str]:
        """
        Get list of tools supported by this application.
        
        Returns:
            List of tool identifiers
        """
        pass
    
    @abstractmethod
    def get_supported_workpiece_types(self) -> List[str]:
        """
        Get list of workpiece types supported by this application.
        
        Returns:
            List of workpiece type identifiers
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
    
    # ========== Safety and Emergency ==========
    
    @abstractmethod
    def emergency_stop(self) -> Dict[str, Any]:
        """
        Emergency stop all robot operations immediately.
        
        Returns:
            Dict containing emergency stop result
        """
        pass
    
    @abstractmethod
    def safety_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive safety check.
        
        Returns:
            Dict containing safety check results and any warnings
        """
        pass
    
    @abstractmethod
    def get_safety_status(self) -> Dict[str, Any]:
        """
        Get current safety system status.
        
        Returns:
            Dict containing safety system status
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
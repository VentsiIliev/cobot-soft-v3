"""
Robot Domain Service

Handles all robot-related operations with explicit return values.
No callbacks - just clean, clear method calls!
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Tuple
from enum import Enum

from ..types.ServiceResult import ServiceResult

# Import endpoint constants
from modules.shared.v1.endpoints import robot_endpoints

if TYPE_CHECKING:
    from frontend.pl_ui.controller.Controller import Controller


class RobotAxis(Enum):
    """Valid robot axes for movement operations"""
    X = "x"
    Y = "y" 
    Z = "z"
    RX = "rx"
    RY = "ry"
    RZ = "rz"


class RobotDirection(Enum):
    """Valid movement directions"""
    POSITIVE = "+"
    NEGATIVE = "-"


class RobotService:
    """
    Domain service for all robot operations.
    
    Provides explicit, type-safe methods for robot control.
    All methods return ServiceResult - no callbacks needed!
    
    Usage:
        result = robot_service.move_to_home()
        if result:
            print("Robot homed successfully!")
        else:
            print(f"Failed to home: {result.message}")
    """
    
    def __init__(self, controller: 'Controller', logger: logging.Logger):
        """
        Initialize the robot service.
        
        Args:
            controller: The main controller instance
            logger: Logger for this service
        """
        self.controller = controller
        self.logger = logger.getChild(self.__class__.__name__)
    
    def move_to_home(self, async_mode: bool = True) -> ServiceResult:
        """
        Move robot to home position.
        
        Args:
            async_mode: Whether to move asynchronously
        
        Returns:
            ServiceResult with success/failure status
        """
        try:
            self.logger.info("Moving robot to home position")
            
            status = self.controller.homeRobot(async_mode)
            
            if hasattr(status, 'value'):
                # If status is an enum or has a value attribute
                success = str(status) == "SUCCESS" or getattr(status, 'value', None) == "SUCCESS"
            else:
                # If it's a simple value
                success = str(status) == "SUCCESS"
            
            if success:
                return ServiceResult.success_result("Robot moved to home position successfully")
            else:
                return ServiceResult.error_result("Failed to move robot to home position")
                
        except Exception as e:
            error_msg = f"Failed to move robot home: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def jog_robot(self, axis: str, direction: str, step: float) -> ServiceResult:
        """
        Jog robot in specified axis and direction.
        
        Args:
            axis: Robot axis (x, y, z, rx, ry, rz)
            direction: Movement direction (+ or -)
            step: Step size for movement
        
        Returns:
            ServiceResult with success/failure status
        """
        try:
            # Validate inputs
            if axis not in [a.value for a in RobotAxis]:
                return ServiceResult.error_result(f"Invalid axis: {axis}. Valid axes: {[a.value for a in RobotAxis]}")
            
            if direction not in [d.value for d in RobotDirection]:
                return ServiceResult.error_result(f"Invalid direction: {direction}. Valid directions: {[d.value for d in RobotDirection]}")
            
            if not isinstance(step, (int, float)) or step <= 0:
                return ServiceResult.error_result("Step size must be a positive number")
            
            self.logger.info(f"Jogging robot: {axis} {direction} {step}")
            
            self.controller.handleJog(axis, direction, step)
            
            return ServiceResult.success_result(f"Robot jogged {axis} {direction} {step}")
                
        except Exception as e:
            error_msg = f"Failed to jog robot: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def move_to_calibration_position(self) -> ServiceResult:
        """Move robot to calibration position."""
        try:
            self.logger.info("Moving robot to calibration position")
            
            self.controller.handleMoveToCalibrationPos()
            
            return ServiceResult.success_result("Robot moved to calibration position")
                
        except Exception as e:
            error_msg = f"Failed to move to calibration position: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def move_to_login_position(self) -> ServiceResult:
        """Move robot to login position."""
        try:
            self.logger.info("Moving robot to login position")
            
            status = self.controller.handleLoginPos()
            
            # Check if the status indicates success
            success = str(status) == "SUCCESS"
            
            if success:
                return ServiceResult.success_result("Robot moved to login position")
            else:
                return ServiceResult.error_result("Failed to move robot to login position")
                
        except Exception as e:
            error_msg = f"Failed to move to login position: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def calibrate_robot(self) -> ServiceResult:
        """
        Calibrate robot system.
        
        Returns:
            ServiceResult with success/failure status and message
        """
        try:
            self.logger.info("Starting robot calibration")
            
            success, message = self.controller.handleCalibrateRobot()
            
            if success:
                return ServiceResult.success_result(f"Robot calibration successful: {message}")
            else:
                return ServiceResult.error_result(f"Robot calibration failed: {message}")
                
        except Exception as e:
            error_msg = f"Robot calibration failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def save_calibration_point(self) -> ServiceResult:
        """Save current position as calibration point."""
        try:
            self.logger.info("Saving robot calibration point")
            
            result = self.controller.handle(robot_endpoints.ROBOT_SAVE_CALIBRATION_POINT)
            
            return ServiceResult.success_result("Calibration point saved successfully")
                
        except Exception as e:
            error_msg = f"Failed to save calibration point: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def reset_errors(self) -> ServiceResult:
        """Reset robot errors."""
        try:
            self.logger.info("Resetting robot errors")
            
            status = self.controller.handleResetErrors()
            
            return ServiceResult.success_result("Robot errors reset successfully")
                
        except Exception as e:
            error_msg = f"Failed to reset robot errors: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def clean_nozzle(self) -> ServiceResult:
        """Execute nozzle cleaning procedure."""
        try:
            self.logger.info("Starting nozzle cleaning procedure")
            
            status = self.controller.handleCleanNozzle()
            
            return ServiceResult.success_result("Nozzle cleaning completed successfully")
                
        except Exception as e:
            error_msg = f"Failed to clean nozzle: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def update_config(self) -> ServiceResult:
        """Update robot configuration."""
        try:
            self.logger.info("Updating robot configuration")
            
            status = self.controller.handleRobotUpdateConfig()
            
            if str(status) == "SUCCESS":
                return ServiceResult.success_result("Robot configuration updated successfully")
            else:
                return ServiceResult.error_result("Failed to update robot configuration")
                
        except Exception as e:
            error_msg = f"Failed to update robot config: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
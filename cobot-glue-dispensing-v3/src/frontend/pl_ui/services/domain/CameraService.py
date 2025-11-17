"""
Camera Domain Service

Handles all camera-related operations with explicit return values.
No callbacks - just clean, clear method calls!
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types.ServiceResult import ServiceResult

# Import endpoint constants
from modules.shared.v1.endpoints import camera_endpoints

if TYPE_CHECKING:
    from frontend.pl_ui.controller.Controller import Controller


class CameraService:
    """
    Domain service for all camera operations.
    
    Provides explicit, type-safe methods for camera control.
    All methods return ServiceResult - no callbacks needed!
    
    Usage:
        result = camera_service.get_latest_frame()
        if result:
            frame = result.data
            display_frame(frame)
        else:
            print(f"Failed to get frame: {result.message}")
    """
    
    def __init__(self, controller: 'Controller', logger: logging.Logger):
        """
        Initialize the camera service.
        
        Args:
            controller: The main controller instance
            logger: Logger for this service
        """
        self.controller = controller
        self.logger = logger.getChild(self.__class__.__name__)
    
    def get_latest_frame(self) -> ServiceResult:
        """
        Get the latest camera frame.
        
        Returns:
            ServiceResult with frame data or error message
        """
        try:
            self.logger.debug("Requesting latest camera frame")
            
            frame = self.controller.updateCameraFeed()
            
            if frame is not None:
                return ServiceResult.success_result(
                    "Frame retrieved successfully",
                    data=frame
                )
            else:
                return ServiceResult.error_result("No frame available from camera")
                
        except Exception as e:
            error_msg = f"Failed to get camera frame: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def enable_raw_mode(self) -> ServiceResult:
        """Enable camera raw mode."""
        try:
            self.logger.info("Enabling camera raw mode")
            
            status = self.controller.handleRawModeOn()
            
            if str(status) == "SUCCESS":
                return ServiceResult.success_result("Camera raw mode enabled")
            else:
                return ServiceResult.error_result("Failed to enable camera raw mode")
                
        except Exception as e:
            error_msg = f"Failed to enable raw mode: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def disable_raw_mode(self) -> ServiceResult:
        """Disable camera raw mode."""
        try:
            self.logger.info("Disabling camera raw mode")
            
            status = self.controller.handleRawModeOff()
            
            if str(status) == "SUCCESS":
                return ServiceResult.success_result("Camera raw mode disabled")
            else:
                return ServiceResult.error_result("Failed to disable camera raw mode")
                
        except Exception as e:
            error_msg = f"Failed to disable raw mode: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def start_contour_detection(self) -> ServiceResult:
        """Start contour detection."""
        try:
            self.logger.info("Starting contour detection")
            
            self.controller.handleStartContourDetection()
            
            return ServiceResult.success_result("Contour detection started")
                
        except Exception as e:
            error_msg = f"Failed to start contour detection: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def stop_contour_detection(self) -> ServiceResult:
        """Stop contour detection."""
        try:
            self.logger.info("Stopping contour detection")
            
            self.controller.handleStopContourDetection()
            
            return ServiceResult.success_result("Contour detection stopped")
                
        except Exception as e:
            error_msg = f"Failed to stop contour detection: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def calibrate_camera(self) -> ServiceResult:
        """
        Calibrate camera system.
        
        Returns:
            ServiceResult with calibration success/failure
        """
        try:
            self.logger.info("Starting camera calibration")
            
            success, message = self.controller.handleCalibrateCamera()
            
            if success:
                return ServiceResult.success_result(f"Camera calibration successful: {message}")
            else:
                return ServiceResult.error_result(f"Camera calibration failed: {message}")
                
        except Exception as e:
            error_msg = f"Camera calibration failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def capture_calibration_image(self) -> ServiceResult:
        """
        Capture an image for calibration.
        
        Returns:
            ServiceResult with capture success/failure
        """
        try:
            self.logger.info("Capturing calibration image")
            
            success, message = self.controller.handleCaptureCalibrationImage()
            
            if success:
                return ServiceResult.success_result(f"Calibration image captured: {message}")
            else:
                return ServiceResult.error_result(f"Failed to capture calibration image: {message}")
                
        except Exception as e:
            error_msg = f"Failed to capture calibration image: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def save_work_area_points(self, points: List[Any]) -> ServiceResult:
        """
        Save work area calibration points.
        
        Args:
            points: List of work area points
        
        Returns:
            ServiceResult with save success/failure
        """
        try:
            if not points:
                return ServiceResult.error_result("Work area points cannot be empty")
            
            self.logger.info(f"Saving work area points: {len(points)} points")
            
            self.controller.handleSaveWorkAreaPoints(points)
            
            return ServiceResult.success_result(
                f"Work area points saved successfully ({len(points)} points)",
                data=points
            )
                
        except Exception as e:
            error_msg = f"Failed to save work area points: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def test_calibration(self) -> ServiceResult:
        """Test camera calibration."""
        try:
            self.logger.info("Testing camera calibration")
            
            self.controller.handleTestCalibration()
            
            return ServiceResult.success_result("Camera calibration test completed")
                
        except Exception as e:
            error_msg = f"Failed to test calibration: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
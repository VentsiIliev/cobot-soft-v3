"""
Camera Handler - API Gateway

Handles all camera and vision-related requests including calibration, image capture, and vision operations.
"""

from modules.shared.v1.Response import Response
from modules.shared.v1 import Constants
from modules.shared.v1.endpoints import camera_endpoints


class CameraHandler:
    """
    Handles camera and vision operations for the API gateway.
    
    This handler manages camera calibration, image capture, work area points, and vision processing.
    """
    
    def __init__(self, application, cameraSystemController):
        """
        Initialize the CameraHandler.
        
        Args:
            application: Main GlueSprayingApplication instance
            cameraSystemController: Camera system controller instance
        """
        self.application = application
        self.cameraSystemController = cameraSystemController
    
    def handle(self, parts, request, data=None):
        """
        Route camera requests to appropriate handlers.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response dictionary with operation result
        """
        # print(f"CameraHandler: Handling request: {request} with parts: {parts}")
        
        # Handle both new RESTful endpoints
        if request in [camera_endpoints.CAMERA_ACTION_CALIBRATE] or (len(parts) > 1 and parts[1] == "calibrate"):
            return self.handle_camera_calibration()
        elif request in [camera_endpoints.CAMERA_ACTION_SAVE_WORK_AREA_POINTS] or (len(parts) > 1 and parts[1] == "saveWorkAreaPoints"):
            return self.handle_save_work_area_points(data)
        elif request in [camera_endpoints.CAMERA_ACTION_GET_LATEST_FRAME,]:
            return self.handle_frame_request(parts, request, data)
        elif request in [camera_endpoints.CAMERA_ACTION_RAW_MODE_ON]:
            return self.handle_mode_change(parts, request, data)
        elif request in [camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF]:
            return self.handle_mode_change(parts, request, data)
        elif request in [camera_endpoints.START_CONTOUR_DETECTION]:
            return self.handle_contour_detection(parts, request, data)
        elif request in [camera_endpoints.STOP_CONTOUR_DETECTION]:
            return self.handle_contour_detection(parts, request, data)
        elif request in [camera_endpoints.CAMERA_ACTION_CAPTURE_CALIBRATION_IMAGE]:
            return self.handle_capture_request(parts, request, data)
        else:
            raise ValueError(f"CameraHandler: Unknown camera request: {request}")
            # Delegate to camera system controller for other operations
            response = self.cameraSystemController.handle(request, parts, data)
            return response
    
    def handle_camera_calibration(self):
        """
        Handle camera calibration requests.
        
        Returns:
            dict: Response indicating success or failure of calibration
        """
        print("CameraHandler: Handling camera calibration")
        
        try:
            result, message = self.application.calibrateCamera()
            print(f"CameraHandler: Calibration result: {result}, message: {message}")
            
            status = Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
            print(f"CameraHandler: Status: {status}")
            
            return Response(status, message=message).to_dict()
            
        except Exception as e:
            print(f"CameraHandler: Error calibrating camera: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Camera calibration error: {e}"
            ).to_dict()
    
    def handle_save_work_area_points(self, points):
        """
        Handle saving work area points.
        
        Args:
            points: Work area points data
            
        Returns:
            dict: Response indicating success or failure
        """
        print(f"CameraHandler: Handling save work area points: {points}")
        
        try:
            self.cameraSystemController.saveWorkAreaPoints(points)
            
            return Response(
                Constants.RESPONSE_STATUS_SUCCESS, 
                message="Work area points saved successfully"
            ).to_dict()
            
        except Exception as e:
            print(f"CameraHandler: Error saving work area points: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error saving work area points: {e}"
            ).to_dict()
    
    def handle_frame_request(self, parts, request, data=None):
        """
        Handle camera frame requests (latest frame, feed updates, etc.).
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response with frame data or operation result
        """
        # print(f"CameraHandler: Handling frame request: {request}")
        
        # Delegate to camera system controller
        return self.cameraSystemController.handle(request, parts, data)
    
    def handle_capture_request(self, parts, request, data=None):
        """
        Handle camera capture requests (calibration images, etc.).
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response with capture result
        """
        print(f"CameraHandler: Handling capture request: {request}")
        
        # Delegate to camera system controller
        return self.cameraSystemController.handle(request, parts, data)
    
    def handle_mode_change(self, parts, request, data=None):
        """
        Handle camera mode changes (raw mode on/off, etc.).
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response indicating success or failure of mode change
        """
        print(f"CameraHandler: Handling mode change: {request}")
        
        # Delegate to camera system controller
        return self.cameraSystemController.handle(request, parts, data)
    
    def handle_contour_detection(self, parts, request, data=None):
        """
        Handle contour detection operations (start/stop).
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response indicating success or failure of contour detection operation
        """
        print(f"CameraHandler: Handling contour detection: {request}")
        
        # Delegate to camera system controller
        return self.cameraSystemController.handle(request, parts, data)
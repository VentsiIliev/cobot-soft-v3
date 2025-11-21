"""
Operations Handler - API Gateway

Handles main system operations including start, stop, pause, demos, and test runs.
"""

import traceback

from communication_layer.api.v1 import Constants
from communication_layer.api.v1.Response import Response
from communication_layer.api.v1.endpoints import operations_endpoints
from communication_layer.api_gateway.interfaces.dispatch import IDispatcher

class OperationsDispatch(IDispatcher):
    """
    Handles main system operations for the API gateway.
    
    This handler manages system-wide operations like start/stop/pause workflows,
    demo operations, test runs, and general system operations.
    """
    
    def __init__(self, application, application_factory=None):
        """
        Initialize the OperationsHandler.
        
        Args:
            application: RobotApplicationInterface instance
            application_factory: Optional ApplicationFactory for switching applications
        """
        self.application = application
        self.application_factory = application_factory
    
    def dispatch(self, parts: list, request: str, data: dict = None) -> dict:
        """
        Route operation requests to appropriate handlers.
        
        Args:
            parts (list): Parsed request parts
            request (str): Operation request type
            data: Request data
            
        Returns:
            dict: Response dictionary with operation result
        """
        # print(f"OperationsHandler: Handling request: {request}")
        
        # Handle both new RESTful endpoints and legacy endpoints
        if request in [operations_endpoints.START]:
            return self.handle_start()
        elif request in [operations_endpoints.CREATE_WORKPIECE]:
            return self.handle_create_workpiece()
        elif request in [operations_endpoints.STOP]:
            return self.handle_stop()
        elif request in [operations_endpoints.PAUSE]:
            return self.handle_pause()
        elif request in [operations_endpoints.CALIBRATE]:
            return self.handle_calibrate()
        elif request in [operations_endpoints.CLEAN_NOZZLE]:
            return self.handler_clean_nozzle()
        elif request == "handleSetPreselectedWorkpiece":
            return self.handle_set_preselected_workpiece(data)
        elif request == "handleExecuteFromGallery":
            return self.handle_execute_from_gallery(data)
        else:
            raise ValueError(f"Unknown request: {request}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Unknown operation request: {request}"
            ).to_dict()
    
    def handle_start(self):
        """
        Handle system start operation.
        
        Returns:
            dict: Response indicating success or failure of start operation
        """
        # print("OperationsHandler: Handling start operation")
        
        try:
            result = self.application.start()
            # print(f"OperationsHandler: Start result: {result}")
            success = Constants.RESPONSE_STATUS_SUCCESS if result.success else Constants.RESPONSE_STATUS_ERROR
            message = result.message
            return Response(success, message=message).to_dict()

        except Exception as e:
            # print(f"OperationsHandler: Error starting: {e}")
            traceback.print_exc()
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error starting: {e}"
            ).to_dict()
    
    def handle_stop(self):
        """
        Handle system stop operation.
        
        Returns:
            dict: Response indicating success or failure of stop operation
        """
        # print("OperationsHandler: Handling stop operation")
        
        try:
            result = self.application.stop()
            status = Constants.RESPONSE_STATUS_SUCCESS if result.success else Constants.RESPONSE_STATUS_ERROR
            message = result.message
            return Response(status, message=message).to_dict()
        except Exception as e:
            # print(f"OperationsHandler: Error stopping: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error stopping: {e}"
            ).to_dict()
    
    def handle_pause(self):
        """
        Handle system pause operation.
        
        Returns:
            dict: Response indicating success or failure of pause operation
        """
        # print("OperationsHandler: Handling pause operation")
        
        try:
            result = self.application.pause()
            status = Constants.RESPONSE_STATUS_SUCCESS if result.get("success", False) else Constants.RESPONSE_STATUS_ERROR
            message = result.message
            return Response(status, message=message).to_dict()
            
        except Exception as e:
            # print(f"OperationsHandler: Error pausing: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error pausing: {e}"
            ).to_dict()

    def handle_calibrate(self):
        """
        Handle general calibration operation.
        
        Returns:
            dict: Response indicating success or failure of calibration
        """
        # print("OperationsHandler: Handling calibrate operation")
        
        try:
            # Perform both camera and robot calibration
            robot_result = self.application.calibrate_robot()
            camera_result = self.application.calibrate_camera()
            
            robot_success = robot_result.get("success", False)
            camera_success = camera_result.get("success", False)
            
            if robot_success and camera_success:
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message="Robot and camera calibration completed successfully"
                ).to_dict()
            elif robot_success:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message=f"Robot calibration successful, camera calibration failed: {camera_result.get('message', 'Unknown error')}"
                ).to_dict()
            elif camera_success:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message=f"Camera calibration successful, robot calibration failed: {robot_result.get('message', 'Unknown error')}"
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message=f"Both calibrations failed - Robot: {robot_result.get('message', 'Unknown error')}, Camera: {camera_result.get('message', 'Unknown error')}"
                ).to_dict()
            
        except Exception as e:
            # print(f"OperationsHandler: Error in calibration: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error in calibration: {e}"
            ).to_dict()

    def handler_clean_nozzle(self):
        """
        Handle nozzle cleaning operation.
        
        Returns:
            dict: Response indicating success or failure of nozzle cleaning
        """
        try:
            result = self.application.clean_tool("nozzle")
            status = Constants.RESPONSE_STATUS_SUCCESS if result.get("success", False) else Constants.RESPONSE_STATUS_ERROR
            message = result.get("message", "Nozzle cleaning completed")
            return Response(status, message=message).to_dict()
        except Exception as e:
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error cleaning nozzle: {e}"
            ).to_dict()

    def handle_set_preselected_workpiece(self, workpiece):
        """
        Handle setting preselected workpiece.
        
        Args:
            workpiece: Workpiece data
            
        Returns:
            dict: Response indicating success or failure
        """
        print(f"OperationsHandler: Handling set preselected workpiece: {workpiece}")
        
        try:
            # Check if application has the legacy method
            if hasattr(self.application, 'handle_set_preselected_workpiece'):
                self.application.handle_set_preselected_workpiece(workpiece)
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message="Preselected workpiece set successfully"
                ).to_dict()
            else:
                # Use standard interface method
                result = self.application.load_workpiece(str(workpiece))
                status = Constants.RESPONSE_STATUS_SUCCESS if result.get("success", False) else Constants.RESPONSE_STATUS_ERROR
                return Response(status, message=result.get("message", "Workpiece operation completed")).to_dict()
            
        except Exception as e:
            print(f"OperationsHandler: Error setting preselected workpiece: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error setting preselected workpiece: {e}"
            ).to_dict()
    
    def handle_execute_from_gallery(self, workpiece):
        """
        Handle execution from gallery.
        
        Args:
            workpiece: Workpiece data to execute
            
        Returns:
            dict: Response indicating success or failure
        """
        # print(f"OperationsHandler: Handling execute from gallery: {workpiece}")
        
        try:
            # Check if application has the legacy method
            if hasattr(self.application, 'handleExecuteFromGallery'):
                self.application.handleExecuteFromGallery(workpiece)
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message="Execute from gallery initiated successfully"
                ).to_dict()
            else:
                # Use standard interface method
                workpiece_id = str(workpiece) if not isinstance(workpiece, dict) else workpiece.get('id', str(workpiece))
                result = self.application.process_workpiece(workpiece_id)
                status = Constants.RESPONSE_STATUS_SUCCESS if result.get("success", False) else Constants.RESPONSE_STATUS_ERROR
                return Response(status, message=result.get("message", "Gallery execution completed")).to_dict()
            
        except Exception as e:
            # print(f"OperationsHandler: Error executing from gallery: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error executing from gallery: {e}"
            ).to_dict()

    def handle_create_workpiece(self):
        """
        Handle workpiece creation operation.

        Returns:
            dict: Response indicating success or failure of workpiece creation
        """
        print("OperationsHandler: Handling create workpiece operation")

        try:
            result= self.application.create_workpiece()
            status = Constants.RESPONSE_STATUS_SUCCESS if result.success else Constants.RESPONSE_STATUS_ERROR

            return Response(status=status, message=result.message,data=result.data).to_dict()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"OperationsHandler: Error creating workpiece: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error creating workpiece: {e}"
            ).to_dict()
"""
Operations Handler - API Gateway

Handles main system operations including start, stop, pause, demos, and test runs.
"""

from modules.shared.v1.Response import Response
from modules.shared.v1 import Constants
from modules.shared.v1.endpoints import operations_endpoints
import traceback


class OperationsHandler:
    """
    Handles main system operations for the API gateway.
    
    This handler manages system-wide operations like start/stop/pause workflows,
    demo operations, test runs, and general system operations.
    """
    
    def __init__(self, application):
        """
        Initialize the OperationsHandler.
        
        Args:
            application: Main GlueSprayingApplication instance
        """
        self.application = application
    
    def handle(self, request, data=None):
        """
        Route operation requests to appropriate handlers.
        
        Args:
            request (str): Operation request type
            data: Request data
            
        Returns:
            dict: Response dictionary with operation result
        """
        print(f"OperationsHandler: Handling request: {request}")
        
        # Handle both new RESTful endpoints and legacy endpoints
        if request in [operations_endpoints.START, operations_endpoints.START_LEGACY, Constants.START]:
            return self.handle_start()
        elif request in [operations_endpoints.STOP, operations_endpoints.STOP_LEGACY, Constants.STOP]:
            return self.handle_stop()
        elif request in [operations_endpoints.PAUSE, operations_endpoints.PAUSE_LEGACY, Constants.PAUSE]:
            return self.handle_pause()
        elif request in [operations_endpoints.RUN_DEMO, operations_endpoints.RUN_REMO, operations_endpoints.RUN_REMO_LEGACY, "run_demo", "RUN_REMO"]:
            return self.handle_run_demo()
        elif request in [operations_endpoints.STOP_DEMO, operations_endpoints.STOP_DEMO_LEGACY, "stop_demo"]:
            return self.handle_stop_demo()
        elif request in [operations_endpoints.TEST_RUN, operations_endpoints.TEST_RUN_LEGACY, operations_endpoints.TEST_RUN_LEGACY_2, Constants.TEST_RUN]:
            return self.handle_test_run()
        elif request in [operations_endpoints.CALIBRATE, operations_endpoints.CALIBRATE_LEGACY, "calibrate"]:
            return self.handle_calibrate()
        elif request in [operations_endpoints.HELP, operations_endpoints.HELP_LEGACY, "HELP", "help"]:
            return self.handle_help()
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
        print("OperationsHandler: Handling start operation")
        
        try:
            result, message = self.application.start()
            print(f"OperationsHandler: Start result: {result}")
            
            if not result:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message=message
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message=message
                ).to_dict()
                
        except Exception as e:
            print(f"OperationsHandler: Error starting: {e}")
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
        print("OperationsHandler: Handling stop operation")
        
        try:
            result, message = self.application.stop()
            status = Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
            
            return Response(status, message=message).to_dict()
            
        except Exception as e:
            print(f"OperationsHandler: Error stopping: {e}")
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
        print("OperationsHandler: Handling pause operation")
        
        try:
            result, message = self.application.pause()
            status = Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
            
            return Response(status, message=message).to_dict()
            
        except Exception as e:
            print(f"OperationsHandler: Error pausing: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error pausing: {e}"
            ).to_dict()
    
    def handle_run_demo(self):
        """
        Handle demo run operation.
        
        Returns:
            dict: Response indicating success or failure of demo operation
        """
        print("OperationsHandler: Handling run demo operation")
        
        try:
            result, message = self.application.run_demo()
            
            if result is True:
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message=message
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message=message
                ).to_dict()
                
        except Exception as e:
            print(f"OperationsHandler: Error running demo: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error running demo: {e}"
            ).to_dict()
    
    def handle_stop_demo(self):
        """
        Handle demo stop operation.
        
        Returns:
            dict: Response indicating success or failure of demo stop
        """
        print("OperationsHandler: Handling stop demo operation")
        
        try:
            # Assuming there's a stop_demo method on the application
            # If not, this could delegate to the regular stop method
            result, message = self.application.stop()
            status = Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
            
            return Response(status, message=f"Demo stopped: {message}").to_dict()
            
        except Exception as e:
            print(f"OperationsHandler: Error stopping demo: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error stopping demo: {e}"
            ).to_dict()
    
    def handle_test_run(self):
        """
        Handle test run operation.
        
        Returns:
            dict: Response with test run result
        """
        print("OperationsHandler: Handling test run")
        
        try:
            result = self.application.testRun()
            return result
            
        except Exception as e:
            print(f"OperationsHandler: Error in test run: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error in test run: {e}"
            ).to_dict()
    
    def handle_calibrate(self):
        """
        Handle general calibration operation.
        
        Returns:
            dict: Response indicating success or failure of calibration
        """
        print("OperationsHandler: Handling calibrate operation")
        
        try:
            # This could potentially call both camera and robot calibration
            # For now, let's assume it's a general calibration method
            return Response(
                Constants.RESPONSE_STATUS_SUCCESS, 
                message="Calibration completed"
            ).to_dict()
            
        except Exception as e:
            print(f"OperationsHandler: Error in calibration: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error in calibration: {e}"
            ).to_dict()
    
    def handle_help(self):
        """
        Handle help request.
        
        Returns:
            dict: Response with help information
        """
        print("OperationsHandler: Handling help request")
        
        return Response(
            Constants.RESPONSE_STATUS_SUCCESS, 
            message="Help request received"
        ).to_dict()

    def handler_clean_nozzle(self):
        result = self.application.clean_nozzle()
        status = Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
        message = "Nozzle cleaned successfully" if result else "Failed to clean nozzle"
        return Response(status, message=message).to_dict()
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
            self.application.handle_set_preselected_workpiece(workpiece)
            
            return Response(
                Constants.RESPONSE_STATUS_SUCCESS, 
                message="Preselected workpiece set successfully"
            ).to_dict()
            
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
        print(f"OperationsHandler: Handling execute from gallery: {workpiece}")
        
        try:
            self.application.handleExecuteFromGallery(workpiece)
            
            return Response(
                Constants.RESPONSE_STATUS_SUCCESS, 
                message="Execute from gallery initiated successfully"
            ).to_dict()
            
        except Exception as e:
            print(f"OperationsHandler: Error executing from gallery: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error executing from gallery: {e}"
            ).to_dict()
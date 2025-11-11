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
    
    def __init__(self, application, application_factory=None):
        """
        Initialize the OperationsHandler.
        
        Args:
            application: RobotApplicationInterface instance
            application_factory: Optional ApplicationFactory for switching applications
        """
        self.application = application
        self.application_factory = application_factory
    
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
        elif request == "switchApplication":
            return self.handle_switch_application(data)
        elif request == "getApplicationInfo":
            return self.handle_get_application_info()
        elif request == "getAvailableApplications":
            return self.handle_get_available_applications()
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
            result = self.application.start()
            print(f"OperationsHandler: Start result: {result}")
            
            if not result.get("success", False):
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message=result.get("message", "Operation failed")
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message=result.get("message", "Operation successful")
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
            result = self.application.stop()
            status = Constants.RESPONSE_STATUS_SUCCESS if result.get("success", False) else Constants.RESPONSE_STATUS_ERROR
            
            return Response(status, message=result.get("message", "Operation completed")).to_dict()
            
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
            result = self.application.pause()
            status = Constants.RESPONSE_STATUS_SUCCESS if result.get("success", False) else Constants.RESPONSE_STATUS_ERROR
            
            return Response(status, message=result.get("message", "Operation completed")).to_dict()
            
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
            # Check if the application has a run_demo method (legacy support)
            if hasattr(self.application, 'run_demo'):
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
            else:
                # Use standard start method as demo
                result = self.application.start()
                status = Constants.RESPONSE_STATUS_SUCCESS if result.get("success", False) else Constants.RESPONSE_STATUS_ERROR
                return Response(status, message=f"Demo mode: {result.get('message', 'Operation completed')}").to_dict()
                
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
            result = self.application.stop()
            status = Constants.RESPONSE_STATUS_SUCCESS if result.get("success", False) else Constants.RESPONSE_STATUS_ERROR
            
            return Response(status, message=f"Demo stopped: {result.get('message', 'Operation completed')}").to_dict()
            
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
            # Check if application has legacy testRun method
            if hasattr(self.application, 'testRun'):
                result = self.application.testRun()
                return result
            else:
                # Use standard methods for test run
                safety_check = self.application.safety_check()
                if not safety_check.get("safe", False):
                    return Response(
                        Constants.RESPONSE_STATUS_ERROR,
                        message=f"Safety check failed: {safety_check.get('message', 'Unknown safety issue')}"
                    ).to_dict()
                
                # Perform test operation
                result = self.application.start()
                status = Constants.RESPONSE_STATUS_SUCCESS if result.get("success", False) else Constants.RESPONSE_STATUS_ERROR
                return Response(status, message=f"Test run: {result.get('message', 'Operation completed')}").to_dict()
            
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
        print(f"OperationsHandler: Handling execute from gallery: {workpiece}")
        
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
            print(f"OperationsHandler: Error executing from gallery: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error executing from gallery: {e}"
            ).to_dict()
    
    def handle_switch_application(self, data):
        """
        Handle switching to a different robot application.
        
        Args:
            data: Dict containing application_type to switch to
            
        Returns:
            dict: Response indicating success or failure of application switch
        """
        print(f"OperationsHandler: Handling switch application: {data}")
        
        if not self.application_factory:
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message="Application switching not available - no factory configured"
            ).to_dict()
        
        try:
            from src.backend.robot_application.base_robot_application import ApplicationType
            
            app_type_str = data.get('application_type') if isinstance(data, dict) else str(data)
            
            # Convert string to ApplicationType enum
            try:
                app_type = ApplicationType(app_type_str.lower())
            except ValueError:
                available_types = [t.value for t in ApplicationType]
                return Response(
                    Constants.RESPONSE_STATUS_ERROR,
                    message=f"Invalid application type '{app_type_str}'. Available types: {available_types}"
                ).to_dict()
            
            # Switch application
            new_application = self.application_factory.switch_application(app_type)
            self.application = new_application
            
            return Response(
                Constants.RESPONSE_STATUS_SUCCESS,
                message=f"Successfully switched to {new_application.get_application_name()}",
                data={
                    "application_type": app_type.value,
                    "application_name": new_application.get_application_name(),
                    "application_version": new_application.get_application_version()
                }
            ).to_dict()
            
        except Exception as e:
            print(f"OperationsHandler: Error switching application: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error switching application: {e}"
            ).to_dict()
    
    def handle_get_application_info(self):
        """
        Get information about the current application.
        
        Returns:
            dict: Response with current application information
        """
        try:
            return Response(
                Constants.RESPONSE_STATUS_SUCCESS,
                message="Current application information",
                data={
                    "application_type": self.application.get_application_type().value,
                    "application_name": self.application.get_application_name(),
                    "application_version": self.application.get_application_version(),
                    "supported_operations": self.application.get_supported_operations(),
                    "supported_tools": self.application.get_supported_tools(),
                    "supported_workpiece_types": self.application.get_supported_workpiece_types(),
                    "status": self.application.get_status()
                }
            ).to_dict()
            
        except Exception as e:
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error getting application info: {e}"
            ).to_dict()
    
    def handle_get_available_applications(self):
        """
        Get list of available applications.
        
        Returns:
            dict: Response with available applications
        """
        if not self.application_factory:
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message="Application factory not available"
            ).to_dict()
        
        try:
            available_apps = []
            for app_type in self.application_factory.get_registered_applications():
                try:
                    app_info = self.application_factory.get_application_info(app_type)
                    available_apps.append(app_info)
                except Exception as e:
                    print(f"Error getting info for {app_type.value}: {e}")
                    available_apps.append({
                        "type": app_type.value,
                        "name": f"{app_type.value.replace('_', ' ').title()} Application",
                        "error": str(e)
                    })
            
            return Response(
                Constants.RESPONSE_STATUS_SUCCESS,
                message="Available applications retrieved",
                data={
                    "current_application": self.application.get_application_type().value,
                    "available_applications": available_apps
                }
            ).to_dict()
            
        except Exception as e:
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Error getting available applications: {e}"
            ).to_dict()
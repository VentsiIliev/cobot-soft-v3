"""
Robot Handler - API Gateway

Handles all robot-related requests including movement, calibration, and robot operations.
"""

from modules.shared.v1.Response import Response
from modules.shared.v1 import Constants
from modules.shared.v1.endpoints import robot_endpoints


class RobotHandler:
    """
    Handles robot operations for the API gateway.
    
    This handler manages robot movement, calibration, jogging, and status operations.
    """
    
    def __init__(self, application, robotController):
        """
        Initialize the RobotHandler.
        
        Args:
            application: Main GlueSprayingApplication instance
            robotController: Robot controller instance
        """
        self.application = application
        self.robotController = robotController
    
    def handle(self, parts, request, data=None):
        """
        Route robot requests to appropriate handlers.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response dictionary with operation result
        """
        print(f"RobotHandler: Handling request: {request} with parts: {parts}")
        
        # Handle both new RESTful endpoints
        if request in [robot_endpoints.ROBOT_CALIBRATE] or (len(parts) > 1 and parts[1] == "calibrate"):
            return self.handle_robot_calibration()
        elif request in [robot_endpoints.ROBOT_EXECUTE_NOZZLE_CLEAN] or (len(parts) >= 3 and parts[1] == "move" and parts[2] == "clean"):
            return self.handle_clean_nozzle()
        elif request in [robot_endpoints.ROBOT_MOVE_TO_HOME_POS]:
            return self.handle_home_position()
        elif request in [robot_endpoints.ROBOT_STOP]:
            return self.handle_robot_stop()
        elif self._is_jog_command(request):
            return self.handle_jog_command(parts, request)
        elif self._is_slot_command(request):
            return self.handle_slot_operation(parts, request)
        elif self._is_position_command(request):
            return self.handle_position_command(parts, request)
        else:
            # Delegate to robot controller for other operations
            return self.robotController.handle(request, parts)
    
    def handle_robot_calibration(self):
        """
        Handle robot calibration requests.
        
        Returns:
            dict: Response indicating success or failure of calibration
        """
        print("RobotHandler: Handling robot calibration")
        
        try:
            result, message, image = self.application.calibrateRobot()
            
            if result:
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message=message, 
                    data={"image": image}
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message=message
                ).to_dict()
                
        except Exception as e:
            print(f"RobotHandler: Error calibrating robot: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error calibrating robot: {e}"
            ).to_dict()
    
    def _is_jog_command(self, request):
        """Check if the request is a robot jog command."""
        jog_endpoints = [
            robot_endpoints.ROBOT_ACTION_JOG_X_PLUS, robot_endpoints.ROBOT_ACTION_JOG_X_MINUS,
            robot_endpoints.ROBOT_ACTION_JOG_Y_PLUS, robot_endpoints.ROBOT_ACTION_JOG_Y_MINUS,
            robot_endpoints.ROBOT_ACTION_JOG_Z_PLUS, robot_endpoints.ROBOT_ACTION_JOG_Z_MINUS
        ]
        return request in jog_endpoints or "/jog/" in request
    
    def _is_slot_command(self, request):
        """Check if the request is a robot slot operation."""
        slot_endpoints = [
            robot_endpoints.ROBOT_SLOT_0_PICKUP, robot_endpoints.ROBOT_SLOT_0_DROP,
            robot_endpoints.ROBOT_SLOT_1_PICKUP, robot_endpoints.ROBOT_SLOT_1_DROP,
            robot_endpoints.ROBOT_SLOT_2_PICKUP, robot_endpoints.ROBOT_SLOT_2_DROP,
            robot_endpoints.ROBOT_SLOT_3_PICKUP, robot_endpoints.ROBOT_SLOT_3_DROP,
            robot_endpoints.ROBOT_SLOT_4_PICKUP, robot_endpoints.ROBOT_SLOT_4_DROP
        ]
        return request in slot_endpoints or "/slots/" in request
    
    def _is_position_command(self, request):
        """Check if the request is a robot position command."""
        position_endpoints = [
            robot_endpoints.ROBOT_GET_CURRENT_POSITION, robot_endpoints.ROBOT_MOVE_TO_POSITION
        ]
        return request in position_endpoints or "/position/" in request
    
    def handle_home_position(self):
        """Handle robot home position movement."""
        print("RobotHandler: Handling home position movement")
        
        try:
            # Delegate to robot controller
            return self.robotController.handle("robot/move/home", ["robot", "move", "home"])
        except Exception as e:
            print(f"RobotHandler: Error moving to home position: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error moving to home position: {e}"
            ).to_dict()
    
    def handle_robot_stop(self):
        """Handle robot stop command."""
        print("RobotHandler: Handling robot stop")
        
        try:
            # Delegate to robot controller
            return self.robotController.handle("robot/stop", ["robot", "stop"])
        except Exception as e:
            print(f"RobotHandler: Error stopping robot: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error stopping robot: {e}"
            ).to_dict()
    
    def handle_clean_nozzle(self):
        """
        Handle nozzle cleaning operation.
        
        Returns:
            dict: Response indicating success or failure of nozzle cleaning
        """
        print("RobotHandler: Handling nozzle cleaning")
        
        try:
            ret = self.application.clean_nozzle()
            
            if ret == 0:
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message="Nozzle cleaned successfully"
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message="Error cleaning nozzle"
                ).to_dict()
                
        except Exception as e:
            print(f"RobotHandler: Error cleaning nozzle: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error cleaning nozzle: {e}"
            ).to_dict()
    
    def handle_jog_command(self, parts, request):
        """
        Handle robot jogging commands.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            
        Returns:
            dict: Response indicating success or failure of jog operation
        """
        print(f"RobotHandler: Handling jog command: {request}")
        
        # Delegate to robot controller which has the jog implementation
        return self.robotController.handle(request, parts)
    
    def handle_position_command(self, parts, request):
        """
        Handle robot position-related commands.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            
        Returns:
            dict: Response with position data or operation result
        """
        print(f"RobotHandler: Handling position command: {request}")
        
        # Delegate to robot controller which handles position operations
        return self.robotController.handle(request, parts)
    
    def handle_slot_operation(self, parts, request):
        """
        Handle robot slot pickup/drop operations.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            
        Returns:
            dict: Response indicating success or failure of slot operation
        """
        print(f"RobotHandler: Handling slot operation: {request}")
        
        # Delegate to robot controller which handles slot operations
        return self.robotController.handle(request, parts)
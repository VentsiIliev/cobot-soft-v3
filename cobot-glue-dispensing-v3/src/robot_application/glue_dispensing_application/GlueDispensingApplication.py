from typing import Dict, Any

from modules.robot.robotService.RobotService import RobotService
from modules.shared.shared.workpiece.WorkpieceService import WorkpieceService
from backend.system.settings.SettingsService import SettingsService
from backend.system.system_handlers.camera_calibration_handler import \
    calibrate_camera
from backend.system.system_handlers.robot_calibration_handler import calibrate_robot
from backend.system.vision.VisionService import _VisionService
# Import base classes
from robot_application.base_robot_application import BaseRobotApplication, ApplicationState
from robot_application.glue_dispensing_application.GlueDispensingApplicationStateManager import \
    GlueDispensingApplicationStateManager
from robot_application.glue_dispensing_application.GlueDispensingMessagePublisher import \
    GlueDispensingMessagePublisher
from robot_application.glue_dispensing_application.GlueDispensingSubscriptionManager import \
    GlueDispensingSubscriptionManager
from robot_application.glue_dispensing_application.glue_dispensing.glue_dispensing_operation import \
    GlueDispensingOperation
from robot_application.glue_dispensing_application.glue_dispensing.state_machine.GlueProcessState import \
    GlueProcessState
from robot_application.glue_dispensing_application.glue_dispensing.state_machine.GlueProcessStateMachine import \
    GlueProcessStateMachine
from robot_application.glue_dispensing_application.handlers import spraying_handler, nesting_handler
from robot_application.glue_dispensing_application.handlers.clean_nozzle_handler import clean_nozzle
from robot_application.glue_dispensing_application.handlers.create_workpiece_handler import \
    CreateWorkpieceHandler
from robot_application.glue_dispensing_application.handlers.handle_start import start
from robot_application.glue_dispensing_application.handlers.match_workpiece_handler import WorkpieceMatcher
from robot_application.glue_dispensing_application.handlers.temp_handlers.execute_from_gallery_handler import \
    execute_from_gallery
from robot_application.glue_dispensing_application.handlers.workpieces_to_spray_paths_handler import \
    WorkpieceToSprayPathsGenerator
from robot_application.glue_dispensing_application.settings.GlueSettings import GlueSettings
from robot_application.glue_dispensing_application.settings.GlueSettingsHandler import GlueSettingsHandler
from robot_application.glue_dispensing_application.tools.GlueCell import GlueCellsManagerSingleton, GlueDataFetcher
from robot_application.interfaces.application_settings_interface import settings_registry
from robot_application.interfaces.robot_application_interface import (
    RobotApplicationInterface, OperationMode
)

"""
ENDPOINTS
- start
- measureHeight
- calibrateRobot
- calibrateCamera
- createWorkpiece

"""

Z_OFFSET_FOR_CALIBRATION_PATTERN = -4 # MM

class GlueSprayingApplication(BaseRobotApplication, RobotApplicationInterface):
    """
    ActionManager is responsible for connecting actions to functions.
    The MainWindow will just emit signals, and ActionManager handles them.
    """

    glueCellsManager = GlueCellsManagerSingleton.get_instance()


    def __init__(self,
                 vision_service: _VisionService,
                 settings_manager: SettingsService,
                 workpiece_service: WorkpieceService,
                 robot_service: RobotService):

        # Initialize logger first (before base class to avoid issues)
        import logging
        self.logger = logging.getLogger(self.__class__.__name__)
        # register glue meters
        glue_fetcher = GlueDataFetcher()
        glue_fetcher.start()
        # Initialize the base class
        super().__init__(vision_service, settings_manager, workpiece_service, robot_service)

        # Register application-specific settings after initialization
        self._register_settings()

        # Override the base managers with glue dispensing specific extensions
        self.message_publisher = GlueDispensingMessagePublisher(self.message_publisher)
        self.state_manager = GlueDispensingApplicationStateManager(self.state_manager)
        self.subscription_manager = GlueDispensingSubscriptionManager(self, self.subscription_manager)
        
        # Update subscriptions with the extended manager
        self.subscription_manager.subscribe_all()

        # Application-specific initialization
        self.preselected_workpiece = None
        self.workpiece_to_spray_paths_generator = WorkpieceToSprayPathsGenerator(self)
        self.create_workpiece_handler = CreateWorkpieceHandler(self)
        
        # Initialize glue process state machine for operation control

        self.glue_process_state_machine = GlueProcessStateMachine(GlueProcessState.INITIALIZING)

        self.workpiece_matcher = WorkpieceMatcher()

        # Initialize glue dispensing operation with proper settings access
        self.glue_dispensing_operation = GlueDispensingOperation(self.robotService, self)

        self.NESTING = True
        self.CONTOUR_MATCHING = True


        self.current_operation = None

    # ========== BaseRobotApplication Abstract Methods Implementation ==========
    
    def get_initial_state(self) -> ApplicationState:
        """Return the initial state for this application"""
        return ApplicationState.INITIALIZING
    
    # ========== Core Operation Control ==========
    
    def start(self, mode: OperationMode = OperationMode.AUTOMATIC, debug=True, **kwargs) -> Dict[str, Any]:
        """Start the robot application operation"""
        try:
            result = start(self, self.CONTOUR_MATCHING, self.NESTING, debug)
            # self.state_manager.update_state(ApplicationState.RUNNING)
            return {
                "success": True,
                "message": "Glue dispensing operation started",
                "mode": mode.value,
                "data": result
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            # self.state_manager.update_state(ApplicationState.ERROR)
            return {
                "success": False,
                "message": f"Failed to start operation: {e}",
                "error": str(e)
            }

    def start_nesting(self, debug=True):
        self.current_operation = "Nesting"
        return nesting_handler.start_nesting(self, self.get_workpieces())

    def start_spraying(self,workpieces, debug=True):
        self.current_operation = "Spraying"
        return spraying_handler.start_spraying(self, workpieces, debug)

    def move_to_nesting_capture_position(self):
        z_offset = self.settingsManager.get_camera_settings().get_capture_pos_offset()
        return self.robotService.move_to_nesting_capture_position(z_offset)

    def move_to_spray_capture_position(self):
        z_offset = self.settingsManager.get_camera_settings().get_capture_pos_offset()
        return self.robotService.move_to_spray_capture_position(z_offset)

    # ========== Tool and Hardware Control ==========

    def clean_nozzle(self) -> Dict[str, Any]:
        """
        Clean the robot nozzle.
        Default implementation - can be overridden by specific applications.
        """
        return clean_nozzle(self.robotService)

    def clean_tool(self, tool_id: str) -> Dict[str, Any]:
        """Clean a specific tool (e.g., nozzle cleaning)"""
        try:
            if tool_id == "nozzle":
                result = self.clean_nozzle()
                return {
                    "success": True,
                    "message": f"Tool {tool_id} cleaned successfully",
                    "data": result
                }
            else:
                return {
                    "success": False,
                    "message": f"Tool {tool_id} not supported for cleaning"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to clean tool: {e}",
                "error": str(e)
            }
    
    def home_robot(self) -> Dict[str, Any]:
        """Move robot to home position"""
        try:
            # Use robot service to move to home position
            result = self.robotService.moveToStartPosition()
            return {
                "success": True,
                "message": "Robot moved to home position",
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to home robot: {e}",
                "error": str(e)
            }

    def stop(self, emergency: bool = False) -> Dict[str, Any]:
        """Stop the robot application operation"""
        try:
            self.state_manager.update_state(ApplicationState.STOPPING)
            result = self.glue_dispensing_operation.stop_operation()
            self.state_manager.update_state(ApplicationState.IDLE)
            return {
                "success": True,
                "message": "Glue dispensing operation stopped",
                "emergency": emergency,
                "data": result
            }
        except Exception as e:
            self.state_manager.update_state(ApplicationState.ERROR)
            return {
                "success": False,
                "message": f"Failed to stop operation: {e}",
                "error": str(e)
            }

    def pause(self) -> Dict[str, Any]:
        """Pause the robot application operation"""
        try:
            self.state_manager.update_state(ApplicationState.PAUSED)
            self.glue_dispensing_operation.pause_operation()
            return {
                "success": True,
                "message": "Glue dispensing operation paused"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to pause operation: {e}",
                "error": str(e)
            }

    def resume(self) -> Dict[str, Any]:
        """Resume the robot application operation"""
        try:
            self.state_manager.update_state(ApplicationState.RUNNING)
            self.glue_dispensing_operation.resume_operation()
            return {
                "success": True,
                "message": "Glue dispensing operation resumed"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to resume operation: {e}",
                "error": str(e)
            }
    
    def reset(self) -> Dict[str, Any]:
        """Reset the robot application to initial state"""
        try:
            # Stop any ongoing operation
            self.stop()
            
            # Reset to initial state
            self.state_manager.update_state(ApplicationState.IDLE)
            
            # Clear preselected workpiece
            self.preselected_workpiece = None
            
            # Reset modes to default
            self.NESTING = True
            self.CONTOUR_MATCHING = True
            
            return {
                "success": True,
                "message": "Application reset to initial state"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to reset application: {e}",
                "error": str(e)
            } # TODO not used!

    # ========== Calibration Management ==========
    
    def calibrate_robot(self) -> Dict[str, Any]:
        """Calibrate the robot coordinate system"""
        try:
            self.state_manager.update_state(ApplicationState.CALIBRATING)
            result = calibrate_robot(self)
            self.state_manager.update_state(ApplicationState.IDLE)
            return {
                "success": True,
                "message": "Robot calibration completed",
                "data": result
            }
        except Exception as e:
            self.state_manager.update_state(ApplicationState.ERROR)
            return {
                "success": False,
                "message": f"Robot calibration failed: {e}",
                "error": str(e)
            }
    
    def calibrate_camera(self) -> Dict[str, Any]:
        """Calibrate the camera system"""
        try:
            self.state_manager.update_state(ApplicationState.CALIBRATING)
            result = calibrate_camera(self)
            self.state_manager.update_state(ApplicationState.IDLE)
            return {
                "success": True,
                "message": "Camera calibration completed",
                "data": result
            }
        except Exception as e:
            self.state_manager.update_state(ApplicationState.ERROR)
            return {
                "success": False,
                "message": f"Camera calibration failed: {e}",
                "error": str(e)
            }
    
    # Legacy methods for backward compatibility
    def calibrateRobot(self):
        return self.calibrate_robot()

    def calibrateCamera(self):
        return self.calibrate_camera()

    def create_workpiece_step_1(self):
        return self.create_workpiece_handler.create_workpiece_step_1()

    def create_workpiece_step_2(self):
        return self.create_workpiece_handler.create_workpiece_step_2()

    # ========== Workpiece Handling ==========
    
    def load_workpiece(self, workpiece_id: str) -> Dict[str, Any]:
        """Load a workpiece for processing"""
        try:
            workpiece = self.workpieceService.get_workpiece_by_id(workpiece_id)
            if workpiece is None:
                return {
                    "success": False,
                    "message": f"Workpiece with ID {workpiece_id} not found"
                }
            
            self.preselected_workpiece = workpiece
            return {
                "success": True,
                "message": f"Workpiece {workpiece_id} loaded successfully",
                "data": {
                    "workpiece_id": workpiece_id,
                    "workpiece_name": workpiece.name if hasattr(workpiece, 'name') else 'Unknown'
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to load workpiece: {e}",
                "error": str(e)
            }
    
    def process_workpiece(self, workpiece_id: str, **parameters) -> Dict[str, Any]:
        """Process a workpiece with the robot application"""
        try:
            # Load the workpiece
            load_result = self.load_workpiece(workpiece_id)
            if not load_result["success"]:
                return load_result
            
            # Start the dispensing operation
            start_result = self.start(**parameters)
            
            return {
                "success": start_result["success"],
                "message": f"Workpiece {workpiece_id} processing {'started' if start_result['success'] else 'failed'}",
                "data": {
                    "workpiece_id": workpiece_id,
                    "processing_result": start_result
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to process workpiece: {e}",
                "error": str(e)
            }
    
    def get_workpieces(self):
        """Legacy method for backward compatibility"""
        if self.preselected_workpiece is None:
            workpieces = self.workpieceService.loadAllWorkpieces()
            print(f" Loaded workpieces: {len(workpieces)}")
        else:
            workpieces = [self.preselected_workpiece]
            print(f" Using preselected workpiece: {self.preselected_workpiece.name}")
        return workpieces

    def get_dynamic_offsets_config(self):
        """
        Return the dynamic offset configuration including step offsets and direction map.
        """
        # Step offsets
        x_step_offset = self.robotService.robot_config.tcp_x_step_offset
        y_step_offset = self.robotService.robot_config.tcp_y_step_offset

        # Optionally: distances (if still used)
        x_distance = getattr(self.robotService.robot_config, 'tcp_x_step_distance', 50.0)
        y_distance = getattr(self.robotService.robot_config, 'tcp_y_step_distance', 50.0)

        # Direction map
        direction_map = self.robotService.robot_config.offset_direction_map
        # print(f"in get_dynamic_offsets_config: direction_map={direction_map}")
        return x_distance, x_step_offset, y_distance, y_step_offset, direction_map

    def get_transducer_offsets(self):
        # NOTE:
        # - The offsets defined here are measured in the robot's 0° TCP (Tool Center Point) orientation.

        x_offset = self.robotService.robot_config.tcp_x_offset # to the top left corner of the transducer
        y_offset = self.robotService.robot_config.tcp_y_offset # to the top left corner of the transducer

        # print(f"Transducer offsets: x_offset={x_offset}, y_offset={y_offset}")
        return [x_offset, y_offset]

    """ TEMP METHODS FOR TESTING WHILE IN DEVELOPMENT """

    def handleExecuteFromGallery(self, workpiece):
        return execute_from_gallery(self,workpiece,Z_OFFSET_FOR_CALIBRATION_PATTERN)

    def changeMode(self,message):
        print(f"Changing mode to: {message}")
        if message == "Spray Only":
            self.NESTING = False
        elif message == "Pick And Spray":
            self.NESTING = True
        else:
            raise ValueError(f"Unknown mode: {message}")

    def run_demo(self):

        if self.preselected_workpiece is None:
            print(f"No preselected workpiece set for demo")
            return False, "No preselected workpiece set for demo"

        workpiece = self.workpieceService.get_workpiece_by_id(self.preselected_workpiece)
        if workpiece is None:
            print(f"Demo workpiece with ID {self.preselected_workpiece} not found.")
            return True, f"Demo workpiece with ID {self.preselected_workpiece} not found."

        print("Demo workpiece found: ", workpiece)
        return True, "Demo workpiece found"

    """ TEMP METHODS FOR TESTING WHILE IN DEVELOPMENT """

    def handle_set_preselected_workpiece(self, wp_id):

        selected_workpiece = None
        all_workpieces = self.workpieceService.loadAllWorkpieces()
        for wp in all_workpieces:
            if str(wp.workpieceId) == str(wp_id):
                selected_workpiece = wp
                break

        if selected_workpiece is not None:
            self.preselected_workpiece = selected_workpiece
            print(f"Preselected workpiece set to ID: {wp_id}")
            print(f"Workpiece: {selected_workpiece}")
            print(f"Pickup point: {selected_workpiece.pickupPoint}")

            return True, f"Preselected workpiece set to ID: {wp_id}"
        else:
            print(f"Workpiece with ID: {wp_id} not found")
            return False, f"Workpiece with ID: {wp_id} not found"

    # ========== Application-Specific Information ==========

    def _register_settings(self):
        """Register glue application settings with the global settings registry"""
        try:
            # Create glue settings instance
            glue_settings = GlueSettings()
            
            # Create glue settings handler  
            glue_handler = GlueSettingsHandler()
            
            # Register both with the global registry
            settings_registry.register_settings_type(glue_settings)
            settings_registry.register_handler(glue_handler)
            
            self.logger.info("Glue application settings registered successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to register glue application settings: {e}")

    def get_glue_settings(self):
        """Get glue settings object for this application"""
        try:
            handler = settings_registry.get_handler("glue")
            return handler.get_settings_object()
        except Exception as e:
            self.logger.error(f"Failed to get glue settings: {e}")
            # Fallback to default settings
            return GlueSettings()

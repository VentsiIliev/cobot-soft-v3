import datetime
from typing import Dict, Any, List, Optional

from modules.VisionSystem.VisionSystem import VisionSystemState
from modules.shared.shared.workpiece.WorkpieceService import WorkpieceService
# Import base classes
from src.backend.robot_application.base_robot_application import BaseRobotApplication, ApplicationType, ApplicationState
from src.backend.robot_application.glue_dispensing_application.GlueDispensingApplicationStateManager import \
    GlueDispensingApplicationStateManager
from src.backend.robot_application.glue_dispensing_application.GlueDispensingMessagePublisher import \
    GlueDispensingMessagePublisher
from src.backend.robot_application.glue_dispensing_application.GlueDispensingSubscriptionManager import \
    GlueDispensingSubscriptionManager
from src.backend.robot_application.glue_dispensing_application.glue_dispensing.glue_dispensing_operation import \
    GlueDispensingOperation
from src.backend.robot_application.robot_application_interface import (
    RobotApplicationInterface, OperationMode, CalibrationStatus
)
from src.backend.robot_application.glue_dispensing_application.handlers import nesting_handler
from src.backend.robot_application.glue_dispensing_application.handlers.handle_start import start
from src.backend.robot_application.glue_dispensing_application.handlers import spraying_handler
from src.backend.robot_application.glue_dispensing_application.handlers.camera_calibration_handler import calibrate_camera
from src.backend.robot_application.glue_dispensing_application.handlers.clean_nozzle_handler import clean_nozzle
from src.backend.robot_application.glue_dispensing_application.handlers.create_workpiece_handler import CreateWorkpieceHandler
from src.backend.robot_application.glue_dispensing_application.handlers.match_workpiece_handler import WorkpieceMatcher
from src.backend.robot_application.glue_dispensing_application.handlers.robot_calibration_handler import calibrate_robot
from src.backend.robot_application.glue_dispensing_application.handlers.temp_handlers.execute_from_gallery_handler import execute_from_gallery
from src.backend.robot_application.glue_dispensing_application.handlers.workpieces_to_spray_paths_handler import WorkpieceToSprayPathsGenerator
from src.backend.system.robot.robotService.RobotService import RobotService
from src.backend.system.robot.robotService.enums.RobotServiceState import RobotServiceState
from src.backend.system.settings.SettingsService import SettingsService
from src.backend.robot_application.glue_dispensing_application.tools.GlueCell import GlueCellsManagerSingleton
from src.backend.system.vision.VisionService import _VisionService
from src.backend.robot_application.interfaces.application_settings_interface import settings_registry
from src.backend.robot_application.glue_dispensing_application.settings.GlueSettings import GlueSettings
from src.backend.robot_application.glue_dispensing_application.settings.GlueSettingsHandler import GlueSettingsHandler

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
        self.workpiece_matcher = WorkpieceMatcher(self)
        
        # Initialize glue dispensing operation with proper settings access
        self.glue_dispensing_operation = GlueDispensingOperation(self.robotService, self)

        self.NESTING = True
        self.CONTOUR_MATCHING = True
        
        # Application-specific error log
        self._error_log = []
        
        # Application-specific calibration status
        self._calibration_status = {
            "robot": CalibrationStatus.NOT_CALIBRATED,
            "camera": CalibrationStatus.NOT_CALIBRATED,
            "nozzle": CalibrationStatus.NOT_CALIBRATED
        }

    # ========== BaseRobotApplication Abstract Methods Implementation ==========
    
    def get_application_type(self) -> ApplicationType:
        """Return the type of this application"""
        return ApplicationType.GLUE_DISPENSING
    
    def get_application_name(self) -> str:
        """Return the human-readable name of this application"""
        return "Glue Dispensing Application"
    
    def get_initial_state(self) -> ApplicationState:
        """Return the initial state for this application"""
        return ApplicationState.INITIALIZING
    
    # ========== Core Operation Control ==========
    
    def start(self, mode: OperationMode = OperationMode.AUTOMATIC, debug=True, **kwargs) -> Dict[str, Any]:
        """Start the robot application operation"""
        try:
            self.state_manager.update_state(ApplicationState.RUNNING)
            result = start(self, self.CONTOUR_MATCHING, self.NESTING, debug)
            return {
                "success": True,
                "message": "Glue dispensing operation started",
                "mode": mode.value,
                "data": result
            }
        except Exception as e:
            self._add_error_log(f"Failed to start operation: {e}")
            self.state_manager.update_state(ApplicationState.ERROR)
            return {
                "success": False,
                "message": f"Failed to start operation: {e}",
                "error": str(e)
            }

    def start_nesting(self, debug=True):
        return nesting_handler.start_nesting(self, self.get_workpieces())

    def start_spraying(self,workpieces, debug=True):
        return spraying_handler.start_spraying(self,workpieces,debug)

    def move_to_nesting_capture_position(self):
        z_offset = self.settingsManager.get_camera_settings().get_capture_pos_offset()
        return self.robotService.move_to_nesting_capture_position(z_offset)

    def move_to_spray_capture_position(self):
        z_offset = self.settingsManager.get_camera_settings().get_capture_pos_offset()
        return self.robotService.move_to_spray_capture_position(z_offset)

    # ========== Tool and Hardware Control ==========
    
    def clean_tool(self, tool_id: str) -> Dict[str, Any]:
        """Clean a specific tool (e.g., nozzle cleaning)"""
        try:
            if tool_id == "nozzle":
                result = clean_nozzle(self.robotService)
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
            self._add_error_log(f"Failed to clean tool {tool_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to clean tool: {e}",
                "error": str(e)
            }
    
    def test_tool(self, tool_id: str, test_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test a specific tool functionality"""
        try:
            if tool_id == "nozzle":
                # Perform nozzle test
                clean_result = self.clean_tool(tool_id)
                return {
                    "success": clean_result["success"],
                    "message": f"Tool {tool_id} test completed",
                    "data": {
                        "test_type": "cleaning_test",
                        "result": clean_result
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"Tool {tool_id} not supported for testing"
                }
        except Exception as e:
            self._add_error_log(f"Failed to test tool {tool_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to test tool: {e}",
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
            self._add_error_log(f"Failed to home robot: {e}")
            return {
                "success": False,
                "message": f"Failed to home robot: {e}",
                "error": str(e)
            }
    
    def clean_nozzle(self):
        """Legacy method for backward compatibility"""
        return clean_nozzle(self.robotService)

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
            self._add_error_log(f"Failed to stop operation: {e}")
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
            self._add_error_log(f"Failed to pause operation: {e}")
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
            self._add_error_log(f"Failed to resume operation: {e}")
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
            self._add_error_log(f"Failed to reset application: {e}")
            return {
                "success": False,
                "message": f"Failed to reset application: {e}",
                "error": str(e)
            }

    # ========== Calibration Management ==========
    
    def calibrate_robot(self, force_recalibration: bool = False) -> Dict[str, Any]:
        """Calibrate the robot coordinate system"""
        try:
            self.state_manager.update_state(ApplicationState.CALIBRATING)
            self._calibration_status["robot"] = CalibrationStatus.IN_PROGRESS
            result = calibrate_robot(self)
            self._calibration_status["robot"] = CalibrationStatus.CALIBRATED
            self.state_manager.update_state(ApplicationState.IDLE)
            return {
                "success": True,
                "message": "Robot calibration completed",
                "data": result
            }
        except Exception as e:
            self._add_error_log(f"Robot calibration failed: {e}")
            self._calibration_status["robot"] = CalibrationStatus.FAILED
            self.state_manager.update_state(ApplicationState.ERROR)
            return {
                "success": False,
                "message": f"Robot calibration failed: {e}",
                "error": str(e)
            }
    
    def calibrate_camera(self, force_recalibration: bool = False) -> Dict[str, Any]:
        """Calibrate the camera system"""
        try:
            self.state_manager.update_state(ApplicationState.CALIBRATING)
            self._calibration_status["camera"] = CalibrationStatus.IN_PROGRESS
            result = calibrate_camera(self)
            self._calibration_status["camera"] = CalibrationStatus.CALIBRATED
            self.state_manager.update_state(ApplicationState.IDLE)
            return {
                "success": True,
                "message": "Camera calibration completed",
                "data": result
            }
        except Exception as e:
            self._add_error_log(f"Camera calibration failed: {e}")
            self._calibration_status["camera"] = CalibrationStatus.FAILED
            self.state_manager.update_state(ApplicationState.ERROR)
            return {
                "success": False,
                "message": f"Camera calibration failed: {e}",
                "error": str(e)
            }
    
    def calibrate_tools(self, tool_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Calibrate robot tools (nozzles, etc.)"""
        try:
            self.state_manager.update_state(ApplicationState.CALIBRATING)
            tools_to_calibrate = tool_ids or ["nozzle"]
            results = {}
            
            for tool_id in tools_to_calibrate:
                self._calibration_status[tool_id] = CalibrationStatus.IN_PROGRESS
                if tool_id == "nozzle":
                    # Use existing nozzle cleaning as calibration
                    clean_result = self.clean_nozzle()
                    results[tool_id] = clean_result
                    self._calibration_status[tool_id] = CalibrationStatus.CALIBRATED
                else:
                    results[tool_id] = {"success": False, "message": f"Tool {tool_id} not supported"}
                    self._calibration_status[tool_id] = CalibrationStatus.FAILED
            
            self.state_manager.update_state(ApplicationState.IDLE)
            return {
                "success": True,
                "message": "Tool calibration completed",
                "data": results
            }
        except Exception as e:
            self._add_error_log(f"Tool calibration failed: {e}")
            return {
                "success": False,
                "message": f"Tool calibration failed: {e}",
                "error": str(e)
            }
    
    def get_calibration_status(self) -> Dict[str, CalibrationStatus]:
        """Get current calibration status for all components"""
        return self._calibration_status.copy()
    
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
            self._add_error_log(f"Failed to load workpiece {workpiece_id}: {e}")
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
            self._add_error_log(f"Failed to process workpiece {workpiece_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to process workpiece: {e}",
                "error": str(e)
            }
    
    def validate_workpiece(self, workpiece_id: str) -> Dict[str, Any]:
        """Validate that a workpiece can be processed by this application"""
        try:
            workpiece = self.workpieceService.get_workpiece_by_id(workpiece_id)
            if workpiece is None:
                return {
                    "success": False,
                    "valid": False,
                    "message": f"Workpiece with ID {workpiece_id} not found",
                    "issues": ["Workpiece does not exist"]
                }
            
            issues = []
            
            # Check if workpiece has required contours
            if not hasattr(workpiece, 'get_main_contour') or workpiece.get_main_contour() is None:
                issues.append("Workpiece missing main contour")
            
            # Check if workpiece has pickup point (if nesting enabled)
            if self.NESTING and (not hasattr(workpiece, 'pickupPoint') or workpiece.pickupPoint is None):
                issues.append("Workpiece missing pickup point (required for nesting mode)")
            
            return {
                "success": True,
                "valid": len(issues) == 0,
                "message": "Workpiece validation completed",
                "issues": issues
            }
        except Exception as e:
            self._add_error_log(f"Failed to validate workpiece {workpiece_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to validate workpiece: {e}",
                "error": str(e)
            }
    
    def get_workpiece_requirements(self) -> Dict[str, Any]:
        """Get requirements for workpieces that can be processed by this application"""
        return {
            "required_fields": ["main_contour"],
            "optional_fields": ["pickup_point", "name", "description"],
            "contour_formats": ["DXF", "polygon_points"],
            "coordinate_system": "robot_base",
            "units": "millimeters",
            "nesting_requirements": {
                "enabled": self.NESTING,
                "required_if_enabled": ["pickup_point"]
            },
            "contour_matching_requirements": {
                "enabled": self.CONTOUR_MATCHING,
                "required_if_enabled": ["reference_contour"]
            }
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
    
    # ========== Configuration Management ==========
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current application configuration"""
        return {
            "nesting_enabled": self.NESTING,
            "contour_matching_enabled": self.CONTOUR_MATCHING,
            "preselected_workpiece": self.preselected_workpiece.workpieceId if self.preselected_workpiece else None,
            "glue_settings": self.settingsManager.get_glue_settings().to_dict() if hasattr(self.settingsManager, 'get_glue_settings') else {},
            "robot_settings": self.settingsManager.get_robot_settings().to_dict() if hasattr(self.settingsManager, 'get_robot_settings') else {},
            "camera_settings": self.settingsManager.get_camera_settings().to_dict() if hasattr(self.settingsManager, 'get_camera_settings') else {}
        }
    
    def update_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update application configuration"""
        try:
            updated_fields = []
            
            if "nesting_enabled" in config:
                self.NESTING = config["nesting_enabled"]
                updated_fields.append("nesting_enabled")
            
            if "contour_matching_enabled" in config:
                self.CONTOUR_MATCHING = config["contour_matching_enabled"]
                updated_fields.append("contour_matching_enabled")
            
            if "preselected_workpiece" in config:
                wp_id = config["preselected_workpiece"]
                if wp_id:
                    load_result = self.load_workpiece(wp_id)
                    if load_result["success"]:
                        updated_fields.append("preselected_workpiece")
                else:
                    self.preselected_workpiece = None
                    updated_fields.append("preselected_workpiece")
            
            return {
                "success": True,
                "message": "Configuration updated successfully",
                "updated_fields": updated_fields
            }
        except Exception as e:
            self._add_error_log(f"Failed to update configuration: {e}")
            return {
                "success": False,
                "message": f"Failed to update configuration: {e}",
                "error": str(e)
            }
    
    def get_default_configuration(self) -> Dict[str, Any]:
        """Get default configuration for this application"""
        return {
            "nesting_enabled": True,
            "contour_matching_enabled": True,
            "preselected_workpiece": None
        }
    
    # ========== Application-Specific Information ==========
    
    def get_application_version(self) -> str:
        """Get the version of this application"""
        return "1.0.0"
    
    def get_supported_operations(self) -> List[str]:
        """Get list of operations supported by this application"""
        return [
            "start", "stop", "pause", "resume", "reset",
            "calibrate_robot", "calibrate_camera", "calibrate_tools",
            "load_workpiece", "process_workpiece", "validate_workpiece",
            "clean_tool", "test_tool", "home_robot",
            "start_nesting", "start_spraying", "create_workpiece_step_1", "create_workpiece_step_2"
        ]
    
    def get_supported_tools(self) -> List[str]:
        """Get list of tools supported by this application"""
        return ["nozzle", "glue_dispenser"]
    
    def get_supported_workpiece_types(self) -> List[str]:
        """Get list of workpiece types supported by this application"""
        return ["flat_part", "contoured_part", "dxf_based"]
    
    # ========== Safety and Emergency ==========
    
    def emergency_stop(self) -> Dict[str, Any]:
        """Emergency stop all robot operations immediately"""
        try:
            self.state_manager.update_state(ApplicationState.ERROR)
            stop_result = self.stop(emergency=True)
            return {
                "success": True,
                "message": "Emergency stop executed",
                "data": stop_result
            }
        except Exception as e:
            self._add_error_log(f"Emergency stop failed: {e}")
            return {
                "success": False,
                "message": f"Emergency stop failed: {e}",
                "error": str(e)
            }
    
    def safety_check(self) -> Dict[str, Any]:
        """Perform comprehensive safety check"""
        try:
            issues = []
            warnings = []
            
            # Check robot service state
            if self.state_manager.robot_service_state == RobotServiceState.ERROR:
                issues.append("Robot service in error state")
            
            # Check vision system state
            if self.state_manager.vision_service_state != VisionSystemState.RUNNING:
                warnings.append("Vision system not running")
            
            # Check calibration status
            for component, status in self._calibration_status.items():
                if status == CalibrationStatus.NOT_CALIBRATED:
                    warnings.append(f"{component} not calibrated")
                elif status == CalibrationStatus.FAILED:
                    issues.append(f"{component} calibration failed")
            
            return {
                "success": True,
                "safe": len(issues) == 0,
                "message": "Safety check completed",
                "issues": issues,
                "warnings": warnings
            }
        except Exception as e:
            self._add_error_log(f"Safety check failed: {e}")
            return {
                "success": False,
                "message": f"Safety check failed: {e}",
                "error": str(e)
            }
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety system status"""
        return {
            "robot_state": self.state_manager.robot_service_state.value if self.state_manager.robot_service_state else "unknown",
            "vision_state": self.state_manager.vision_service_state.value if self.state_manager.vision_service_state else "unknown",
            "application_state": self.state_manager.state.value,
            "calibration_status": {k: v.value for k, v in self._calibration_status.items()}
        }
    
    # ========== Status and Monitoring ==========
    
    def get_operation_statistics(self) -> Dict[str, Any]:
        """Get operation statistics and performance metrics"""
        return {
            "total_operations": 0,  # TODO: Implement operation counting
            "successful_operations": 0,
            "failed_operations": 0,
            "average_cycle_time": 0.0,
            "uptime": 0.0,
            "error_count": len(self._error_log)
        }
    
    def get_health_check(self) -> Dict[str, Any]:
        """Perform health check on all application components"""
        try:
            health_status = {
                "overall": "healthy",
                "components": {
                    "robot_service": "healthy" if self.robotService else "unavailable",
                    "vision_service": "healthy" if self.visionService else "unavailable",
                    "workpiece_service": "healthy" if self.workpieceService else "unavailable",
                    "settings_service": "healthy" if self.settingsManager else "unavailable"
                }
            }
            
            # Check if any component is unhealthy
            if "unavailable" in health_status["components"].values():
                health_status["overall"] = "degraded"
            
            return {
                "success": True,
                "health_status": health_status
            }
        except Exception as e:
            self._add_error_log(f"Health check failed: {e}")
            return {
                "success": False,
                "message": f"Health check failed: {e}",
                "error": str(e)
            }
    
    def get_error_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent error log entries"""
        return self._error_log[-limit:] if limit > 0 else self._error_log[:]
    
    def _add_error_log(self, message: str):
        """Add an error to the error log"""
        self._error_log.append({
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "level": "error"
        })
        
        # Keep only last 1000 entries
        if len(self._error_log) > 1000:
            self._error_log = self._error_log[-1000:]
    
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
            self._add_error_log(f"Settings registration failed: {e}")
    
    def get_glue_settings(self):
        """Get glue settings object for this application"""
        try:
            from src.backend.robot_application.interfaces.application_settings_interface import settings_registry
            handler = settings_registry.get_handler("glue")
            return handler.get_settings_object()
        except Exception as e:
            self.logger.error(f"Failed to get glue settings: {e}")
            # Fallback to default settings
            from src.backend.robot_application.glue_dispensing_application.settings.GlueSettings import GlueSettings
            return GlueSettings()

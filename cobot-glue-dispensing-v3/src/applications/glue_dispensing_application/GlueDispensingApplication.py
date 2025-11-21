from typing import Dict, Any

from typing_extensions import override

from applications.glue_dispensing_application.services.glueSprayService.GlueSprayService import GlueSprayService
from applications.glue_dispensing_application.services.workpiece.glue_workpiece_service import GlueWorkpieceService
from communication_layer.api.v1.topics import GlueTopics, SystemTopics
from core.application.interfaces.application_settings_interface import ApplicationSettingsRegistry
from core.application.interfaces.robot_application_interface import RobotApplicationInterface

import logging

from backend.system.settings.SettingsService import SettingsService
from core.application_state_management import SubscriptionManger, OperationState
from core.operation_state_management import OperationStatePublisher
from core.operation_state_management import OperationResult

from core.services.robot_service.impl.base_robot_service import RobotService
from core.services.vision.VisionService import _VisionService

from core.base_robot_application import BaseRobotApplication, ApplicationState, ApplicationMetadata

from applications.glue_dispensing_application.glue_process.glue_dispensing_operation import \
    GlueDispensingOperation

from applications.glue_dispensing_application.handlers import spraying_handler, nesting_handler
from applications.glue_dispensing_application.handlers.clean_nozzle_handler import clean_nozzle
from applications.glue_dispensing_application.handlers.create_workpiece_handler import \
    CreateWorkpieceHandler, CrateWorkpieceResult
from applications.glue_dispensing_application.handlers.handle_start import start
from applications.glue_dispensing_application.handlers.match_workpiece_handler import WorkpieceMatcher
from applications.glue_dispensing_application.handlers.temp_handlers.execute_from_gallery_handler import \
    execute_from_gallery
from applications.glue_dispensing_application.handlers.workpieces_to_spray_paths_handler import \
    WorkpieceToSprayPathsGenerator
from applications.glue_dispensing_application.settings.GlueSettings import GlueSettings
from applications.glue_dispensing_application.settings.GlueSettingsHandler import GlueSettingsHandler
from core.system_state_management import ServiceRegistry
from modules.shared.tools.GlueCell import GlueCellsManagerSingleton, GlueDataFetcher

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
                 workpiece_service: GlueWorkpieceService,
                 robot_service: RobotService,
                 settings_registry: ApplicationSettingsRegistry,
                 service_registry: ServiceRegistry,
                 **kwargs
                 ):

        # Initialize logger first (before base class to avoid issues)
        self.logger = logging.getLogger(self.__class__.__name__)

        self.vision_service = vision_service
        self.settings_manager = settings_manager
        self.workpiece_service=workpiece_service
        self.robot_service = robot_service
        self.settings_registry = settings_registry
        self.service_registry = service_registry
        # Initialize the base class
        super().__init__(self.vision_service, self.settings_manager, self.robot_service,self.settings_registry)

        # Register application-specific settings after initialization
        self._register_settings()

        # Application-specific initialization
        self.preselected_workpiece = None
        self.workpiece_to_spray_paths_generator = WorkpieceToSprayPathsGenerator(self)
        self.create_workpiece_handler = CreateWorkpieceHandler(self)

        self.workpiece_matcher = WorkpieceMatcher()
        self.glue_service= GlueSprayService(generatorTurnOffTimeout=10, settings=self.get_glue_settings())
        # TODO: register glue service in service registry when the glue service state management is implemented
        # self.service_registry.register_service(self.glue_service.service_id,"glue-service/state",ServiceState.UNKNOWN)
        # print(f"Registered Services in Glue App: {service_registry.get_registered_services()}")
        # Initialize glue dispensing operation with proper settings access
        self.glue_dispensing_operation = GlueDispensingOperation(self.robot_service, self.glue_service,self)
        self.glue_dispensing_operation.set_state_publisher(OperationStatePublisher(self.broker))
        self.broker.publish(SystemTopics.OPERATION_STATE, OperationState.IDLE)

        self.NESTING = True
        self.CONTOUR_MATCHING = True
        self.current_operation = self.glue_dispensing_operation



    @property
    def operation(self):
        return self.current_operation

    @override
    def set_current_operation(self):
        """determine the current operation based on mode"""
        self.current_operation = self.glue_dispensing_operation
    @override
    def _on_operation_start(self, debug=True, **kwargs) ->OperationResult:
        return start(self, self.CONTOUR_MATCHING, self.NESTING, debug)

    @staticmethod
    def get_metadata() -> ApplicationMetadata:
        return ApplicationMetadata(
            name="Glue Spraying Application",
            version="1.0.0",
            dependencies=["_VisionService",
                          "SettingsService",
                          "GlueRobotService",
                          "ApplicationSettingsRegistry"],
        )


    def initialize_glue_data_fetcher(self):
        glue_fetcher = GlueDataFetcher()
        glue_fetcher.start()

    # ========== BaseRobotApplication Abstract Methods Implementation ==========
    
    def get_initial_state(self) -> ApplicationState:
        """Return the initial state for this application"""
        return ApplicationState.INITIALIZING

    def start_nesting(self, debug=True)-> OperationResult:

        result =  nesting_handler.start_nesting(self, self.get_workpieces())
        return OperationResult(success=result.success,message=result.message)

    def start_spraying(self,workpieces, debug=True)-> OperationResult:

        return spraying_handler.start_spraying(self, workpieces, debug)

    def move_to_nesting_capture_position(self, z_offset=0):
        ret = self.robot_service.moveToStartPosition(z_offset=z_offset)

        if ret != 0:
            return ret

        target_pose = self.robot_service.robot_config.getHomePositionParsed()
        target_pose[2] += z_offset  # apply z_offset
        self.robot_service._waitForRobotToReachPosition(target_pose, 1, 0.1)
        return ret

    def move_to_spray_capture_position(self, z_offset=0):
        ret = self.robot_service.move_to_calibration_position(z_offset=z_offset)

        if ret != 0:
            return ret

        target_pose = self.robot_service.robot_config.getCalibrationPositionParsed()
        target_pose[2] += z_offset  # apply z_offset
        self.robot_service._waitForRobotToReachPosition(target_pose, 1, 0.1)
        return ret

    # ========== Tool and Hardware Control ==========

    def clean_nozzle(self) -> Dict[str, Any]:
        """
        Clean the robot nozzle.
        Default implementation - can be overridden by specific applications.
        """
        return clean_nozzle(self.robot_service)

    def clean_tool(self, tool_id: str) -> OperationResult:
        """Clean a specific tool (e.g., nozzle cleaning)"""
        try:
            if tool_id == "nozzle":
                result = self.clean_nozzle()
                return OperationResult(
                    success=True,
                    message=f"Tool {tool_id} cleaned successfully",
                    data=result
                )

            else:
                return OperationResult(
                    success=False,
                    message=f"Tool {tool_id} not supported for cleaning"
                )

        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Failed to clean tool {tool_id}: {e}",
                error=str(e)
            )

    
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


    def create_workpiece(self) -> CrateWorkpieceResult:
        return  self.create_workpiece_handler.create_workpiece()

    # ========== Workpiece Handling ==========
    
    def load_workpiece(self, workpiece_id: str) -> Dict[str, Any]:
        """Load a workpiece for processing"""
        try:
            workpiece = self.workpiece_service.get_workpiece_by_id(workpiece_id)
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
            workpieces = self.workpiece_service.load_all()
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
        x_step_offset = self.robot_service.robot_config.tcp_x_step_offset
        y_step_offset = self.robot_service.robot_config.tcp_y_step_offset

        # Optionally: distances (if still used)
        x_distance = getattr(self.robot_service.robot_config, 'tcp_x_step_distance', 50.0)
        y_distance = getattr(self.robot_service.robot_config, 'tcp_y_step_distance', 50.0)

        # Direction map
        direction_map = self.robot_service.robot_config.offset_direction_map
        # print(f"in get_dynamic_offsets_config: direction_map={direction_map}")
        return x_distance, x_step_offset, y_distance, y_step_offset, direction_map

    def get_transducer_offsets(self):
        # NOTE:
        # - The offsets defined here are measured in the robot's 0° TCP (Tool Center Point) orientation.

        x_offset = self.robot_service.robot_config.tcp_x_offset # to the top left corner of the transducer
        y_offset = self.robot_service.robot_config.tcp_y_offset # to the top left corner of the transducer

        # print(f"Transducer offsets: x_offset={x_offset}, y_offset={y_offset}")
        return [x_offset, y_offset]

    """ TEMP METHODS FOR TESTING WHILE IN DEVELOPMENT """

    def handleExecuteFromGallery(self, workpiece):
        return execute_from_gallery(self,workpiece,Z_OFFSET_FOR_CALIBRATION_PATTERN)

    def on_mode_change(self,message):
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

        workpiece = self.workpiece_service.get_workpiece_by_id(self.preselected_workpiece)
        if workpiece is None:
            print(f"Demo workpiece with ID {self.preselected_workpiece} not found.")
            return True, f"Demo workpiece with ID {self.preselected_workpiece} not found."

        print("Demo workpiece found: ", workpiece)
        return True, "Demo workpiece found"

    """ TEMP METHODS FOR TESTING WHILE IN DEVELOPMENT """

    def handle_set_preselected_workpiece(self, wp_id):
        selected_workpiece = None
        all_workpieces = self.workpiece_service.load_all()
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
            self.settings_registry.register_settings_type(glue_settings)
            self.settings_registry.register_handler(glue_handler)
            
            self.logger.info("Glue application settings registered successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to register glue application settings: {e}")

    def get_glue_settings(self):
        """Get glue settings object for this application"""
        try:
            handler = self.settings_registry.get_handler("glue_settings")
            return handler.get_settings_object()
        except Exception as e:
            self.logger.error(f"Failed to get glue settings: {e}")
            # Fallback to default settings
            return GlueSettings()

    """SUPER CLASS METHODS FOR EXTENSIONS OR OVERRIDE IF NEEDED"""

    @override
    def start(self, debug=True, **kwargs) -> OperationResult:
        """Start the robot application operation
        calling the super class start method which in turn calls _on_operation_start
        keeping this method for clarity and possible future customizations"""
        return super().start()
        # return start(self, self.CONTOUR_MATCHING, self.NESTING, debug)

    @override
    def stop(self, emergency: bool = False) -> OperationResult:
        """Stop the robot application operation"""
        # CALLING SUPER CLASS STOP METHOD. KEEPING THIS METHOD FOR CLARITY AND POSSIBLE FUTURE CUSTOMIZATIONS
        print(f"[GlueSprayingApplication] Stopping operation, emergency={emergency}")
        return super().stop()

    @override
    def pause(self) -> OperationResult:
        """Pause the robot application operation"""
        # CALLING SUPER CLASS PAUSE METHOD. KEEPING THIS METHOD FOR CLARITY AND POSSIBLE FUTURE CUSTOMIZATIONS
        return super().pause()

    @override
    def resume(self) -> OperationResult:
        """Resume the robot application operation"""
        # CALLING SUPER CLASS RESUME METHOD. KEEPING THIS METHOD FOR CLARITY AND POSSIBLE FUTURE CUSTOMIZATIONS
        return super().resume()

    @override
    def calibrate_robot(self) -> Dict[str, Any]:
        """Calibrate the robot coordinate system"""
        # CALLING THE SUPER CALIBRATE ROBOT METHOD AND KEEPING THIS FOR CLARITY AND POSSIBLE CHANGES
        return super().calibrate_robot()

    @override
    def calibrate_camera(self) -> Dict[str, Any]:
        """Calibrate the camera system"""
        # CALLING THE SUPER CALIBRATE CAMERA METHOD AND KEEPING THIS FOR CLARITY AND POSSIBLE CHANGES
        return super().calibrate_camera()

    @override
    def home_robot(self):
        """Move robot to home position"""
        return super().home_robot()

"""
Base Robot Application

This module provides the abstract base class for all robot applications.
All specific robot applications (glue dispensing, paint application, etc.)
should inherit from this base class and implement the required abstract methods.
"""

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List

from communication_layer.api.v1.topics import SystemTopics, RobotTopics
from core.services.robot_service.impl.base_robot_service import  RobotService
from core.services.robot_service.interfaces.IRobotService import IRobotService
from core.system_state_management import SystemState
from modules.shared.MessageBroker import MessageBroker
from core.services.vision.VisionService import _VisionService
from backend.system.settings.SettingsService import SettingsService
from backend.system.SystemStatePublisherThread import SystemStatePublisherThread
from core.operations_handlers.robot_calibration_handler import calibrate_robot
from core.operations_handlers.camera_calibration_handler import calibrate_camera
from core.application.interfaces.application_settings_interface import ApplicationSettingsRegistry
from core.application_state_management import ApplicationState, ApplicationStateManager, ApplicationMessagePublisher
from modules.shared.tools.Laser import Laser
from modules.shared.tools.ToolChanger import ToolChanger
from modules.shared.tools.ToolManager import ToolManager
from modules.shared.tools.VacuumPump import VacuumPump


class ApplicationType(Enum):
    """Enum defining available robot application types"""
    GLUE_DISPENSING = "glue_dispensing"
    PAINT_APPLICATION = "paint_application"




@dataclass
class ApplicationMetadata:
    """Metadata for robot applications"""
    name: str
    version: str
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class BaseRobotApplication(ABC):
    """
    Abstract base class for all robot applications.
    
    This class provides the common infrastructure and interface that all
    robot applications should implement. Specific applications like glue
    dispensing, paint application, etc. should inherit from this class.
    """
    
    def __init__(self,
                 vision_service: _VisionService,
                 settings_manager: SettingsService,
                 robot_service: RobotService,
                 settings_registry:ApplicationSettingsRegistry,
                 **kwargs
                 ):
        """
        Initialize the base robot application.
        
        Args:
            vision_service: Vision system service
            settings_manager: Settings management service
            robot_service: Robot control service
        """

        # Core services
        self.visionService = vision_service
        self.settingsManager = settings_manager
        self.robotService = robot_service
        self.settings_registry = settings_registry
        self.system_state_topic = SystemTopics.SYSTEM_STATE
        self.system_state = SystemState.UNKNOWN

        # Message broker and communication
        self.broker = MessageBroker()
        self.message_publisher = ApplicationMessagePublisher(self.broker)
        self.state_manager = ApplicationStateManager(self.message_publisher)
        self.state_manager.start_state_publisher_thread()
        # subscribe to system state updates


        self.toolChanger = ToolChanger()
        self.tool_manager = ToolManager(self.toolChanger, self)
        self.pump = VacuumPump()
        self.laser = Laser()
        self.robotService.tool_manager = self.tool_manager


        # Initialize application
        self._initialize_application()

    def get_subscriptions(self):
        subscriptions = []
        # SUBSCRIBE TO PROCESS STATE UPDATES
        process_state_subscription = [SystemTopics.PROCESS_STATE,self.state_manager.on_process_state_update]
        # SUBSCRIBE TO MODE CHANGE UPDATES
        mode_change_subscription = [SystemTopics.SYSTEM_MODE_CHANGE,self.on_mode_change]
        # SUBSCRIBE TO SYSTEM STATE UPDATES
        system_state_subscription = [self.system_state_topic,self.on_system_state_update]
        subscriptions.append(system_state_subscription)
        subscriptions.append(process_state_subscription)
        subscriptions.append(mode_change_subscription)
        return subscriptions

    def on_system_state_update(self, state):
        self.system_state = state

    
    @staticmethod
    @abstractmethod
    def get_metadata() -> ApplicationMetadata:
        """Return application metadata"""
        return ApplicationMetadata(name="BaseRobotApplication",
                                   version="1.0.0",
                                   dependencies=["_VisionService",
                                                 "SettingsService",
                                                 "BaseRobotService",
                                                 "ApplicationSettingsRegistry"])


 


    def _initialize_application(self):
        """Initialize the application infrastructure"""
        # Start camera feed in separate thread
        self.cameraThread = threading.Thread(target=self.visionService.run, daemon=True)
        self.cameraThread.start()
    
    # Abstract methods that must be implemented by specific applications

    @abstractmethod
    def get_initial_state(self) -> ApplicationState:
        """Return the initial state for this application"""
        return ApplicationState.INITIALIZING

    @abstractmethod
    def start(self, **kwargs) -> Dict[str, Any]:
        """
        Start the robot application operation.

        Returns:
            Dict containing operation result and any relevant data
        """
        pass

    @abstractmethod
    def stop(self) -> Dict[str, Any]:
        """
        Stop the robot application operation.

        Returns:
            Dict containing operation result
        """
        pass

    @abstractmethod
    def pause(self) -> Dict[str, Any]:
        """
        Pause the robot application operation.

        Returns:
            Dict containing operation result
        """
        pass

    @abstractmethod
    def resume(self) -> Dict[str, Any]:
        """
        Resume the robot application operation.

        Returns:
            Dict containing operation result
        """
        pass


    @abstractmethod
    def on_mode_change(self,mode):
        """
        Handle mode change requests.

        Args:
            mode: New mode to switch to
        """
        pass

    def calibrate_robot(self) -> Dict[str, Any]:
        """
        Calibrate the robot system.
        Default implementation - can be overridden by specific applications.
        """
        return calibrate_robot(self)
    
    def calibrate_camera(self) -> Dict[str, Any]:
        """
        Calibrate the camera system.
        Default implementation - can be overridden by specific applications.
        """
        return calibrate_camera(self)
    
    def shutdown(self):
        """Shutdown the application and cleanup resources"""
        # self.state_manager.update_state(ApplicationState.STOPPED)
        # self.state_manager.stop_state_publisher_thread()
        # self.subscription_manager.unsubscribe_all()
        pass
    # Optional methods for application-specific features
    
    def get_supported_operations(self) -> List[str]:
        """
        Get list of operations supported by this application.
        Can be overridden by specific applications.
        """
        return ["start", "stop", "pause", "resume", "calibrate_robot", "calibrate_camera"]
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the current application configuration.
        Can be overridden by specific applications.
        
        Returns:
            Dict with validation result and any issues found
        """
        return {
            "valid": True,
            "issues": []
        }
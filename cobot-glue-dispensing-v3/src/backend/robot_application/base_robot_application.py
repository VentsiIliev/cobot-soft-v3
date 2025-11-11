"""
Base Robot Application

This module provides the abstract base class for all robot applications.
All specific robot applications (glue dispensing, paint application, etc.)
should inherit from this base class and implement the required abstract methods.
"""

import threading
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, List

from modules.shared.MessageBroker import MessageBroker
from modules.shared.shared.workpiece.WorkpieceService import WorkpieceService
from modules.shared.v1.topics import SystemTopics
from src.backend.system.robot.robotService.RobotService import RobotService
from src.backend.system.vision.VisionService import _VisionService
from src.backend.system.settings.SettingsService import SettingsService
from src.backend.system.SystemStatePublisherThread import SystemStatePublisherThread


class ApplicationType(Enum):
    """Enum defining available robot application types"""
    GLUE_DISPENSING = "glue_dispensing"
    PAINT_APPLICATION = "paint_application"
    PICK_AND_PLACE = "pick_and_place"
    WELDING = "welding"


class ApplicationState(Enum):
    """Base application states that all robot applications should support"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"
    CALIBRATING = "calibrating"


class BaseMessagePublisher:
    """Base message publisher for robot applications"""
    
    def __init__(self, broker: MessageBroker):
        self.broker = broker
        self.state_topic = SystemTopics.APPLICATION_STATE
        self.application_topic = SystemTopics.APPLICATION_INFO
    
    def publish_state(self, state: ApplicationState):
        """Publish application state"""
        self.broker.publish(self.state_topic, {
            "state": state.value,
            "timestamp": self._get_timestamp()
        })
    
    def publish_application_info(self, app_type: ApplicationType, app_name: str):
        """Publish current application information"""
        self.broker.publish(self.application_topic, {
            "type": app_type.value,
            "name": app_name,
            "timestamp": self._get_timestamp()
        })
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        import datetime
        return datetime.datetime.now().isoformat()


class BaseApplicationStateManager:
    """Base state manager for robot applications"""
    
    def __init__(self, initial_state: ApplicationState, message_publisher: BaseMessagePublisher):
        self.state = initial_state
        self.message_publisher = message_publisher
        self.vision_service_state = None
        self.robot_service_state = None
        self.system_state_publisher = None
        self._last_state = None
    
    def update_state(self, new_state: ApplicationState):
        """Update application state"""
        if self.state != new_state:
            self._last_state = self.state
            self.state = new_state
            self.publish_state()
    
    def publish_state(self):
        """Publish current state"""
        # print(f"BaseApplicationStateManager Publishing application state: {self.state}")
        self.message_publisher.publish_state(self.state)
    
    def start_state_publisher_thread(self):
        """Start the state publisher thread"""
        if self.system_state_publisher is None:
            self.system_state_publisher = SystemStatePublisherThread(self.publish_state)
            self.system_state_publisher.start()
    
    def stop_state_publisher_thread(self):
        """Stop the state publisher thread"""
        if self.system_state_publisher:
            self.system_state_publisher.stop()
            self.system_state_publisher = None
    
    def on_robot_service_state_update(self, state):
        """Handle robot service state updates"""
        self.robot_service_state = state
    
    def on_vision_system_state_update(self, state):
        """Handle vision system state updates"""
        self.vision_service_state = state


class BaseSubscriptionManager:
    """Base subscription manager for robot applications"""
    
    def __init__(self, application: 'BaseRobotApplication', broker: MessageBroker):
        self.application = application
        self.broker = broker
        self.subscriptions = {}
    
    def subscribe_all(self):
        """Subscribe to all required topics"""
        self.subscribe_vision_topics()
        self.subscribe_robot_service_topics()
    
    def subscribe_robot_service_topics(self):
        """Subscribe to robot service topics"""
        topic = self.application.robotService.state_topic
        callback = self.application.state_manager.on_robot_service_state_update
        self.broker.subscribe(topic, callback)
        self.subscriptions[topic] = callback
    
    def subscribe_vision_topics(self):
        """Subscribe to vision service topics"""
        topic = self.application.visionService.stateTopic
        callback = self.application.state_manager.on_vision_system_state_update
        self.broker.subscribe(topic, callback)
        self.subscriptions[topic] = callback
    
    def unsubscribe_all(self):
        """Unsubscribe from all topics"""
        for topic, callback in self.subscriptions.items():
            self.broker.unsubscribe(topic, callback)
        self.subscriptions.clear()


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
                 workpiece_service: WorkpieceService,
                 robot_service: RobotService):
        """
        Initialize the base robot application.
        
        Args:
            vision_service: Vision system service
            settings_manager: Settings management service
            workpiece_service: Workpiece management service
            robot_service: Robot control service
        """
        
        # Core services
        self.visionService = vision_service
        self.settingsManager = settings_manager
        self.workpieceService = workpiece_service
        self.robotService = robot_service
        
        # Message broker and communication
        self.broker = MessageBroker()
        self.message_publisher = BaseMessagePublisher(broker=self.broker)
        
        # State management
        initial_state = self.get_initial_state()
        self.state_manager = BaseApplicationStateManager(
            initial_state=initial_state,
            message_publisher=self.message_publisher
        )
        
        # Subscription management
        self.subscription_manager = BaseSubscriptionManager(
            application=self,
            broker=self.broker
        )
        
        # Initialize application
        self._initialize_application()
    
    def _initialize_application(self):
        """Initialize the application infrastructure"""
        # Start camera feed in separate thread
        self.cameraThread = threading.Thread(target=self.visionService.run, daemon=True)
        self.cameraThread.start()
        
        # Start state publisher and subscriptions
        self.state_manager.start_state_publisher_thread()
        self.subscription_manager.subscribe_all()
        
        # Publish application info
        self.message_publisher.publish_application_info(
            self.get_application_type(),
            self.get_application_name()
        )
        
        # Keep initial state - let service callbacks determine when ready
        print(f"BaseRobotApplication initialized with state: {self.state_manager.state}")
    
    # Abstract methods that must be implemented by specific applications
    
    @abstractmethod
    def get_application_type(self) -> ApplicationType:
        """Return the type of this application"""
        pass
    
    @abstractmethod
    def get_application_name(self) -> str:
        """Return the human-readable name of this application"""
        pass
    
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
    
    # Common methods with default implementations (can be overridden)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current application status.
        
        Returns:
            Dict containing current status information
        """
        return {
            "application_type": self.get_application_type().value,
            "application_name": self.get_application_name(),
            "state": self.state_manager.state.value,
            "robot_state": self.state_manager.robot_service_state,
            "vision_state": self.state_manager.vision_service_state
        }
    
    def calibrate_robot(self) -> Dict[str, Any]:
        """
        Calibrate the robot system.
        Default implementation - can be overridden by specific applications.
        """
        from src.backend.system.handlers.robot_calibration_handler import calibrate_robot
        return calibrate_robot(self)
    
    def calibrate_camera(self) -> Dict[str, Any]:
        """
        Calibrate the camera system.
        Default implementation - can be overridden by specific applications.
        """
        from src.backend.system.handlers.camera_calibration_handler import calibrate_camera
        return calibrate_camera(self)
    
    def clean_nozzle(self) -> Dict[str, Any]:
        """
        Clean the robot nozzle.
        Default implementation - can be overridden by specific applications.
        """
        from src.backend.system.handlers.clean_nozzle_handler import clean_nozzle
        return clean_nozzle(self.robotService)
    
    def get_workpieces(self) -> List[Any]:
        """
        Get available workpieces.
        Default implementation - can be overridden by specific applications.
        """
        return self.workpieceService.loadAllWorkpieces()
    
    def shutdown(self):
        """Shutdown the application and cleanup resources"""
        self.state_manager.update_state(ApplicationState.STOPPING)
        self.state_manager.stop_state_publisher_thread()
        self.subscription_manager.unsubscribe_all()
    
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
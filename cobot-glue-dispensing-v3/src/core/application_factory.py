"""
Application Factory

This module provides a factory for creating and managing robot applications.
It allows easy switching between different robot applications and manages
their lifecycle.
"""

from typing import Dict, Optional, Type, List
import logging

from .application.interfaces.robot_application_interface import RobotApplicationInterface
from .base_robot_application import BaseRobotApplication, ApplicationType

from backend.system.vision.VisionService import _VisionService
from backend.system.settings.SettingsService import SettingsService
from modules.shared.core.workpiece.WorkpieceService import WorkpieceService
from modules.robot.robotService.RobotService import RobotService
from applications.glue_dispensing_application.GlueDispensingApplication import GlueSprayingApplication
from applications.example_painting_application.application import PaintingApplication
logger = logging.getLogger(__name__)


class ApplicationRegistryError(Exception):
    """Raised when there are issues with application registration"""
    pass


class ApplicationCreationError(Exception):
    """Raised when application creation fails"""
    pass


class ApplicationFactory:
    """
    Factory for creating and managing robot applications.
    
    This factory provides:
    - Application type registration and discovery
    - Dynamic application creation
    - Application lifecycle management
    - Easy switching between different applications
    """
    
    def __init__(self, 
                 vision_service: _VisionService,
                 settings_service: SettingsService,
                 workpiece_service: WorkpieceService,
                 robot_service: RobotService):
        """
        Initialize the application factory with core services.
        
        Args:
            vision_service: Vision system service
            settings_service: Settings management service
            workpiece_service: Workpiece management service
            robot_service: Robot control service
        """
        self.vision_service = vision_service
        self.settings_service = settings_service
        self.workpiece_service = workpiece_service
        self.robot_service = robot_service
        
        # Registry of application types to their implementation classes
        self._application_registry: Dict[ApplicationType, Type[BaseRobotApplication]] = {}
        
        # Currently active application instance
        self._current_application: Optional[RobotApplicationInterface] = None
        self._current_application_type: Optional[ApplicationType] = None
        
        # Application instances cache (for quick switching)
        self._application_cache: Dict[ApplicationType, RobotApplicationInterface] = {}

        # Whether to cache application instances
        self._use_cache = True
        
        logger.info("ApplicationFactory initialized")
    
    def register_application(self, 
                           app_type: ApplicationType, 
                           app_class: Type[BaseRobotApplication]) -> None:
        """
        Register an application type with its implementation class.
        
        Args:
            app_type: Type of the application
            app_class: Class that implements the application
            
        Raises:
            ApplicationRegistryError: If registration fails
        """
        if not issubclass(app_class, BaseRobotApplication):
            raise ApplicationRegistryError(
                f"Application class {app_class.__name__} must inherit from BaseRobotApplication"
            )
        
        if app_type in self._application_registry:
            logger.warning(f"Overriding existing registration for {app_type.value}")
        
        self._application_registry[app_type] = app_class
        logger.info(f"Registered application: {app_type.value} -> {app_class.__name__}")
    
    def unregister_application(self, app_type: ApplicationType) -> None:
        """
        Unregister an application type.
        
        Args:
            app_type: Type of the application to unregister
        """
        if app_type in self._application_registry:
            del self._application_registry[app_type]
            
            # Remove from cache if present
            if app_type in self._application_cache:
                self._shutdown_application(self._application_cache[app_type])
                del self._application_cache[app_type]
            
            # Clear current application if it's the one being unregistered
            if self._current_application_type == app_type:
                self._current_application = None
                self._current_application_type = None
            
            logger.info(f"Unregistered application: {app_type.value}")
    
    def create_application(self, 
                         app_type: ApplicationType,
                         use_cache: bool = None) -> RobotApplicationInterface:
        """
        Create an instance of the specified application type.
        
        Args:
            app_type: Type of application to create
            use_cache: Whether to use cached instance if available
            
        Returns:
            Instance of the requested application
            
        Raises:
            ApplicationCreationError: If creation fails
        """
        use_cache = use_cache if use_cache is not None else self._use_cache
        
        # Check if we have a cached instance
        if use_cache and app_type in self._application_cache:
            logger.info(f"Returning cached instance of {app_type.value}")
            return self._application_cache[app_type]
        
        # Check if application type is registered
        if app_type not in self._application_registry:
            raise ApplicationCreationError(
                f"Application type {app_type.value} is not registered. "
                f"Available types: {list(self._application_registry.keys())}"
            )
        
        try:
            # Get the application class
            app_class = self._application_registry[app_type]
            
            # Create the application instance
            logger.info(f"Creating new instance of {app_type.value}")
            application = app_class(
                vision_service=self.vision_service,
                settings_manager=self.settings_service,
                workpiece_service=self.workpiece_service,
                robot_service=self.robot_service
            )
            
            # Cache the instance if caching is enabled
            if use_cache:
                self._application_cache[app_type] = application
            
            logger.info(f"Successfully created application: {app_type.value}")
            return application
            
        except Exception as e:
            logger.error(f"Failed to create application {app_type.value}: {e}")
            raise ApplicationCreationError(f"Failed to create {app_type.value}: {e}") from e
    
    def switch_application(self, app_type: ApplicationType) -> RobotApplicationInterface:
        """
        Switch to a different application type.
        
        This method will:
        1. Stop the current application if running
        2. Create/get the new application
        3. Set it as the current application
        
        Args:
            app_type: Type of application to switch to
            
        Returns:
            The new current application instance
            
        Raises:
            ApplicationCreationError: If switching fails
        """
        try:
            # If we're already using this application type, return current instance
            if (self._current_application_type == app_type and 
                self._current_application is not None):
                logger.info(f"Already using {app_type.value}, returning current instance")
                return self._current_application
            
            # Stop current application if it exists
            if self._current_application is not None:
                logger.info(f"Stopping current application: {self._current_application_type.value}")
                try:
                    self._current_application.stop()
                except Exception as e:
                    logger.warning(f"Error stopping current application: {e}")
            
            # Create/get the new application
            logger.info(f"Switching to application: {app_type.value}")
            new_application = self.create_application(app_type)
            
            # Set as current application
            self._current_application = new_application
            self._current_application_type = app_type
            
            logger.info(f"Successfully switched to {app_type.value}")
            return new_application
            
        except Exception as e:
            logger.error(f"Failed to switch to application {app_type.value}: {e}")
            raise ApplicationCreationError(f"Failed to switch to {app_type.value}: {e}") from e
    
    def get_current_application(self) -> Optional[RobotApplicationInterface]:
        """
        Get the currently active application.
        
        Returns:
            Current application instance or None if no application is active
        """
        return self._current_application
    
    def get_current_application_type(self) -> Optional[ApplicationType]:
        """
        Get the type of the currently active application.
        
        Returns:
            Current application type or None if no application is active
        """
        return self._current_application_type
    
    def get_registered_applications(self) -> List[ApplicationType]:
        """
        Get list of all registered application types.
        
        Returns:
            List of registered application types
        """
        return list(self._application_registry.keys())

    
    def is_application_registered(self, app_type: ApplicationType) -> bool:
        """
        Check if an application type is registered.
        
        Args:
            app_type: Application type to check
            
        Returns:
            True if registered, False otherwise
        """
        return app_type in self._application_registry
    
    def set_cache_enabled(self, enabled: bool) -> None:
        """
        Enable or disable application instance caching.
        
        Args:
            enabled: Whether to enable caching
        """
        self._use_cache = enabled
        
        if not enabled:
            # Clear existing cache
            self.clear_cache()
        
        logger.info(f"Application caching {'enabled' if enabled else 'disabled'}")
    
    def clear_cache(self) -> None:
        """
        Clear all cached application instances.
        """
        for app_type, application in self._application_cache.items():
            try:
                self._shutdown_application(application)
            except Exception as e:
                logger.warning(f"Error shutting down cached application {app_type.value}: {e}")
        
        self._application_cache.clear()
        logger.info("Application cache cleared")
    
    def shutdown(self) -> None:
        """
        Shutdown the factory and all managed applications.
        """
        logger.info("Shutting down ApplicationFactory")
        
        # Stop current application
        if self._current_application is not None:
            try:
                self._current_application.stop()
                self._shutdown_application(self._current_application)
            except Exception as e:
                logger.warning(f"Error stopping current application: {e}")
        
        # Clear cache and shutdown all cached applications
        self.clear_cache()
        
        # Clear current application reference
        self._current_application = None
        self._current_application_type = None
        
        logger.info("ApplicationFactory shutdown complete")
    
    def _shutdown_application(self, application: RobotApplicationInterface) -> None:
        """
        Safely shutdown an application instance.
        
        Args:
            application: Application instance to shutdown
        """
        try:
            if hasattr(application, 'shutdown'):
                application.shutdown()
        except Exception as e:
            logger.warning(f"Error during application shutdown: {e}")


# ========== Auto-Discovery and Registration ==========

def auto_register_applications(factory: ApplicationFactory) -> None:
    """
    Automatically discover and register available applications.
    
    Args:
        factory: ApplicationFactory instance to register applications with
    """
    logger.info("Auto-registering available applications")
    
    try:
        # Register Glue Dispensing Application
        factory.register_application(ApplicationType.GLUE_DISPENSING, GlueSprayingApplication)
        logger.info("Registered GlueDispensingApplication")
    except ImportError as e:
        logger.warning(f"Could not register GlueDispensingApplication: {e}")
    except Exception as e:
        logger.warning(f"Error registering GlueDispensingApplication: {e}")

    try:
        # Register Painting Application
        factory.register_application(ApplicationType.PAINT_APPLICATION, PaintingApplication)
        logger.info("Registered PaintingApplication")
    except ImportError as e:
        logger.warning(f"Could not register PaintingApplication: {e}")
    except Exception as e:
        logger.warning(f"Error registering PaintingApplication: {e}")

    # TODO: Add other applications as they become available
    # try:
    #     from backend.robot_application.paint_application.PaintApplication import PaintApplication
    #     factory.register_application(ApplicationType.PAINT_APPLICATION, PaintApplication)
    #     logger.info("Registered PaintApplication")
    # except ImportError as e:
    #     logger.warning(f"Could not register PaintApplication: {e}")
    
    logger.info(f"Auto-registration complete. Registered applications: {factory.get_registered_applications()}")


# ========== Factory Creation Helper ==========

def create_application_factory(vision_service: _VisionService,
                             settings_service: SettingsService,
                             workpiece_service: WorkpieceService,
                             robot_service: RobotService,
                             auto_register: bool = True) -> ApplicationFactory:
    """
    Create and configure an ApplicationFactory with automatic application discovery.
    
    Args:
        vision_service: Vision system service
        settings_service: Settings management service
        workpiece_service: Workpiece management service
        robot_service: Robot control service
        auto_register: Whether to automatically register discovered applications
        
    Returns:
        Configured ApplicationFactory instance
    """
    factory = ApplicationFactory(
        vision_service=vision_service,
        settings_service=settings_service,
        workpiece_service=workpiece_service,
        robot_service=robot_service
    )
    
    if auto_register:
        auto_register_applications(factory)
    
    return factory

#
# def settings_registry():
#     return None
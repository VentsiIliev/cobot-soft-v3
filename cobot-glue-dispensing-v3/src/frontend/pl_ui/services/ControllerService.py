"""
Controller Service

Central coordinator for all UI-to-backend operations.
Uses dependency injection - no global state!
"""

import logging
from typing import TYPE_CHECKING

# Import domain services
from .domain.SettingsService import SettingsService
from .domain.RobotService import RobotService
from .domain.CameraService import CameraService
from .domain.WorkpieceService import WorkpieceService
from .domain.OperationService import OperationsService
from .domain.AuthService import AuthService

if TYPE_CHECKING:
    # Avoid circular imports while maintaining type hints
    from frontend.pl_ui.controller.Controller import Controller


class ControllerService:
    """
    Main coordinator for all backend operations.
    
    Provides clean, explicit APIs through domain-specific services.
    No callbacks, no global state - just clear dependency injection.
    
    Usage:
        # In main application startup:
        controller = Controller(request_sender)
        service = ControllerService(controller)
        
        # In UI components - inject the service:
        widget = SettingsAppWidget(parent, controller_service=service)
        
        # In UI component methods:
        result = self.service.settings.update_setting(key, value, component_type)
        if result:
            self.show_success("Settings saved!")
        else:
            self.show_error(f"Failed: {result.message}")
    """
    
    def __init__(self, controller: 'Controller'):
        """
        Initialize the controller service with all domain services.
        
        Args:
            controller: The main controller instance
        """
        self.controller = controller
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize all domain services immediately (no lazy loading)
        self.settings = SettingsService(controller, self.logger)
        self.robot = RobotService(controller, self.logger)
        self.camera = CameraService(controller, self.logger)
        self.workpiece = WorkpieceService(controller, self.logger)
        self.operations = OperationsService(controller, self.logger)
        self.auth = AuthService(controller, self.logger)
        
        self.logger.info("ControllerService initialized with all domain services")
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return f"ControllerService(services={list(self.__dict__.keys())})"
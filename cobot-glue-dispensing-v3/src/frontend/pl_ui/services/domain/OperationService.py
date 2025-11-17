"""
Operations Domain Service

Handles all operation-related commands with explicit return values.
No callbacks - just clean, clear method calls!
"""

import logging
from typing import TYPE_CHECKING

from ..types.ServiceResult import ServiceResult

# Import endpoint constants
from modules.shared.v1.endpoints import operations_endpoints

if TYPE_CHECKING:
    from frontend.pl_ui.controller.Controller import Controller


class OperationsService:
    """
    Domain service for all operation commands.
    
    Provides explicit, type-safe methods for operation control.
    All methods return ServiceResult - no callbacks needed!
    
    Usage:
        result = operations_service.start()
        if result:
            print("Operation started successfully!")
        else:
            print(f"Failed to start: {result.message}")
    """
    
    def __init__(self, controller: 'Controller', logger: logging.Logger):
        """
        Initialize the operations service.
        
        Args:
            controller: The main controller instance
            logger: Logger for this service
        """
        self.controller = controller
        self.logger = logger.getChild(self.__class__.__name__)
    
    def start(self) -> ServiceResult:
        """
        Start the current operation.
        
        Returns:
            ServiceResult with start success/failure
        """
        try:
            self.logger.info("Starting operation")
            
            self.controller.handleStart()
            
            return ServiceResult.success_result("Operation started successfully")
                
        except Exception as e:
            error_msg = f"Failed to start operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def pause(self) -> ServiceResult:
        """
        Pause the current operation.
        
        Returns:
            ServiceResult with pause success/failure
        """
        try:
            self.logger.info("Pausing operation")
            
            self.controller.handlePause()
            
            return ServiceResult.success_result("Operation paused successfully")
                
        except Exception as e:
            error_msg = f"Failed to pause operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def stop(self) -> ServiceResult:
        """
        Stop the current operation.
        
        Returns:
            ServiceResult with stop success/failure
        """
        try:
            self.logger.info("Stopping operation")
            
            self.controller.handleStop()
            
            return ServiceResult.success_result("Operation stopped successfully")
                
        except Exception as e:
            error_msg = f"Failed to stop operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def run_demo(self) -> ServiceResult:
        """
        Run demo operation.
        
        Returns:
            ServiceResult with demo start success/failure
        """
        try:
            self.logger.info("Starting demo operation")
            
            status = self.controller.handleRunDemo()
            
            if str(status) == "SUCCESS":
                return ServiceResult.success_result("Demo operation started successfully")
            else:
                return ServiceResult.error_result("Failed to start demo operation")
                
        except Exception as e:
            error_msg = f"Failed to run demo: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def stop_demo(self) -> ServiceResult:
        """
        Stop demo operation.
        
        Returns:
            ServiceResult with demo stop success/failure
        """
        try:
            self.logger.info("Stopping demo operation")
            
            status = self.controller.handleStopDemo()
            
            if str(status) == "SUCCESS":
                return ServiceResult.success_result("Demo operation stopped successfully")
            else:
                return ServiceResult.error_result("Failed to stop demo operation")
                
        except Exception as e:
            error_msg = f"Failed to stop demo: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def test_run(self) -> ServiceResult:
        """
        Run test operation.
        
        Returns:
            ServiceResult with test run success/failure
        """
        try:
            self.logger.info("Starting test run")
            
            self.controller.handleTestRun()
            
            return ServiceResult.success_result("Test run started successfully")
                
        except Exception as e:
            error_msg = f"Failed to run test: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
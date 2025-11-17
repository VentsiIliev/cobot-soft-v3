"""
Workpiece Domain Service

Handles all workpiece-related operations with explicit return values.
No callbacks - just clean, clear method calls!
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..types.ServiceResult import ServiceResult

# Import endpoint constants
from modules.shared.v1.endpoints import workpiece_endpoints

if TYPE_CHECKING:
    from frontend.pl_ui.controller.Controller import Controller


class WorkpieceService:
    """
    Domain service for all workpiece operations.
    
    Provides explicit, type-safe methods for workpiece CRUD.
    All methods return ServiceResult - no callbacks needed!
    
    Usage:
        result = workpiece_service.get_all_workpieces()
        if result:
            workpieces = result.data
            display_workpieces(workpieces)
        else:
            print(f"Failed to get workpieces: {result.message}")
    """
    
    def __init__(self, controller: 'Controller', logger: logging.Logger):
        """
        Initialize the workpiece service.
        
        Args:
            controller: The main controller instance
            logger: Logger for this service
        """
        self.controller = controller
        self.logger = logger.getChild(self.__class__.__name__)
    
    def get_all_workpieces(self) -> ServiceResult:
        """
        Get all workpieces from the system.
        
        Returns:
            ServiceResult with list of workpieces or error message
        """
        try:
            self.logger.info("Retrieving all workpieces")
            
            workpieces = self.controller.handleGetAllWorpieces()
            
            if workpieces is not None:
                return ServiceResult.success_result(
                    f"Retrieved {len(workpieces)} workpieces",
                    data=workpieces
                )
            else:
                return ServiceResult.error_result("Failed to retrieve workpieces")
                
        except Exception as e:
            error_msg = f"Failed to get workpieces: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def get_workpiece_by_id(self, workpiece_id: str) -> ServiceResult:
        """
        Get a specific workpiece by ID.
        
        Args:
            workpiece_id: The ID of the workpiece to retrieve
        
        Returns:
            ServiceResult with workpiece data or error message
        """
        try:
            if not workpiece_id or workpiece_id.strip() == "":
                return ServiceResult.error_result("Workpiece ID cannot be empty")
            
            self.logger.info(f"Retrieving workpiece with ID: {workpiece_id}")
            
            success, workpiece = self.controller.getWorkpieceById(workpiece_id)
            
            if success:
                return ServiceResult.success_result(
                    f"Workpiece retrieved successfully",
                    data=workpiece
                )
            else:
                return ServiceResult.error_result(f"Failed to retrieve workpiece: {workpiece}")
                
        except Exception as e:
            error_msg = f"Failed to get workpiece {workpiece_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def delete_workpiece(self, workpiece_id: str) -> ServiceResult:
        """
        Delete a workpiece by ID.
        
        Args:
            workpiece_id: The ID of the workpiece to delete
        
        Returns:
            ServiceResult with deletion success/failure
        """
        try:
            if not workpiece_id or workpiece_id.strip() == "":
                return ServiceResult.error_result("Workpiece ID cannot be empty")
            
            self.logger.info(f"Deleting workpiece with ID: {workpiece_id}")
            
            success, message = self.controller.handleDeleteWorkpiece(workpiece_id)
            
            if success:
                return ServiceResult.success_result(f"Workpiece deleted successfully: {message}")
            else:
                return ServiceResult.error_result(f"Failed to delete workpiece: {message}")
                
        except Exception as e:
            error_msg = f"Failed to delete workpiece {workpiece_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def create_workpiece_step1(self) -> ServiceResult:
        """
        Start workpiece creation process (step 1).
        
        Returns:
            ServiceResult with step 1 success/failure
        """
        try:
            self.logger.info("Starting workpiece creation step 1")
            
            success, message = self.controller.handleCreateWorkpieceStep1()
            
            if success:
                return ServiceResult.success_result(f"Workpiece creation step 1 successful: {message}")
            else:
                return ServiceResult.error_result(f"Workpiece creation step 1 failed: {message}")
                
        except Exception as e:
            error_msg = f"Failed workpiece creation step 1: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def create_workpiece_step2(self) -> ServiceResult:
        """
        Continue workpiece creation process (step 2).
        
        Returns:
            ServiceResult with step 2 success/failure and data
        """
        try:
            self.logger.info("Starting workpiece creation step 2")
            
            success, message, data = self.controller.handleCreateWorkpieceStep2()
            
            if success:
                return ServiceResult.success_result(
                    f"Workpiece creation step 2 successful: {message}",
                    data=data
                )
            else:
                return ServiceResult.error_result(f"Workpiece creation step 2 failed: {message}")
                
        except Exception as e:
            error_msg = f"Failed workpiece creation step 2: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def save_workpiece(self, workpiece_data: Dict[str, Any]) -> ServiceResult:
        """
        Save workpiece data.
        
        Args:
            workpiece_data: The workpiece data to save
        
        Returns:
            ServiceResult with save success/failure
        """
        try:
            if not workpiece_data:
                return ServiceResult.error_result("Workpiece data cannot be empty")
            
            self.logger.info("Saving workpiece data")
            
            result = self.controller.saveWorkpiece(workpiece_data)
            
            return ServiceResult.success_result(
                "Workpiece saved successfully",
                data=result
            )
                
        except Exception as e:
            error_msg = f"Failed to save workpiece: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def execute_from_gallery(self, workpiece: Any) -> ServiceResult:
        """
        Execute a workpiece from the gallery.
        
        Args:
            workpiece: The workpiece to execute
        
        Returns:
            ServiceResult with execution success/failure
        """
        try:
            if not workpiece:
                return ServiceResult.error_result("Workpiece cannot be empty")
            
            self.logger.info(f"Executing workpiece from gallery")
            
            self.controller.handleExecuteFromGallery(workpiece)
            
            return ServiceResult.success_result("Workpiece execution started successfully")
                
        except Exception as e:
            error_msg = f"Failed to execute workpiece from gallery: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def set_preselected_workpiece(self, workpiece: Any) -> ServiceResult:
        """
        Set a workpiece as preselected.
        
        Args:
            workpiece: The workpiece to preselect
        
        Returns:
            ServiceResult with success/failure
        """
        try:
            if not workpiece:
                return ServiceResult.error_result("Workpiece cannot be empty")
            
            self.logger.info("Setting preselected workpiece")
            
            self.controller.handleSetPreselectedWorkpiece(workpiece)
            
            return ServiceResult.success_result("Workpiece preselected successfully")
                
        except Exception as e:
            error_msg = f"Failed to set preselected workpiece: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
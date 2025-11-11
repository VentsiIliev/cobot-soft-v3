"""
Workpiece Handler - API Gateway

Handles all workpiece-related requests including CRUD operations, creation workflow, and DXF import.
"""

from modules.shared.v1.Response import Response
from modules.shared.v1 import Constants
from modules.shared.shared.workpiece.Workpiece import WorkpieceField
from modules.shared.v1.endpoints import workpiece_endpoints
import traceback


class WorkpieceHandler:
    """
    Handles workpiece operations for the API gateway.
    
    This handler manages workpiece creation, saving, deletion, and import operations.
    """
    
    def __init__(self, application, workpieceController):
        """
        Initialize the WorkpieceHandler.
        
        Args:
            application: Main GlueSprayingApplication instance
            workpieceController: Workpiece controller instance
        """
        self.application = application
        self.workpieceController = workpieceController
    
    def handle(self, parts, request, data=None):
        """
        Route workpiece requests to appropriate handlers.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response dictionary with operation result
        """
        print(f"WorkpieceHandler: Handling request: {request} with parts: {parts}")
        
        # Handle both new RESTful endpoints and legacy endpoints
        if request in [workpiece_endpoints.WORKPIECE_SAVE, workpiece_endpoints.WORKPIECE_SAVE_LEGACY] or (len(parts) > 1 and parts[1] == "save"):
            return self.handle_save_workpiece(request, parts, data)
        elif request in [workpiece_endpoints.WORKPIECE_SAVE_DXF, workpiece_endpoints.WORKPIECE_SAVE_DXF_LEGACY] or (len(parts) > 1 and parts[1] == "dxf"):
            return self.handle_save_workpiece_from_dxf(data)
        elif request in [workpiece_endpoints.WORKPIECE_CREATE, workpiece_endpoints.WORKPIECE_CREATE_LEGACY] or (len(parts) > 1 and parts[1] == "create"):
            return self.handle_create_workpiece()
        elif request in [workpiece_endpoints.WORKPIECE_CREATE_STEP_1, workpiece_endpoints.WORKPIECE_CREATE_STEP_1_LEGACY] or (len(parts) > 1 and parts[1] == "create_step_1"):
            return self.handle_create_workpiece_step_1()
        elif request in [workpiece_endpoints.WORKPIECE_CREATE_STEP_2, workpiece_endpoints.WORKPIECE_CREATE_STEP_2_LEGACY] or (len(parts) > 1 and parts[1] == "create_step_2"):
            return self.handle_create_workpiece_step_2()
        elif request in [workpiece_endpoints.WORKPIECE_GET_ALL, workpiece_endpoints.WORKPIECE_GET_ALL_LEGACY, workpiece_endpoints.WORPIECE_GET_ALL] or (len(parts) > 1 and parts[1] == "getall"):
            return self.handle_get_all_workpieces()
        elif request in [workpiece_endpoints.WORKPIECE_DELETE, workpiece_endpoints.WORKPIECE_DELETE_LEGACY, workpiece_endpoints.WORKPIECE_DELETE_LEGACY_2] or (len(parts) > 1 and parts[1] == "delete"):
            return self.handle_delete_workpiece(data)
        elif request in [workpiece_endpoints.WORKPIECE_GET_BY_ID, workpiece_endpoints.WORKPIECE_GET_BY_ID_LEGACY, workpiece_endpoints.WORKPIECE_GET_BY_ID_LEGACY_2] or (len(parts) > 1 and parts[1] == "getbyid"):
            return self.handle_get_workpiece_by_id(data)
        else:
            raise ValueError(f"Unknown request: {request}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR,
                message=f"Invalid workpiece command: {request}"
            ).to_dict()
    
    def handle_save_workpiece(self, request, parts, data):
        """
        Handle workpiece saving with spray pattern transformation.
        
        Args:
            request (str): Full request string
            parts (list): Parsed request parts
            data (dict): Workpiece data to save
            
        Returns:
            dict: Response indicating success or failure
        """
        print("WorkpieceHandler: Handling save workpiece")
        
        try:
            # Extract and transform spray pattern
            sprayPattern = data.get(WorkpieceField.SPRAY_PATTERN.value, {})
            contours = sprayPattern.get("Contour")
            fill = sprayPattern.get("Fill")
            
            # Handle external contours
            externalContours = data.get(WorkpieceField.CONTOUR.value, [])
            print(f"WorkpieceHandler: Original contours: {externalContours}")
            
            if externalContours is None or len(externalContours) == 0:
                externalContour = []
            else:
                # externalContours should be in dict format {"contour": points, "settings": {...}}
                externalContour = externalContours
            
            data[WorkpieceField.CONTOUR.value] = externalContour
            
            # Update spray pattern
            sprayPattern['Contour'] = contours
            sprayPattern['Fill'] = fill
            data[WorkpieceField.SPRAY_PATTERN.value] = sprayPattern
            
            print(f"WorkpieceHandler: Data after transform: {data}")
            
            # Save workpiece
            result = self.workpieceController._saveWorkpiece(data)
            
            if result:
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message="Workpiece saved successfully"
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message="Error saving workpiece"
                ).to_dict()
                
        except Exception as e:
            print(f"WorkpieceHandler: Error saving workpiece: {e}")
            traceback.print_exc()
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error saving workpiece: {e}"
            ).to_dict()
    
    def handle_save_workpiece_from_dxf(self, data):
        """
        Handle workpiece import from DXF format.
        
        Args:
            data: DXF workpiece data
            
        Returns:
            dict: Response indicating success or failure
        """
        print("WorkpieceHandler: Handling save workpiece from DXF")
        
        try:
            result = self.workpieceController.handlePostRequest(data)
            
            if result:
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message="Workpiece saved successfully"
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message="Error saving workpiece"
                ).to_dict()
                
        except Exception as e:
            print(f"WorkpieceHandler: Error saving workpiece from DXF: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error saving workpiece from DXF: {e}"
            ).to_dict()
    
    def handle_create_workpiece(self):
        """
        Handle workpiece creation workflow.
        
        Returns:
            dict: Response with workpiece creation data
        """
        print("WorkpieceHandler: Handling create workpiece")
        
        try:
            result, data = self.application.createWorkpiece()
            
            if not result:
                return Response(Constants.RESPONSE_STATUS_ERROR, message=data).to_dict()
            
            height, contourArea, contour, scaleFactor, image, message, originalContours = data
            
            # Temporary workaround: force height to 4
            if height is None:
                height = 4
            if height < 4 or height > 4:
                height = 4
            
            # Cache data in the workpiece controller
            self.workpieceController.cacheInfo = {
                WorkpieceField.HEIGHT.value: height,
                WorkpieceField.CONTOUR_AREA.value: contourArea,
            }
            self.workpieceController.scaleFactor = scaleFactor
            
            originalContour = []
            if originalContours is not None and len(originalContours) > 0:
                originalContour = originalContours[0]
            
            dataDict = {
                WorkpieceField.HEIGHT.value: height, 
                "image": image,
                "contours": originalContour
            }
            
            return Response(
                Constants.RESPONSE_STATUS_SUCCESS, 
                message=message, 
                data=dataDict
            ).to_dict()
            
        except Exception as e:
            print(f"WorkpieceHandler: Uncaught exception in create workpiece: {e}")
            traceback.print_exc()
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Uncaught exception: {e}"
            ).to_dict()
    
    def handle_create_workpiece_step_1(self):
        """
        Handle workpiece creation step 1.
        
        Returns:
            dict: Response indicating success or failure of step 1
        """
        print("WorkpieceHandler: Handling create workpiece step 1")
        
        try:
            result, message = self.application.create_workpiece_step_1()
            
            if result:
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message=message
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message=message
                ).to_dict()
                
        except Exception as e:
            print(f"WorkpieceHandler: Error in create workpiece step 1: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error in create workpiece step 1: {e}"
            ).to_dict()
    
    def handle_create_workpiece_step_2(self):
        """
        Handle workpiece creation step 2.
        
        Returns:
            dict: Response with step 2 data
        """
        print("WorkpieceHandler: Handling create workpiece step 2")
        
        try:
            result, data = self.application.create_workpiece_step_2()
            
            if not result:
                return Response(Constants.RESPONSE_STATUS_ERROR, message=data).to_dict()
            
            height, contourArea, contour, scaleFactor, image, message, originalContours = data
            
            # Temporary workaround: force height to 4
            if height is None:
                height = 4
            if height < 4 or height > 4:
                height = 4
            
            # Cache data in the workpiece controller
            self.workpieceController.cacheInfo = {
                WorkpieceField.HEIGHT.value: height,
                WorkpieceField.CONTOUR_AREA.value: contourArea,
            }
            self.workpieceController.scaleFactor = scaleFactor
            
            originalContour = []
            if originalContours is not None and len(originalContours) > 0:
                originalContour = originalContours[0]
            
            dataDict = {
                WorkpieceField.HEIGHT.value: height, 
                "image": image,
                "contours": originalContour
            }
            
            return Response(
                Constants.RESPONSE_STATUS_SUCCESS, 
                message=message, 
                data=dataDict
            ).to_dict()
            
        except Exception as e:
            print(f"WorkpieceHandler: Error in create workpiece step 2: {e}")
            traceback.print_exc()
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error in create workpiece step 2: {e}"
            ).to_dict()
    
    def handle_get_all_workpieces(self):
        """
        Handle getting all workpieces.
        
        Returns:
            dict: Response with all workpieces data
        """
        print("WorkpieceHandler: Handling get all workpieces")
        
        try:
            return self.workpieceController._getAllWorkpieces()
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error getting all workpieces: {e}"
            ).to_dict()
    
    def handle_get_workpiece_by_id(self, data):
        """
        Handle getting workpiece by ID.
        
        Args:
            data (dict): Request data containing workpiece ID
            
        Returns:
            dict: Response with workpiece data or error
        """
        print(f"WorkpieceHandler: Handling get workpiece by ID: {data}")
        
        try:
            workpieceId = data.get("workpieceId", None)
            if workpieceId is None:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message="Workpiece ID not provided"
                ).to_dict()
            
            workpiece = self.workpieceController.getWorkpieceById(workpieceId)
            
            if workpiece:
                # Convert workpiece object to dictionary for serialization
                workpiece_dict = workpiece.toDict()
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    data=workpiece_dict
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message="Workpiece not found"
                ).to_dict()
                
        except Exception as e:
            print(f"WorkpieceHandler: Error getting workpiece by ID: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error getting workpiece by ID: {e}"
            ).to_dict()
    
    def handle_delete_workpiece(self, data):
        """
        Handle workpiece deletion.
        
        Args:
            data (dict): Request data containing workpiece ID
            
        Returns:
            dict: Response indicating success or failure
        """
        print(f"WorkpieceHandler: Handling delete workpiece: {data}")
        
        try:
            workpieceId = data.get("workpieceId", None)
            if workpieceId is None:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message="Workpiece ID not provided"
                ).to_dict()
            
            result = self.workpieceController.deleteWorkpiece(workpieceId)
            
            if result:
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message="Workpiece deleted successfully"
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message="Error deleting workpiece"
                ).to_dict()
                
        except Exception as e:
            print(f"WorkpieceHandler: Error deleting workpiece: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error deleting workpiece: {e}"
            ).to_dict()
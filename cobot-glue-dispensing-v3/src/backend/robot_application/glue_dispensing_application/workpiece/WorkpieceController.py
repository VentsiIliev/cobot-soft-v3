from modules.shared.shared.workpiece.WorkpieceService import WorkpieceService
from modules.shared.v1 import Constants
from src.backend.robot_application.glue_dispensing_application.workpiece.Workpiece import Workpiece
import modules.shared.v1.endpoints.workpiece_endpoints as workpiece_endpoints


class WorkpieceController:
    """
    Controller for handling workpiece-related requests.

    Supports:
        - CRUD operations
        - Multi-step creation workflow
        - DXF import
        - Legacy endpoints
    """

    def __init__(self, workpieceService: WorkpieceService):
        if not isinstance(workpieceService, WorkpieceService):
            raise ValueError("workpieceService must be an instance of WorkpieceService")
        self.workpieceService = workpieceService

    # =========================
    # MAIN HANDLER
    # =========================
    def handle(self, request, parts, data=None):
        """
        Main handler for workpiece requests.

        Args:
            request (str): Full request string
            parts (list): Split request path parts
            data (dict, optional): Data for POST/save operations

        Returns:
            dict or bool: Response or operation result
        """
        try:
            # === GET ALL WORKPIECES ===
            if request in [workpiece_endpoints.WORKPIECE_GET_ALL, workpiece_endpoints.WORPIECE_GET_ALL, workpiece_endpoints.WORKPIECE_GET_ALL_LEGACY]:
                return self._getAllWorkpieces()

            # === GET WORKPIECE BY ID ===
            elif request in [workpiece_endpoints.WORKPIECE_GET_BY_ID, workpiece_endpoints.WORKPIECE_GET_BY_ID_LEGACY, workpiece_endpoints.WORKPIECE_GET_BY_ID_LEGACY_2]:
                workpieceId = data.get("id") if data else None
                return self._getWorkpieceById(workpieceId)

            # === SAVE WORKPIECE ===
            elif request in [workpiece_endpoints.WORKPIECE_SAVE, workpiece_endpoints.SAVE_WORKPIECE, workpiece_endpoints.WORKPIECE_SAVE_LEGACY]:
                return self._saveWorkpiece(data)

            # === DELETE WORKPIECE ===
            elif request in [workpiece_endpoints.WORKPIECE_DELETE, workpiece_endpoints.WORKPIECE_DELETE_LEGACY, workpiece_endpoints.WORKPIECE_DELETE_LEGACY_2]:
                workpieceId = data.get("id") if data else None
                return self._deleteWorkpiece(workpieceId)

            # === DXF IMPORT ===
            elif request in [workpiece_endpoints.WORKPIECE_SAVE_DXF, workpiece_endpoints.WORKPIECE_SAVE_DXF_LEGACY, workpiece_endpoints.SAVE_WORKPIECE_DXF]:
                return self._saveWorkpieceDXF(data)

            # === MULTI-STEP CREATION ===
            elif request in [
                workpiece_endpoints.WORKPIECE_CREATE,
                workpiece_endpoints.WORKPIECE_CREATE_LEGACY,
            ]:
                return self._createWorkpiece(data)

            elif request in [
                workpiece_endpoints.WORKPIECE_CREATE_STEP_1,
                workpiece_endpoints.CREATE_WORKPIECE_STEP_1,
                workpiece_endpoints.WORKPIECE_CREATE_STEP_1_LEGACY,
            ]:
                return self._createWorkpieceStep(1, data)

            elif request in [
                workpiece_endpoints.WORKPIECE_CREATE_STEP_2,
                workpiece_endpoints.CREATE_WORKPIECE_STEP_2,
                workpiece_endpoints.WORKPIECE_CREATE_STEP_2_LEGACY,
            ]:
                return self._createWorkpieceStep(2, data)

            else:
                raise ValueError(f"Unknown workpiece endpoint: {request}")

        except Exception as e:
            print(f"Error handling workpiece request: {e}")
            return {
                "status": Constants.RESPONSE_STATUS_ERROR,
                "message": f"Error processing request: {e}",
                "data": None,
            }

    # =========================
    # INTERNAL HANDLERS
    # =========================

    def _getAllWorkpieces(self):
        workpieces = self.workpieceService.loadAllWorkpieces()
        for wp in workpieces:
            print(f"Loaded workpiece: ID={wp.workpieceId}, Name={wp.name}")

        return {
            "status": Constants.RESPONSE_STATUS_SUCCESS,
            "message": "Loaded all workpieces",
            "data": workpieces,
        }

    def _getWorkpieceById(self, workpieceId):
        if not workpieceId:
            return {
                "status": Constants.RESPONSE_STATUS_ERROR,
                "message": "No workpiece ID provided",
                "data": None,
            }
        workpiece = self.workpieceService.get_workpiece_by_id(workpieceId)
        if not workpiece:
            return {
                "status": Constants.RESPONSE_STATUS_ERROR,
                "message": f"Workpiece {workpieceId} not found",
                "data": None,
            }
        return {
            "status": Constants.RESPONSE_STATUS_SUCCESS,
            "message": f"Workpiece {workpieceId} retrieved",
            "data": workpiece,
        }

    def _saveWorkpiece(self, data):
        if not data:
            return {
                "status": Constants.RESPONSE_STATUS_ERROR,
                "message": "No data provided for saving workpiece",
                "data": None,
            }
        try:
            workpiece = Workpiece.fromDict(data)
        except Exception as e:
            return {
                "status": Constants.RESPONSE_STATUS_ERROR,
                "message": f"Error creating Workpiece from data: {e}",
                "data": None,
            }
        result = self.workpieceService.saveWorkpiece(workpiece)
        status = Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
        return {"status": status, "message": "Workpiece saved", "data": None}

    def _deleteWorkpiece(self, workpieceId):
        if not workpieceId:
            return {
                "status": Constants.RESPONSE_STATUS_ERROR,
                "message": "No workpiece ID provided for deletion",
                "data": None,
            }
        result = self.workpieceService.deleteWorkpiece(workpieceId)
        status = Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
        return {"status": status, "message": "Workpiece deleted" if result else "Failed to delete workpiece", "data": None}

    def _saveWorkpieceDXF(self, data):
        # You can implement DXF import logic here
        return {"status": Constants.RESPONSE_STATUS_SUCCESS, "message": "DXF import not implemented yet", "data": None}

    def _createWorkpiece(self, data):
        # Placeholder for multi-step creation workflow
        return {"status": Constants.RESPONSE_STATUS_SUCCESS, "message": "Create workpiece not implemented yet", "data": None}

    def _createWorkpieceStep(self, step, data):
        # Placeholder for individual creation steps
        return {"status": Constants.RESPONSE_STATUS_SUCCESS, "message": f"Create workpiece step {step} not implemented yet", "data": None}
    
    def getWorkpieceById(self, workpieceId):
        """
        Public method to get workpiece by ID.
        Returns the actual workpiece object, not a response dict.
        
        Args:
            workpieceId (str): The ID of the workpiece to retrieve
            
        Returns:
            Workpiece or None: The workpiece object if found, None otherwise
        """
        if not workpieceId:
            print("No workpiece ID provided")
            return None
        
        try:
            workpiece = self.workpieceService.get_workpiece_by_id(workpieceId)
            return workpiece
        except Exception as e:
            print(f"Error getting workpiece by ID {workpieceId}: {e}")
            return None

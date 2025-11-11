# from shared.shared.database.repositories.WorkPieceRepository import WorkPieceRepository
from modules.shared.shared.workpiece.WorkpieceJsonRepository import WorkpieceJsonRepository
from modules.shared.shared.workpiece.Workpiece import  WorkpieceField
from src.backend.system.workpiece.Workpiece import Workpiece
import os
class WorkPieceRepositorySingleton:
    """
       Singleton class responsible for managing a single instance of the Workpiece repository.
       The class ensures that only one instance of the repository is created and provides a global
       point of access to it.

       This class uses `WorkpieceJsonRepository` to handle storage and retrieval of workpieces
       as JSON data.

       Attributes:
           _instance (WorkpieceJsonRepository or None): The single instance of the repository.

       Methods:
           get_instance(cls): Returns the singleton instance of the WorkpieceJsonRepository.
       """

    _instance = None

    @classmethod
    def get_instance(cls):
        """
                Retrieves the singleton instance of the `WorkpieceJsonRepository`. If the instance does
                not exist, it is created and initialized with necessary parameters.

                The repository is initialized with a directory path and a list of fields representing the
                attributes of a Workpiece. This ensures that the repository is set up to manage and store
                Workpiece objects correctly.

                Args:
                    cls (type): The class type, used to access the singleton instance.

                Returns:
                    WorkpieceJsonRepository: The singleton instance of the repository.

                Notes:
                    The instance is created with the directory `"system/storage"` and
                    a set of `WorkpieceField` attributes such as `WORKPIECE_ID`, `NAME`, `DESCRIPTION`,
                    and others required for managing Workpiece data.

                Example:
                    repo = WorkPieceRepositorySingleton.get_instance()
                    workpiece_data = repo.get_workpieces()  # Example of interacting with the repository
                """
        if cls._instance is None:
            # Compute an absolute path to the storage directory relative to this file
            storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'storage'))
            fields = [WorkpieceField.WORKPIECE_ID, WorkpieceField.NAME, WorkpieceField.DESCRIPTION,
                      WorkpieceField.TOOL_ID,WorkpieceField.GRIPPER_ID,
                      WorkpieceField.GLUE_TYPE, WorkpieceField.PROGRAM, WorkpieceField.MATERIAL, WorkpieceField.CONTOUR,
                      WorkpieceField.OFFSET, WorkpieceField.HEIGHT, WorkpieceField.SPRAY_PATTERN,
                      WorkpieceField.CONTOUR_AREA,
                      WorkpieceField.NOZZLES]
            cls._instance = WorkpieceJsonRepository(storage_dir, fields, Workpiece)
        return cls._instance
from core.application.interfaces.robot_application_interface import RobotApplicationInterface
from modules.shared.v1 import Constants
from applications.glue_dispensing_application.workpiece.WorkpieceController import WorkpieceController

# Import specialized handlers
from .auth_handler import AuthHandler
from .robot_handler import RobotHandler
from .camera_handler import CameraHandler
from .workpiece_handler import WorkpieceHandler
from .settings_handler import SettingsHandler
from .operations_handler import OperationsHandler

# Import endpoint modules
from modules.shared.v1.endpoints import auth_endpoints, operations_endpoints, camera_endpoints


class RequestHandler:
    """
      Handles the incoming requests and routes them to appropriate handlers
      based on the type of request (GET, POST, EXECUTE).

      Attributes:
          controller: The main controller for handling operations.
          settingsController: Controller for managing settings.
          cameraSystemController: Controller for camera system operations.
          glueNozzleController: Controller for glue nozzle operations.
          workpieceController: Controller for managing workpieces.
          robotController: Controller for managing robot operations.
      """
    def __init__(self, application: RobotApplicationInterface, settingsController, cameraSystemController, workpieceController:WorkpieceController, robotController, application_factory=None):
        """
              Initializes the RequestHandler with the necessary controllers.

              Args:
                  application (RobotApplicationInterface): The robot application instance.
                  settingsController (object): The settings controller.
                  cameraSystemController (object): The camera system controller.
                  workpieceController (object): The workpieces controller.
                  robotController (object): The robot controller.
                  application_factory (ApplicationFactory): Optional factory for application switching.
              """
        self.application = application
        self.settingsController = settingsController
        self.cameraSystemController = cameraSystemController
        self.workpieceController = workpieceController
        self.robotController = robotController

        # Initialize specialized handlers
        self.auth_handler = AuthHandler()
        self.robot_handler = RobotHandler(self.application, self.robotController)
        self.camera_handler = CameraHandler(self.application, self.cameraSystemController)
        self.workpiece_handler = WorkpieceHandler(self.application, self.workpieceController)
        self.settings_handler = SettingsHandler(self.settingsController)
        self.operations_handler = OperationsHandler(self.application, application_factory)

        self.resource_dispatch = {
            Constants.REQUEST_RESOURCE_ROBOT.lower(): self.robot_handler.handle,
            Constants.REQUEST_RESOURCE_CAMERA.lower(): self.camera_handler.handle,
            Constants.REQUEST_RESOURCE_SETTINGS.lower(): self.settings_handler.handle,
            Constants.REQUEST_RESOURCE_WORKPIECE.lower(): self.workpiece_handler.handle,
        }

    def handleRequest(self, request, data=None):
        """
        Main request handler that routes requests to specialized handlers.
        
        This method now delegates to specialized handlers for better organization.
        """
        # print(f"RequestHandler: Processing request: {request}")

        # Authentication requests
        if request in [auth_endpoints.QR_LOGIN]:
            return self.auth_handler.handle(request, data)

        # Main operations requests
        operations_requests = [
            operations_endpoints.START, operations_endpoints.STOP, operations_endpoints.PAUSE, operations_endpoints.TEST_RUN,
            operations_endpoints.RUN_DEMO, operations_endpoints.STOP_DEMO, operations_endpoints.CALIBRATE, operations_endpoints.HELP,
            "handleSetPreselectedWorkpiece", "handleExecuteFromGallery"
        ]
        if request in operations_requests:
            return self.operations_handler.handle(request, data)

        # Camera work area points
        if (request in [camera_endpoints.CAMERA_ACTION_SAVE_WORK_AREA_POINTS] or
            (len(self._parseRequest(request)) >= 2 and self._parseRequest(request)[1] == "saveWorkAreaPoints")):
            return self.camera_handler.handle_save_work_area_points(data)

        # Parse request for resource-based routing
        parts = self._parseRequest(request)

        # Try to detect which resource (robot, camera, settings, workpieces) is present in the path
        resource = next((p.lower() for p in parts if p.lower() in self.resource_dispatch), None)
        if resource:
            return self.resource_dispatch[resource](parts, request, data)

        print(f"RequestHandler: No handler found for request: {request}")
        print(f"Resource parsed: {resource}")
        print(f"Available resources: {list(self.resource_dispatch.keys())}")
        raise ValueError(f"Unknown request: {request}")


    def _parseRequest(self, request: str):
        """
        Parses the incoming request path into parts.
        Example:
            '/api/v1/workpieces/create/step-1' -> ['api', 'v1', 'workpieces', 'create', 'step-1']
        """
        return [p for p in request.strip("/").split("/") if p]


import logging
import os

from applications.glue_dispensing_application.workpiece.WorkPieceRepositorySingleton import WorkPieceRepositorySingleton
from frontend.pl_ui.localization import setup_localization

setup_localization()


from modules.shared.MessageBroker import MessageBroker
from modules.shared.core.workpiece.WorkpieceService import WorkpieceService
from modules.shared.v1.DomesticRequestSender import DomesticRequestSender
from core.application_factory import create_application_factory
from core.base_robot_application import ApplicationType
from backend.system.SensorPublisher import SensorPublisher

from modules.robot.RobotController import RobotController
from modules.robot.robotService.RobotService import RobotService
# IMPORT CONTROLLERS
from backend.system.settings.SettingsController import SettingsController

# IMPORT SERVICES
from backend.system.settings.SettingsService import SettingsService


from backend.system.vision.CameraSystemController import CameraSystemController
from backend.system.vision.VisionService import VisionServiceSingleton
from applications.glue_dispensing_application.workpiece.WorkpieceController import WorkpieceController
from backend.system.utils import PathResolver


if os.environ.get("WAYLAND_DISPLAY"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

logging.basicConfig(
    level=logging.CRITICAL,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
)

sensorPublisher = SensorPublisher()



API_VERSION = 1
newGui = True
testRobot = False
if newGui:
    from frontend.pl_ui.runPlUi import PlGui
else:
    pass

if __name__ == "__main__":
    messageBroker = MessageBroker()
    # INIT SERVICES
    camera_settings_path = PathResolver.get_settings_file_path("camera_settings.json")
    robot_settings_path = PathResolver.get_settings_file_path("robot_settings.json")
    settings_file_paths = {
        "camera":camera_settings_path,
        "robot_settings": robot_settings_path,
        "robot_config": PathResolver.get_settings_file_path("robot_config.json"),
    }

    settingsService = SettingsService(settings_file_paths=settings_file_paths)
    robot_config = settingsService.load_robot_config()

    if testRobot:
        from modules.robot.FairinoRobot import TestRobotWrapper
        robot = TestRobotWrapper()
    else:
        from modules.robot.FairinoRobot import FairinoRobot
        robot = FairinoRobot(robot_config.robot_ip)

    cameraService = VisionServiceSingleton().get_instance()

    repository = WorkPieceRepositorySingleton().get_instance()
    workpieceService = WorkpieceService(repository=repository)

    robotService = RobotService(robot, settingsService)

    # INIT CONTROLLERS
    settingsController = SettingsController(settingsService)
    cameraSystemController = CameraSystemController(cameraService)

    workpieceController = WorkpieceController(workpieceService)
    robotController = RobotController(robotService)

    # INIT APPLICATION FACTORY
    
    application_factory = create_application_factory(
        vision_service=cameraService,
        settings_service=settingsService, 
        workpiece_service=workpieceService,
        robot_service=robotService,
        auto_register=True
    )
    
    # GET CURRENT APPLICATION (defaulting to glue dispensing)
    # current_application = application_factory.switch_application(ApplicationType.PAINT_APPLICATION)
    current_application = application_factory.switch_application(ApplicationType.GLUE_DISPENSING)

    # INIT REQUEST HANDLER
    if API_VERSION == 1:

        from communication_layer.api_gateway.handlers.request_handler import RequestHandler
        requestHandler = RequestHandler(current_application, settingsController, cameraSystemController,
                                        workpieceController, robotController, application_factory)


    else:
        raise ValueError("Unsupported API_VERSION. Please set to 1 or 2.")

    logging.info("Request Handler initialized")
    """GUI RELATED INITIALIZATIONS"""

    # INIT DOMESTIC REQUEST SENDER
    domesticRequestSender = DomesticRequestSender(requestHandler)
    logging.info("Domestic Request Sender initialized")
    # INIT MAIN WINDOW

    if API_VERSION == 1:
        from frontend.pl_ui.controller.Controller import Controller
        controller = Controller(domesticRequestSender)
    else:
        raise ValueError("Unsupported API_VERSION. Please set to 1")


    from frontend.pl_ui.runPlUi import PlGui
    gui = PlGui(controller=controller)
    gui.start()


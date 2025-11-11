# from src.backend.GlueDispensingApplication.tools.Trolly import Trolly
import logging
import os

from src.frontend.pl_ui.localization import setup_localization
setup_localization()


from modules.shared.MessageBroker import MessageBroker
from modules.shared.shared.workpiece.WorkpieceService import WorkpieceService
from modules.shared.v1.DomesticRequestSender import DomesticRequestSender
from src.backend.GlueDispensingApplication.GlueSprayingApplication import GlueSprayingApplication
from src.backend.GlueDispensingApplication.SensorPublisher import SensorPublisher

from src.backend.GlueDispensingApplication.robot.RobotController import RobotController
from src.backend.GlueDispensingApplication.robot.robotService.RobotService import RobotService
# IMPORT CONTROLLERS
from src.backend.GlueDispensingApplication.settings.SettingsController import SettingsController
# from src.backend.GlueDispensingApplication.RequestHandler import RequestHandler
# IMPORT SERVICES
from src.backend.GlueDispensingApplication.settings.SettingsService import SettingsService
from src.backend.GlueDispensingApplication.tools.GlueCell import GlueDataFetcher


from src.backend.GlueDispensingApplication.vision.CameraSystemController import CameraSystemController
from src.backend.GlueDispensingApplication.vision.VisionService import VisionServiceSingleton
from src.backend.GlueDispensingApplication.workpiece.WorkpieceController import WorkpieceController


if os.environ.get("WAYLAND_DISPLAY"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

logging.basicConfig(
    level=logging.CRITICAL,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
)

sensorPublisher = SensorPublisher()

# register glue meters
glueFetcher = GlueDataFetcher()
glueFetcher.start()

API_VERSION = 1
newGui = True
testRobot = False
if newGui:
    from src.frontend.pl_ui.runPlUi import PlGui
else:
    pass

if __name__ == "__main__":
    messageBroker = MessageBroker()
    # INIT SERVICES
    settingsService = SettingsService()
    robot_config = settingsService.load_robot_config()

    if testRobot:
        from src.backend.GlueDispensingApplication.robot.FairinoRobot import TestRobotWrapper
        robot = TestRobotWrapper()
    else:
        from src.backend.GlueDispensingApplication.robot.FairinoRobot import FairinoRobot
        robot = FairinoRobot(robot_config.robot_ip)

    cameraService = VisionServiceSingleton().get_instance()

    workpieceService = WorkpieceService()

    robotService = RobotService(robot, settingsService)


    # INIT CONTROLLERS
    settingsController = SettingsController(settingsService)
    cameraSystemController = CameraSystemController(cameraService)

    workpieceController = WorkpieceController(workpieceService)
    robotController = RobotController(robotService)

    # INIT APPLICATION

    glueSprayingApplication = GlueSprayingApplication(cameraService, settingsService, workpieceService,
                                                      robotService)  # Initialize ActionManager with a placeholder callback
    # INIT REQUEST HANDLER
    if API_VERSION == 1:

        from src.communication_layer.api_gateway.handlers.request_handler import RequestHandler
        requestHandler = RequestHandler(glueSprayingApplication, settingsController, cameraSystemController,
                                        workpieceController, robotController)


    else:
        raise ValueError("Unsupported API_VERSION. Please set to 1 or 2.")

    logging.info("Request Handler initialized")
    """GUI RELATED INITIALIZATIONS"""

    # INIT DOMESTIC REQUEST SENDER
    domesticRequestSender = DomesticRequestSender(requestHandler)
    logging.info("Domestic Request Sender initialized")
    # INIT MAIN WINDOW

    if API_VERSION == 1:
        from src.frontend.pl_ui.controller.Controller import Controller
        controller = Controller(domesticRequestSender)


    from src.frontend.pl_ui.runPlUi import PlGui
    gui = PlGui(controller=controller)
    gui.start()


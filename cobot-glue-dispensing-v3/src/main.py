import logging
import os

from applications.glue_dispensing_application.controllers.glue_robot_controller import GlueRobotController
from applications.glue_dispensing_application.controllers.glue_workpiece_controller import GlueWorkpieceController
from applications.glue_dispensing_application.repositories.workpiece.GlueWorkPieceRepositorySingleton import \
    GlueWorkPieceRepositorySingleton
from applications.glue_dispensing_application.services.workpiece.glue_workpiece_service import GlueWorkpieceService
from communication_layer.api_gateway.dispatch.main_router import RequestHandler
from core.application.interfaces.application_settings_interface import ApplicationSettingsRegistry
from core.application.ApplicationContext import set_current_application, get_core_settings_path
from core.controllers.vision.camera_system_controller import CameraSystemController
from core.services.robot_service.impl.RobotStateManager import RobotStateManager
from core.services.robot_service.impl.base_robot_service import RobotService

from core.services.robot_service.impl.robot_monitor.fairino_monitor import FairinoRobotMonitor
from frontend.core.utils.localization import setup_localization

# Import SystemStateManager and related components
from core.system_state_management import SystemStateManager, SYSTEM_STATE_PRIORITY, ServiceState, SystemState, ServiceRegistry
from communication_layer.api.v1.topics import RobotTopics, VisionTopics


from modules.shared.MessageBroker import MessageBroker
from communication_layer.api_gateway.DomesticRequestSender import DomesticRequestSender
from core.application_factory import create_application_factory
from core.base_robot_application import ApplicationType

# IMPORT CONTROLLERS
from backend.system.settings.SettingsController import SettingsController

# IMPORT SERVICES
from backend.system.settings.SettingsService import SettingsService
from core.services.vision.VisionService import VisionServiceSingleton
from backend.system.utils import PathResolver

setup_localization()

if os.environ.get("WAYLAND_DISPLAY"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

logging.basicConfig(
    level=logging.CRITICAL,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s'
)

# sensorPublisher = SensorPublisher()

API_VERSION = 1
newGui = True
testRobot = False
if newGui:
    from frontend.core.runPlUi import PlGui
else:
    pass

if __name__ == "__main__":
    # Set the current application context (this determines which app's storage to use for core settings)
    set_current_application("glue_dispensing_application")

    # Global registry instance
    settings_registry = ApplicationSettingsRegistry()

    # Use application-specific core settings paths
    settings_file_paths = {
        "camera": get_core_settings_path("camera_settings.json") or PathResolver.get_settings_file_path("camera_settings.json"),
        "robot_config": get_core_settings_path("robot_config.json") or PathResolver.get_settings_file_path("robot_config.json"),
    }

    settings_service = SettingsService(settings_file_paths=settings_file_paths,settings_registry=settings_registry)

    # INIT ROBOT
    robot_config = settings_service.get_robot_config()
    if testRobot:
        from core.model.robot import TestRobotWrapper
        robot = TestRobotWrapper()
    else:
        from core.model.robot import fairino_robot
        robot = fairino_robot.FairinoRobot(robot_config.robot_ip)

    # INIT CAMERA SERVICE
    cameraService = VisionServiceSingleton().get_instance()

    # INIT GLUE WORKPIECE REPOSITORY AND SERVICE
    repository = GlueWorkPieceRepositorySingleton().get_instance()
    workpieceService = GlueWorkpieceService(repository=repository)

    # INIT ROBOT SERVICE
    robot_state_manager_cycle_time = 0.03  # 30ms cycle time
    robot_monitor = FairinoRobotMonitor(robot_config.robot_ip, cycle_time=0.03)
    robot_state_manager = RobotStateManager(robot_monitor=robot_monitor)
    robotService = RobotService(robot, settings_service, robot_state_manager)

    # INIT SYSTEM STATE MANAGER
    # Create and configure the system-wide state manager
    service_registry = ServiceRegistry()
    service_registry.register_service(robotService.service_id,RobotTopics.SERVICE_STATE,ServiceState.UNKNOWN)
    service_registry.register_service(cameraService.service_id,VisionTopics.SERVICE_STATE,ServiceState.UNKNOWN)
    system_state_manager = SystemStateManager(SYSTEM_STATE_PRIORITY, MessageBroker(),service_registry)

    # Subscribe to system state updates (optional - for logging/debugging)
    def on_system_state_change(state: SystemState):
        print(f"[Main] System state changed to: {state.value}")

    system_state_manager.subscribers.append(on_system_state_change)
    system_state_manager.start_state_publisher_thread()

    # INIT CONTROLLERS
    settingsController = SettingsController(settings_service,settings_registry)
    cameraSystemController = CameraSystemController(cameraService)
    workpieceController = GlueWorkpieceController(workpieceService)
    robotController = GlueRobotController(robotService)

    # INIT APPLICATION FACTORY
    application_factory = create_application_factory(
        vision_service=cameraService,
        settings_service=settings_service,
        workpiece_service=workpieceService,
        robot_service=robotService,
        settings_registry=settings_registry,
        service_registry= service_registry,
        auto_register=True
    )

    # GET CURRENT APPLICATION (defaulting to glue dispensing)
    # current_application = application_factory.switch_application(ApplicationType.TEST_APPLICATION)
    current_application = application_factory.switch_application(ApplicationType.GLUE_DISPENSING)

    # INIT REQUEST HANDLER
    if API_VERSION == 1:
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
        from frontend.core.ui_controller.UIController import UIController
        controller = UIController(domesticRequestSender)
    else:
        raise ValueError("Unsupported API_VERSION. Please set to 1")


    from frontend.core.runPlUi import PlGui
    gui = PlGui(controller=controller)
    gui.start()

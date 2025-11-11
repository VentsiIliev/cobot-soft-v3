import threading

from src.backend.GlueDispensingApplication.handlers.camera_calibration_handler import calibrate_camera
from src.backend.GlueDispensingApplication.handlers.clean_nozzle_handler import clean_nozzle
from src.backend.GlueDispensingApplication.handlers.create_workpiece_handler import  CreateWorkpieceHandler
from src.backend.GlueDispensingApplication.handlers.handle_start import start
from src.backend.GlueDispensingApplication.handlers.match_workpiece_handler import WorkpieceMatcher
from src.backend.GlueDispensingApplication.handlers.robot_calibration_handler import calibrate_robot
from src.backend.GlueDispensingApplication.handlers.temp_handlers.execute_from_gallery_handler import execute_from_gallery
from src.backend.GlueDispensingApplication.handlers.workpieces_to_spray_paths_handler import WorkpieceToSprayPathsGenerator
from src.backend.GlueDispensingApplication.glue_dispensing.glue_dispensing_operation import GlueDispensingOperation
from src.backend.GlueDispensingApplication.robot.robotService.enums.RobotServiceState import RobotServiceState

from src.backend.GlueDispensingApplication.settings.SettingsService import SettingsService

from modules.shared.MessageBroker import MessageBroker
from modules.shared.shared.workpiece.WorkpieceService import WorkpieceService
from src.backend.GlueDispensingApplication.robot.robotService.RobotService import RobotService
from src.backend.GlueDispensingApplication.vision.VisionService import _VisionService
from src.backend.GlueDispensingApplication.tools.GlueCell import GlueCellsManagerSingleton
from src.backend.GlueDispensingApplication.GlueSprayApplicationState import GlueSprayApplicationState
from src.backend.GlueDispensingApplication.SystemStatePublisherThread import SystemStatePublisherThread
from modules.VisionSystem.VisionSystem import VisionSystemState
from src.backend.GlueDispensingApplication.handlers import nesting_handler
from src.backend.GlueDispensingApplication.handlers import spraying_handler

"""
ENDPOINTS
- start
- measureHeight
- calibrateRobot
- calibrateCamera
- createWorkpiece

"""

class SubscriptionManager:
    def __init__(self, glue_application,broker):
        self.glue_application = glue_application
        self.broker = broker
        # store topic -> callback
        self.subscriptions = {}

    def subscribe_all(self):
        self.subscribe_mode_change()
        self.subscribe_vision_topics()
        self.subscribe_robot_service_topics()

    def subscribe_robot_service_topics(self):
        topic = self.glue_application.robotService.state_topic
        callback = self.glue_application.state_manager.onRobotServiceStateUpdate
        self.broker.subscribe(topic, callback)
        self.subscriptions[topic] = callback

    def subscribe_vision_topics(self):
        topic = self.glue_application.visionService.stateTopic
        callback = self.glue_application.state_manager.onVisonSystemStateUpdate
        self.broker.subscribe(topic, callback)
        self.subscriptions[topic] = callback

    def subscribe_mode_change(self):
        topic = "glue-spray-app/mode"
        callback = self.glue_application.changeMode
        self.broker.subscribe(topic, callback)
        self.subscriptions[topic] = callback

class MessagePublisher:
    def __init__(self,broker):
        self.broker = broker
        self.brightness_region_topic = "vision-system/brightness-region"
        self.robot_trajectory_image_topic = "robot/trajectory/updateImage"
        self.trajectory_start_topic = "robot/trajectory/start"
        self.state_topic = "system/state"

    def publish_brightness_region(self,region):
        self.broker.publish(self.brightness_region_topic, {"region": region})

    def publish_trajectory_image(self,image):
        self.broker.publish(self.robot_trajectory_image_topic, {"image": image})

    def publish_trajectory_start(self):
        self.broker.publish(self.trajectory_start_topic, "")

    def publish_state(self,state):
        self.broker.publish(self.state_topic, state)

class ApplicationStateManager:
    def __init__(self,initial_state,message_publisher):
        self.visonServiceState = None
        self.robotServiceState = None
        self.system_state_publisher = None
        self.state = initial_state
        self.message_publisher = message_publisher
        self._last_state = None

    def update_state(self,new_state):
        if self.state != new_state:
            self.state = new_state
            self.publish_state()

    def publish_state(self):
        try:
            if True:
                self.message_publisher.publish_state(self.state)
                self._last_state = self.state
        except Exception as e:
            import traceback
            traceback.print_exc()

    def start_state_publisher_thread(self):
        self.system_state_publisher = SystemStatePublisherThread(publish_state_func=self.publish_state, interval=0.1)
        self.system_state_publisher.start()

    def stop_state_publisher_thread(self):
        if self.system_state_publisher:
            self.system_state_publisher.stop()
            self.system_state_publisher.join()

    def onRobotServiceStateUpdate(self, state):
        self.robotServiceState = state

        # Robot not ready (initializing or error)
        if self.robotServiceState in [RobotServiceState.INITIALIZING, RobotServiceState.ERROR]:
            self.update_state(GlueSprayApplicationState.INITIALIZING)
        # Both robot and vision ready
        elif self.robotServiceState == RobotServiceState.IDLE and self.visonServiceState == VisionSystemState.RUNNING:
            # when both are ready start the camera feed updates
            self.update_state(GlueSprayApplicationState.IDLE)
        # Robot is actively working and vision is ready
        elif self.robotServiceState in [RobotServiceState.STARTING, RobotServiceState.MOVING_TO_FIRST_POINT,
                                        RobotServiceState.EXECUTING_PATH,
                                        RobotServiceState.TRANSITION_BETWEEN_PATHS] and self.visonServiceState == VisionSystemState.RUNNING:
            # when robot is working pause the camera feed updates
            self.update_state(GlueSprayApplicationState.STARTED)

    def onVisonSystemStateUpdate(self, state):
        self.visonServiceState = state
        if self.visonServiceState == VisionSystemState.RUNNING and self.robotServiceState == RobotServiceState.IDLE:
            self.update_state(GlueSprayApplicationState.IDLE)


Z_OFFSET_FOR_CALIBRATION_PATTERN = -4 # MM

class GlueSprayingApplication:
    """
    ActionManager is responsible for connecting actions to functions.
    The MainWindow will just emit signals, and ActionManager handles them.
    """

    glueCellsManager = GlueCellsManagerSingleton.get_instance()


    def __init__(self,
                 visionService: _VisionService,
                 settingsManager: SettingsService,
                 workpieceService: WorkpieceService,
                 robotService: RobotService):

        super().__init__()

        self.settingsManager = settingsManager
        self.visionService = visionService
        self.visonServiceState = None

        self.workpieceService = workpieceService

        self.robotService = robotService
        self.robotServiceState = None

        # Start the camera feed in a separate thread
        self.cameraThread = threading.Thread(target=self.visionService.run, daemon=True)
        self.cameraThread.start()

        self.preselected_workpiece = None

        self.broker=MessageBroker()
        self.message_publisher = MessagePublisher(broker=self.broker)
        self.state_manager = ApplicationStateManager(initial_state=GlueSprayApplicationState.INITIALIZING,
                                          message_publisher=self.message_publisher)
        self.state_manager.start_state_publisher_thread()
        self.subscription_manager = SubscriptionManager(glue_application=self,broker=self.broker)
        self.subscription_manager.subscribe_all()
        self.workpiece_to_spray_paths_generator = WorkpieceToSprayPathsGenerator(self)
        self.create_workpiece_handler = CreateWorkpieceHandler(self)
        self.workpiece_matcher = WorkpieceMatcher(self)

        self.glue_dispensing_operation = GlueDispensingOperation(self.robotService)

        self.NESTING = True
        self.CONTOUR_MATCHING = True

    # Action functions
    def start(self, debug=True):
        return start(self,self.CONTOUR_MATCHING,self.NESTING,debug)

    def start_nesting(self, debug=True):
        return nesting_handler.start_nesting(self,self.get_workpieces())

    def start_spraying(self,workpieces, debug=True):
        return spraying_handler.start_spraying(self,workpieces,debug)

    def move_to_nesting_capture_position(self):
        z_offset = self.settingsManager.get_camera_settings().get_capture_pos_offset()
        return self.robotService.move_to_nesting_capture_position(z_offset)

    def move_to_spray_capture_position(self):
        z_offset = self.settingsManager.get_camera_settings().get_capture_pos_offset()
        return self.robotService.move_to_spray_capture_position(z_offset)

    def clean_nozzle(self):
        return clean_nozzle(self.robotService)

    def stop(self):

        return self.glue_dispensing_operation.stop_operation()

    def pause(self):
        self.glue_dispensing_operation.pause_operation()

    def resume(self):
        self.glue_dispensing_operation.resume_operation()

    def calibrateRobot(self):
        return calibrate_robot(self)

    def calibrateCamera(self):
        return calibrate_camera(self)

    def create_workpiece_step_1(self):
        return self.create_workpiece_handler.create_workpiece_step_1()

    def create_workpiece_step_2(self):
        return self.create_workpiece_handler.create_workpiece_step_2()

    def get_workpieces(self):
        if self.preselected_workpiece is None:
            workpieces = self.workpieceService.loadAllWorkpieces()
            print(f" Loaded workpieces: {len(workpieces)}")
        else:
            workpieces = [self.preselected_workpiece]
            print(f" Using preselected workpiece: {self.preselected_workpiece.name}")
        return workpieces

    def get_dynamic_offsets_config(self):
        """
        Return the dynamic offset configuration including step offsets and direction map.
        """
        # Step offsets
        x_step_offset = self.robotService.robot_config.tcp_x_step_offset
        y_step_offset = self.robotService.robot_config.tcp_y_step_offset

        # Optionally: distances (if still used)
        x_distance = getattr(self.robotService.robot_config, 'tcp_x_step_distance', 50.0)
        y_distance = getattr(self.robotService.robot_config, 'tcp_y_step_distance', 50.0)

        # Direction map
        direction_map = self.robotService.robot_config.offset_direction_map
        # print(f"in get_dynamic_offsets_config: direction_map={direction_map}")
        return x_distance, x_step_offset, y_distance, y_step_offset, direction_map

    def get_transducer_offsets(self):
        # NOTE:
        # - The offsets defined here are measured in the robot's 0° TCP (Tool Center Point) orientation.

        x_offset = self.robotService.robot_config.tcp_x_offset # to the top left corner of the transducer
        y_offset = self.robotService.robot_config.tcp_y_offset # to the top left corner of the transducer

        # print(f"Transducer offsets: x_offset={x_offset}, y_offset={y_offset}")
        return [x_offset, y_offset]

    """ TEMP METHODS FOR TESTING WHILE IN DEVELOPMENT """

    def handleExecuteFromGallery(self, workpiece):
        return execute_from_gallery(self,workpiece,Z_OFFSET_FOR_CALIBRATION_PATTERN)

    def changeMode(self,message):
        print(f"Changing mode to: {message}")
        if message == "Spray Only":
            self.NESTING = False
        elif message == "Pick And Spray":
            self.NESTING = True
        else:
            raise ValueError(f"Unknown mode: {message}")


    def run_demo(self):

        if self.preselected_workpiece is None:
            print(f"No preselected workpiece set for demo")
            return False, "No preselected workpiece set for demo"

        workpiece = self.workpieceService.get_workpiece_by_id(self.preselected_workpiece)
        if workpiece is None:
            print(f"Demo workpiece with ID {self.preselected_workpiece} not found.")
            return True, f"Demo workpiece with ID {self.preselected_workpiece} not found."

        print("Demo workpiece found: ", workpiece)
        return True, "Demo workpiece found"

    """ TEMP METHODS FOR TESTING WHILE IN DEVELOPMENT """

    def handle_set_preselected_workpiece(self, wp_id):

        selected_workpiece = None
        all_workpieces = self.workpieceService.loadAllWorkpieces()
        for wp in all_workpieces:
            if str(wp.workpieceId) == str(wp_id):
                selected_workpiece = wp
                break

        if selected_workpiece is not None:
            self.preselected_workpiece = selected_workpiece
            print(f"Preselected workpiece set to ID: {wp_id}")
            print(f"Workpiece: {selected_workpiece}")
            print(f"Pickup point: {selected_workpiece.pickupPoint}")

            return True, f"Preselected workpiece set to ID: {wp_id}"
        else:
            print(f"Workpiece with ID: {wp_id} not found")
            return False, f"Workpiece with ID: {wp_id} not found"

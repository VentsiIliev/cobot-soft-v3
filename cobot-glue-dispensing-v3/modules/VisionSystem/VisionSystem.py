import threading

import cv2
import numpy as np
from enum import Enum

# Internal shared settings
from modules.shared.shared.settings.conreateSettings.CameraSettings import CameraSettings

# Vision System core modules
from modules.VisionSystem.brightness_manager import BrightnessManager
from modules.VisionSystem.camera_initialization import CameraInitializer
from modules.VisionSystem.data_loading import DataManager
from modules.VisionSystem.message_publisher import MessagePublisher
from modules.VisionSystem.settings_manager import SettingsManager
from modules.VisionSystem.state_manager import StateManager
from modules.VisionSystem.subscribtion_manager import SubscriptionManager
from modules.VisionSystem.QRcodeScanner import detect_and_decode_barcode

# Vision System handlers
from modules.VisionSystem.handlers.aruco_detection_handler import detect_aruco_markers
from modules.VisionSystem.handlers.camera_calibration_handler import (
    calibrate_camera,
    capture_calibration_image
)
from modules.VisionSystem.handlers.contour_detection_handler import handle_contour_detection

# External or domain-specific image processing
from libs.plvision.PLVision import ImageProcessing

# Conditional logging import
from src.backend.system.utils.custom_logging import (
    setup_logger, LoggerContext, log_debug_message, log_info_message
)

ENABLE_LOGGING = True  # Enable or disable logging
vision_system_logger = setup_logger("VisionSystem") if ENABLE_LOGGING else None



class VisionSystemState(Enum):
    INITIALIZING = "initializing"
    IDLE = "idle"
    CALIBRATING = "calibrating"
    RUNNING = "running"
    ERROR = "error"


class VisionSystem:
    def __init__(self, configFilePath=None, camera_settings=None):
        self.logger_context = LoggerContext(ENABLE_LOGGING, vision_system_logger)
        self.data_manager = DataManager(self, ENABLE_LOGGING, vision_system_logger)
        self.settings_manager = SettingsManager()

        self.message_publisher = MessagePublisher()
        self.state_manager = StateManager(initial_state=VisionSystemState.INITIALIZING,
                                          message_publisher=self.message_publisher,
                                          log_enabled=ENABLE_LOGGING,
                                          logger=vision_system_logger)

        self.state_manager.start_state_publisher_thread()


        self.threshold_by_area = "spray"
        self.calibrationImages = []

        # Initialize camera settings
        if camera_settings is not None:
            self.camera_settings = camera_settings
            log_debug_message(self.logger_context,message=f"Camera settings provided directly to VisionSystem.init")

        else:
            # Load from config file or use defaults

            if configFilePath is not None:
                config_data = self.settings_manager.loadSettings(configFilePath)
                self.camera_settings = CameraSettings(config_data)
                log_info_message(self.logger_context,message=f"Loading camera settings from {configFilePath}")

            else:
                self.camera_settings = CameraSettings()
                log_info_message(self.logger_context, message=f"No config file provided - using default camera settings")


        self.brightnessManager = BrightnessManager(self)
        self.subscription_manager = SubscriptionManager(self).subscribe_all()

        # Initialize camera with retry logic for intermittent issues
        camera_index = self.camera_settings.get_camera_index()
        camera_initializer = CameraInitializer(log_enabled=ENABLE_LOGGING,
                                               logger=vision_system_logger,
                                               width=self.camera_settings.get_camera_width(),
                                               height=self.camera_settings.get_camera_height())
        self.camera,camera_index = camera_initializer.initializeCameraWithRetry(camera_index)
        self.camera_settings.set_camera_index(camera_index)


        # Load camera calibration data
        self.isSystemCalibrated = False
        self.data_manager.loadPerspectiveMatrix()
        self.data_manager.loadCameraCalibrationData()
        self.data_manager.loadCameraToRobotMatrix()
        self.data_manager.loadWorkAreaPoints()

        # System is calibrated if we have camera data and camera-to-robot matrix
        # Perspective matrix is optional (only for single-image ArUco-based calibrations)
        if self.data_manager.cameraData is None or self.data_manager.cameraToRobotMatrix is None:
            self.isSystemCalibrated = False
        else:
            self.isSystemCalibrated = True
            if self.perspectiveMatrix is not None:
                log_info_message(self.logger_context,
                                 message=f"System calibrated with perspective correction")

            else:
                log_info_message(self.logger_context,
                                 message=f"System calibrated without perspective correction")


        # Extract camera matrix and distortion coefficients
        if self.isSystemCalibrated:
            self.cameraMatrix = self.data_manager.get_camera_matrix()
            self.cameraDist = self.data_manager.get_distortion_coefficients()

        # Initialize image variables
        self.image = None
        self.rawImage = None
        self.correctedImage = None
        self.rawMode = False

        # Initialize skip frames counter
        self.current_skip_frames = 0
        self.data_manager.print_focal_length()


    @property
    def cameraToRobotMatrix(self):
        return self.data_manager.cameraToRobotMatrix

    @property
    def perspectiveMatrix(self):
        return self.data_manager.perspectiveMatrix

    @property
    def stateTopic(self):
        return self.message_publisher.stateTopic

    def captureCalibrationImage(self):
        return capture_calibration_image(vision_system=self,
                                         log_enabled=ENABLE_LOGGING,
                                         logger=vision_system_logger)

    def run(self):
        self.image = self.camera.capture()

        # Handle frame skipping
        if self.current_skip_frames < self.camera_settings.get_skip_frames():
            self.current_skip_frames += 1
            return None, None, None

        if self.image is None:
            return None, None, None

        self.state_manager.update_state(VisionSystemState.RUNNING)
        self.rawImage = self.image.copy()

        # Handle brightness adjustment if enabled
        if self.camera_settings.get_brightness_auto():
            self.brightnessManager.adjust_brightness()

        if self.rawMode:
            return None, self.rawImage, None

        if self.camera_settings.get_contour_detection():
            return handle_contour_detection(self)

        self.correctedImage = self.correctImage(self.image)

        return None, self.correctedImage, None

    def correctImage(self, imageParam):
        """
        Undistorts and applies perspective correction to the given image.
        """
        # First, undistort the image using camera calibration parameters
        imageParam = ImageProcessing.undistortImage(
            imageParam,
            self.cameraMatrix,
            self.cameraDist,
            self.camera_settings.get_camera_width(),
            self.camera_settings.get_camera_height(),
            crop=False
        )

        # Apply perspective transformation if available (only for single-image calibrations with ArUco markers)
        if self.perspectiveMatrix is not None:
            imageParam = cv2.warpPerspective(
                imageParam,
                self.perspectiveMatrix,
                (self.camera_settings.get_camera_width(), self.camera_settings.get_camera_height())
            )

        return imageParam

    def on_threshold_update(self,message):
        # message format {"region": "pickup"})
        area = message.get("region","")
        self.threshold_by_area = area

    def get_thresh_by_area(self,area):
        if area == "pickup":
            return self.camera_settings.get_threshold_pickup_area()
        elif area == "spray":
            return  self.camera_settings.get_threshold()
        else:
            raise ValueError("Invalid region for threshold update")

    def calibrateCamera(self):
        return calibrate_camera(vision_system=self,
                         log_enabled=ENABLE_LOGGING,
                         logger=vision_system_logger)

    def captureImage(self):
        """
        Capture and return the corrected image.
        """
        return self.correctedImage

    def updateSettings(self, settings: dict):
        return self.settings_manager.updateSettings(vision_system=self,
                                                    settings=settings,
                                                    logging_enabled=ENABLE_LOGGING,
                                                    logger=vision_system_logger)


    def saveWorkAreaPoints(self, data):
        return self.data_manager.saveWorkAreaPoints(data)

    def getPickupAreaPoints(self):
        """Get pickup area points if available."""
        return getattr(self, 'pickupAreaPoints', None)

    def getSprayAreaPoints(self):
        """Get spray area points if available."""
        return getattr(self, 'sprayAreaPoints', None)


    def detectArucoMarkers(self, flip=False, image=None):
        return detect_aruco_markers(vision_system=self,
                                    log_enabled=ENABLE_LOGGING,
                                    logger=vision_system_logger,
                                    flip=flip,
                                    image=image)


    def detectQrCode(self):
        """
        Detect and decode QR codes in the raw image.
        """
        data = detect_and_decode_barcode(self.rawImage)
        return data

    def get_camera_settings(self):
        """
        Get the current camera settings object.
        """
        return self.camera_settings

    def testCalibration(self):
        # find the required aruco markers
        required_ids = set(range(9))
        try:
            arucoCorners, arucoIds, image = self.detectArucoMarkers(flip=False, image=self.correctedImage)
        except:
            return False, None, None

        if arucoIds is not None:
            found_ids = np.array(arucoIds).flatten().tolist()
            cv2.aruco.drawDetectedMarkers(image, arucoCorners, np.array(arucoIds, dtype=np.int32))

            # Create dictionary of found markers
            id_to_corner = {int(id_): corner for id_, corner in zip(arucoIds.flatten(), arucoCorners)}

            # Transform and print points for all found markers
            if len(found_ids) > 0:
                # Get available markers and their points
                available_markers = [i for i in sorted(required_ids) if i in id_to_corner.keys()]
                points = [id_to_corner[i][0] for i in available_markers]

                if points:
                    src_pts = np.array(points, dtype=np.float32)
                    src_pts = src_pts.reshape(-1, 1, 2)  # (N, 1, 2) format for perspectiveTransform

                    # Transform to robot coordinate space
                    transformed_pts = cv2.perspectiveTransform(src_pts, self.cameraToRobotMatrix)
                    transformed_pts = transformed_pts.reshape(-1, 2)

                    for i, (marker_id, pt) in enumerate(zip(available_markers, transformed_pts)):
                        print(f"Marker {marker_id}: X = {pt[0]:.2f}, Y = {pt[1]:.2f}")

            # Check if we have all required markers
            if len(found_ids) >= 9 and required_ids.issubset(id_to_corner.keys()):
                # Extract top-left corners in order of IDs 0 through 8
                ordered_camera_points = [id_to_corner[i][0] for i in sorted(required_ids)]
                return True, ordered_camera_points, image
            else:
                return False, None, image
        else:
            return False, None, None


    """PRIVATE METHODS SECTION"""

    @perspectiveMatrix.setter
    def perspectiveMatrix(self, value):
        self._perspectiveMatrix = value

    def start_system_thread(self):
        self.cameraThread = threading.Thread(target=self.run, daemon=True)
        self.cameraThread.start()

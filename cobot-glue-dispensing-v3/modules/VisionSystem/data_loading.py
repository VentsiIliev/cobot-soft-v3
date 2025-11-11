import json
import os

import numpy as np

from src.backend.system.utils.custom_logging import log_if_enabled, LoggingLevel

# Paths to camera calibration data
CAMERA_DATA_PATH = os.path.join(os.path.dirname(__file__), 'calibration', 'cameraCalibration', 'storage',
                                'calibration_result', 'camera_calibration.npz')

PERSPECTIVE_MATRIX_PATH = os.path.join(os.path.dirname(__file__), 'calibration', 'cameraCalibration', 'storage',
                                       'calibration_result', 'perspectiveTransform.npy')
CAMERA_TO_ROBOT_MATRIX_PATH = os.path.join(os.path.dirname(__file__), 'calibration', 'cameraCalibration', 'storage',
                                           'calibration_result', 'cameraToRobotMatrix_robot_tcp.npy')

WORK_AREA_POINTS_PATH = os.path.join(os.path.dirname(__file__), 'calibration', 'cameraCalibration', 'storage',
                                        'calibration_result', 'workAreaPoints.npy')

# Separate paths for pickup and spray areas
PICKUP_AREA_POINTS_PATH = os.path.join(os.path.dirname(__file__), 'calibration', 'cameraCalibration', 'storage',
                                       'calibration_result', 'pickupAreaPoints.npy')
SPRAY_AREA_POINTS_PATH = os.path.join(os.path.dirname(__file__), 'calibration', 'cameraCalibration', 'storage',
                                      'calibration_result', 'sprayAreaPoints.npy')



class DataManager:
    def __init__(self,vision_system,logging_enabled,logger):
        self.vision_system = vision_system
        self.ENABLE_LOGGING = logging_enabled
        self.logger = logger
        self.workAreaPoints = None
        self.work_area_polygon = None
        self.pickupAreaPoints = None
        self.sprayAreaPoints = None
        self.cameraToRobotMatrix = None
        self.cameraData = None
        self.perspectiveMatrix = None
        self.isSystemCalibrated = False


    def loadWorkAreaPoints(self):
        try:
            self.workAreaPoints = np.load(WORK_AREA_POINTS_PATH)
            self.work_area_polygon = np.array(self.workAreaPoints, dtype=np.int32).reshape((-1, 1, 2))
            self.isSystemCalibrated = True
        except FileNotFoundError:
            self.workAreaPoints = None
            self.isSystemCalibrated = False
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.ERROR,
                           message=f"Work area points file not found at {WORK_AREA_POINTS_PATH}",
                           broadcast_to_ui=False)

        # Load pickup area points
        try:
            self.pickupAreaPoints = np.load(PICKUP_AREA_POINTS_PATH)
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.INFO,
                           message="Pickup area points loaded successfully",
                           broadcast_to_ui=False)
        except FileNotFoundError:
            self.pickupAreaPoints = None
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.ERROR,
                           message="Pickup area points file not found - will be created when first saved",
                           broadcast_to_ui=False)
        # Load spray area points
        try:
            self.sprayAreaPoints = np.load(SPRAY_AREA_POINTS_PATH)
        except FileNotFoundError:
            self.sprayAreaPoints = None
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.ERROR,
                           message="Spray area points file not found - will be created when first saved",
                           broadcast_to_ui=False)


    def loadCameraToRobotMatrix(self):
        try:
            self.cameraToRobotMatrix = np.load(CAMERA_TO_ROBOT_MATRIX_PATH)
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.INFO,
                           message=f"Camera to Robot matrix loaded from: {CAMERA_TO_ROBOT_MATRIX_PATH}",
                           broadcast_to_ui=False)
        except FileNotFoundError:
            self.cameraToRobotMatrix = None
            self.isSystemCalibrated = True
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.ERROR,
                           message=f"File not found: {CAMERA_TO_ROBOT_MATRIX_PATH}",
                           broadcast_to_ui=False)
            raise ValueError()


    def loadCameraCalibrationData(self):
        try:
            self.cameraData = np.load(CAMERA_DATA_PATH)
            self.isSystemCalibrated = True
        except FileNotFoundError:
            self.cameraData = None
            self.isSystemCalibrated = False
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.ERROR,
                           message=f"Camera calibration data file not found at {CAMERA_DATA_PATH}",
                           broadcast_to_ui=False)


    def loadPerspectiveMatrix(self):
        try:
            self.perspectiveMatrix = np.load(PERSPECTIVE_MATRIX_PATH)
            print(f"✅ Perspective matrix loaded from: {PERSPECTIVE_MATRIX_PATH}")
        except FileNotFoundError:
            self.perspectiveMatrix = None
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.INFO,
                           message=f"No perspective matrix found at: {PERSPECTIVE_MATRIX_PATH}",
                           broadcast_to_ui=False)




    def saveWorkAreaPoints(self, data):
        """
        Saves the work area points captured by the camera service.
        Supports both legacy format (list of points) and new format (dict with area_type and corners).
        """

        print(f"In  VisionSystem.saveWorkAreaPoints with data: {data}")

        if data is None or len(data) == 0:
            return False, "No data provided to save"

        try:
            # Handle new format with area type
            if isinstance(data, dict) and 'area_type' in data and 'corners' in data:
                area_type = data['area_type']
                points = data['corners']

                if area_type not in ['pickup', 'spray']:
                    return False, f"Invalid area_type: {area_type}. Must be 'pickup' or 'spray'"

                if points is None or len(points) == 0:
                    return False, f"No points provided for {area_type} area"

                points_array = np.array(points, dtype=np.float32)

                # Save to area-specific file
                if area_type == 'pickup':
                    np.save(PICKUP_AREA_POINTS_PATH, points_array)
                    self.pickupAreaPoints = points_array
                    message = f"Pickup area points saved successfully"
                    log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                                   level=LoggingLevel.INFO,
                                   message=f"Saved pickup area points to {PICKUP_AREA_POINTS_PATH}",
                                   broadcast_to_ui=False)
                else:  # spray
                    np.save(SPRAY_AREA_POINTS_PATH, points_array)
                    log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                                   level=LoggingLevel.INFO,
                                   message=f"Saved spray area points to {PICKUP_AREA_POINTS_PATH}",
                                   broadcast_to_ui=False)
                    self.sprayAreaPoints = points_array
                    message = f"Spray area points saved successfully"

                # Also save to legacy path for backward compatibility if this is the first area saved
                if not hasattr(self, 'workAreaPoints') or self.workAreaPoints is None:
                    np.save(WORK_AREA_POINTS_PATH, points_array)
                    self.workAreaPoints = points_array
                    self.work_area_polygon = np.array(self.workAreaPoints, dtype=np.int32).reshape((-1, 1, 2))
                    log_if_enabled(enabled=self.ENABLE_LOGGING,
                                    logger=self.logger,
                                   level=LoggingLevel.INFO,
                                   message=f"Also saved to legacy work area points at {WORK_AREA_POINTS_PATH}",
                                   broadcast_to_ui=False)

                return True, message

            # Handle legacy format (list of points)
            else:
                points = data
                points_array = np.array(points, dtype=np.float32)
                np.save(WORK_AREA_POINTS_PATH, points_array)
                self.workAreaPoints = points_array
                self.work_area_polygon = np.array(self.workAreaPoints, dtype=np.int32).reshape((-1, 1, 2))
                log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                               level=LoggingLevel.INFO,
                               message=f"Work area points saved successfully (legacy format)",
                               broadcast_to_ui=False)
                return True, "Work area points saved successfully (legacy format)"

        except Exception as e:
            log_if_enabled(enabled=self.ENABLE_LOGGING,
                           logger=self.logger,
                           level=LoggingLevel.INFO,
                           message=f"Error saving work area points: {str(e)}",
                           broadcast_to_ui=False)
            return False, f"Error saving work area points: {str(e)}"

    def get_camera_matrix(self):
        return self.cameraData['mtx'] if self.cameraData is not None else None

    def print_focal_length(self, sensor_width_mm=3.6, image_width_px=1280):
        mtx = self.get_camera_matrix()
        if mtx is None:
            print("No camera matrix found.")
            return

        fx = mtx[0, 0]
        fy = mtx[1, 1]
        cx = mtx[0, 2]
        cy = mtx[1, 2]

        print("Camera Matrix (K):\n", mtx)
        print(f"Focal lengths (pixels): fx = {fx:.2f}, fy = {fy:.2f}")
        print(f"Principal point: cx = {cx:.2f}, cy = {cy:.2f}")

        # Optional: convert to mm
        if sensor_width_mm is not None and image_width_px is not None:
            f_mm = fx * (sensor_width_mm / image_width_px)
            print(f"Approx focal length: {f_mm:.2f} mm")

    def get_distortion_coefficients(self):
        return self.cameraData['dist'] if self.cameraData is not None else None
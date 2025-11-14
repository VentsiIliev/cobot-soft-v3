import platform
import time

import cv2

from backend.system.utils.custom_logging import log_if_enabled, LoggingLevel
from libs.plvision.PLVision.Camera import Camera

class CameraInitializer:
    def __init__(self,log_enabled,logger,width,height):
        self.log_enabled = log_enabled
        self.logger = logger
        self.width = width
        self.height = height

    def initializeCameraWithRetry(self, camera_index, max_retries=10, retry_delay=1.0):
        """
        Initialize camera with retry logic for intermittent availability issues.
        """
        for attempt in range(max_retries):
            try:
                log_if_enabled(enabled=self.log_enabled,
                               logger=self.logger,
                               level=LoggingLevel.INFO,
                               message=f"Attempting to initialize camera at index {camera_index} (attempt {attempt + 1}/{max_retries})",
                               broadcast_to_ui=False)
    
                # Add small delay to let USB settle (except first attempt)
                if attempt > 0:
                    time.sleep(retry_delay)
    
                # Create camera instance
                test_camera = Camera(
                    camera_index,
                    self.width,
                    self.height
                )
    
                # Test if camera opens
                if test_camera.cap.isOpened():
                    # Test if we can actually capture a frame
                    ret, frame = test_camera.cap.read()
                    if ret and frame is not None:
                        log_if_enabled(enabled=self.log_enabled,
                                       logger=self.logger,
                                       level=LoggingLevel.INFO,
                                       message=f"Camera successfully initialized at index {camera_index} on attempt {attempt + 1}",
                                       broadcast_to_ui=False)
                        return test_camera,camera_index
                    else:
                        log_if_enabled(enabled=self.log_enabled,
                                       logger=self.logger,
                                       level=LoggingLevel.INFO,
                                       message=f"Camera {camera_index} opened but cannot capture frames",
                                       broadcast_to_ui=False)
    
                        test_camera.cap.release()
                else:
                    log_if_enabled(enabled=self.log_enabled,
                                   logger=self.logger,
                                   level=LoggingLevel.INFO,
                                   message=f"Camera {camera_index} failed to open on attempt {attempt + 1}",
                                   broadcast_to_ui=False)
    
            except Exception as e:
                log_if_enabled(enabled=self.log_enabled,
                               logger=self.logger,
                               level=LoggingLevel.INFO,
                               message=f"Error on attempt {attempt + 1}: {e}",
                               broadcast_to_ui=False)
    
        # If all retries failed, try to find alternative camera
        log_if_enabled(enabled=self.log_enabled,
                       logger=self.logger,
                       level=LoggingLevel.INFO,
                       message=f"Camera at index {camera_index} failed after {max_retries} attempts",
                       broadcast_to_ui=False)
        log_if_enabled(enabled=self.log_enabled,
                       logger=self.logger,
                       level=LoggingLevel.INFO,
                       message="Searching for alternative cameras...",
                       broadcast_to_ui=False)
        return self._findAndInitializeCamera()
    
    
    def _findAndInitializeCamera(self):
        """
        Find and initialize the first available camera.
        """
        log_if_enabled(enabled=self.log_enabled,
                       logger=self.logger,
                       level=LoggingLevel.INFO,
                       message="Searching for available cameras...",
                       broadcast_to_ui=False)
        # Try common camera indices first
        for cam_id in range(0, 10):
            try:
                log_if_enabled(enabled=self.log_enabled,
                               logger=self.logger,
                               level=LoggingLevel.INFO,
                               message=f"Testing camera index {cam_id}...",
                               broadcast_to_ui=False)
                test_camera = Camera(
                    cam_id,
                    self.width,
                    self.height
                )
    
                if test_camera.cap.isOpened():
                    # Test if we can actually capture a frame
                    ret, frame = test_camera.cap.read()
                    if ret and frame is not None:
                        log_if_enabled(enabled=self.log_enabled,
                                       logger=self.logger,
                                       level=LoggingLevel.INFO,
                                       message=f"Found working camera at index {cam_id}",
                                       broadcast_to_ui=False)

                        return test_camera,cam_id
                    else:
                        test_camera.cap.release()
                        log_if_enabled(enabled=self.log_enabled,
                                       logger=self.logger,
                                       level=LoggingLevel.INFO,
                                       message=f"Camera {cam_id} opened but cannot capture frames",
                                       broadcast_to_ui=False)
                else:
                    log_if_enabled(enabled=self.log_enabled,
                                   logger=self.logger,
                                   level=LoggingLevel.INFO,
                                   message=f"Camera {cam_id} failed to open",
                                   broadcast_to_ui=False)
    
            except Exception as e:
                log_if_enabled(enabled=self.log_enabled,
                               logger=self.logger,
                               level=LoggingLevel.INFO,
                               message=f"Error testing camera {cam_id}: {e}",
                               broadcast_to_ui=False)
    
        # If no camera found in basic search, try Linux-specific detection
        if platform.system().lower() == "linux":
            try:
                available_cameras = self.find_first_available_camera()
                for cam_id in available_cameras:
                    try:
                        test_camera = Camera(
                            cam_id,
                            self.width,
                            self.height
                        )
                        if test_camera.cap.isOpened():
                            log_if_enabled(enabled=self.log_enabled,
                                           logger=self.logger,
                                           level=LoggingLevel.INFO,
                                           message=f"Found working camera at index {cam_id} (via Linux detection)",
                                           broadcast_to_ui=False)
                            return test_camera,cam_id
                    except Exception as e:
                        log_if_enabled(enabled=self.log_enabled,
                                       logger=self.logger,
                                       level=LoggingLevel.INFO,
                                       message=f"Error with camera {cam_id}: {e}",
                                       broadcast_to_ui=False)
            except Exception as e:
                log_if_enabled(enabled=self.log_enabled,
                               logger=self.logger,
                               level=LoggingLevel.INFO,
                               message=f"Linux camera detection failed: {e}",
                               broadcast_to_ui=False)
    
        # Create a dummy camera as fallback
        log_if_enabled(enabled=self.log_enabled,
                       logger=self.logger,
                       level=LoggingLevel.INFO,
                       message="No working cameras found - creating dummy camera",
                       broadcast_to_ui=False)
        return Camera(0, self.width, self.height)
    
    
    def find_first_available_camera(self, max_devices=10):
        """
        Find the first available camera on Linux systems.
        """
        from modules.shared.utils import linuxUtils
        import re
    
        cams = linuxUtils.list_video_devices_v4l2()
        candidate_indices = []
    
        for name, paths in cams.items():
            if "integrated" in name.lower():
                continue  # Skip internal webcams
    
            for path in paths:
                if "/dev/video" in path:
                    match = re.search(r"/dev/video(\d+)", path)
                    if match:
                        candidate_indices.append(int(match.group(1)))
    
        available_cameras = []
        # Test each candidate index to see if it's available
        for cam_id in candidate_indices:
            log_if_enabled(enabled=self.log_enabled,
                           logger=self.logger,
                           level=LoggingLevel.INFO,
                           message=f"   Checking camera id: {cam_id}",
                           broadcast_to_ui=False)
            cap = cv2.VideoCapture(cam_id)
            if cap.isOpened():
                cap.release()
                available_cameras.append(cam_id)
    
        return available_cameras
import queue
import time
from src.backend.GlueDispensingApplication import CompareContours
import cv2
import threading
import numpy as np
from modules.shared.shared.workpiece.WorkpieceService import WorkpieceService
# from GlueDispensingApplication.robot.RobotCalibrationService import CAMERA_TO_ROBOT_MATRIX_PATH
from src.backend.GlueDispensingApplication.utils import utils
from modules.VisionSystem.VisionSystem import VisionSystem
import os
from modules.shared.MessageBroker import MessageBroker
from libs.plvision.PLVision.arucoModule import *

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'storage', 'settings', 'camera_settings.json')






# PICKUP_AREA_CAMERA_TO_ROBOT_MATRIX_PATH = '/home/ilv/Cobot-Glue-Nozzle/VisionSystem/calibration/cameraCalibration/storage/calibration_result/pickupCamToRobotMatrix.npy'
PICKUP_AREA_CAMERA_TO_ROBOT_MATRIX_PATH = os.path.join(os.path.dirname(__file__),'..', '..', 'VisionSystem', 'calibration', 'cameraCalibration', 'storage', 'calibration_result', 'pickupCamToRobotMatrix.npy')

class _VisionService(VisionSystem):
    """
        Vision service class for processing camera frames and detecting contours, workpieces, and ArUco markers.

    This class extends the VisionSystem and handles real-time frame processing, contour detection,
    filtering workpieces within a defined area, and interfacing with robot calibration and workpieces services.

    Attributes:
        MAX_QUEUE_SIZE (int): Maximum number of frames to store in the queue.
        frameQueue (queue.Queue): A queue to store the most recent frames for processing.
        contours (list): Detected contours in the current frame.
        workAreaCorners (dict): Coordinates defining the workpieces pickup area.
        filteredContours (list): Contours that are filtered based on the work area.
        drawOverlay (bool): Flag to determine whether to draw overlays on the frame.
        pickupCamToRobotMatrix (numpy.ndarray): Matrix to transform camera points to robot coordinates.

    """
    def __init__(self):
        """
            Initializes the VisionService with camera settings and prepares the frame queue and other attributes.

            This constructor initializes the camera service, the frame queue to store the latest frames,
            and loads the camera-to-robot matrix for transformation.

            Args:
                None
            """
        super().__init__(configFilePath=CONFIG_FILE_PATH)

        self.MAX_QUEUE_SIZE = 100  # Maximum number of frames to store in the queue
        self.frameQueue = queue.Queue(maxsize=self.MAX_QUEUE_SIZE)
        self.superRun = super().run
        self.latest_frame = None
        self.frame_lock = threading.Lock()

        self.contours = None
        self.workAreaCorners = None
        self.filteredContours = None
        self.pickupCamToRobotMatrix = self._loadPickupCamToRobotMatrix()
        broker = MessageBroker()
        broker.subscribe("vision/transformToCamera",self.transformRobotPointToCamera)

    def _loadPickupCamToRobotMatrix(self):
        """
             Loads the camera-to-robot transformation matrix from a predefined file.

             The matrix is required for transforming the camera coordinates to the robot's coordinate system.

             Returns:
                 numpy.ndarray or None: The transformation matrix if successful, otherwise None.
             """
        if not os.path.exists(PICKUP_AREA_CAMERA_TO_ROBOT_MATRIX_PATH):
            print(f"Error: Matrix file not found at {PICKUP_AREA_CAMERA_TO_ROBOT_MATRIX_PATH}")
            self.pickupCamToRobotMatrix = None
            # return None

        try:
            self.pickupCamToRobotMatrix = np.load(PICKUP_AREA_CAMERA_TO_ROBOT_MATRIX_PATH)
            # print("Matrix loaded:", self.pickupCamToRobotMatrix)
        except Exception as e:
            print(f"Error loading matrix: {e}")
            self.pickupCamToRobotMatrix = None

        return self.pickupCamToRobotMatrix

    def run(self):
        """
              Main loop that continuously processes frames from the camera.

              It detects contours, applies overlays if necessary, and processes workpieces within the defined work area.

              This method keeps running indefinitely, so it should be called in a separate thread or process.

              Returns:
                  None
              """
        print("Starting VisionService run loop...")
        broker = MessageBroker()
        last_publish_time = 0
        publish_interval = 1.0  # seconds)
        # if self.workAreaCorners is None:
        #     # print("No workAreaCorners found. Set them first.")
        #     pass

        while True:
            self.contours, frame, _ = super().run()
            # self.contours, frame, _  = self.captureFrameThreadSafe()
            state = "waiting_image" if frame is None else "ok"
            now = time.time()
            if now - last_publish_time >= publish_interval:
                broker.publish("vision/state", {"state": state})
                last_publish_time = now
            if frame is None:
                continue
            # if self.contours is not None:

                # if self.workAreaCorners is None:
                #     self.setWorkpiecePickupArea()

                # self.applyWorkAreaFilter(frame)

            # if self.frameQueue.qsize() >= self.MAX_QUEUE_SIZE:
            #     self.frameQueue.get()  # Remove the oldest frame
            # self.frameQueue.put(frame)

            # update latest_frame safely
            with self.frame_lock:
                self.latest_frame = frame



    def getLatestFrame(self):
        """
            Retrieves the latest frame from the queue.

            Returns:
                numpy.ndarray or None: The most recent frame, or None if the queue is empty.
            """
        # if not hasattr(self, "_getLatestFrame_call_count"):
        #     self._getLatestFrame_call_count = 0
        #     self._getLatestFrame_last_time = time.time()
        #
        # self._getLatestFrame_call_count += 1
        # now = time.time()
        # elapsed = now - self._getLatestFrame_last_time
        # if elapsed >= 1.0:  # print every second
        #     print(
        #         f"[DEBUG] getLatestFrame called {self._getLatestFrame_call_count} times in the last {elapsed:.2f} seconds")
        #     self._getLatestFrame_call_count = 0
        #     self._getLatestFrame_last_time = now

        with self.frame_lock:
            if self.latest_frame is None:
                return None
            # convert to RGB before returning
            return cv2.cvtColor(self.latest_frame, cv2.COLOR_BGR2RGB)

        return frame

    def getContours(self):
        """
               Returns the detected contours from the most recent frame.

               Returns:
                   list: A list of contours detected in the most recent frame.
               """
        return self.contours

    def updateCameraSettings(self, settings: dict):
        """
             Updates the camera settings with the provided dictionary of settings.

             Args:
                 settings (dict): The new camera settings to apply.

             Returns:
                 bool: True if the settings were updated successfully, otherwise False.
             """
        return self.updateSettings(settings)

    def getFrameWidth(self):
        """
              Returns the width of the captured frame.

              Returns:
                  int: The width of the frame.
              """
        return self.frameHeight

    def getFrameHeight(self):
        """
               Returns the height of the captured frame.

               Returns:
                   int: The height of the frame.
               """
        return self.frameWidth

    def getCameraToRobotMatrix(self):
        """
              Returns the camera-to-robot transformation matrix.

              Returns:
                  numpy.ndarray or None: The matrix if successfully loaded, otherwise None.
              """
        return self.cameraToRobotMatrix

    def calibrateCamera(self):
        """
               Initiates the camera calibration process.

               Returns:
                   bool: Calibration result indicating success or failure.
               """
        result =  super().calibrateCamera()
        print("Calibration result: ", result)
        return result

    def setRawMode(self, rawMode: bool):
        """
                Sets the camera's raw mode, enabling or disabling it.

                Args:
                    rawMode (bool): True to enable raw mode, False to disable.
                """
        print("Setting raw mode to: ", rawMode)
        self.rawMode = rawMode

    def detectArucoMarkers(self,flip=False,image= None):
        """
              Detects ArUco markers in the provided image.

              Args:
                  flip (bool): If True, the image will be flipped before processing.
                  image (numpy.ndarray): The image in which to detect ArUco markers.

              Returns:
                  tuple: The detected ArUco marker corners, ids, and the processed image.
              """
        return super().detectArucoMarkers(flip,image)

    def captureImage(self):
        """
              Captures an image from the camera.

              Returns:
                  numpy.ndarray: The captured image.
              """
        image = super().captureImage()
        return image

    def setWorkpiecePickupArea(self):
        """
              Identifies the workpieces pickup area by detecting specific ArUco markers.

              The method will attempt to detect enough ArUco markers (4 specific ones) and define the pickup
              area based on their locations.

              Returns:
                  tuple: A boolean indicating success or failure, a message, and the captured image.
              """
        maxAttempts = 30
        while maxAttempts > 0:
            # print("Aruco Attempt: ", maxAttempts)
            arucoCorners, arucoIds, image = self.detectArucoMarkers()
            # print("ids: ", arucoIds)
            if arucoIds is not None and len(arucoIds) >= 9:
                break  # Stop retrying if enough markers are detected
            maxAttempts -= 1

        if arucoIds is None or len(arucoIds) == 0:
            # print("No ArUco markers found")
            message = "No ArUco markers found"
            return False, message, image

        # Dictionary to store corners for each ID
        id_to_corners = {}
        for i, aruco_id in enumerate(arucoIds.flatten()):
            id_to_corners[aruco_id] = arucoCorners[i][0]  # Store all 4 corners of this ID

        required_ids = {26, 27, 28, 29}
        if not required_ids.issubset(id_to_corners.keys()):
            message = "Missing ArUco markers"
            # print(message)
            return False, message, image

        # Assign corners based on IDs
        top_left = id_to_corners[26][0]
        top_right = id_to_corners[27][0]
        bottom_right = id_to_corners[28][0]
        bottom_left = id_to_corners[29][0]

        # Save corners to workAreaCorners.txt
        self.workAreaCorners = {
            "top_left": top_left.tolist(),
            "top_right": top_right.tolist(),
            "bottom_right": bottom_right.tolist(),
            "bottom_left": bottom_left.tolist(),
        }
        with open("workAreaCorners.txt", "w") as file:
            file.write(str(self.workAreaCorners))

        # print("Workpiece pickup area corners saved successfully.")
        return True, "Corners saved successfully", image

    def applyWorkAreaFilter(self,frame):
        """
            Filters the detected contours based on the defined work area.

            The work area is defined by the coordinates stored in `workAreaCorners`. Only contours within
            this area are kept for further processing.

            Args:
                frame (numpy.ndarray): The current camera frame to apply the filter on.

            Returns:
                list: A list of filtered contours within the work area.
            """
        if self.workAreaCorners is None:

            return []

        if self.contours is None:
            return []

        # Get bounding rectangle from corners
        x_coords = [
            self.workAreaCorners["top_left"][0],
            self.workAreaCorners["top_right"][0],
            self.workAreaCorners["bottom_right"][0],
            self.workAreaCorners["bottom_left"][0],
        ]
        y_coords = [
            self.workAreaCorners["top_left"][1],
            self.workAreaCorners["top_right"][1],
            self.workAreaCorners["bottom_right"][1],
            self.workAreaCorners["bottom_left"][1],
        ]

        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        self.filteredContours = []
        for cnt in self.contours:
            # cv2.drawContours(frame, [cnt], -1, (255, 0, 255), 2)
            cnt = cnt.reshape(-1, 2)  # Flatten to (N,2)

            # Check if all points of contour are inside the bounding box
            if np.all((cnt[:, 0] >= min_x) & (cnt[:, 0] <= max_x) &
                      (cnt[:, 1] >= min_y) & (cnt[:, 1] <= max_y)):
                self.filteredContours.append(cnt.reshape(-1, 1, 2).astype(np.float32))  # Reshape back to contour format
                # Draw the filtered contour with purple color
                cv2.drawContours(frame, [cnt], -1, (255, 0, 255), 1)
            # Draw the bounding box area for debugging (optional)
        # cv2.rectangle(frame, (int(min_x), int(min_y)), (int(max_x), int(max_y)), (0, 255, 255), 2)

        return self.filteredContours

    def detectQrCode(self):
        return super().detectQrCode()

    def stopContourDetection(self):
        self.contourDetection = False

    def startContourDetection(self):
        self.contourDetection = True


    def captureFrameThreadSafe(self):
        """
        Thread-safe method to capture a single frame using the camera lock.
        This prevents conflicts when multiple threads try to access camera frames.
        
        Returns:
            tuple: (contours, frame, filtered_contours) - same as superRun() but thread-safe
        """
        with self.frame_lock:
            print(f"Calling superRun() in thread {threading.current_thread().name}")
            return self.superRun()

    def transformRobotPointToCamera(self,message):
        # message format {"x": x, "y": y}
        x = message.get("x")
        y = message.get("y")
        point = (x, y)
        return utils.transformSinglePointToCamera(point,self.cameraToRobotMatrix)

class VisionServiceSingleton:
    """
        A Singleton class to manage a single instance of VisionService.

        This class ensures that only one instance of the VisionService is created and accessed globally.
        The `get_instance` method returns the same instance every time it is called.

        Methods:
            get_instance():
                Returns the single instance of the VisionService.
        """
    _visionServiceInstance = None  # Static variable to hold the instance

    @staticmethod
    def get_instance()-> _VisionService:
        """
               Returns the singleton instance of the VisionService.

               If the instance has not been created yet, it initializes the _VisionService class.

               Returns:
                   VisionService: The singleton instance of the VisionService.
               """
        if VisionServiceSingleton._visionServiceInstance is None:
            VisionServiceSingleton._visionServiceInstance = _VisionService()
        return VisionServiceSingleton._visionServiceInstance

if __name__ == "__main__":
    # Example usage
    import cv2
    vision_service = VisionServiceSingleton.get_instance()
    print("After instantiation, vision_service is: ", vision_service)

    import threading

    threading.Thread(target=vision_service.run,
                     daemon=True).start()  # This will start the camera processing loop in a new thread

    # You can call other methods like getLatestFrame, processContours, etc. as needed
    while True:
        image = vision_service.getLatestFrame()
        if image is not None:
            cv2.imshow("Latest Frame", image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    # For example, to get the latest frame:


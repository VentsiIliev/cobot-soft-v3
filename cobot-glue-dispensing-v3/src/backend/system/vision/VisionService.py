import queue
import time
import numpy as np
import cv2
# from system.robot.RobotCalibrationService import CAMERA_TO_ROBOT_MATRIX_PATH
from backend.system.utils import utils
from modules.VisionSystem.VisionSystem import VisionSystem
import os
from modules.shared.MessageBroker import MessageBroker
import threading
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'storage', 'settings', 'camera_settings.json')





from modules.shared.v1.topics import VisionTopics
# PICKUP_AREA_CAMERA_TO_ROBOT_MATRIX_PATH = '/home/ilv/Cobot-Glue-Nozzle/VisionSystem/calibration/cameraCalibration/storage/calibration_result/pickupCamToRobotMatrix.npy'
PICKUP_AREA_CAMERA_TO_ROBOT_MATRIX_PATH = os.path.join(os.path.dirname(__file__),'..','..', '..', 'VisionSystem', 'calibration', 'cameraCalibration', 'storage', 'calibration_result', 'pickupCamToRobotMatrix.npy')

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
        broker.subscribe(VisionTopics.TRANSFORM_TO_CAMERA_POINT,self.transformRobotPointToCamera)

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

            with self.frame_lock:
                self.latest_frame = frame



    def getLatestFrame(self):
        """
            Retrieves the latest frame from the queue.

            Returns:
                numpy.ndarray or None: The most recent frame, or None if the queue is empty.
            """

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


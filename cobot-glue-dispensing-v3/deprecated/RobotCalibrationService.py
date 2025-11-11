# import numpy as np
# import cv2
#
# """
# RobotCalibrationService
# -----------------------
# This class handles calibration of a robot with respect to a camera system. It maps 2D camera image points
# to 2D robot coordinates by computing a transformation matrix (homography). The calibration results are saved
# to disk for reuse.
# """
#
# CAMERA_TO_ROBOT_MATRIX_PATH = "VisionSystem/calibration/cameraCalibration/storage/calibration_result/cameraToRobotMatrix.npy"
# ROBOT_POINTS_PATH = "VisionSystem/calibration/cameraCalibration/storage/calibration_result/robotPoints.txt"
# CAMERA_POINTS_PATH = "VisionSystem/calibration/cameraCalibration/storage/calibration_result/cameraPoints.txt"
#
#
# class RobotCalibrationService:
#     """
#        Service responsible for calibrating the robot based on manually collected robot and camera points.
#
#        Attributes:
#            cameraToRobotMatrix (np.ndarray): The computed transformation matrix.
#            robotPointIndex (int): Index for managing robot point entries.
#            message (str): Status message for the most recent operation.
#        """
#
#     def __init__(self):
#         """
#                 Initialize the calibration service. Loads existing robot points from file.
#
#                 Raises:
#                     FileNotFoundError: If the robot points file does not exist or is invalid.
#                 """
#         self.__cameraPoints = []
#         self.__robotPoints = []
#         self.cameraToRobotMatrix = None
#         self.robotPointIndex = 0
#         self.message = ""
#
#         try:
#             self.__robotPoints = np.loadtxt(ROBOT_POINTS_PATH).reshape(-1, 3).tolist()
#         except (FileNotFoundError, ValueError):
#             print("No valid robot points found")
#             raise FileNotFoundError("No valid robot points found")
#
#     def calibrate(self):
#         """
#                Perform calibration by computing a transformation matrix between camera and robot coordinates.
#
#                Returns:
#                    tuple: (success (bool), message (str))
#                """
#         print("Calibrating robot...")
#         if len(self.__robotPoints) < 3:
#             print(f"Error: Not enough robot points. {len(self.__robotPoints)}")
#             self.message = f"Error: Not enough robot points. {len(self.__robotPoints)}"
#             return False, self.message
#
#         if len(self.__cameraPoints) < 3:
#             print(f"Error: Not enough camera points. {len(self.__cameraPoints)}")
#             self.message = f"Error: Not enough camera points. {len(self.__cameraPoints)}"
#             return False, self.message
#
#         self.__computeMatrix()
#         print("Points saved: ", len(self.__robotPoints))
#
#         self.__saveMatrix()
#
#         np.savetxt(ROBOT_POINTS_PATH, np.array(self.__robotPoints), fmt="%.6f")
#         np.savetxt(CAMERA_POINTS_PATH, np.array(self.__cameraPoints), fmt="%.6f")
#
#         # Reset points after calibration
#         self.__cameraPoints = []
#         self.message = "Camera to robot transformation computed successfully"
#         return True, self.message
#
#     def __computeMatrix(self):
#         """
#               Internal method to compute the homography matrix between 2D camera points and 2D robot points.
#               """
#         print("Computing matrix...")
#
#         # Convert to NumPy arrays (float32)
#         camera_pts = np.array(self.__cameraPoints, dtype=np.float32)
#         robot_pts = np.array(self.__robotPoints, dtype=np.float32)
#
#         print("Camera points for calib: ", camera_pts)
#         print("Robot points for calib: ", robot_pts)
#
#         # Use only (x, y) coordinates for homography
#         robotCalibPoints = robot_pts[:, :2]
#
#         # Compute homography matrix (3x3)
#         self.cameraToRobotMatrix, _ = cv2.findHomography(camera_pts[:, :2], robotCalibPoints)
#
#     def __saveMatrix(self):
#         """
#               Internal method to save the computed transformation matrix to a .npy file.
#               """
#         print("Saving matrix...")
#         np.save(CAMERA_TO_ROBOT_MATRIX_PATH, self.cameraToRobotMatrix)
#
#     def setCameraPoints(self, points):
#         """
#              Set the camera points for calibration.
#
#              Args:
#                  points (list): List of (x, y) tuples or lists from the camera image.
#              """
#         print(f"Setting camera points... {points}")
#         self.__cameraPoints = points
#
#     def setRobotPoints(self, points):
#         """
#               Set the robot points for calibration.
#
#               Args:
#                   points (list): List of (x, y, z) coordinates from the robot system.
#               """
#         self.__robotPoints = points
#
#     def getCameraPoints(self):
#         """
#               Get the current camera points.
#
#               Returns:
#                   list: The list of camera (x, y) points.
#               """
#         return self.__cameraPoints
#
#     def getRobotPoints(self):
#         """
#               Get the current robot points.
#
#               Returns:
#                   list: The list of robot (x, y, z) points.
#               """
#         return self.__robotPoints
#
#     def saveRobotPoint(self, point):
#         """
#              Save a new robot point or update the existing point at the current index.
#
#              Args:
#                  point (list): A single (x, y, z) robot point.
#              """
#         """ Safely append or replace robot points while keeping the z-coordinate intact. """
#         if self.robotPointIndex < len(self.__robotPoints):
#             self.__robotPoints[self.robotPointIndex] = point
#         else:
#             self.__robotPoints.append(point)  # Append if index is beyond current list size
#
#         self.robotPointIndex += 1
#
#     def getNextRobotPoint(self):
#         """
#             Get the next robot point to be used for calibration input.
#
#             Returns:
#                 list or None: The next robot point or None if index is out of range.
#             """
#         """ Ensure safe access to the next robot point """
#         if self.robotPointIndex < len(self.__robotPoints):
#             return self.__robotPoints[self.robotPointIndex]
#         return None  # Return None if out of bounds

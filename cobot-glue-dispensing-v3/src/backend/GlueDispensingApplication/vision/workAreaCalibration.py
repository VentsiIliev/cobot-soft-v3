import numpy as np
import cv2
import os
import time

PICKUP_AREA_CAMERA_TO_ROBOT_MATRIX_PATH = os.path.join(os.path.dirname(__file__), '..','..', 'VisionSystem', 'calibration', 'cameraCalibration', 'storage', 'calibration_result', 'pickupCamToRobotMatrix.npy')
TOP_LEFT_ID = 26
TOP_RIGHT_ID = 27
BOTTOM_RIGHT_ID = 28
BOTTOM_LEFT_ID = 29

def calibratePickupArea(visionService):
    """
       Calibrates the pickup area by detecting ArUco markers and calculating the homography matrix
       that transforms camera coordinates to robot coordinates.

       This function attempts to detect the required ArUco markers in the pickup area and associates
       their detected corners with predefined robot coordinates. It then calculates the transformation
       matrix (homography) that maps the camera points to the robot's coordinate system.

       The resulting homography matrix is saved to a file for future use in the robot's vision system.

       Args:
           visionService (VisionService): The instance of the VisionService class used to detect ArUco markers
                                           and interact with the camera system.

       Returns:
           tuple: A tuple containing:
               - bool: True if calibration is successful, False otherwise.
               - str: A message providing additional information (success or failure).
               - numpy.ndarray: The image used during the calibration process, which contains the detected ArUco markers.

       Steps:
           1. Attempt to detect ArUco markers up to 30 times.
           2. If enough markers are detected (at least 9), the calibration proceeds.
           3. Match the detected markers' corners with predefined robot coordinates.
           4. Calculate the homography matrix that transforms the camera points to robot points.
           5. Save the resulting transformation matrix to a predefined path.

       Notes:
           - The ArUco markers should be arranged in a way that their corners map correctly to the robot's workspace.
           - The robot coordinates are read from a file and should be available at the specified path.
       """
    time.sleep(0.5)
    maxAttempts = 30
    while maxAttempts > 0:
        print("Aruco Attempt: ", maxAttempts)
        arucoCorners, arucoIds, image = visionService.detectArucoMarkers()
        print("ids: ", arucoIds)
        if arucoIds is not None and len(arucoIds) >= 9:
            break  # Stop retrying if enough markers are detected
        maxAttempts -= 1

    if arucoIds is None or len(arucoIds) == 0:
        print("No ArUco markers found")
        message = "No ArUco markers found"
        return False, message, image

    # Dictionary to store corners for each ID
    id_to_corners = {}
    for i, aruco_id in enumerate(arucoIds.flatten()):
        id_to_corners[aruco_id] = arucoCorners[i][0]  # Store all 4 corners of this ID

    required_ids = {TOP_LEFT_ID, TOP_RIGHT_ID, BOTTOM_RIGHT_ID, BOTTOM_LEFT_ID}
    if not required_ids.issubset(id_to_corners.keys()):
        message = "Missing ArUco markers"
        print(message)
        return False, message, image

    # Assign corners based on IDs
    top_left = id_to_corners[TOP_LEFT_ID][0]
    top_right = id_to_corners[TOP_RIGHT_ID][0]
    bottom_right = id_to_corners[BOTTOM_RIGHT_ID][0]
    bottom_left = id_to_corners[BOTTOM_LEFT_ID][0]

    # Save corners to workAreaCorners.txt
    workAreaCorners = {
            "top_left": top_left.tolist(),
            "top_right": top_right.tolist(),
            "bottom_right": bottom_right.tolist(),
            "bottom_left": bottom_left.tolist(),
        }
    with open("workAreaCameraPoints.txt", "w") as file:
        file.write(str(workAreaCorners))

    cameraPoints = [top_left,top_right,bottom_right,bottom_left]

    path = 'GlueDispensingApplication/vision/pickupAreaRobotPoints'
    robotPoints = np.loadtxt(path).reshape(-1, 3).tolist()

    # Convert to NumPy arrays (float32)
    camera_pts = np.array(cameraPoints, dtype=np.float32)
    robot_pts = np.array(robotPoints, dtype=np.float32)

    # Use only (x, y) coordinates for homography
    robot_pts = robot_pts[:, :2]

    cameraToRobotMatrix, _ = cv2.findHomography(camera_pts[:, :2], robot_pts)

    pickupCamToRobotMatrixPath = PICKUP_AREA_CAMERA_TO_ROBOT_MATRIX_PATH
    # pickupCamToRobotMatrixPath = '/home/ilv/Cobot-Glue-Nozzle/VisionSystem/calibration/cameraCalibration/storage/calibration_result/pickupCamToRobotMatrix'
    np.save(pickupCamToRobotMatrixPath,cameraToRobotMatrix)
    print("Pick up matrix saved")






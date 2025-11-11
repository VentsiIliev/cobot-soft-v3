import numpy as np

# Load homography matrix from file
homography_path = '/home/plp/cobot-soft/Cobot-Glue-Nozzle/VisionSystem/calibration/cameraCalibration/storage/calibration_result/cameraToRobotMatrix.npy'
H = np.load(homography_path)

# Example test: transform a point from camera to robot coordinates
def _test_homography(H, point):
    # point: (x, y) in camera coordinates
    pt = np.array([point[0], point[1], 1.0])
    transformed = H @ pt
    transformed /= transformed[2]
    return transformed[:2]

if __name__ == '__main__':
    # Example camera point
    camera_point = (0, 0)
    robot_point = _test_homography(H, camera_point)
    print(f'Camera point {camera_point} maps to robot point {robot_point}')
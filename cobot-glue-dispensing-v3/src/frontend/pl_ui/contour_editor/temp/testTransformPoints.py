# from VisionSystem.VisionSystem import VisionSystem
# from system.utils import utils
# from system.robot.RobotWrapper import RobotWrapper
# import numpy as np
#
# robotIp = '192.168.58.2'
# robot = RobotWrapper(robotIp)
#
# filename = "robot_path.txt"
#
# with open(filename, 'r') as f:
#     lines = f.readlines()
# if not lines:
#     print("No data in path file.")
#     exit()
#
# x_vals = []
# y_vals = []
# points = []
# for line in lines:
#     try:
#         x_str, y_str = line.strip().split(',')
#         x = float(x_str)
#         y = float(y_str)
#         point = [x, y]  # Store as [x, y]
#         points.append(point)
#     except ValueError:
#         print(f"Skipping invalid line: {line.strip()}")
#
# visionSystem = VisionSystem()
# cameraToRobotMatrix = visionSystem.cameraToRobotMatrix
# print("Matrix: ", cameraToRobotMatrix)
#
# # Apply transformation without adding extra dimensions
# transformedPoints = utils.applyTransformation(cameraToRobotMatrix, points)
# transformedPoints = np.array(transformedPoints).reshape(-1, 1, 2).astype(np.int32)
#
#
# print("Original Points:", points)
# print("Transformed Points:", transformedPoints)
#
# # Print point[0] as [x, y]
# for point in transformedPoints:
#     x = point[0][0]
#     y = point[0][1]
#     print(f"x = {x} y = {y}")
#     robotPoint = [x,y,115,180,0,0]
#     robot.moveL(robotPoint,0,0,30,30,1)
#
# startPosition = [-4.36, 421.145, 757.939, 180, 0, 0]
# robot.moveCart(startPosition, 0, 0, vel=100, acc=30)
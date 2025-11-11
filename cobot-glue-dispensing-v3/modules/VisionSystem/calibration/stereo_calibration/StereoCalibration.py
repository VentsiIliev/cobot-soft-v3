"""
===========================================================
STEREO CAMERA CALIBRATION AND DEPTH ESTIMATION PIPELINE
===========================================================

Author: [Your Name]
Description:
    This script performs the complete stereo calibration
    and depth estimation pipeline using OpenCV.

    Steps:
    1. Load calibration images
    2. Detect chessboard corners
    3. Calibrate individual cameras
    4. Perform stereo calibration
    5. Rectify image pairs
    6. Compute disparity map
    7. Generate depth map (3D reconstruction)

Dependencies:
    - OpenCV (cv2)
    - NumPy
"""
import sys

import cv2
print(cv2.__version__)
import numpy as np
import glob
import os

# --------------------------------------------------------
# 1. USER PARAMETERS
# --------------------------------------------------------

# Define chessboard parameters
CHESSBOARD_SIZE = (17, 11)  # (corners_per_row, corners_per_col)
SQUARE_SIZE = 15.0  # Size of each chessboard square (mm or any unit)

# Paths to stereo calibration images
# The left and right images must correspond (e.g., left01.jpg <-> right01.jpg)
left_images_path = "/home/plp/cobot-soft-v2.1.8/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/VisionSystem/calibration/stereo_calibration/calibration_images/left/*.png"
right_images_path = "/home/plp/cobot-soft-v2.1.8/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/VisionSystem/calibration/stereo_calibration/calibration_images/right/*.png"



# Output directory
output_dir = "/home/plp/cobot-soft-v2.1.8/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/VisionSystem/calibration/stereo_calibration/output"
os.makedirs(output_dir, exist_ok=True)

# --------------------------------------------------------
# 2. PREPARE OBJECT POINTS
# --------------------------------------------------------

# Prepare a single array of 3D points for the chessboard corners
objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHESSBOARD_SIZE[0], 0:CHESSBOARD_SIZE[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE  # Scale by the real-world square size

# Arrays to store object points and image points
objpoints = []  # 3D points in real-world space
imgpoints_left = []  # 2D points in left image
imgpoints_right = []  # 2D points in right image

# --------------------------------------------------------
# 3. LOAD AND PROCESS IMAGES
# --------------------------------------------------------

print(f"Left images path: {left_images_path}")
print(f"Right images path: {right_images_path}")
left_images = sorted(glob.glob(left_images_path))
right_images = sorted(glob.glob(right_images_path))



assert len(left_images) == len(right_images), "Left and right image counts do not match!"

# Define criteria for corner refinement
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

print(f"[INFO] Found {len(left_images)} image pairs for calibration...")

for i, (left_path, right_path) in enumerate(zip(left_images, right_images)):
    img_left = cv2.imread(left_path)
    img_right = cv2.imread(right_path)
    print(f"[INFO] Processing pair {i + 1}:")
    print(f"       Left: {left_path}")
    print(f"       Right: {right_path}")
    # Optional: resize to fit screen
    # img_left_resized = cv2.resize(img_left, (640, 360))
    # img_right_resized = cv2.resize(img_right, (640, 360))
    # combined = np.hstack((img_left_resized, img_right_resized))
    # cv2.imshow(f"Pair {i}", combined)
    # key = cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # if key == 27:  # ESC to quit
    #     break

    gray_left = cv2.cvtColor(img_left, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(img_right, cv2.COLOR_BGR2GRAY)

    # Find chessboard corners
    ret_left, corners_left = cv2.findChessboardCorners(gray_left, CHESSBOARD_SIZE, None)
    ret_right, corners_right = cv2.findChessboardCorners(gray_right, CHESSBOARD_SIZE, None)

    if ret_left and ret_right:
        objpoints.append(objp)

        # Refine corner positions for subpixel accuracy
        corners_left = cv2.cornerSubPix(gray_left, corners_left, (11, 11), (-1, -1), criteria)
        corners_right = cv2.cornerSubPix(gray_right, corners_right, (11, 11), (-1, -1), criteria)

        imgpoints_left.append(corners_left)
        imgpoints_right.append(corners_right)

        # Optional: visualize detected corners
        cv2.drawChessboardCorners(img_left, CHESSBOARD_SIZE, corners_left, ret_left)
        cv2.drawChessboardCorners(img_right, CHESSBOARD_SIZE, corners_right, ret_right)
        cv2.imwrite(f"{output_dir}/corners_{i:02d}_left.jpg", img_left)
        cv2.imwrite(f"{output_dir}/corners_{i:02d}_right.jpg", img_right)

print(f"[INFO] Successfully detected corners in {len(objpoints)} pairs.")

if len(objpoints) == 0:
    print("No corners were detected in any image pair. Check your images and chessboard parameters.")
    sys.exit(1)
# --------------------------------------------------------
# 4. INDIVIDUAL CAMERA CALIBRATION
# --------------------------------------------------------

print("[INFO] Calibrating each camera individually...")

ret_left, mtx_left, dist_left, _, _ = cv2.calibrateCamera(objpoints, imgpoints_left, gray_left.shape[::-1], None, None)
ret_right, mtx_right, dist_right, _, _ = cv2.calibrateCamera(objpoints, imgpoints_right, gray_right.shape[::-1], None,
                                                             None)



# --------------------------------------------------------
# 5. STEREO CALIBRATION
# --------------------------------------------------------

print("[INFO] Performing stereo calibration...")

flags = 0
flags |= cv2.CALIB_FIX_INTRINSIC  # Keep intrinsics fixed (useful if already calibrated)

criteria_stereo = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 100, 1e-5)

ret, _, _, _, _, R, T, E, F = cv2.stereoCalibrate(
    objpoints, imgpoints_left, imgpoints_right,
    mtx_left, dist_left, mtx_right, dist_right,
    gray_left.shape[::-1], criteria=criteria_stereo, flags=flags
)
baseline = np.linalg.norm(T)
print(f"Baseline (distance between cameras): {baseline:.2f} units")
print("[INFO] Stereo calibration completed.")
print("Rotation Matrix:\n", R)
print("Translation Vector:\n", T)

# --------------------------------------------------------
# 6/7. RECTIFICATION AND REMAPPING (SAFE VERSION)
# --------------------------------------------------------

print("[INFO] Computing rectification transforms and remapping images safely...")

# Compute rectification transforms
R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
    mtx_left, dist_left,
    mtx_right, dist_right,
    gray_left.shape[::-1],  # width, height
    R, T,
    flags=cv2.CALIB_ZERO_DISPARITY,
    alpha=1  # keep all pixels
)

# Create undistort & rectify maps
map1_left, map2_left = cv2.initUndistortRectifyMap(
    mtx_left, dist_left, R1, P1, gray_left.shape[::-1], cv2.CV_16SC2
)
map1_right, map2_right = cv2.initUndistortRectifyMap(
    mtx_right, dist_right, R2, P2, gray_left.shape[::-1], cv2.CV_16SC2
)

# Load a test pair
test_left = cv2.imread(left_images[0])
test_right = cv2.imread(right_images[0])

# Validate image size
if test_left.shape[:2][::-1] != gray_left.shape[::-1]:
    print("[WARNING] Test image size does not match calibration image size!")

# Remap images
rect_left = cv2.remap(test_left, map1_left, map2_left, interpolation=cv2.INTER_LINEAR)
rect_right = cv2.remap(test_right, map1_right, map2_right, interpolation=cv2.INTER_LINEAR)

# Crop to valid ROI to remove black borders
x1, y1, w1, h1 = roi1
x2, y2, w2, h2 = roi2

# Crop only if ROI is non-zero
if w1 > 0 and h1 > 0:
    rect_left = rect_left[y1:y1+h1, x1:x1+w1]

if w2 > 0 and h2 > 0:
    rect_right = rect_right[y2:y2+h2, x2:x2+w2]


# Save rectified images
cv2.imwrite(f"{output_dir}/rectified_left.jpg", rect_left)
cv2.imwrite(f"{output_dir}/rectified_right.jpg", rect_right)

print("[INFO] Rectified test pair saved successfully!")
print(f"Rectified image shapes: Left={rect_left.shape}, Right={rect_right.shape}")


# --------------------------------------------------------
# 8. DISPARITY COMPUTATION
# --------------------------------------------------------

print("[INFO] Computing disparity map...")

# Convert to grayscale for disparity
grayL = cv2.cvtColor(rect_left, cv2.COLOR_BGR2GRAY)
grayR = cv2.cvtColor(rect_right, cv2.COLOR_BGR2GRAY)

# Create StereoSGBM matcher (tunable parameters)
stereo = cv2.StereoSGBM_create(
    minDisparity=0,
    numDisparities=128,  # must be divisible by 16
    blockSize=5,
    P1=8 * 3 * 5 ** 2,
    P2=32 * 3 * 5 ** 2,
    disp12MaxDiff=1,
    uniquenessRatio=10,
    speckleWindowSize=100,
    speckleRange=32
)

disparity = stereo.compute(grayL, grayR).astype(np.float32) / 16.0

# Normalize for visualization
disp_vis = cv2.normalize(disparity, None, 0, 255, cv2.NORM_MINMAX)
disp_vis = np.uint8(disp_vis)
cv2.imwrite(f"{output_dir}/disparity.jpg", disp_vis)

print("[INFO] Disparity map computed and saved.")

# --------------------------------------------------------
# 9. DEPTH MAP REPROJECTION
# --------------------------------------------------------

print("[INFO] Reprojecting disparity to 3D...")

# Reproject to 3D space (Z is depth)
points_3D = cv2.reprojectImageTo3D(disparity, Q)

# Mask out infinite/invalid points
mask_map = disparity > disparity.min()
output_points = points_3D[mask_map]
output_colors = rect_left[mask_map]


# Save point cloud as .ply
def write_ply(filename, verts, colors):
    """Save point cloud to PLY file."""
    verts = verts.reshape(-1, 3)
    colors = colors.reshape(-1, 3)
    verts = np.hstack([verts, colors])
    with open(filename, 'w') as f:
        f.write('ply\nformat ascii 1.0\n')
        f.write('element vertex %d\n' % len(verts))
        f.write('property float x\nproperty float y\nproperty float z\n')
        f.write('property uchar red\nproperty uchar green\nproperty uchar blue\n')
        f.write('end_header\n')
        np.savetxt(f, verts, fmt='%f %f %f %d %d %d')


write_ply(f"{output_dir}/point_cloud.ply", output_points, output_colors)
print(f"[INFO] 3D point cloud saved to {output_dir}/point_cloud.ply")

print("[✅ DONE] Stereo calibration and depth estimation pipeline complete!")

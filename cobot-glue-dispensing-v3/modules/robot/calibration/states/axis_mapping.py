import json
import time

import numpy as np

from modules.robot.calibration.states.robot_calibration_states import RobotCalibrationStates
from modules.robot.enums.axis import ImageAxis, Direction, ImageToRobotMapping, AxisMapping
from modules.robot.calibration.states.state_result import StateResult

def handle_axis_mapping_state(system, calibration_vision, calibration_robot_controller, logger_context):
    """Handles the axis mapping calibration state."""
    try:
        mapping = auto_calibrate_image_to_robot_mapping(system, calibration_vision, calibration_robot_controller)
        return StateResult(success=True,message="Axis mapping calibration successful",next_state=RobotCalibrationStates.LOOKING_FOR_CHESSBOARD,data=mapping)

    except Exception as e:
        error_message = f"Axis mapping calibration failed: {str(e)}"
        return StateResult(success=False,message=error_message,next_state=RobotCalibrationStates.ERROR,data=None)

def get_marker_position(system, calibration_vision, MARKER_ID, MAX_ATTEMPTS):
    """Blocks until marker with specific MARKER_ID is found, returns (x_px, y_px) as floats."""
    for _ in range(MAX_ATTEMPTS):
        frame = system.getLatestFrame()
        if frame is None:
            continue

        result = calibration_vision.detect_specific_marker(frame, MARKER_ID)

        if result.found and result.aruco_ids is not None:
            # Flatten IDs array
            ids = np.array(result.aruco_ids).flatten()

            # Check if our desired marker exists
            if MARKER_ID in ids:
                # Get index of the marker
                idx = np.where(ids == MARKER_ID)[0][0]

                # Get top-left corner of that marker
                corner = result.aruco_corners[idx][0]  # first corner of the marker
                corner = np.asarray(corner).flatten()
                x_px, y_px = float(corner[0]), float(corner[1])

                print(f"get_marker_position: Found MARKER_ID {MARKER_ID} at (x={x_px:.2f}, y={y_px:.2f})")
                return x_px, y_px

    raise RuntimeError(f"Marker {MARKER_ID} not found during axis mapping.")



def auto_calibrate_image_to_robot_mapping(system, calibration_vision, calibration_robot_controller):
    print("=== Performing Axis Mapping Calibration ===")

    MARKER_ID = 4
    MOVE_MM = 100
    MAX_ATTEMPTS = 100
    DELAY_AFTER_MOVE = 1.0

    # Step 1: initial position
    before_x, before_y = get_marker_position(system, calibration_vision, MARKER_ID, MAX_ATTEMPTS)

    # Step 2: Move X +
    ret = calibration_robot_controller.move_x_relative(MOVE_MM, blocking=True)
    if ret != 0:
        raise RuntimeError(f"Robot failed to move X {MOVE_MM}")
    time.sleep(DELAY_AFTER_MOVE)
    after_x, after_y = get_marker_position(system, calibration_vision, MARKER_ID, MAX_ATTEMPTS)
    dx_img_xmove = after_x - before_x
    dy_img_xmove = after_y - before_y
    calibration_robot_controller.move_x_relative(-MOVE_MM, blocking=True)

    # Step 3: Move Y -
    before_y_x, before_y_y = get_marker_position(system, calibration_vision, MARKER_ID, MAX_ATTEMPTS)
    ret = calibration_robot_controller.move_y_relative(-MOVE_MM, blocking=True)
    if ret != 0:
        raise RuntimeError(f"Robot failed to move Y {-MOVE_MM}")
    time.sleep(DELAY_AFTER_MOVE)
    after_y_x, after_y_y = get_marker_position(system, calibration_vision, MARKER_ID, MAX_ATTEMPTS)
    dx_img_ymove = after_y_x - before_y_x
    dy_img_ymove = after_y_y - before_y_y
    calibration_robot_controller.move_y_relative(MOVE_MM, blocking=True)

    # Step 4: Determine axis mapping
    def compute_axis_mapping(dx, dy, robot_move_mm):
        if abs(dx) > abs(dy):
            image_axis = ImageAxis.X
            img_delta = dx
        else:
            image_axis = ImageAxis.Y
            img_delta = dy

        direction = Direction.PLUS if robot_move_mm * img_delta < 0 else Direction.MINUS
        return image_axis, direction

    robot_x_image_axis, robot_x_direction = compute_axis_mapping(dx_img_xmove, dy_img_xmove, MOVE_MM)
    robot_y_image_axis, robot_y_direction = compute_axis_mapping(dx_img_ymove, dy_img_ymove, -MOVE_MM)

    # Step 5: create mapping
    image_to_robot_mapping = ImageToRobotMapping(
        robot_x=AxisMapping(image_axis=robot_x_image_axis, direction=robot_x_direction),
        robot_y=AxisMapping(image_axis=robot_y_image_axis, direction=robot_y_direction),
    )

    # Step 6: log
    log_message = f"""
=== Axis Mapping Calibration Summary ===
Marker ID used: {MARKER_ID}
Movement distance (mm): {MOVE_MM}

-- Robot X Move (+X) --
Initial marker: (x={before_x:.2f}, y={before_y:.2f})
After move: (x={after_x:.2f}, y={after_y:.2f})
Image delta: dx={dx_img_xmove:.2f}, dy={dy_img_xmove:.2f}
Mapped to image axis: {robot_x_image_axis.name}
Direction: {robot_x_direction.name}

-- Robot Y Move (-Y) --
Initial marker: (x={before_y_x:.2f}, y={before_y_y:.2f})
After move: (x={after_y_x:.2f}, y={after_y_y:.2f})
Image delta: dx={dx_img_ymove:.2f}, dy={dy_img_ymove:.2f}
Mapped to image axis: {robot_y_image_axis.name}
Direction: {robot_y_direction.name}

Final Image-to-Robot Mapping Object:
Robot X: {image_to_robot_mapping.robot_x}
Robot Y: {image_to_robot_mapping.robot_y}
========================================
"""
    print(log_message)
    return image_to_robot_mapping

# RUN 1
# === Axis Mapping Calibration Summary ===
# Marker ID used: 4
# Movement distance (mm): 100
#
# -- Robot X Move --
# Initial marker position: (x=592.00, y=269.00)
# After +X move: (x=489.00, y=269.00)
# Image delta: dx=-103.00, dy=0.00
# Mapped to image axis: X
# Direction: PLUS
#
# -- Robot Y Move --
# Initial marker position: (x=592.00, y=269.00)
# After -Y move: (x=592.00, y=167.00)
# Image delta: dx=0.00, dy=-102.00
# Mapped to image axis: Y
# Direction: PLUS
#
# Final Image-to-Robot Mapping Object:
# Robot X: AxisMapping(image_axis=<ImageAxis.X: 1>, direction=<Direction.PLUS: 1>)
# Robot Y: AxisMapping(image_axis=<ImageAxis.Y: 2>, direction=<Direction.PLUS: 1>)
# ========================================

# RUN 2
#
# === Axis Mapping Calibration Summary ===
# Marker ID used: 4
# Movement distance (mm): 100
#
# -- Robot X Move --
# Initial marker position: (x=592.00, y=269.00)
# After +X move: (x=489.00, y=269.00)
# Image delta: dx=-103.00, dy=0.00
# Mapped to image axis: X
# Direction: PLUS
#
# -- Robot Y Move --
# Initial marker position: (x=580.00, y=271.00)
# After -Y move: (x=592.00, y=167.00)
# Image delta: dx=12.00, dy=-104.00
# Mapped to image axis: Y
# Direction: PLUS
#
# Final Image-to-Robot Mapping Object:
# Robot X: AxisMapping(image_axis=<ImageAxis.X: 1>, direction=<Direction.PLUS: 1>)
# Robot Y: AxisMapping(image_axis=<ImageAxis.Y: 2>, direction=<Direction.PLUS: 1>)
# ========================================

# RUN 3
# === Axis Mapping Calibration Summary ===
# Marker ID used: 4
# Movement distance (mm): 100
#
# -- Robot X Move --
# Initial marker position: (x=592.00, y=269.00)
# After +X move: (x=489.00, y=269.00)
# Image delta: dx=-103.00, dy=0.00
# Mapped to image axis: X
# Direction: PLUS
#
# -- Robot Y Move --
# Initial marker position: (x=592.00, y=269.00)
# After -Y move: (x=592.00, y=167.00)
# Image delta: dx=0.00, dy=-102.00
# Mapped to image axis: Y
# Direction: PLUS
#
# Final Image-to-Robot Mapping Object:
# Robot X: AxisMapping(image_axis=<ImageAxis.X: 1>, direction=<Direction.PLUS: 1>)
# Robot Y: AxisMapping(image_axis=<ImageAxis.Y: 2>, direction=<Direction.PLUS: 1>)
# ========================================

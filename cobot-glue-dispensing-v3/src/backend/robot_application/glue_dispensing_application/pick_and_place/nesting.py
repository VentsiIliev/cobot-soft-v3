# Configuration
import math
import os
from datetime import datetime
from src.backend.system.tools.Laser import Laser
from VisionSystem.heightMeasuring.LaserTracker import LaserTrackService
from src.backend.system.tools.enums.Gripper import Gripper
from src.backend.system.utils.custom_logging import LoggingLevel, log_if_enabled, \
    setup_logger
from src.backend.system.utils.contours import is_contour_inside_polygon

import time
# import logging
import cv2
import numpy as np
from modules.shared.shared.ContourStandartized import Contour
from src.backend.system import CompareContours
from src.backend.robot_application.glue_dispensing_application.pick_and_place.Plane import Plane
from src.backend.system.utils import utils
from modules.shared.MessageBroker import MessageBroker

# Import matplotlib for debug plotting
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend for threading safety
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Debug plotting will be disabled.")

# Global logger variable
ENABLE_LOGGING = True  # Enable or disable logging

Z_OFFSET_FOR_CALIBRATION_PATTERN = -4
GRIPPER_X_OFFSET = 100.429  # mm, between transducer and gripper tip measured at rz = 0
GRIPPER_Y_OFFSET = 1.991  # mm, between transducer and gripper tip measured at rz = 0
DOUBLE_GRIPPER_Z_OFFSET = 14  # mm, between transducer and gripper tip
SINGLE_GRIPPER_Z_OFFSET = 19  # mm, between transducer and gripper tip
RZ_ORIENTATION = 90  # degrees
ROTATION_OFFSET_BETWEEN_PICKUP_AND_DROP_PLACE = 90  # degrees
DELAY_BETWEEN_CAPTURING_NEW_IMAGE = 1  # seconds ensuring robot is stationary and camera is stable

# Initialize logger if enabled
if ENABLE_LOGGING:
    nesting_logger = setup_logger("nesting")
else:
    nesting_logger = None




def calculate_drop_off_position(match, centroid, orientation, plane, pickup_height,gripper):
    """
    Calculate the drop-off position for a workpiece on the placement plane.

    Args:
        match: The matched workpiece object
        centroid: Original centroid coordinates
        orientation: Object orientation in degrees
        plane: Plane object for placement calculations
        pickup_height: Height at which the workpiece was picked up

    Returns:
        tuple: (drop_off_position, width, height, plane_updated)
    """

    # === LOGGING ===
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"Starting drop-off calculation for orientation: {orientation:.2f}°")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"Input: centroid={centroid}, pickup_height={pickup_height}mm")

    # === FUNCTIONALITY ===
    # Get and rotate contour
    cnt = match.get_main_contour()
    cntObject = Contour(cnt)
    cntObject.rotate(-orientation, centroid)  # Align with X-axis

    # Calculate workpiece dimensions
    minRect = cntObject.getMinAreaRect()
    bboxCenter = (minRect[0][0], minRect[0][1])
    width = minRect[1][0]
    height = minRect[1][1]
    if width < height:
        width, height = height, width

    # === LOGGING ===
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"Rotating contour by {-orientation:.2f}° to align with X-axis")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG,
                   "Swapped width/height to ensure width >= height" if width != minRect[1][0] else "")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"WORKPIECE DIMENSIONS:")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  ├─ Width:  {width:.2f} mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  ├─ Height: {height:.2f} mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  └─ Bbox center: ({bboxCenter[0]:.2f}, {bboxCenter[1]:.2f})")

    # === FUNCTIONALITY ===
    # Update the tallest contour for row spacing
    previous_tallest = plane.tallestContour
    if height > plane.tallestContour:
        plane.tallestContour = height

    # Calculate target placement position
    targetPointX = plane.xOffset + plane.xMin + (width / 2)
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"Calculated target X position: {targetPointX:.1f} = {plane.xOffset} + {plane.xMin}+{width/2} mm")
    targetPointY = plane.yMax - plane.yOffset - (height / 2)
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"Calculated target Y position: {targetPointY:.1f} = {plane.yOffset} + {plane.yMax}+{height/2} mm")

    # === LOGGING ===
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG,
                   f"Updated tallest contour: {previous_tallest:.1f} → {height:.1f} mm" if height > previous_tallest else "")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"PLACEMENT CALCULATION:")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  ├─ Current offset: ({plane.xOffset:.1f}, {plane.yOffset:.1f}) mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  ├─ Target point:  ({targetPointX:.1f}, {targetPointY:.1f}) mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  └─ Plane bounds:  ({plane.xMin}-{plane.xMax}, {plane.yMin}-{plane.yMax}) mm")

    # === FUNCTIONALITY ===
    # Handle row overflow - move to next row if needed
    if targetPointX + (width / 2) > plane.xMax:
        # === LOGGING ===
        log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.WARNING, f"⚠️  Width exceeded, moving to next row")
        log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"Exceeded by: {(targetPointX + width / 2) - plane.xMax:.1f} mm")

        # === FUNCTIONALITY ===
        plane.rowCount += 1
        plane.xOffset = 0
        plane.yOffset += plane.tallestContour + 50
        targetPointX = plane.xMin + (width / 2)
        targetPointY = plane.yMax - plane.yOffset
        plane.tallestContour = height  # Reset for new row

        # === LOGGING ===
        log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"NEW ROW {plane.rowCount}:")
        log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  ├─ Reset to: ({targetPointX:.1f}, {targetPointY:.1f}) mm")
        log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  └─ Row spacing: {plane.tallestContour + 50:.1f} mm")

        # === FUNCTIONALITY ===
        # Check vertical bounds
        if targetPointY - (height / 2) < plane.yMin:
            # === LOGGING ===
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.ERROR, "❌ PLANE FULL: Cannot fit more workpieces vertically")
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"Needed: {targetPointY - height / 2:.1f}, Available: {plane.yMin}")

            # === FUNCTIONALITY ===
            plane.isFull = True
            return None, width, height, plane

    # === FUNCTIONALITY ===
    # Position the contour at target location
    translation_x = targetPointX - bboxCenter[0]
    translation_y = targetPointY - bboxCenter[1]
    cntObject.translate(translation_x, translation_y)
    newCentroid = cntObject.getCentroid()

    # Calculate final drop-off position
    if gripper == Gripper.DOUBLE:
        drop_off_rz = -90
    else:

        drop_off_rz = 0
    drop_off_position1 = [newCentroid[0], newCentroid[1], pickup_height + 50, 180, 0, drop_off_rz]
    drop_off_position2 = [newCentroid[0], newCentroid[1], pickup_height + 20, 180, 0, drop_off_rz]

    # Update offset for next contour
    plane.xOffset += width + plane.spacing

    # === LOGGING ===
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"Translating contour by: ({translation_x:.2f}, {translation_y:.2f}) mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"FINAL DROP-OFF:")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  ├─ Translated centroid: ({newCentroid[0]:.2f}, {newCentroid[1]:.2f}) mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  ├─ Drop height: {pickup_height + 10} mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO,
                   f"  └─ Rotation: {drop_off_rz}° ({RZ_ORIENTATION}° - {ROTATION_OFFSET_BETWEEN_PICKUP_AND_DROP_PLACE}°)")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"Updated X offset for next piece: {plane.xOffset:.1f} mm")

    return drop_off_position1,drop_off_position2, width, height, plane, cntObject.get()


def calculate_pickup_positions(flat_centroid, match_height, robotService, orientation,gripper):
    """
    Calculate pickup positions with coordinate transformation and gripper offsets.

    Args:
        flat_centroid: Transformed centroid coordinates from homography
        match_height: Height of the workpiece to pick up
        robotService: Robot service for accessing config

    Returns:
        list: List of pickup positions [descent, pickup, lift]
    """


    # === LOGGING ===
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"Starting pickup position calculation for centroid: {flat_centroid}")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"Input parameters: match_height={match_height}mm")

    # === FUNCTIONALITY ===
    # Apply 90° coordinate transformation
    pickup_x_rotated = -flat_centroid[1]  # 90° rotation: x' = -y
    pickup_y_rotated = flat_centroid[0]  # 90° rotation: y' = x

    if gripper == Gripper.DOUBLE:
        rz = RZ_ORIENTATION - 90
    else:
        rz = RZ_ORIENTATION


    orientation_radians = math.radians(rz-orientation) # convert to radians
    gripper_x_offset_rotated, gripper_y_offset_rotated = __rotate_offsets(
        GRIPPER_X_OFFSET,
        GRIPPER_Y_OFFSET,
        orientation_radians
    )

    # Apply rotated offsets to rotated position
    final_pickup_x = pickup_x_rotated + gripper_x_offset_rotated
    final_pickup_y = pickup_y_rotated + gripper_y_offset_rotated

    # Calculate heights
    z_min = robotService.robot_config.safety_limits.z_min
    descent_height = z_min + 150  # Safe descent height above minimum

    if gripper == Gripper.DOUBLE:
        pickup_height = z_min + DOUBLE_GRIPPER_Z_OFFSET + match_height
    elif gripper == Gripper.SINGLE:
        pickup_height = z_min + SINGLE_GRIPPER_Z_OFFSET + match_height
    else:
        raise ValueError(f"Unknown gripper type: {gripper}")


    # Create pickup sequence: descent -> pickup -> lift

    # choose angle
    # compute candidate angles
    angle1 = rz - orientation
    angle2 = rz + orientation

    # normalize to [-180, 180] then pick the one closer to 0
    def _norm_deg(a):
        return ((a + 180) % 360) - 180

    angle1 = _norm_deg(angle1)
    angle2 = _norm_deg(angle2)
    angle_closer_to_zero = angle1 if abs(angle1) <= abs(angle2) else angle2
    print(f"angle1: {angle1}, angle2: {angle2}, chosen angle: {angle_closer_to_zero}")

    height_measure_position = [pickup_x_rotated, pickup_y_rotated, descent_height, 180, 0, rz-orientation]

    pickup_positions = [
        [final_pickup_x, final_pickup_y, descent_height, 180, 0, rz-orientation],  # Descent
        [final_pickup_x, final_pickup_y, pickup_height, 180, 0, rz-orientation],  # Pickup
        [final_pickup_x, final_pickup_y, descent_height, 180, 0, rz-orientation] # Lift
    ]
    params = flat_centroid, pickup_x_rotated, pickup_y_rotated, orientation_radians, gripper_x_offset_rotated, gripper_y_offset_rotated, final_pickup_x, final_pickup_y, z_min, descent_height, pickup_height, pickup_positions
    log_pickup_position_calculation_result(params)

    return pickup_positions, height_measure_position,pickup_height


def start_nesting(visionService, robotService,preselected_workpiece,z_offset_for_calibration_pattern):
    Z_OFFSET_FOR_CALIBRATION_PATTERN = z_offset_for_calibration_pattern
    # === LOGGING ===
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, "=" * 80)
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, "🤖 STARTING NESTING OPERATION")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, "=" * 80)

    # === FUNCTIONALITY ===
    workpieces = preselected_workpiece

    plane = Plane()
    count = 0
    workpiece_found = False
    placed_contours = []  # Track placed contours for debug plotting
    cycle_number = 0  # Track cycle number for debug plotting

    # === LOGGING ===
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"Loaded {len(workpieces)} workpiece templates")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"Plane configuration: {plane.xMin}-{plane.xMax} x {plane.yMin}-{plane.yMax}")

    laser = Laser()
    laser.turnOn()
    laserTrackingService = LaserTrackService()
    # === FUNCTIONALITY ===
    while True:
        cycle_number += 1  # Increment cycle counter for debug plotting
        # === LOGGING ===
        log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"\n🔄 CYCLE {cycle_number}: Starting new detection cycle")
        log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, "Moving robot to start position (home)")

        # === FUNCTIONALITY ===
        # Move robot and capture new image
        ret = robotService.move_to_nesting_capture_position(z_offset = Z_OFFSET_FOR_CALIBRATION_PATTERN)
        if ret != 0:
            laser.turnOff()
            return False, "Failed to move to start position"


        broker = MessageBroker()
        broker.publish("vision-system/threshold", {"region": "pickup"})

        time.sleep(DELAY_BETWEEN_CAPTURING_NEW_IMAGE)

        max_retries = 10
        retry_delay = 1  # seconds between retries

        newContours = None
        for attempt in range(1, max_retries + 1):
            newContours = visionService.contours
            print(f"Attempt {attempt}: Retrieved {len(newContours) if newContours else 0} contours")
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                           f"Robot positioned, waiting {DELAY_BETWEEN_CAPTURING_NEW_IMAGE}s for image capture")
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                           f"Attempt {attempt}/{max_retries}: Retrieved contours from vision system: {len(newContours) if newContours else 0}")

            if newContours is not None and len(newContours) > 0:
                break

            if attempt < max_retries:
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,
                               f"No contours detected, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
        else:
            # === LOGGING ===
            log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.WARNING,
                           "❌ NO CONTOURS FOUND: Vision system detected no objects after retries")
            # === FUNCTIONALITY ===
            if workpiece_found:
                # Drop off gripper before completing nesting
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, "✅ NESTING COMPLETE: Dropping off gripper")
                robotService.dropOffGripper(robotService.currentGripper)
                laser.turnOff()
                return True, "No more workpieces to pick"
            laser.turnOff()
            return False, "No contours found"

        # add first point to the end to close the contour
        for i, cnt in enumerate(newContours):
            if len(cnt) > 0:
                # Close the contour by adding first point to the end using numpy concatenation
                # Ensure dimensions match: cnt is (n, 1, 2), so reshape first point to (1, 1, 2)
                first_point = cnt[0].reshape(1, 1, 2)
                newContours[i] = np.vstack([cnt, first_point])

        # === LOGGING ===
        log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"📷 VISION: Detected {len(newContours)} contours")

        # === FUNCTIONALITY ===
        # Filter contours by pickup area
        pickup_area = visionService.getPickupAreaPoints()

        if pickup_area is not None and len(pickup_area) >= 4:
            initial_count = len(newContours)
            filtered_contours = []
            for contour in newContours:
                if is_contour_inside_polygon(contour, pickup_area[0], pickup_area[1], pickup_area[2], pickup_area[3]):
                    filtered_contours.append(contour)
            newContours = filtered_contours

            # === LOGGING ===
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO,
                           f"🎯 FILTERING: {initial_count} → {len(newContours)} contours inside pickup area")
        else:
            # === LOGGING ===
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.WARNING, "⚠️  No pickup area defined, processing all contours")

        # === FUNCTIONALITY ===
        # Match workpieces with detected contours
        matches_data, noMatches, _ = CompareContours.findMatchingWorkpieces(workpieces, newContours)
        orientations = matches_data["orientations"]
        matches = matches_data["workpieces"]

        if matches is not None and len(matches) > 0:
            workpiece_found = True
        else:

            if workpiece_found:
                # === LOGGING ===
                log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, "✅ NESTING COMPLETE: No more workpieces detected")
                # === FUNCTIONALITY ===
                robotService.dropOffGripper(robotService.currentGripper)

                ret = robotService.move_to_nesting_capture_position(z_offset = Z_OFFSET_FOR_CALIBRATION_PATTERN)
                if ret != 0:
                    laser.turnOff()
                    return False, "Failed to move to start position"
                return True, "No more workpieces to pick"
            else:
                # === LOGGING ===
                log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.WARNING, "❌ NO MATCHES: No workpieces matched detected contours")
                # === FUNCTIONALITY ===
                return False, "No workpieces matched detected contours"

        # === LOGGING ===
        log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, "Starting workpiece matching process...")

        # === FUNCTIONALITY ===
        if not matches:
            # === LOGGING ===
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.WARNING, "❌ MATCHING: No matching workpieces found!")
            # === FUNCTIONALITY ===
            from modules.shared.localization.enums.Message import Message
            laser.turnOff()
            return False, Message.NO_WORKPIECE_DETECTED

        # === LOGGING ===
        log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"✅ MATCHING: Found {len(matches)} workpiece matches")

        # === FUNCTIONALITY ===
        # Process each matched workpiece
        for match_i, match in enumerate(matches):
            ret = robotService.move_to_nesting_capture_position(z_offset = Z_OFFSET_FOR_CALIBRATION_PATTERN)
            # === LOGGING ===
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"\n🎯 PROCESSING MATCH {match_i + 1}/{len(matches)}")

            # === FUNCTIONALITY ===
            contour = match.get_main_contour()
            cnt_obj = Contour(contour)
            match_height = 3
            gripper = match.gripperID

            if match.pickupPoint is not None:
                # Parse pickup point string "x,y" and convert to tuple (x, y)
                if isinstance(match.pickupPoint, str):
                    try:
                        x_str, y_str = match.pickupPoint.split(',')
                        centroid = (int(float(x_str)), int(float(y_str)))
                        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, f"Using pickup point: {centroid}")
                    except (ValueError, AttributeError) as e:
                        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.WARNING, f"Invalid pickup point format '{match.pickupPoint}', using centroid instead: {e}")
                        centroid = cnt_obj.getCentroid()
                else:
                    # Assume it's already in correct format (tuple/list)
                    centroid = match.pickupPoint
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, f"Using pickup point: {centroid}")
            else:
                centroid = cnt_obj.getCentroid()
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, f"Using centroid: {centroid}")

            # Apply homography transformation
            transformed_centroid = utils.applyTransformation(visionService.cameraToRobotMatrix, [centroid])
            centroid_for_height_measure = utils.applyTransformation(visionService.cameraToRobotMatrix, [centroid],apply_transducer_offset=False)
            flat_centroid = transformed_centroid
            while isinstance(flat_centroid, (list, tuple)) and len(flat_centroid) == 1:
                flat_centroid = flat_centroid[0]

            # === LOGGING ===
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"Match details: height={match_height}mm, gripper={gripper}")
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, "Applying homography transformation...")
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"HOMOGRAPHY TRANSFORMATION:")
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  ├─ Camera coordinates: {centroid} pixels")
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  ├─ Robot coordinates:  {flat_centroid} mm")
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  ├─ Object orientation: {orientations[match_i]:.2f}°")
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  └─ Assigned gripper:   {gripper}")

            # === FUNCTIONALITY ===
            # Calculate pickup and drop-off positions
            pickup_positions,height_measure_position, pickup_height = calculate_pickup_positions(flat_centroid, match_height, robotService,
                                                                         orientations[match_i],gripper)
            drop_off_result = calculate_drop_off_position(match, centroid, orientations[match_i], plane, pickup_height,gripper)


            # === LOGGING ===
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, "Calculating drop-off position...")

            # === FUNCTIONALITY ===
            if drop_off_result[0] is None:  # Plane is full
                # === LOGGING ===
                log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.WARNING, "⚠️  PLANE FULL: Cannot place more workpieces")
                # === FUNCTIONALITY ===
                plane.isFull = True
                break

            drop_off_position1,drop_off_position2, width, height, plane, placed_contour = drop_off_result
            # apply gripper offsets to drop-off position

            if gripper == Gripper.DOUBLE:
                # rotate the offsets by -90 degrees and apply them
                orientation_radians = math.radians(-90)
                rotated_x, rotated_y = __rotate_offsets(GRIPPER_X_OFFSET, GRIPPER_Y_OFFSET, orientation_radians)
                drop_off_position1[0] += rotated_x
                drop_off_position1[1] += rotated_y
                drop_off_position2[0] += rotated_x
                drop_off_position2[1] += rotated_y
            else:
                # apply standard gripper offsets
                drop_off_position1[0] += GRIPPER_X_OFFSET
                drop_off_position1[1] += GRIPPER_Y_OFFSET
                drop_off_position2[0] += GRIPPER_X_OFFSET
                drop_off_position2[1] += GRIPPER_Y_OFFSET

            count += 1

            # Add placed contour to tracking list for debug plotting
            placed_contours.append({
                'contour': placed_contour,
                'drop_position': drop_off_position1,
                'dimensions': (width, height),
                'cycle': cycle_number,
                'match_index': match_i + 1
            })

            # === LOGGING ===
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO,
                           f"📍 DROP-OFF: Position calculated at {drop_off_position1[:2]} mm (Z: {drop_off_position1[2]} mm)")
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG,f"Drop-off position: {drop_off_position1}")
            log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"Workpiece dimensions: {width:.1f} x {height:.1f} mm")
            
            # === DEBUG PLOTTING ===
            # Save debug plot after drop position is calculated
            __save_nesting_debug_plot(plane, placed_contours, cycle_number, match_i + 1)

            # === FUNCTIONALITY ===
            # Execute pickup sequence

            # check if the workpiece gripper is different then the currently attached one
            try:
                target_gripper_id = int(gripper.value)
            except (ValueError, AttributeError) as e:
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.ERROR, 
                              f"Invalid gripper value: {gripper.value}. Error: {e}")
                laser.turnOff()
                return False
            
            if robotService.currentGripper != target_gripper_id:
                # if different, drop the current gripper (if any) and pick up the new one
                if robotService.currentGripper is not None:
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, 
                                  f"Dropping off current gripper: {robotService.currentGripper}")
                    success, message = robotService.dropOffGripper(robotService.currentGripper)
                    if not success:
                        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.ERROR, 
                                      f"Failed to drop off gripper {robotService.currentGripper}: {message}")
                        laser.turnOff()
                        return False

                # pick up the new gripper
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, 
                              f"Picking up gripper: {target_gripper_id}")
                success, message = robotService.pickupGripper(target_gripper_id)
                if not success:
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.ERROR, 
                                  f"Failed to pick up gripper {target_gripper_id}: {message}")
                    laser.turnOff()
                    return False
                
                # Verify the gripper change was successful
                if robotService.currentGripper != target_gripper_id:
                    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.ERROR, 
                                  f"Gripper change verification failed. Expected: {target_gripper_id}, Current: {robotService.currentGripper}")
                    return False
                
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, 
                              f"Successfully switched to gripper: {target_gripper_id}")
            else:
                log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG, 
                              f"Gripper {target_gripper_id} already attached, no change needed")

            height_measure_pos = height_measure_position  # already calculated
            print(f"Height measure position before adjustment: {height_measure_pos}")
            print(f"Centroid for height measure: {centroid_for_height_measure}")
            # Extract raw centroid coordinates
            cx = centroid_for_height_measure[0][0][0][0]
            cy = centroid_for_height_measure[0][0][0][1]

            # --- Rotate centroid by 90 degrees counterclockwise around origin ---
            rotated_cx = -cy
            rotated_cy = cx

            # Assign rotated coordinates to height measure position
            height_measure_pos[0] = rotated_cx
            height_measure_pos[1] = rotated_cy

            height_measure_pos[2] = 350  # set a safe height for measurement
            height_measure_pos[5] = RZ_ORIENTATION

            result, measured_height, value_in_pixels = measure_height_at_position(robotService,
                                                                                  visionService,
                                                                                  laserTrackingService,
                                                                                  height_measure_pos,
                                                                                  laser)
            measured_height = measured_height+2 # temp add 1 mm

            if not result:
                laser.turnOff()
                return False, "Failed to measure height."

            log_if_enabled(enabled=ENABLE_LOGGING,
                           logger=nesting_logger,
                           level=LoggingLevel.INFO,
                           message=f"Measured workpiece height: result={result} {value_in_pixels} mm")

            # robotService.pump.turnOn(robotService.robot)
            # 3. Execute pick and place sequence
            ret = execute_pick_and_place_sequence(robotService,pickup_positions,
                                                  drop_off_position1,
                                                  drop_off_position2,
                                                  measured_height, gripper)
            if ret != 0:
                robotService.pump.turnOff(robotService.robot)
                laser.turnOff()
                return False, "Failed to move to pickup position"

def measure_height_at_position(robot_service,vision_service,laser_tracking_service,position,laser):
    ret = move_to(robot_service, position)

    if ret != 0:
        laser.turnOff()
        return False, "Failed to move to height measuring position"

    # 2.Turn laser on and measure height
    time.sleep(1)  # wait for brightness to stabilize
    skip_images_count = 5
    while skip_images_count > 0:
        # skip initial images to allow auto-exposure to stabilize
        _ = vision_service.getLatestFrame()
        skip_images_count -= 1
        if skip_images_count <= 0:
            break
    latest_image = vision_service.getLatestFrame()
    # convert to RGB
    latest_image = cv2.cvtColor(latest_image, cv2.COLOR_BGR2RGB)

    if latest_image is None:
        laser.turnOff()
        return False, "Failed to capture image for height measurement"
    cv2.imwrite("debug_laser_image.png", latest_image)
    return laser_tracking_service.measure_height(latest_image)

def execute_pick_sequence(robot_service,pickup_positions,measured_height,gripper):
    ret = True
    for i, pos in enumerate(pickup_positions):
        # Create a copy to avoid modifying the original
        adjusted_pos = pos.copy()

        # Update Z coordinate based on measured height for pickup position (index 1)
        if i == 1:  # Pickup position (descent=0, pickup=1, lift=2)
            z_min = robot_service.robot_config.safety_limits.z_min
            if gripper == Gripper.DOUBLE:
                adjusted_pos[2] = z_min + DOUBLE_GRIPPER_Z_OFFSET + measured_height
            elif gripper == Gripper.SINGLE:
                adjusted_pos[2] = z_min + SINGLE_GRIPPER_Z_OFFSET + measured_height

        log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.DEBUG,
                       f"Moving to pickup position {i}: {adjusted_pos} (original: {pos})")

        ret = move_to(robot_service, adjusted_pos)
        if ret != 0:
            ret = False
            break
    return ret


def execute_place_sequence(robot_service,drop_off_position1, drop_off_position2):
    # Execute drop-off sequence via waypoint
    descent_height = robot_service.robot_config.safety_limits.z_min + 100
    waypoint = [-317.997, 261.207, descent_height + 50, 180, 0, 0]

    ret = move_to(robot_service, waypoint)
    if ret !=0:
        return ret
    ret = move_to(robot_service, drop_off_position1)
    if ret !=0:
        return ret
    ret = move_to(robot_service, drop_off_position2)

    robot_service.pump.turnOff(robot_service.robot)
    return ret

def execute_pick_and_place_sequence(robot_service, pickup_positions, drop_off_position1, drop_off_position2,measured_height,gripper):

    ret = execute_pick_sequence(robot_service,pickup_positions,measured_height,gripper)
    if ret != 0:
        return ret
    ret = execute_place_sequence(robot_service, drop_off_position1, drop_off_position2)
    if ret != 0:
        return ret
    ret = robot_service.moveToCalibrationPosition(z_offset=Z_OFFSET_FOR_CALIBRATION_PATTERN)
    return ret


def move_to(robot_service,position):
    ret = robot_service.moveToPosition(position=position,
                                tool=robot_service.robot_config.robot_tool,
                                workpiece=robot_service.robot_config.robot_user,
                                velocity=robot_service.robot_config.global_motion_settings.global_velocity,
                                acceleration=robot_service.robot_config.global_motion_settings.global_acceleration,
                                waitToReachPosition=True)
    return  ret

def __save_nesting_debug_plot(plane, placed_contours, cycle_number, match_index):
    """
    Save a debug plot showing the nested contours after drop position calculation.
    
    Args:
        plane: The placement plane object with bounds and current state
        placed_contours: List of contours that have been placed so far
        cycle_number: Current nesting cycle number
        match_index: Current match index within the cycle
    """
    if not MATPLOTLIB_AVAILABLE:
        log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.WARNING, "Matplotlib not available - skipping debug plot")
        return
    
    try:
        # Create figure and axis
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Set up plot bounds with some margin
        margin = 50  # mm
        x_min = plane.xMin - margin
        x_max = plane.xMax + margin
        y_min = plane.yMin - margin 
        y_max = plane.yMax + margin
        
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_aspect('equal')
        
        # Draw plane boundaries
        plane_rect = patches.Rectangle(
            (plane.xMin, plane.yMin), 
            plane.xMax - plane.xMin, 
            plane.yMax - plane.yMin,
            linewidth=2, 
            edgecolor='red', 
            facecolor='none',
            label='Placement Plane'
        )
        ax.add_patch(plane_rect)
        
        # Draw placed contours
        colors = ['blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        for i, contour_data in enumerate(placed_contours):
            contour = contour_data['contour']
            color = colors[i % len(colors)]
            
            # Extract x and y coordinates from contour
            if len(contour.shape) == 3 and contour.shape[1] == 1:
                # Standard OpenCV contour format (n, 1, 2)
                x_coords = contour[:, 0, 0]
                y_coords = contour[:, 0, 1]
            elif len(contour.shape) == 2 and contour.shape[1] == 2:
                # Simple (n, 2) format
                x_coords = contour[:, 0]
                y_coords = contour[:, 1]
            else:
                log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.WARNING, f"Unexpected contour shape: {contour.shape}")
                continue
                
            # Close the contour by adding first point at the end
            x_coords = np.append(x_coords, x_coords[0])
            y_coords = np.append(y_coords, y_coords[0])
            
            # Plot contour
            ax.plot(x_coords, y_coords, color=color, linewidth=2, 
                   label=f"Workpiece {i+1}")
            
            # Fill contour with transparency
            ax.fill(x_coords, y_coords, color=color, alpha=0.3)
            
            # Mark centroid
            centroid_x = np.mean(x_coords[:-1])  # Exclude duplicate first point
            centroid_y = np.mean(y_coords[:-1])
            ax.plot(centroid_x, centroid_y, 'o', color=color, markersize=8, 
                   markeredgecolor='black', markeredgewidth=1)
        
        # Add grid and labels
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X (mm)', fontsize=12)
        ax.set_ylabel('Y (mm)', fontsize=12)
        ax.set_title(f'Nesting Debug - Cycle {cycle_number}, Match {match_index}\n'
                    f'Placed: {len(placed_contours)} workpieces, Row: {plane.rowCount}', 
                    fontsize=14, fontweight='bold')
        
        # Add legend
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Add plane info text
        info_text = (f"Plane Info:\n"
                    f"Bounds: ({plane.xMin}, {plane.yMin}) to ({plane.xMax}, {plane.yMax})\n"
                    f"Current Offset: ({plane.xOffset:.1f}, {plane.yOffset:.1f})\n"
                    f"Current Row: {plane.rowCount}\n"
                    f"Tallest in Row: {plane.tallestContour:.1f}mm\n"
                    f"Spacing: {plane.spacing}mm")
        
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Save plot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nesting_debug_cycle{cycle_number:02d}_match{match_index:02d}_{timestamp}.png"
        
        # Create debug directory if it doesn't exist
        debug_dir = "nesting_visualizations"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
            
        filepath = os.path.join(debug_dir, filename)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"🎨 DEBUG PLOT: Saved nesting visualization to {filepath}")
        
    except Exception as e:
        log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.ERROR, f"Failed to save debug plot: {e}")


def __rotate_offsets(x_offset, y_offset, orientation_radians):
      """
      Rotate x,y offsets by given orientation angle

      Args:
          x_offset: Original X offset
          y_offset: Original Y offset
          orientation_radians: Rotation angle in radians

      Returns:
          tuple: (rotated_x_offset, rotated_y_offset)
      """
      cos_theta = math.cos(orientation_radians)
      sin_theta = math.sin(orientation_radians)

      # 2D rotation matrix transformation
      rotated_x = x_offset * cos_theta - y_offset * sin_theta
      rotated_y = x_offset * sin_theta + y_offset * cos_theta

      return rotated_x, rotated_y

""" LOGGING FUNCTIONS """

def log_pickup_position_calculation_result(params):
    flat_centroid, pickup_x_rotated, pickup_y_rotated, orientation_radians, gripper_x_offset_rotated, gripper_y_offset_rotated, final_pickup_x, final_pickup_y, z_min, descent_height, pickup_height, pickup_positions = params
    # === LOGGING ===
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"COORDINATE TRANSFORMATION:")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  ├─ Before 90° rotation: ({flat_centroid[0]:.2f}, {flat_centroid[1]:.2f}) mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  └─ After 90° rotation:  ({pickup_x_rotated:.2f}, {pickup_y_rotated:.2f}) mm")
    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO, f"GRIPPER OFFSET TRANSFORMATION:")
    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,  f"  ├─ Original offsets: ({GRIPPER_X_OFFSET}, {GRIPPER_Y_OFFSET}) mm")
    log_if_enabled(ENABLE_LOGGING, nesting_logger, LoggingLevel.INFO,  f"  └─ Rotated offsets:  ({gripper_x_offset_rotated:.2f}, {gripper_y_offset_rotated:.2f}) mm (rotated by {math.degrees(orientation_radians):.2f}°)")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"FINAL PICKUP CALCULATION:")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  ├─ Rotated position: ({pickup_x_rotated:.2f}, {pickup_y_rotated:.2f}) mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO,
                   f"  ├─ Applied offsets:  ({gripper_x_offset_rotated:.2f}, {gripper_y_offset_rotated:.2f}) mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"  └─ Final position:   ({final_pickup_x:.2f}, {final_pickup_y:.2f}) mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"HEIGHT CALCULATIONS:")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"  ├─ Z minimum:     {z_min} mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"  ├─ Descent height: {descent_height} mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"  └─ Pickup height:  {pickup_height} mm")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.INFO, f"Generated {len(pickup_positions)} pickup positions (descent → pickup → lift)")
    log_if_enabled(ENABLE_LOGGING,nesting_logger,LoggingLevel.DEBUG, f"Pickup sequence: {pickup_positions}")

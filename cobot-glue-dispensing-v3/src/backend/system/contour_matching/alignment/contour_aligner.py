import copy

import numpy as np

from modules.shared.shared.ContourStandartized import Contour
from src.backend.system.contour_matching.alignment.mask_refinement import _refine_alignment_with_mask
from src.backend.system.contour_matching.alignment.transformations import apply_translation, apply_rotation
from src.backend.system.contour_matching.alignment.workpiece_update import update_workpiece_data
from src.backend.system.contour_matching.debug.plot_generator import plot_contour_alignment
from src.backend.system.contour_matching.matching_config import REFINEMENT_THRESHOLD


def get_contour_objects(entries):
    objects = []
    for entry in entries:
        contour_data = entry.get("contour")
        if contour_data:
            objects.append(Contour(contour_data))
    return objects


def handle_refinement_stage(contourObj,sprayContourObjs,sprayFillObjs,newContour):
    # ✅ Mask-based refinement to avoid mirrored shapes
        # print(f"    Performing mask-based alignment refinement...")
    best_rotation, best_overlap = _refine_alignment_with_mask(
        contourObj.get(),
        newContour,
        search_range=2,  # Search ±10 degrees
        step=1  # 1 degree steps
    )
    if abs(best_rotation) > REFINEMENT_THRESHOLD:  # Apply refinement if significant
        centroid_after_translation = contourObj.getCentroid()
        # Apply refinement rotation to all contours
        contourObj.rotate(best_rotation, centroid_after_translation)
        apply_rotation(sprayContourObjs,best_rotation,centroid_after_translation)
        apply_rotation(sprayFillObjs,best_rotation,centroid_after_translation)

def transform_pickup_point(workpiece, rotationDiff, centroidDiff, centroid):
    # ✅ Update pickup point if it exists
    if hasattr(workpiece, 'pickupPoint') and workpiece.pickupPoint is not None:
        # Parse pickup point string if needed
        if isinstance(workpiece.pickupPoint, str):
            try:
                x_str, y_str = workpiece.pickupPoint.split(',')
                pickup_x, pickup_y = float(x_str), float(y_str)
                print(f"  📍 Original pickup point: ({pickup_x:.1f}, {pickup_y:.1f})")

                # Apply the same transformations as applied to contours
                # 1. Apply rotation around the centroid
                pickup_point = np.array([[pickup_x, pickup_y]], dtype=np.float32)
                pickup_contour_obj = Contour(pickup_point.reshape(-1, 1, 2))
                pickup_contour_obj.rotate(rotationDiff, pivot=centroid)
                pickup_contour_obj.translate(centroidDiff[0], centroidDiff[1])

                # Get transformed coordinates
                transformed_pickup = pickup_contour_obj.get()[0][0]  # Extract the point
                transformed_x, transformed_y = transformed_pickup[0], transformed_pickup[1]
                return [transformed_x, transformed_y]
            except(ValueError, AttributeError) as e:
                print(f"  ⚠️ Invalid pickup point format '{workpiece.pickupPoint}': {e}")
    return None

def _alignContours(matched, debug=False):
    """
    Align matched contours to the workpieces by rotating and translating based on differences.

    Args:
        matched (list): List of matched workpieces and their corresponding contour differences.

        debug (bool): If True, show detailed debug plots of the alignment process.

    Returns:
        list: List of workpieces with aligned contours.
    """
    transformedMatchesDict = {"workpieces": [], "orientations": [], "mlConfidences": [], "mlResults": []}

    for i, match in enumerate(matched):
        workpiece = copy.deepcopy(match["workpieces"])
        newContour = match["newContour"]
        rotationDiff = match["rotationDiff"]
        centroidDiff = match["centroidDiff"]
        contourOrientation = match["contourOrientation"]
        contourObj = match["contourObj"]
        sprayContourObjs = match["sprayContourObjs"]
        sprayFillObjs = match["sprayFillObjs"]

        # ✅ Apply transformations
        centroid = contourObj.getCentroid()
        # Store original positions for debug visualization
        if debug:
            original_contour = contourObj.get().copy()
            original_new_contour = newContour.copy()
            original_spray_contours = [obj.get().copy() for obj in sprayContourObjs]

        contourObj.rotate(rotationDiff, centroid)

        # # Store after rotation for debug
        if debug:
            rotated_contour = contourObj.get().copy()

        apply_rotation(sprayContourObjs,rotationDiff,centroid)
        apply_rotation(sprayFillObjs,rotationDiff,centroid)

        contourObj.translate(*centroidDiff)
        apply_translation(sprayContourObjs,centroidDiff[0],centroidDiff[1])
        apply_translation(sprayFillObjs,centroidDiff[0],centroidDiff[1])

        transformed_pickup_point = transform_pickup_point(workpiece, rotationDiff, centroidDiff, centroid)

        handle_refinement_stage(contourObj, sprayContourObjs, sprayFillObjs,newContour)
        update_workpiece_data(workpiece,contourObj,sprayContourObjs,sprayFillObjs,transformed_pickup_point)
        # Debug visualization for _alignContours
        if debug:
            final_contour = contourObj.get().copy()
            plot_contour_alignment(original_contour, original_new_contour, centroid, original_spray_contours, workpiece,
                                   rotated_contour, final_contour, rotationDiff, centroidDiff, contourOrientation,
                                   sprayContourObjs, sprayFillObjs, i)


        transformedMatchesDict["workpieces"].append(workpiece)

        transformedMatchesDict["orientations"].append(contourOrientation)
        # Preserve ML confidence from the original match dictionary
        transformedMatchesDict["mlConfidences"].append(match.get("mlConfidence", 0.0))
        transformedMatchesDict["mlResults"].append(match.get("mlResult", "UNKNOWN"))


    return transformedMatchesDict



import copy
from typing import Any, Dict
from typing import List, Optional, Tuple

import numpy as np

from backend.system.contour_matching.debug.plot_generator import plot_contour_alignment
from backend.system.contour_matching.matching.match_info import MatchInfo
from modules.shared.core.ContourStandartized import Contour
from backend.system.contour_matching.alignment.mask_refinement import _refine_alignment_with_mask
from backend.system.contour_matching.alignment.workpiece_update import update_workpiece_data
from backend.system.contour_matching.matching_config import REFINEMENT_THRESHOLD


def apply_rotation(contours, angle, pivot):
    for c in contours:
        c.rotate(angle, pivot)

def apply_translation(contours, dx, dy):
    for c in contours:
        c.translate(dx, dy)

def align_single_contour(
    target: Contour,
    reference: np.ndarray,
    spray_contours: Optional[List[Contour]] = None,
    spray_fills: Optional[List[Contour]] = None,
    rotation_diff: float = 0.0,
    translation_diff: Tuple[float, float] = (0.0, 0.0),
    refine: bool = True
) -> None:
    """
    Align a single target contour to a reference contour, optionally applying the same
    transformation to associated spray contours/fills and performing mask-based refinement.
    Works in-place.

    Args:
        target (Contour): Contour to align.
        reference (np.ndarray): Reference contour.
        spray_contours (Optional[List[Contour]]): Spray contours associated with the target.
        spray_fills (Optional[List[Contour]]): Spray fills associated with the target.
        rotation_diff (float): Initial rotation difference in degrees.
        translation_diff (Tuple[float, float]): Initial translation difference (dx, dy).
        refine (bool): Whether to perform mask-based refinement.
    """
    spray_contours = spray_contours or []
    spray_fills = spray_fills or []

    centroid = target.getCentroid()

    # --- Initial rotation ---
    target.rotate(rotation_diff, centroid)
    apply_rotation(spray_contours, rotation_diff, centroid)
    apply_rotation(spray_fills, rotation_diff, centroid)

    # --- Initial translation ---
    dx, dy = translation_diff
    target.translate(dx, dy)
    apply_translation(spray_contours, dx, dy)
    apply_translation(spray_fills, dx, dy)

    # --- Mask-based refinement ---
    if refine:
        best_rotation, _ = _refine_alignment_with_mask(
            target.get(),
            reference
        )
        if abs(best_rotation) > REFINEMENT_THRESHOLD:
            centroid_after = target.getCentroid()
            target.rotate(best_rotation, centroid_after)
            apply_rotation(spray_contours, best_rotation, centroid_after)
            apply_rotation(spray_fills, best_rotation, centroid_after)


def align_contours_generic(
    target_contours: List[Contour],
    reference_contours: List[np.ndarray],
    spray_contours_list: Optional[List[List[Contour]]] = None,
    spray_fills_list: Optional[List[List[Contour]]] = None,
    rotation_diffs: Optional[List[float]] = None,
    translation_diffs: Optional[List[Tuple[float, float]]] = None,
    refine: bool = True
) -> None:
    """
    Align multiple target contours to corresponding reference contours using `align_single_contour`.
    """
    spray_contours_list = spray_contours_list or [[] for _ in target_contours]
    spray_fills_list = spray_fills_list or [[] for _ in target_contours]
    rotation_diffs = rotation_diffs or [0.0] * len(target_contours)
    translation_diffs = translation_diffs or [(0.0, 0.0)] * len(target_contours)

    for i, (target, reference) in enumerate(zip(target_contours, reference_contours)):
        align_single_contour(
            target=target,
            reference=reference,
            spray_contours=spray_contours_list[i],
            spray_fills=spray_fills_list[i],
            rotation_diff=rotation_diffs[i],
            translation_diff=translation_diffs[i],
            refine=refine
        )



def _alignContours(matched: List[MatchInfo], debug: bool = False) -> Dict[str, List[Any]]:
    """
    Align matched contours to the workpieces using the workpiece-agnostic batch function.

    Args:
        matched (List[MatchInfo]): List of matched workpieces with contour info.
        debug (bool): Whether to generate debug plots.

    Returns:
        Dict[str, List[Any]]: Aligned workpieces, orientations, ML confidences, ML results.
    """
    transformedMatchesDict: Dict[str, List[Any]] = {
        "workpieces": [],
        "orientations": [],
        "mlConfidences": [],
        "mlResults": [],
    }

    # Prepare lists for batch alignment
    target_contours = [match.contourObj for match in matched]
    reference_contours = [match.new_contour for match in matched]
    spray_contours_list = [match.sprayContourObjs for match in matched]
    spray_fills_list = [match.sprayFillObjs for match in matched]
    rotation_diffs = [match.rotation_diff for match in matched]
    translation_diffs = [match.centroid_diff for match in matched]

    # --- Store debug originals if needed ---
    if debug:
        original_data = []
        for target, reference, sprays in zip(target_contours, reference_contours, spray_contours_list):
            original_data.append({
                "target": target.get().copy(),
                "reference": reference.copy(),
                "sprays": [s.get().copy() for s in sprays]
            })

    # --- Perform batch alignment ---
    align_contours_generic(
        target_contours=target_contours,
        reference_contours=reference_contours,
        spray_contours_list=spray_contours_list,
        spray_fills_list=spray_fills_list,
        rotation_diffs=rotation_diffs,
        translation_diffs=translation_diffs,
        refine=True
    )

    # --- Update workpieces and optionally generate debug plots ---
    for i, match in enumerate(matched):
        workpiece = copy.deepcopy(match.workpiece)
        contourObj = target_contours[i]
        sprayContourObjs = spray_contours_list[i]
        sprayFillObjs = spray_fills_list[i]

        transformed_pickup_point = None
        if hasattr(workpiece, "pickupPoint"):
            from backend.system.contour_matching.alignment.alignment_utils import transform_pickup_point
            transformed_pickup_point = transform_pickup_point(
                workpiece, rotation_diffs[i], translation_diffs[i], contourObj.getCentroid()
            )

        update_workpiece_data(workpiece, contourObj, sprayContourObjs, sprayFillObjs, transformed_pickup_point)

        if debug:
            data = original_data[i]
            plot_contour_alignment(
                data["target"],
                data["reference"],
                contourObj.getCentroid(),
                data["sprays"],
                workpiece,
                contourObj.get(),  # rotated and translated
                contourObj.get(),  # final
                rotation_diffs[i],
                translation_diffs[i],
                match.contour_orientation,
                sprayContourObjs,
                sprayFillObjs,
                i,
            )

        # --- Store results ---
        transformedMatchesDict["workpieces"].append(workpiece)
        transformedMatchesDict["orientations"].append(match.contour_orientation)
        transformedMatchesDict["mlConfidences"].append(getattr(match, "mlConfidence", 0.0))
        transformedMatchesDict["mlResults"].append(getattr(match, "mlResult", "UNKNOWN"))

    return transformedMatchesDict

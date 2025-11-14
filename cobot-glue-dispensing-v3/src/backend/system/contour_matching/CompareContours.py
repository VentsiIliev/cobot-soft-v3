import copy
from pathlib import Path
from typing import Any, Tuple

import numpy as np

from backend.system.contour_matching.matching.match_info import MatchInfo
from backend.system.contour_matching.matching.strategies.geometric_matching_strategy import \
    GeometricMatchingStrategy
from backend.system.contour_matching.matching.strategies.matching_strategy_interface import MatchingStrategy
from backend.system.contour_matching.matching.strategies.ml_matching_strategy import MLMatchingStrategy
from modules.shapeMatchinModelTraining.modelManager import load_latest_model

from modules.shared.shared.ContourStandartized import Contour
from backend.system.contour_matching.alignment.contour_aligner import _alignContours
from backend.system.contour_matching.matching_config import *


def get_contour_objects(entries):
    """Convert entry contour data to Contour objects."""
    objects = []
    for entry in entries:
        contour_data = entry.get("contour")
        if contour_data is not None:
            objects.append(Contour(contour_data))
    return objects


def load_model_with_fallback() -> Any:
    """
    Load the most recent trained ML model with a safe fallback mechanism.
    """
    model_dir = (
        Path(__file__).resolve().parent
        / "contourMatching"
        / "shapeMatchinModelTraining"
        / "saved_models"
    )

    if not model_dir.exists():
        print(f"⚠️ Model directory not found at {model_dir}. Trying fallback path.")
        model_dir = Path.cwd() / "system" / "contourMatching" / "shapeMatchinModelTraining" / "saved_models"

    return load_latest_model(save_dir=str(model_dir))

def prepare_data_for_alignment(matched: list[MatchInfo]):
    """
    Prepares matched data for alignment by adding contour and spray pattern objects.
    Works with MatchInfo dataclass instances.
    """
    prepared_matches = []

    for match in matched:
        # ✅ Use dataclass attributes instead of dict keys
        workpiece = copy.deepcopy(match.workpiece)
        # Prepare main contour object
        main_contour = workpiece.get_main_contour()
        contour_obj = Contour(main_contour)
        # Retrieve spray pattern data
        spray_contour_entries = workpiece.get_spray_pattern_contours()
        spray_fill_entries = workpiece.get_spray_pattern_fills()
        # Convert to Contour objects
        spray_contour_objs = get_contour_objects(spray_contour_entries)
        spray_fill_objs = get_contour_objects(spray_fill_entries)
        # ✅ Attach new fields dynamically (for alignment stage)
        match.contourObj = contour_obj
        match.sprayContourObjs = spray_contour_objs
        match.sprayFillObjs = spray_fill_objs

        prepared_matches.append(match)

    return prepared_matches


def findMatchingWorkpieces(workpieces, newContours):
    """
    Find matching workpieces based on new contours and align them.

    This function compares the contours of workpieces with the new contours and aligns them
    based on the similarity and defect thresholds.

    Returns:
        tuple: (finalMatches, noMatches, newContoursWithMatches)
    """
    print(f"🔍 ENTERING findMatchingWorkpieces with {len(workpieces)} workpieces and {len(newContours)} contours")

    # --- FIND MATCHES ---
    strategy = None
    if USE_COMPARISON_MODEL:
        model = load_model_with_fallback()
        strategy = MLMatchingStrategy(model)
    else:
        # Geometric-based
        strategy = GeometricMatchingStrategy(similarity_threshold=0.8)

    matched, noMatches, newContoursWithMatches = match_workpieces(workpieces, newContours, strategy)

    # --- PREPARE FOR ALIGNMENT ---
    new_matched = prepare_data_for_alignment(matched)

    # --- ALIGN ---
    finalMatches = _alignContours(new_matched, debug=DEBUG_ALIGN_CONTOURS)

    return finalMatches, noMatches, newContoursWithMatches



def match_workpieces(
    workpieces: list[Any],
    newContours: list[np.ndarray],
    strategy: MatchingStrategy,
) -> Tuple[list[MatchInfo], list[Contour], list[Contour]]:
    """
    Generic matching loop that uses a provided strategy (ML or geometric).
    """
    matched: list[MatchInfo] = []
    noMatches: list[Contour] = []
    matchedContours: list[Contour] = []

    for contour_data in newContours.copy():
        contour = Contour(contour_data)
        best = strategy.find_best_match(workpieces, contour)

        if best.is_match:
            match_info = MatchInfo(
                workpiece=best.workpiece,
                new_contour=contour.get(),
                centroid_diff=best.centroid_diff,
                rotation_diff=best.rotation_diff,
                contour_orientation=best.contour_angle,
                mlConfidence=best.confidence,
                mlResult=best.result,
            )
            matched.append(match_info)
            matchedContours.append(contour)
            print(f"✅ Matched contour to WP {best.workpiece_id} ({best.confidence:.2f})")
        else:
            contour._ml_result = best.result
            contour._ml_confidence = best.confidence
            contour._ml_wp_id = best.workpiece_id
            noMatches.append(contour)
            print(f"❌ No match (best={best.result}, conf={best.confidence:.2f})")

    return matched, noMatches, matchedContours







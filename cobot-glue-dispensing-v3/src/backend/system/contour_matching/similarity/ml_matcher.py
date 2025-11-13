import numpy as np
import cv2
from modules.shared.shared.ContourStandartized import Contour
from new_development.shapeMatchinModelTraining.modelManager import load_latest_model, predict_similarity

from src.backend.system.contour_matching.alignment.difference_calculator import _calculateDifferences
from src.backend.system.contour_matching.matching_config import DEBUG_CALCULATE_DIFFERENCES


def match_workpiece(workpieces_list, newContours: list[np.ndarray]):
    """
    ML-based version of _findMatches.
    Compares each new contour with known workpieces using the trained model.

    Returns:
        matched (list): List of dicts containing match info (same structure as _findMatches)
        noMatches (list): List of new contours that could not be matched
        newContourWithMatches (list): List of contours that were matched
    """

    print("Finding matches using ML model...")
    from pathlib import Path

    # Resolve saved_models relative to this file so the code doesn't rely on an absolute path
    model_dir = Path(__file__).resolve().parent / "contourMatching" / "shapeMatchinModelTraining" / "saved_models"

    # If the expected folder doesn't exist (e.g., running from a different layout), try a fallback
    if not model_dir.exists():
        print(f"Warning: model_dir {model_dir} not found. Trying fallback relative to cwd.")
        model_dir = Path.cwd() / "system" / "contourMatching" / "shapeMatchinModelTraining" / "saved_models"

    model = load_latest_model(save_dir=str(model_dir))

    matched = []
    noMatches = []
    newContourWithMatches = []

    # Work on a copy since we’ll remove processed contours
    remainingContours = newContours.copy()

    # Track ML predictions for ALL contours (even non-matches) for visualization
    ml_predictions = {}  # Store {contour_id: (result, confidence, wp_id)}

    while remainingContours:
        cnt = remainingContours.pop(0)
        cnt = Contour(cnt)  # Convert to Contour object to use the methods
        best_match = None
        best_confidence = 0.0
        best_ml_result = "DIFFERENT"
        best_wp_id = None

        for wp in workpieces_list:

            wp_contour = Contour(wp.get_main_contour())

            result, confidence, features = predict_similarity(model,
                                                       wp_contour.get(),
                                                       cnt.get())

            # CRITICAL: Prioritize SAME results over DIFFERENT, even if DIFFERENT has higher confidence
            # When multiple workpieces exist, we want the one that MATCHES, not the one with highest confidence
            if result == "SAME":
                # For SAME results, prefer higher confidence
                if best_match is None or confidence > best_confidence:
                    best_match = wp
                    best_confidence = confidence
                    best_ml_result = result
                    best_wp_id = wp.workpieceId
                    best_centroid_diff, best_rotation_diff, contourAngle = _calculateDifferences(wp_contour, cnt,DEBUG_CALCULATE_DIFFERENCES)
            else:
                # For DIFFERENT/UNCERTAIN, only track if we haven't found a SAME match yet
                if best_match is None and confidence > best_confidence:
                    best_confidence = confidence
                    best_ml_result = result
                    best_wp_id = wp.workpieceId

        # Store ML prediction for this contour
        contour_id = id(cnt.get().tobytes())
        ml_predictions[contour_id] = (best_ml_result, best_confidence, best_wp_id)

        if best_match is not None:
            # Build same structure as _findMatches() with ML confidence added
            matchDict = {
                "workpieces": best_match,
                "newContour": cnt.get(),
                "centroidDiff": best_centroid_diff,
                "rotationDiff": best_rotation_diff,
                "contourOrientation": contourAngle,
                "mlConfidence": best_confidence,  # Add ML confidence to result
                "mlResult": best_ml_result  # Add ML result (SAME/DIFFERENT/UNCERTAIN)
            }
            matched.append(matchDict)
            newContourWithMatches.append(cnt)
            print(f"✅ Matched contour to workpiece {best_match.workpieceId} (confidence={best_confidence:.2f})")

        else:
            print(f"❌ No match found for this contour (best: {best_ml_result} with {best_confidence:.1%} confidence)")
            # Attach ML prediction to the no-match contour for visualization
            cnt._ml_result = best_ml_result
            cnt._ml_confidence = best_confidence
            cnt._ml_wp_id = best_wp_id
            noMatches.append(cnt)

    return matched, noMatches, newContourWithMatches
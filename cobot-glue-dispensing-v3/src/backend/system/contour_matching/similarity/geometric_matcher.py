import cv2
import numpy as np

from modules.shared.shared.ContourStandartized import Contour
from src.backend.system.contour_matching.alignment.difference_calculator import _calculateDifferences
from src.backend.system.contour_matching.debug.plot_generator import _create_debug_plot
from src.backend.system.contour_matching.matching_config import DEBUG_SIMILARITY, SIMILARITY_THRESHOLD
from src.backend.system.contour_matching.utils import _remove_contour


def _findMatches(newContours, workpieces):
    print(f"Finding matches")
    matched = []
    noMatches = []
    newContourWithMatches = []
    count = 0

    for contour in newContours.copy():
        contour = Contour(contour)
        best_match = None
        best_similarity = -1
        best_centroid_diff = None
        best_rotation_diff = None
        contourAngle = None

        for workpiece in workpieces:
            workpieceContour = Contour(workpiece.get_main_contour())
            if workpieceContour is None:
                continue

            similarity = _getSimilarity(workpieceContour.get(),
                                        contour.get(),
                                        debug=DEBUG_SIMILARITY)

            if similarity > SIMILARITY_THRESHOLD and similarity > best_similarity:
                best_match = workpiece
                best_similarity = similarity
                best_centroid_diff, best_rotation_diff, contourAngle = _calculateDifferences(workpieceContour, contour)

        if best_match is not None:
            # Store matched contour
            newContourWithMatches.append(contour.get())
            matchDict = {
                "workpieces": best_match,
                "newContour": contour.get(),
                "centroidDiff": best_centroid_diff,
                "rotationDiff": best_rotation_diff,
                "contourOrientation": contourAngle
            }
            matched.append(matchDict)
            _remove_contour(newContours, contour.get())

            # --- DRAW MATCH ON FRESH CANVAS ---
            canvas = np.ones((720, 1280, 3), dtype=np.uint8) * 255  # white canvas
            workpieceContour = Contour(best_match.get_main_contour())

            workpieceContour.draw(canvas, color=(0, 255, 0), thickness=2)  # Workpiece in GREEN
            cv2.putText(canvas, f"WP {best_match.workpieceId}", tuple(workpieceContour.getCentroid()), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

            contour.draw(canvas, color=(0, 0, 255), thickness=2)  # New contour in RED
            cv2.putText(canvas, "NEW", tuple(contour.getCentroid()), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

            # Add similarity score
            cv2.putText(canvas, f"Similarity: {best_similarity:.1f}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2)

            # Highlight match
            cv2.putText(canvas, "MATCH!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 3)
            cv2.imwrite(f"findMatches_MATCH_{count}.png", canvas)
            count += 1
        else:
            print(f"    No match found for this contour")

    noMatches = newContours
    return matched, noMatches, newContourWithMatches

# def _getSimilarity(contour1, contour2, debug=True):
#     """
#     Simplified contour similarity test using only Hu moments.
#     Returns a percentage similarity score.
#     """
#     MOMENT_THRESHOLD = 0.05  # Only used for debug tagging
#
#     contour1 = np.array(contour1, dtype=np.float32)
#     contour2 = np.array(contour2, dtype=np.float32)
#     print(f"Calculating similarity between contours of lengths {len(contour1)} and {len(contour2)}")
#     # Compute Hu moments distance
#     moment_diff = cv2.matchShapes(contour1, contour2, cv2.CONTOURS_MATCH_I1, 0.0)
#     print(f"raw_similarity (moment diff): {moment_diff:.4f}")
#     similarity_percent = (1 - moment_diff) * 100
#     # moment_diff = np.clip(moment_diff, 0.0, 1.0)
#     # similarity_percent = float(np.clip(100 * np.exp(-moment_diff * 10), 0, 100))
#
#     # --- Area penalty ---
#     area1 = cv2.contourArea(contour1)
#     area2 = cv2.contourArea(contour2)
#     area_diff= abs(area1-area2)
#     area_ratio= 0
#     if area1 > 0 and area2 > 0:
#         area_ratio = min(area1, area2) / max(area1, area2)
#
#         AREA_TOLERANCE = 0.90  # Allow 10% difference
#         if area_ratio < AREA_TOLERANCE:
#             # Penalize only if area difference exceeds tolerance
#             similarity_percent *= area_ratio ** 2  # square makes it harsher
#     else:
#         similarity_percent = 0
#
#     similarity_percent = float(np.clip(similarity_percent, 0, 100))
#
#     # Store metrics for debugging
#     metrics = {
#         "moment_diff": moment_diff,
#         "area_ratio":area_ratio,
#         "area_diff":area_diff,
#         "similarity_percent": similarity_percent,
#     }
#
#     if debug:
#         _create_debug_plot(contour1, contour2, metrics)
#     print(f"Similarity Score: {similarity_percent:.2f}% (Moment Diff: {moment_diff:.4f})")
#     return similarity_percent

def _getSimilarity(contour1, contour2, debug=True):
    """
    Simplified contour similarity test using only area difference.
    Returns a percentage similarity score based on area ratio.
    """
    contour1 = np.array(contour1, dtype=np.float32)
    contour2 = np.array(contour2, dtype=np.float32)

    print(f"Calculating similarity between contours of lengths {len(contour1)} and {len(contour2)}")

    # Compute areas
    area1 = cv2.contourArea(contour1)
    area2 = cv2.contourArea(contour2)
    area_diff = abs(area1 - area2)

    if area1 > 0 and area2 > 0:
        # Compute area ratio
        area_ratio = min(area1, area2) / max(area1, area2)
        similarity_percent = area_ratio * 100
    else:
        area_ratio = 0
        similarity_percent = 0

    # Clip to [0, 100]
    similarity_percent = float(np.clip(similarity_percent, 0, 100))

    # Store metrics for debugging
    metrics = {
        "area1": area1,
        "area2": area2,
        "area_diff": area_diff,
        "area_ratio": area_ratio,
        "similarity_percent": similarity_percent,
        "moment_diff": 0
    }

    if debug:
        _create_debug_plot(contour1, contour2, metrics)

    print(f"Similarity Score: {similarity_percent:.2f}% (Area Diff: {area_diff:.2f})")
    return similarity_percent




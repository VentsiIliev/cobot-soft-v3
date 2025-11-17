from typing import Any

import cv2
import numpy as np

from backend.system.contour_matching.debug.plot_generator import _create_debug_plot
from backend.system.contour_matching.matching.best_match_result import BestMatchResult
from modules.shared.core.ContourStandartized import Contour


class GeometricMatchingStrategy:
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    def find_best_match(
        self, workpieces: list[Any], contour: Contour
    ) -> BestMatchResult:
        from backend.system.contour_matching.alignment.difference_calculator import _calculateDifferences

        best = BestMatchResult(workpiece=None, confidence=0.0, result="DIFFERENT")

        for wp in workpieces:
            wp_contour = Contour(wp.get_main_contour())
            similarity = self._getSimilarity(wp_contour.get(), contour.get())

            if similarity > self.similarity_threshold * 100 and similarity > best.confidence:
                centroid_diff, rotation_diff, contour_angle = _calculateDifferences(wp_contour, contour)
                best = BestMatchResult(
                    workpiece=wp,
                    confidence=similarity,
                    result="SAME",
                    centroid_diff=centroid_diff,
                    rotation_diff=rotation_diff,
                    contour_angle=contour_angle,
                    workpiece_id=getattr(wp, "workpieceId", None),
                )

        return best

    def _getSimilarity(self,contour1, contour2, debug=True):
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

    def debug_draw(self,best_match, contour, best_similarity, count):
        # --- DRAW MATCH ON FRESH CANVAS ---
        canvas = np.ones((720, 1280, 3), dtype=np.uint8) * 255  # white canvas
        workpieceContour = Contour(best_match.get_main_contour())

        workpieceContour.draw(canvas, color=(0, 255, 0), thickness=2)  # Workpiece in GREEN
        cv2.putText(canvas, f"WP {best_match.workpieceId}", tuple(workpieceContour.getCentroid()),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 255, 0), 2)

        contour.draw(canvas, color=(0, 0, 255), thickness=2)  # New contour in RED
        cv2.putText(canvas, "NEW", tuple(contour.getCentroid()), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Add similarity score
        cv2.putText(canvas, f"Similarity: {best_similarity:.1f}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        # Highlight match
        cv2.putText(canvas, "MATCH!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)
        cv2.imwrite(f"findMatches_MATCH_{count}.png", canvas)


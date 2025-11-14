from typing import Any

from backend.system.contour_matching.matching.best_match_result import BestMatchResult
from modules.shared.shared.ContourStandartized import Contour


class MLMatchingStrategy:
    def __init__(self, model: Any):
        self.model = model

    def find_best_match(
        self, workpieces: list[Any], contour: Contour
    ) -> BestMatchResult:
        from backend.system.contour_matching.alignment.difference_calculator import _calculateDifferences
        from backend.system.contour_matching.matching_config import DEBUG_CALCULATE_DIFFERENCES
        from new_development.shapeMatchinModelTraining.modelManager import predict_similarity

        best = BestMatchResult(workpiece=None, confidence=0.0, result="DIFFERENT")

        for wp in workpieces:
            wp_contour = Contour(wp.get_main_contour())
            result, confidence, _ = predict_similarity(self.model, wp_contour.get(), contour.get())
            wp_id = getattr(wp, "workpieceId", None)

            if result == "SAME":
                if best.workpiece is None or confidence > best.confidence:
                    centroid_diff, rotation_diff, contour_angle = _calculateDifferences(
                        wp_contour, contour, DEBUG_CALCULATE_DIFFERENCES
                    )
                    best = BestMatchResult(
                        workpiece=wp,
                        confidence=confidence,
                        result=result,
                        centroid_diff=centroid_diff,
                        rotation_diff=rotation_diff,
                        contour_angle=contour_angle,
                        workpiece_id=wp_id,
                    )
            elif best.workpiece is None and confidence > best.confidence:
                best = BestMatchResult(
                    workpiece=None,
                    confidence=confidence,
                    result=result,
                    workpiece_id=wp_id,
                )

        return best


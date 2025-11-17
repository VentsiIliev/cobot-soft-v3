from typing import Protocol, Any

from backend.system.contour_matching.matching.best_match_result import BestMatchResult
from modules.shared.core.ContourStandartized import Contour


class MatchingStrategy(Protocol):
    """Interface for contour-workpiece matching strategies."""
    def find_best_match(
        self, workpieces: list[Any], contour: Contour
    ) -> "BestMatchResult":
        ...

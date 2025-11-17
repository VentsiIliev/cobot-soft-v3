from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from modules.shared.core.ContourStandartized import Contour


@dataclass
class MatchInfo:
    """Stores information about a matched contour and its corresponding workpiece."""
    workpiece: Any
    new_contour: np.ndarray
    centroid_diff: Optional[Any]
    rotation_diff: Optional[Any]
    contour_orientation: Optional[float]

    # Optional fields added later
    contourObj: Optional[Contour] = None
    sprayContourObjs: Optional[list[Contour]] = None
    sprayFillObjs: Optional[list[Contour]] = None
    mlConfidence: float = 0.0
    mlResult: str = "UNKNOWN"
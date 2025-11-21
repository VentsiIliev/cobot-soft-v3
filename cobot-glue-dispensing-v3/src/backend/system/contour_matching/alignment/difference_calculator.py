import numpy as np
from modules.shared.core.ContourStandartized import Contour
# from backend.system.contour_matching.debug.plot_generator import get_similarity_debug_plot
from pathlib import Path

def _calculateDifferences(workpieceContour: Contour, contour: Contour, debug: bool = False):
    """
    Calculate the centroid and rotation differences between two contours.

    Args:
        workpieceContour (Contour): Contour object representing the workpiece contour.
        contour (Contour): Contour object representing the new contour.
        debug (bool): Whether to generate debug plots.

    Returns:
        tuple: (centroidDiff, rotationDiff, contourAngle)
    """
    contour = _ensure_closed(contour)

    # --- Compute centroids ---
    workpieceCentroid = workpieceContour.getCentroid()
    contourCentroid = contour.getCentroid()
    centroidDiff = np.array(contourCentroid) - np.array(workpieceCentroid)

    # --- Compute rotation difference ---
    wpAngle = workpieceContour.getOrientation()
    contourAngle = contour.getOrientation()
    rotationDiff = (contourAngle - wpAngle + 180) % 360 - 180  # Normalize to [-180, 180]

    # --- Optional debug output ---
    if debug:
        _debug_contours(workpieceContour, contour, wpAngle, contourAngle, rotationDiff,
                        workpieceCentroid, contourCentroid, centroidDiff)

    return centroidDiff, rotationDiff, contourAngle


def _ensure_closed(contour: Contour) -> Contour:
    """
    Ensure the contour is closed (first point = last point).
    """
    points = contour.get()
    if not np.array_equal(points[0], points[-1]):
        closed_points = np.vstack([points, points[0].reshape(1, 1, 2)])
        return Contour(closed_points)
    return contour


def _debug_contours(workpieceContour, contour, wpAngle, contourAngle, rotationDiff,
                    workpieceCentroid, contourCentroid, centroidDiff):
    """
    Handle debug output for contour differences.
    """
    debug_dir = Path(__file__).resolve().parent / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    file_path = debug_dir / "contour_debug.txt"

    with file_path.open("w", encoding="utf-8") as f:
        f.write(f"Workpiece orientation: {wpAngle}\n")
        f.write(f"Workpiece points: {workpieceContour.get()}\n")
        f.write(f"Contour orientation: {contourAngle}\n")
        f.write(f"Contour points: {contour.get()}\n")
        f.write(f"Calculated rotation difference: {rotationDiff}\n")

    print(f"Contour debug written to: {file_path}")

    # Optional debug plot
    get_similarity_debug_plot(
        workpieceContour, contour, workpieceCentroid, contourCentroid,
        wpAngle, contourAngle, centroidDiff, rotationDiff
    )

import numpy as np
from modules.shared.shared.ContourStandartized import Contour
from src.backend.system.contour_matching.debug.plot_generator import get_similarity_debug_plot


def _calculateDifferences(workpieceContour, contour,debug=False):
    """
       Calculate the centroid and rotation differences between two contours.

       Args:
           workpieceContour (Contour): Contour object representing the workpieces contour.
           contour (Contour): Contour object representing the new contour.

       Returns:
           tuple: Centroid difference (numpy array) and rotation difference (float).
       """

    # check if the new contour last point is different then the first point if so close the contour
    if not np.array_equal(contour.get()[0], contour.get()[-1]):
        print("    Closing contour by adding first point to the end")
        closed_points = np.vstack([
            contour.get(),
            contour.get()[0].reshape(1, 1, 2)
        ])

        contour = Contour(closed_points)

    workpieceCentroid = workpieceContour.getCentroid()
    contourCentroid = contour.getCentroid()
    centroidDiff = np.array(contourCentroid) - np.array(workpieceCentroid)
    wpAngle = workpieceContour.getOrientation()
    contourAngle = contour.getOrientation()
    rotationDiff = contourAngle - wpAngle
    rotationDiff = (rotationDiff + 180) % 360 - 180  # Normalize to [-180, 180]

    handle_debug(debug, wpAngle, workpieceContour, contourAngle, contour, rotationDiff,workpieceCentroid, contourCentroid, centroidDiff)



    return centroidDiff, rotationDiff, contourAngle

def handle_debug(debug, wpAngle, workpieceContour, contourAngle, contour, rotationDiff,workpieceCentroid, contourCentroid, centroidDiff):

    # Debug plotting for _calculateDifferences
    if debug:
        from pathlib import Path

        # ... after computing wpAngle, contourAngle, rotationDiff ...
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
        get_similarity_debug_plot(workpieceContour, contour, workpieceCentroid, contourCentroid, wpAngle, contourAngle,
                                  centroidDiff, rotationDiff)
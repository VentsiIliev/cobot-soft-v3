import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtCore import QPointF


from modules.shared.core.contour_editor.BezierSegmentManager import Segment


def contour_to_bezier(contour, control_point_ratio=0.5, close_contour=True):
    """
    Converts a contour to a single Segment with Bezier control points.

    Args:
        contour (list or numpy array): OpenCV-style contour [[x, y]].
        control_point_ratio (float): Where to place the control point between two anchor points.
        close_contour (bool): Whether to close the contour if it's not already.

    Returns:
        List[Segment]: A single Segment object containing all anchor and control points.
    """
    if len(contour) < 2:
        return []

    # Check for closure if requested
    if close_contour:
        start_pt = contour[0][0]
        end_pt = contour[-1][0]
        if not np.allclose(start_pt, end_pt):  # Check if already closed
            contour = np.vstack([contour, [contour[0]]])  # Close it by adding first point to end

    segment = Segment()

    # Add anchor points
    for pt in contour:
        point = QPointF(pt[0][0], pt[0][1])
        segment.add_point(point)

    # Add control points between each pair of consecutive anchor points
    for i in range(len(segment.points) - 1):
        p0 = segment.points[i]
        p1 = segment.points[i + 1]
        control_x = (1 - control_point_ratio) * p0.x() + control_point_ratio * p1.x()
        control_y = (1 - control_point_ratio) * p0.y() + control_point_ratio * p1.y()
        control_pt = QPointF(control_x, control_y)
        segment.add_control_point(i, control_pt)

    return [segment]


def plot_contour_and_bezier(contour, bezier_segments):
    plt.figure(figsize=(10, 6))
    contour_points = np.array([point[0] for point in contour], dtype=np.int32)
    plt.plot(contour_points[:, 0], contour_points[:, 1], label="Contour", color="blue", marker="o")

    for segment in bezier_segments:
        points = segment.points
        controls = segment.controls
        n = len(points)

        for i in range(n):
            p0 = points[i]
            p1 = points[(i + 1) % n]  # Wrap around
            c = controls[i]

            bezier_points = []
            for t in np.linspace(0, 1, 100):
                x = (1 - t) ** 2 * p0.x() + 2 * (1 - t) * t * c.x() + t ** 2 * p1.x()
                y = (1 - t) ** 2 * p0.y() + 2 * (1 - t) * t * c.y() + t ** 2 * p1.y()
                bezier_points.append([x, y])

            bezier_points = np.array(bezier_points)
            plt.plot(bezier_points[:, 0], bezier_points[:, 1], color="red")

    plt.title("Contour and Bezier Curves")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.gca().invert_yaxis()
    plt.legend(loc="upper right")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# # Example usage:
# # OpenCV contour obtained from cv2.findContours() (as a numpy array of points)
# contour = np.array([[[100, 100]], [[200, 100]], [[200, 200]], [[100, 200]]], dtype=np.int32)
#
# # Convert contour to Bezier
# bezier_segments = contour_to_bezier(contour)
#
# # Plot the contour and Bezier curves
# plot_contour_and_bezier(contour, bezier_segments)

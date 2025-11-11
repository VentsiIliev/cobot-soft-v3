import numpy as np
from PyQt6.QtCore import QPointF


def get_significant_points(points, num_points=None):
    """
    Returns the most significant points based on curvature.
    If num_points is None or >= len(points), returns all points.
    """
    if len(points) <= 2:
        return points
    scores = curvature_scores(points)
    if num_points is None or num_points >= len(points):
        return points
    indices = np.argsort(-scores)  # descending order
    return [points[i] for i in indices[:num_points]]

def curvature_scores(points):
    if len(points) < 3:
        # Not enough points for curvature, return zeros
        return np.zeros(len(points))

    pts = np.array([[p.x(), p.y()] for p in points], dtype=np.float64)
    diff1 = np.diff(pts, axis=0)  # shape (N-1, 2)
    diff2 = np.diff(diff1, axis=0)  # shape (N-2, 2)

    # 2D cross product scalar
    cross = diff1[:-1, 0] * diff2[:, 1] - diff1[:-1, 1] * diff2[:, 0]
    curvature = np.abs(cross) / (np.linalg.norm(diff1[:-1], axis=1) ** 3 + 1e-6)

    # pad to match length of points
    scores = np.pad(curvature, (1, 1), mode='edge')
    return scores

def get_visible_points(points,scale_factor):
    """
    Determine how many points to show based on current zoom level.
    """
    min_points = 5
    max_points = len(points)
    # linear scaling: fraction of points to show
    fraction = min(1.0, scale_factor / 5.0)  # adjust denominator for zoom sensitivity
    num_points = int(min_points + fraction * (max_points - min_points))
    return get_significant_points(points, num_points)

def _declutter_points_screen_space(painter, points,width,height):
    transform = painter.transform()
    screen_pts = np.array([[transform.map(pt).x(), transform.map(pt).y()] for pt in points])
    if len(screen_pts) == 0:
        return []

    min_dist = 20  # pixels between visible points
    w_cells = int(width // min_dist) + 2
    h_cells = int(height // min_dist) + 2
    occupied = np.zeros((w_cells, h_cells), dtype=bool)

    visible = []
    for x, y in screen_pts:
        gx = int(x // min_dist)
        gy = int(y // min_dist)

        # Clamp to valid range
        gx = max(0, min(gx, w_cells - 1))
        gy = max(0, min(gy, h_cells - 1))

        if not occupied[gx, gy]:
            visible.append(QPointF(x, y))
            occupied[gx, gy] = True

    return visible

def _cluster_screen_points(painter, points,cluster_distance_px):
    """
    Merge points that fall close together in screen space.
    Returns centroids in *screen space*, not mapped back.
    """
    if not points:
        return []

    transform = painter.transform()
    screen_pts = np.array([[transform.map(pt).x(), transform.map(pt).y()] for pt in points])
    if len(screen_pts) == 0:
        return []

    # Grid-based clustering in screen space
    grid_size = cluster_distance_px
    grid = {}
    for x, y in screen_pts:
        gx, gy = int(x // grid_size), int(y // grid_size)
        grid.setdefault((gx, gy), []).append((x, y))

    # Centroids (in screen space)
    clustered = [QPointF(np.mean(xs), np.mean(ys)) for xs, ys in [list(zip(*pts)) for pts in grid.values()]]
    return clustered
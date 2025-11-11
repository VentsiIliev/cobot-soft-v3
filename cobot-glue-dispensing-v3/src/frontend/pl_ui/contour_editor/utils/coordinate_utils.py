from PyQt6.QtCore import QPointF


def map_to_image_space(pos,translation,scale_factor):
    point = (pos - translation) / scale_factor
    return point

def calculate_distance(p1: QPointF, p2: QPointF) -> float:
    """Compute Euclidean distance between two image-space points."""
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    return (dx ** 2 + dy ** 2) ** 0.5


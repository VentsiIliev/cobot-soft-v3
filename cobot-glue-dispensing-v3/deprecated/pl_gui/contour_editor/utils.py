import numpy as np
import cv2
from PyQt6.QtGui import QImage, QPixmap
from shapely.geometry import Polygon, LineString

def zigZag(contour, spacing):
    # Convert contour to a Shapely polygon
    contour_poly = Polygon(contour.squeeze())
    if not contour_poly.is_valid:
        contour_poly = contour_poly.buffer(0)  # Fix self-intersections if any

    # Get rotated bounding box
    bbox = cv2.minAreaRect(contour)
    box = cv2.boxPoints(bbox)
    center = np.mean(box, axis=0)
    width, height = bbox[1]
    angle = bbox[2]

    if width < height:
        shorter_dim = width
        longer_dim = height
        vertical = True
    else:
        shorter_dim = height
        longer_dim = width
        vertical = False

    # Generate zigzag lines in the bbox's local frame (unrotated)
    lines = []
    for i in range(0, int(shorter_dim), spacing):
        if vertical:
            x = -shorter_dim / 2 + i
            pt1 = [x, -longer_dim / 2]
            pt2 = [x, longer_dim / 2]
        else:
            y = -shorter_dim / 2 + i
            pt1 = [-longer_dim / 2, y]
            pt2 = [longer_dim / 2, y]
        lines.append((pt1, pt2))

    # Rotate and translate lines to match the actual bbox orientation
    theta = np.radians(angle)
    rot_matrix = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta), np.cos(theta)]
    ])

    final_coords = []
    for pt1, pt2 in lines:
        # Rotate
        pt1_rot = rot_matrix @ np.array(pt1) + center
        pt2_rot = rot_matrix @ np.array(pt2) + center

        # Clip line with actual contour
        line = LineString([pt1_rot, pt2_rot])
        clipped = line.intersection(contour_poly)

        # Add resulting points or line segments
        if clipped.is_empty:
            continue
        elif clipped.geom_type == "LineString":
            final_coords.extend(list(clipped.coords))
        elif clipped.geom_type == "MultiLineString":
            for part in clipped:
                final_coords.extend(list(part.coords))

    return np.array(final_coords)


def shrink_contour_points(contour_points, shrink_amount):
    """
    Shrink a polygon defined by contour_points inward by shrink_amount.
    Returns the new contour points as a numpy array.
    """
    from shapely.geometry import Polygon

    if len(contour_points) < 3:
        return None

    poly = Polygon(contour_points)
    if not poly.is_valid:
        poly = poly.buffer(0)

    shrunk_poly = poly.buffer(-shrink_amount)
    if shrunk_poly.is_empty:
        return None

    if shrunk_poly.geom_type == "MultiPolygon":
        shrunk_poly = max(shrunk_poly.geoms, key=lambda p: p.area)

    return np.array(shrunk_poly.exterior.coords)

def qpixmap_to_cv(qpixmap):
    qimage = qpixmap.toImage().convertToFormat(QImage.Format.Format_RGB888)
    width = qimage.width()
    height = qimage.height()
    ptr = qimage.bits()
    ptr.setsize(height * width * 3)
    arr = np.array(ptr, dtype=np.uint8).reshape((height, width, 3))
    return arr

def create_light_gray_pixmap(width=1280, height=720):
    # Create a light gray image (RGB)
    gray_value = 200  # 0=black, 255=white
    img = np.full((height, width, 3), gray_value, dtype=np.uint8)
    # Convert numpy image to QImage
    qimage = QImage(img.data, width, height, 3 * width, QImage.Format.Format_RGB888)

    # Convert QImage to QPixmap
    pixmap = QPixmap.fromImage(qimage)

    return pixmap
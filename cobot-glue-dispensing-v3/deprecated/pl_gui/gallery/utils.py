from PyQt6.QtGui import QPainter, QImage, QPen
from PyQt6.QtCore import QPointF, Qt
# from API.shared.workpiece.WorkpieceService import WorkpieceService
from deprecated.pl_gui.gallery.ThumbnailWidget import ThumbnailWidget
from PyQt6.QtGui import QPixmap
from datetime import datetime

def generate_pixmap_from_contour_and_spray(contour, spray_pattern, size=(800, 800), margin=20):
    width, height = size
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)

    # Collect all points from contour segments
    all_points = []
    for seg in contour:
        if isinstance(seg, dict) and "contour" in seg:
            all_points.extend([pt[0] for pt in seg["contour"]])

    # Collect all points from spray_pattern segments
    for paths in spray_pattern.values():
        for seg in paths:
            if isinstance(seg, dict) and "contour" in seg:
                all_points.extend([pt[0] for pt in seg["contour"]])

    if not all_points:
        painter.end()
        return QPixmap.fromImage(image)

    xs = [pt[0] for pt in all_points]
    ys = [pt[1] for pt in all_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    shape_width = max_x - min_x
    shape_height = max_y - min_y

    # Compute scale factor to fit shape inside image with margin
    scale_x = (width - 2 * margin) / shape_width if shape_width > 0 else 1
    scale_y = (height - 2 * margin) / shape_height if shape_height > 0 else 1
    scale = min(scale_x, scale_y)

    # Center of shape
    shape_center_x = min_x + shape_width / 2
    shape_center_y = min_y + shape_height / 2

    # Center of image
    image_center_x = width / 2
    image_center_y = height / 2

    def transform(pt):
        # Translate to center, scale, flip Y, then shift to image center
        x = (pt[0] - shape_center_x) * scale + image_center_x
        y = (shape_center_y - pt[1]) * scale + image_center_y  # flipped Y
        return QPointF(x, y)

    # --- Draw contour ---
    pen_contour = QPen(Qt.GlobalColor.black)
    pen_contour.setWidth(2)
    painter.setPen(pen_contour)

    contour_pts = []
    for seg in contour:
        if isinstance(seg, dict) and "contour" in seg:
            contour_pts.extend([transform(pt[0]) for pt in seg["contour"]])
    if contour_pts:
        for i in range(len(contour_pts) - 1):
            painter.drawLine(contour_pts[i], contour_pts[i + 1])
        painter.drawLine(contour_pts[-1], contour_pts[0])
    # --- Draw spray patterns ---
    colors = {
        "Contour": Qt.GlobalColor.red,
        "Fill": Qt.GlobalColor.blue
    }

    for key, paths in spray_pattern.items():
        pen = QPen(colors.get(key, Qt.GlobalColor.darkGray))
        pen.setWidth(1)
        painter.setPen(pen)
        for seg in paths:
            if isinstance(seg, dict) and "contour" in seg:
                points = [transform(pt[0]) for pt in seg["contour"]]
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])

    painter.end()
    return QPixmap.fromImage(image)

def create_thumbnail_widget_from_workpiece(workpiece, filename="Untitled", timestamp=None):
    """
    Creates a ThumbnailWidget from a given Workpiece instance.

    Args:
        workpiece (Workpiece): The Workpiece instance with contour and sprayPattern.
        filename (str): Display name (e.g. file name or workpiece name).
        timestamp (str): Last modified timestamp. If None, uses current time.

    Returns:
        ThumbnailWidget: A ready-to-use thumbnail widget.
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Generate the pixmap using contour and spray pattern
    contour = workpiece.contour
    spray_pattern = workpiece.sprayPattern
    pixmap = generate_pixmap_from_contour_and_spray(contour, spray_pattern, size=(800, 800))

    return ThumbnailWidget(filename=filename, pixmap=pixmap, timestamp=timestamp)
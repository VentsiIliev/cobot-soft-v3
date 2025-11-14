import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QPainter, QImage, QPen, QPixmap
from PyQt6.QtCore import QSize, QPointF, Qt
# from shared.shared.workpiece.WorkpieceService import WorkpieceService
from frontend.pl_ui.ui.windows.gallery.ThumbnailWidget import ThumbnailWidget
from PyQt6.QtGui import QPixmap
from datetime import datetime

def generate_pixmap_from_contour_and_spray(contour, spray_pattern, pickup_point=None, size=(800, 800), margin=20):
    width, height = size
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)

    # Extract main contour points for bounding box calculation
    main_contour_points = []
    print(f"Generating pixmap with contour type: {type(contour)}, contour shape: {getattr(contour, 'shape', 'no shape')}, contour: {contour}")
    print(f"Spray_pattern keys: {list(spray_pattern.keys()) if spray_pattern else 'None'}, pickup_point: {pickup_point}")
    
    # Handle main contour - it should be the actual contour points, not segments
    if contour is not None and len(contour) > 0:
        print(f"Contour has {len(contour)} elements")
        # Contour is typically a numpy array of points
        if hasattr(contour, '__iter__'):
            try:
                # Handle different contour formats
                if hasattr(contour, 'shape'):
                    print(f"Contour shape: {contour.shape}")
                    if len(contour.shape) == 3:  # (n, 1, 2) format
                        main_contour_points.extend([pt[0] for pt in contour])
                        print(f"Added {len(contour)} points from (n,1,2) format")
                    elif len(contour.shape) == 2:  # (n, 2) format
                        main_contour_points.extend(contour)
                        print(f"Added {len(contour)} points from (n,2) format")
                else:
                    print("Contour has no shape attribute, treating as list/tuple")
                    main_contour_points.extend(contour)
            except Exception as e:
                print(f"Error processing contour: {e}")
                # Fallback for other formats
                if isinstance(contour, (list, tuple)):
                    main_contour_points.extend(contour)
                    print(f"Added {len(contour)} points from fallback list/tuple")
    
    print(f"Extracted {len(main_contour_points)} main contour points")

    # Collect all points for bounding box calculation (main contour + spray patterns)
    all_points = []
    
    # Add main contour points
    if main_contour_points:
        valid_points = [pt for pt in main_contour_points if hasattr(pt, '__len__') and len(pt) >= 2]
        all_points.extend(valid_points)
    
    # Add spray pattern points
    if spray_pattern:
        for paths in spray_pattern.values():
            if paths:  # Check if paths exist
                for seg in paths:
                    if isinstance(seg, dict) and "contour" in seg and seg["contour"] is not None:
                        spray_contour = seg["contour"]
                        if hasattr(spray_contour, '__iter__'):
                            try:
                                if len(spray_contour.shape) == 3:  # (n, 1, 2) format
                                    all_points.extend([pt[0] for pt in spray_contour])
                                elif len(spray_contour.shape) == 2:  # (n, 2) format
                                    all_points.extend(spray_contour)
                            except:
                                if isinstance(spray_contour, (list, tuple)):
                                    all_points.extend(spray_contour)
    
    if not all_points:
        painter.end()
        return QPixmap.fromImage(image)
    
    # Use all points for bounding box calculation
    try:
        xs = [pt[0] for pt in all_points]
        ys = [pt[1] for pt in all_points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
    except Exception as e:
        print(f"Error processing bounding box points: {e}")
        painter.end()
        return QPixmap.fromImage(image)

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
        # This transformation preserves relative positions between main contour and spray patterns
        x = (pt[0] - shape_center_x) * scale + image_center_x
        y = (shape_center_y - pt[1]) * scale + image_center_y  # flipped Y
        return QPointF(x, y)

    # --- Draw main contour ---
    pen_contour = QPen(Qt.GlobalColor.black)
    pen_contour.setWidth(3)  # Slightly thicker for main contour
    painter.setPen(pen_contour)

    print(f"About to draw main contour. Contour is None: {contour is None}, Contour length: {len(contour) if contour is not None else 'N/A'}")
    if contour is not None and len(contour) > 0:
        contour_pts = []
        try:
            # Handle different contour formats
            if hasattr(contour, 'shape') and len(contour.shape) == 3:  # (n, 1, 2) format
                contour_pts = [transform(pt[0]) for pt in contour]
                print(f"Drawing main contour with {len(contour_pts)} points from (n,1,2) format")
            elif hasattr(contour, 'shape') and len(contour.shape) == 2:  # (n, 2) format  
                contour_pts = [transform(pt) for pt in contour]
                print(f"Drawing main contour with {len(contour_pts)} points from (n,2) format")
            elif isinstance(contour, (list, tuple)):
                contour_pts = [transform(pt) for pt in contour]
                print(f"Drawing main contour with {len(contour_pts)} points from list/tuple format")
                
            # Draw main contour
            if contour_pts and len(contour_pts) > 1:
                print(f"Drawing {len(contour_pts)} contour lines")
                for i in range(len(contour_pts) - 1):
                    painter.drawLine(contour_pts[i], contour_pts[i + 1])
                # Close the contour
                painter.drawLine(contour_pts[-1], contour_pts[0])
                print("Main contour drawing completed")
            else:
                print(f"Not enough contour points to draw: {len(contour_pts) if contour_pts else 0}")
        except Exception as e:
            print(f"Warning: Failed to draw main contour: {e}")
    else:
        print("No main contour to draw")
    # --- Draw spray patterns ---
    colors = {
        "Contour": Qt.GlobalColor.red,
        "Fill": Qt.GlobalColor.blue
    }

    if spray_pattern:
        for key, paths in spray_pattern.items():
            if paths:  # Check if paths exist
                pen = QPen(colors.get(key, Qt.GlobalColor.darkGray))
                pen.setWidth(2 if key == "Contour" else 1)  # Thicker for spray contours
                painter.setPen(pen)
                
                for seg in paths:
                    if isinstance(seg, dict) and "contour" in seg and seg["contour"] is not None:
                        spray_contour = seg["contour"]
                        points = []
                        
                        try:
                            # Handle different spray contour formats
                            if hasattr(spray_contour, 'shape'):
                                if len(spray_contour.shape) == 3:  # (n, 1, 2) format
                                    points = [transform(pt[0]) for pt in spray_contour]
                                elif len(spray_contour.shape) == 2:  # (n, 2) format
                                    points = [transform(pt) for pt in spray_contour]
                            elif isinstance(spray_contour, (list, tuple)):
                                points = [transform(pt) for pt in spray_contour]
                            
                            # Draw spray pattern lines
                            if points and len(points) > 1:
                                for i in range(len(points) - 1):
                                    painter.drawLine(points[i], points[i + 1])
                                    
                        except Exception as e:
                            print(f"Warning: Failed to draw spray pattern {key}: {e}")

    # --- Draw pickup point if provided ---
    if pickup_point is not None:
        try:
            # Parse pickup point string if needed
            if isinstance(pickup_point, str) and ',' in pickup_point:
                x_str, y_str = pickup_point.split(',')
                pickup_x, pickup_y = float(x_str), float(y_str)
            elif isinstance(pickup_point, (list, tuple)) and len(pickup_point) >= 2:
                pickup_x, pickup_y = pickup_point[0], pickup_point[1]
            else:
                pickup_x = pickup_y = None
                
            if pickup_x is not None and pickup_y is not None:
                pickup_transformed = transform([pickup_x, pickup_y])
                
                # Draw pickup point as orange circle with crosshair
                pen_pickup = QPen(Qt.GlobalColor.darkYellow)
                pen_pickup.setWidth(3)
                painter.setPen(pen_pickup)
                painter.setBrush(Qt.GlobalColor.yellow)
                
                # Draw circle
                circle_radius = 8
                painter.drawEllipse(pickup_transformed, circle_radius, circle_radius)
                
                # Draw crosshair
                painter.drawLine(pickup_transformed.x() - 6, pickup_transformed.y(), 
                               pickup_transformed.x() + 6, pickup_transformed.y())
                painter.drawLine(pickup_transformed.x(), pickup_transformed.y() - 6,
                               pickup_transformed.x(), pickup_transformed.y() + 6)
                               
        except Exception as e:
            print(f"Warning: Failed to draw pickup point: {e}")

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

    # Extract the main contour data using the workpiece's own method
    contour = None
    if hasattr(workpiece, 'get_main_contour'):
        try:
            contour = workpiece.get_main_contour()
        except Exception as e:
            print(f"Error getting main contour: {e}")
            contour = None
    elif hasattr(workpiece, 'contour') and workpiece.contour is not None:
        if isinstance(workpiece.contour, dict) and "contour" in workpiece.contour:
            contour = workpiece.contour["contour"]
        else:
            contour = workpiece.contour

    # Extract spray pattern - it should be a dict with keys like "Contour", "Fill"
    spray_pattern = None
    if hasattr(workpiece, 'sprayPattern') and workpiece.sprayPattern is not None:
        if isinstance(workpiece.sprayPattern, dict):
            spray_pattern = workpiece.sprayPattern
        else:
            # Handle legacy format
            spray_pattern = {"Contour": workpiece.sprayPattern}

    # Extract pickup point
    pickup_point = None
    if hasattr(workpiece, 'pickupPoint') and workpiece.pickupPoint is not None:
        pickup_point = workpiece.pickupPoint

    # Generate the pixmap using all available data
    pixmap = generate_pixmap_from_contour_and_spray(
        contour=contour, 
        spray_pattern=spray_pattern, 
        pickup_point=pickup_point,
        size=(800, 800)
    )

    return ThumbnailWidget(filename=filename, pixmap=pixmap, timestamp=timestamp, workpieceId=workpiece.workpieceId)
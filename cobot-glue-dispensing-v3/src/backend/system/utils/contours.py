import cv2
import numpy as np
import numpy as np

def standardize_contour(contour, dtype=np.float32):
    """
    Converts any OpenCV contour or list of points to a (N, 2) NumPy array.
    Handles shapes like (N, 1, 2), (N, 2), or nested Python lists.
    """
    contour = np.asarray(contour)
    if contour.size == 0:
        return np.zeros((0, 2), dtype=dtype)

    # Common OpenCV shape (N, 1, 2)
    if contour.ndim == 3 and contour.shape[1] == 1:
        contour = contour[:, 0, :]

    # Make sure it’s (N, 2)
    contour = contour.reshape(-1, 2).astype(dtype)
    return contour


def to_cv_contour(contour):
    """
    Converts a standardized (N, 2) contour back to OpenCV’s (N, 1, 2) format.
    """
    contour = np.asarray(contour)
    if contour.size == 0:
        return np.zeros((0, 1, 2), dtype=np.int32)
    return contour.reshape(-1, 1, 2).astype(np.int32)


def standardize_point(point, dtype=np.float32):
    """
    Standardize a single point or list of points into (2,) or (N, 2).
    """
    point = np.asarray(point, dtype=dtype)
    if point.ndim == 1 and point.size == 2:
        return point
    return point.reshape(-1, 2)


def is_contour_inside_polygon(contour, top_left, top_right, bottom_right, bottom_left):
    """
    Fixed version using a different approach - checking if contour bounding rect is inside polygon
    """
    # Get the bounding rectangle of the contour
    x, y, w, h = cv2.boundingRect(contour)

    # Check if all 4 corners of the contour's bounding rect are inside the polygon
    bbox_points = [top_left, top_right, bottom_right, bottom_left]
    polygon = np.array(bbox_points, dtype=np.int32)

    contour_corners = [
        (x, y),  # top-left
        (x + w, y),  # top-right
        (x + w, y + h),  # bottom-right
        (x, y + h)  # bottom-left
    ]

    # Check if all corners of contour bounding rect are inside the polygon

    for corner in contour_corners:
        if cv2.pointPolygonTest(polygon, (float(corner[0]), float(corner[1])), False) < 0:
            return False

    # Additional check: verify all actual contour points are inside
    for point in contour:
        px, py = point[0]
        if cv2.pointPolygonTest(polygon, (float(px), float(py)), False) < 0:
            return False

    return True

def flatten_and_convert_to_list(contour_array):
    """Ensure contour array is Nx2 list of floats."""
    print(f"  _flatten_and_convert input type: {type(contour_array)}, shape: {np.array(contour_array).shape if hasattr(contour_array, '__len__') else 'no shape'}")
    arr = np.array(contour_array, dtype=float).reshape(-1, 2)  # Flatten to Nx2
    result = arr.tolist()
    print(f"  _flatten_and_convert output: first 3 points = {result[:3] if len(result) > 3 else result}")
    print(f"  _flatten_and_convert precision check: {arr[0] if len(arr) > 0 else 'empty'}")
    return result

def close_contours_if_open(contours):
    for i, cnt in enumerate(contours):
        if len(cnt) > 0:
            # Close the contour by adding first point to the end using numpy concatenation
            # Ensure dimensions match: cnt is (n, 1, 2), so reshape first point to (1, 1, 2)
            first_point = cnt[0].reshape(1, 1, 2)
            contours[i] = np.vstack([cnt, first_point])
    return contours

def calculate_mask_overlap(contour1, contour2, canvas_size=(800, 800)):
    """
    Calculate overlap between two contours using binary masks.

    Args:
        contour1: First contour (workpiece contour after initial alignment)
        contour2: Second contour (target/new contour)
        canvas_size: Size of the canvas to draw masks on

    Returns:
        float: Overlap ratio (Intersection over Union)
    """
    # Ensure contours are in the right format
    c1 = np.array(contour1, dtype=np.int32)
    c2 = np.array(contour2, dtype=np.int32)

    # Reshape if needed
    if len(c1.shape) == 3:
        c1 = c1.reshape(-1, 1, 2)
    else:
        c1 = c1.reshape(-1, 1, 2)

    if len(c2.shape) == 3:
        c2 = c2.reshape(-1, 1, 2)
    else:
        c2 = c2.reshape(-1, 1, 2)

    # Create masks
    mask1 = np.zeros(canvas_size, dtype=np.uint8)
    mask2 = np.zeros(canvas_size, dtype=np.uint8)

    # Draw filled contours
    cv2.drawContours(mask1, [c1], -1, 255, -1)  # -1 means filled
    cv2.drawContours(mask2, [c2], -1, 255, -1)

    # Calculate intersection and union
    intersection = np.logical_and(mask1, mask2)
    union = np.logical_or(mask1, mask2)

    # Calculate IoU (Intersection over Union)
    intersection_area = np.sum(intersection)
    union_area = np.sum(union)

    if union_area == 0:
        return 0.0

    iou = intersection_area / union_area
    return iou

def convexity_ratio(contour):
    """Compute how concave a shape is (area vs convex hull area)."""
    hull = cv2.convexHull(contour)
    area = cv2.contourArea(contour)
    hull_area = cv2.contourArea(hull)
    if hull_area == 0:
        return 0
    return area / hull_area
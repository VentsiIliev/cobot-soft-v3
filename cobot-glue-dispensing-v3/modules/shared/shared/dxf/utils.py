import numpy as np


def scale_contours(contours, scale_x, scale_y):
    """
    Scale contours by given scale factors in X and Y directions.

    Args:
        contours: Can be:
            - Single contour: numpy array of shape (n, 1, 2) or (n, 2)
            - List of contours: list of numpy arrays
            - None: returns None
        scale_x (float): Scale factor for X coordinates
        scale_y (float): Scale factor for Y coordinates

    Returns:
        Scaled contours in the same format as input
    """
    if contours is None:
        return None

    def scale_single_contour(contour):
        if contour is None or len(contour) == 0:
            return contour

        # Make a copy to avoid modifying original
        scaled_contour = contour.copy()

        # Handle different contour formats
        if len(scaled_contour.shape) == 3:  # OpenCV format (n, 1, 2)
            scaled_contour[:, 0, 0] *= scale_x  # X coordinates
            scaled_contour[:, 0, 1] *= scale_y  # Y coordinates
        elif len(scaled_contour.shape) == 2:  # Simple format (n, 2)
            scaled_contour[:, 0] *= scale_x  # X coordinates
            scaled_contour[:, 1] *= scale_y  # Y coordinates

        return scaled_contour

    # Handle single contour vs list of contours
    if isinstance(contours, list):
        # List of contours
        return [scale_single_contour(contour) for contour in contours]
    else:
        # Single contour
        return scale_single_contour(contours)


def scale_and_center_contours(contours, scale_x, scale_y, image_width, image_height):
    """
    Scale contours and center them in the image.

    Args:
        contours: Contours to scale (single contour or list)
        scale_x, scale_y: Scale factors
        image_width, image_height: Target image dimensions

    Returns:
        Scaled and centered contours
    """
    # First scale the contours
    scaled_contours = scale_contours(contours, scale_x, scale_y)

    if scaled_contours is None:
        return None

    # Collect all points to find bounding box
    all_points = []

    def collect_points(contour_data):
        if isinstance(contour_data, list):
            for contour in contour_data:
                if contour is not None and len(contour) > 0:
                    if len(contour.shape) == 3:  # (n, 1, 2)
                        all_points.extend(contour.reshape(-1, 2))
                    else:  # (n, 2)
                        all_points.extend(contour)
        else:
            if contour_data is not None and len(contour_data) > 0:
                if len(contour_data.shape) == 3:  # (n, 1, 2)
                    all_points.extend(contour_data.reshape(-1, 2))
                else:  # (n, 2)
                    all_points.extend(contour_data)

    collect_points(scaled_contours)

    if not all_points:
        return scaled_contours

    # Calculate bounding box and centering offset
    all_points = np.array(all_points)
    min_x, min_y = np.min(all_points, axis=0)
    max_x, max_y = np.max(all_points, axis=0)

    current_center_x = (min_x + max_x) / 2
    current_center_y = (min_y + max_y) / 2

    target_center_x = image_width / 2
    target_center_y = image_height / 2

    # offset_x = target_center_x - current_center_x
    # offset_y = target_center_y - current_center_y

    offset_x = 0
    offset_y = 0

    # Apply centering offset
    def center_single_contour(contour):
        if contour is None or len(contour) == 0:
            return contour

        centered_contour = contour.copy()

        if len(centered_contour.shape) == 3:  # (n, 1, 2)
            centered_contour[:, 0, 0] += offset_x
            centered_contour[:, 0, 1] += offset_y
        else:  # (n, 2)
            centered_contour[:, 0] += offset_x
            centered_contour[:, 1] += offset_y

        return centered_contour

    if isinstance(scaled_contours, list):
        return [center_single_contour(contour) for contour in scaled_contours]
    else:
        return center_single_contour(scaled_contours)



import numpy as np
import cv2


class DXFCoordinateConverter:
    """
    Handles conversion from DXF coordinates (mm) to pixel coordinates
    with proper centering in the target image.
    """

    def __init__(self, image_width=640, image_height=360, mm_per_pixel=1.0):
        """
        Initialize the coordinate converter.

        Args:
            image_width (int): Target image width in pixels
            image_height (int): Target image height in pixels
            mm_per_pixel (float): Scale factor - how many mm per pixel
        """
        self.image_width = image_width
        self.image_height = image_height
        self.mm_per_pixel = mm_per_pixel
        self.pixels_per_mm = 1.0 / mm_per_pixel

    def convert_dxf_to_pixels(self, dxf_contours, center_in_image=True):
        """
        Convert DXF coordinates to pixel coordinates.

        Args:
            dxf_contours: Single contour or list of contours in DXF coordinates (mm)
            center_in_image (bool): Whether to center the contours in the image

        Returns:
            Converted contours in pixel coordinates
        """
        if dxf_contours is None or len(dxf_contours) == 0:
            return dxf_contours

        # Handle single contour vs list of contours
        is_single_contour = isinstance(dxf_contours, np.ndarray) and len(dxf_contours.shape) == 3

        if is_single_contour:
            contours_list = [dxf_contours]
        else:
            contours_list = dxf_contours

        converted_contours = []

        if center_in_image and contours_list:
            # Calculate bounding box of all contours to find center
            all_points = []
            for contour in contours_list:
                if contour is not None and len(contour) > 0:
                    # Handle different contour formats
                    if len(contour.shape) == 3:  # OpenCV format (n, 1, 2)
                        points = contour.reshape(-1, 2)
                    else:  # Simple format (n, 2)
                        points = contour
                    all_points.extend(points)

            if all_points:
                all_points = np.array(all_points)
                dxf_min_x, dxf_min_y = np.min(all_points, axis=0)
                dxf_max_x, dxf_max_y = np.max(all_points, axis=0)

                # Calculate DXF bounds center
                dxf_center_x = (dxf_min_x + dxf_max_x) / 2
                dxf_center_y = (dxf_min_y + dxf_max_y) / 2

                # Calculate target image center
                image_center_x = self.image_width / 2
                image_center_y = self.image_height / 2

        for contour in contours_list:
            if contour is None or len(contour) == 0:
                converted_contours.append(contour)
                continue

            # Handle different contour formats
            if len(contour.shape) == 3:  # OpenCV format (n, 1, 2)
                points = contour.reshape(-1, 2)
                opencv_format = True
            else:  # Simple format (n, 2)
                points = contour
                opencv_format = False

            # Convert mm to pixels
            pixel_points = points * self.pixels_per_mm

            if center_in_image and all_points is not None:
                # Translate to center the contours in the image
                # First, translate DXF center to origin
                pixel_points[:, 0] -= dxf_center_x * self.pixels_per_mm
                pixel_points[:, 1] -= dxf_center_y * self.pixels_per_mm

                # Then translate to image center
                pixel_points[:, 0] += image_center_x
                pixel_points[:, 1] += image_center_y

            # Convert back to original format
            if opencv_format:
                pixel_contour = pixel_points.reshape(-1, 1, 2).astype(np.float32)
            else:
                pixel_contour = pixel_points.astype(np.float32)

            converted_contours.append(pixel_contour)

        # Return in same format as input
        if is_single_contour:
            return converted_contours[0] if converted_contours else None
        else:
            return converted_contours
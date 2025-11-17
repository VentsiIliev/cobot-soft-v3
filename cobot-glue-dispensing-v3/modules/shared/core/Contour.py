import cv2
import numpy as np


class Contour:
    def __init__(self, contour_points):
        # print contour_points type and shape
        # print(f"Initializing Contour with points type before reshape: {type(contour_points)}, shape: {getattr(contour_points, 'shape', None)}")
        contour_points = contour_points.reshape((-1, 1, 2)).astype(np.float32)
        # print(f"Initializing Contour with points typ e after reshape: {type(contour_points)}, shape: {getattr(contour_points, 'shape', None)}")
        if not isinstance(contour_points, np.ndarray):
            contour_points = np.array(contour_points, dtype=np.float32)
        self.contour_points = contour_points

    def get_contour_points(self):
        return self.contour_points

    def getArea(self):
        """CALCULATE AND RETURN THE CONTOUR AREA"""
        print(f"Contour points type: {type(self.contour_points)}, shape: {self.contour_points.shape}")
        return cv2.contourArea(self.contour_points)

    def getBbox(self):
        """RETURN THE BBBOX OF THE CONTOUR"""
        return cv2.boundingRect(self.contour_points)

    def getMinAreaRect(self):
        """RETURN THE MINIMUM AREA RECTANGLE ENCLOSING THE CONTOUR"""
        return cv2.minAreaRect(self.contour_points)

    def getMoments(self):
        """RETURN THE MOMENTS OF THE CONTOUR"""
        return cv2.moments(self.contour_points)

    def getPerimeter(self):
        """RETURN THE PERIMETER OF THE CONTOUR"""
        return cv2.arcLength(self.contour_points, True)

    def getCentroid(self):
        """RETURN THE CENTROID OF THE CONTOUR"""
        M = self.getMoments()
        if M["m00"] == 0:
            # Handle empty or degenerate contour by using bounding box center
            bbox = self.getBbox()
            if bbox[2] > 0 and bbox[3] > 0:  # Valid bounding box
                cX = int(bbox[0] + bbox[2] / 2)
                cY = int(bbox[1] + bbox[3] / 2)
                return (cX, cY)
            else:
                # Last resort: use first point if available
                if len(self.contour_points) > 0:
                    first_point = self.contour_points[0][0]
                    return (int(first_point[0]), int(first_point[1]))
                else:
                    return (0, 0)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        return (cX, cY)

    def getCentroidDistance(self, point):
        """RETURN THE DISTANCE FROM THE CENTROID TO A GIVEN POINT"""
        cX, cY = self.getCentroid()
        return np.sqrt((cX - point[0]) ** 2 + (cY - point[1]) ** 2)

    def getConvexHull(self):
        """RETURN THE CONVEX HULL OF THE CONTOUR"""
        return cv2.convexHull(self.contour_points)

    def getOrientation(self):
        """
        The `getOrientation` function calculates the orientation of a contour relative to the horizontal axis.
        It uses image moments to determine the angle of the contour's principal axis.
        The angle is computed using the central moments `mu11`, `mu20`, and `mu02`, and it is returned in degrees.
        The scaling factor `0.5` is used to halve the computed angle, as the formula for orientation involves dividing
        the result of the `arctan2` function by 2. This ensures the correct orientation is derived.
        The function returns 0 if the contour is a perfect circle (`mu20 = 0`).
        """
        moments = self.getMoments()
        
        # Use a small tolerance instead of exact zero check
        if abs(moments["mu20"]) < 1e-10:  # Very small tolerance for floating point comparison
            return 0
        
        angle = 0.5 * np.arctan2(2 * moments["mu11"], moments["mu20"] - moments["mu02"])
        
        # Convert radians to degrees
        return np.degrees(angle)

    def getConvexityDefects(self):
        """GET THE CONVEXITY DEFECTS OF THE CONTOUR"""

        # Ensure contour_points is a NumPy array with correct shape
        contour = np.array(self.contour_points, dtype=np.int32)

        # Remove duplicate points to prevent self-intersections
        contour = np.unique(contour.reshape(-1, 2), axis=0)

        if len(contour) < 3:
            return False, None

        # Reshape to (N, 1, 2) for OpenCV
        contour = contour.reshape(-1, 1, 2)

        # Compute convex hull indices (not points)
        try:
            hull = cv2.convexHull(contour, returnPoints=False)

            if hull is None or len(hull) < 3:
                return False, None

            # Sort hull indices to enforce monotonicity
            hull = np.sort(hull.flatten())[:, np.newaxis]

            # Compute convexity defects
            defects = cv2.convexityDefects(contour, hull)

            if defects is None:
                return False, None

            return True, defects

        except cv2.error as e:
            print(f"[ConvexityDefects Error] {e}")
            return False, None

    def simplify(self, epsilon_factor=0.01):
        """SIMPLIFY THE CONTOUR USING APPROX POLY DP"""

        # Ensure contour is a valid NumPy array
        contour = np.array(self.contour_points, dtype=np.float32)

        # Ensure contour is in (N,1,2) shape
        if contour.ndim != 3 or contour.shape[1] != 1 or contour.shape[2] != 2:
            contour = contour.reshape(-1, 1, 2)

        # Compute perimeter
        perimeter = cv2.arcLength(contour, True)

        # Compute dynamic epsilon
        epsilon = epsilon_factor * perimeter

        # Apply simplification
        simplified_contour = cv2.approxPolyDP(contour, epsilon, True)
        self.contour_points = simplified_contour  # Update contour points
        return simplified_contour

    def smooth(self, alpha=0.1):
        """SMOOTH THE CONTOUR POINTS USING EXPOENTIAL MOVING AVERAGE"""
        contour_smooth = np.copy(self.contour_points)
        for i in range(1, len(contour_smooth)):
            contour_smooth[i] = contour_smooth[i - 1] * (1 - alpha) + contour_smooth[i] * alpha
        return contour_smooth

    def match(self, other_contour):
        """COMPARE THE CONTOUR WITH ANOTHER CONTOUR"""
        return cv2.matchShapes(self.contour_points, other_contour, 1, 0.0)

    """ --- ROTATION SECTION --- """

    def rotate(self, angle, pivot):
        """Rotates the contour around a given pivot point while keeping floating-point precision."""
        # print(f"Rotating contour by {angle} degrees around pivot {pivot}")
        self.contour_points[:] = self.__rotateContour(self.contour_points, angle, pivot)  # Modify in place

    def __rotatePoint(self, point, angle_rad, pivot):
        """Rotates a single point around a pivot using a precomputed angle in radians."""
        pivotX, pivotY = pivot
        pointX, pointY = point

        cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)

        rotatedX = pivotX + cos_a * (pointX - pivotX) - sin_a * (pointY - pivotY)
        rotatedY = pivotY + sin_a * (pointX - pivotX) + cos_a * (pointY - pivotY)

        return [rotatedX, rotatedY]  # Keep as float

    def __rotateContour(self, contour, angle, pivot):
        """Rotates an entire contour efficiently."""

        angle_rad = np.radians(angle)  # Convert once, avoid redundant conversions
        return np.array([[self.__rotatePoint(point[0], angle_rad, pivot)] for point in contour], dtype=np.float32)

    """ --- TRANSLATION SECTION --- """

    def translate(self, dx, dy):
        """Translates the contour by (dx, dy)."""
        self.contour_points[:] = self.__translateContour(self.contour_points, dx, dy)  # Modify in place
        # print(f"Translated contour by ({dx}, {dy})")
    def __translateContour(self, contour, dx, dy):
        """Translates an entire contour efficiently."""
        translation = np.array([dx, dy], dtype=np.float32)  # Create translation vector once
        return contour + translation  # Element-wise addition

    """ --- SCALING SECTION --- """

    def scale(self, factor):
        """Scales the contour by the given factor."""
        self.contour_points[:] = self.__scaleContour(self.contour_points, factor)  # Modify in place

    def __scaleContour(self, contour, factor):
        """Scales an entire contour efficiently."""
        return contour * factor  # Element-wise multiplication to scale all points by the factor


    def shrink(self, offset_x, offset_y):
        """
        Shrinks the contour inward by the specified pixel amounts in X and Y directions
        while maintaining shape consistency.

        :param offset_x: The shrink amount in pixels for the X direction.
        :param offset_y: The shrink amount in pixels for the Y direction.
        """

        # Convert contour to binary image for processing
        bbox = cv2.boundingRect(self.contour_points)  # Get bounding box
        mask = np.zeros((bbox[3] + 2 * offset_y, bbox[2] + 2 * offset_x), dtype=np.uint8)

        # Shift contour into mask space
        shifted_contour = self.contour_points - [bbox[0] - offset_x, bbox[1] - offset_y]

        # Draw filled contour
        cv2.fillPoly(mask, [shifted_contour.astype(np.int32)], 255)

        # Perform erosion (shrinking) using a rectangular kernel
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * offset_x, 2 * offset_y))
        eroded_mask = cv2.erode(mask, kernel, iterations=1)

        # Find the new shrunk contour
        contours, _ = cv2.findContours(eroded_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Instead of modifying in place, update the reference to match different shape sizes
            self.contour_points = contours[0] + [bbox[0] - offset_x, bbox[1] - offset_y]

    """ --- DRAWING SECTION --- """

    def draw(self, frame, color=(0, 255, 0), thickness=2):
        """DRAW THE CONTOUR"""
        # Convert contour to the correct type for OpenCV
        contour_for_drawing = self.contour_points.astype(np.int32)  # Convert to int32

        # Check for negative coordinates and make them positive for drawing
        # contour_for_drawing = np.abs(contour_for_drawing)

        # Draw the contour on the frame
        cv2.drawContours(frame, [contour_for_drawing], -1, color, thickness)

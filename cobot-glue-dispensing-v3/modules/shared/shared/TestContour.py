import cv2
import numpy as np
import unittest
from Contour import Contour


class TestContour(unittest.TestCase):

    def setUp(self):
        # Sample contour (a triangle)
        self.contour_points = np.array([[[100, 100]], [[200, 100]], [[150, 200]]], dtype=np.int32)
        self.contour = Contour(self.contour_points)

    def test_get_contour_points(self):
        """Test getting contour points"""
        points = self.contour.get_contour_points()
        self.assertTrue(np.array_equal(points, self.contour_points))
        print("TESTING CONTOUR POINTS")
        print("Contour points are:", self.contour_points)
        print("Returned contour points:", points)
        print("\n")

    def test_get_area(self):
        """Test calculating the area of the contour"""
        area = self.contour.getArea()
        # Manually calculated area for a triangle (base * height / 2)
        expected_area = 5000  # For the given triangle
        self.assertEqual(area, expected_area)
        print("TESTING AREA OF CONTOUR")
        print("Contour points are:", self.contour_points)
        print("Area of the contour is:", area)
        print("Expected area of the contour is:", expected_area)
        print("\n")

    def test_get_bbox(self):
        bbox = self.contour.getBbox()  # Use self.contour instead of contour
        expected_bbox = (100, 100, 101, 101)
        self.assertTrue(np.allclose(bbox, expected_bbox, atol=1))  # Allow some tolerance
        print("TESTING BOUNDING BOX")
        print("Bounding box is:", bbox)
        print("Expected bounding box:", expected_bbox)
        print("\n")

    def test_get_min_area_rect(self):
        """Test calculating minimum area rectangle"""
        min_area_rect = self.contour.getMinAreaRect()
        self.assertIsInstance(min_area_rect, tuple)  # It returns (center, (width, height), angle)
        print("TESTING MINIMUM AREA RECTANGLE")
        print("Min area rect is:", min_area_rect)
        print("\n")

    def test_get_moments(self):
        """Test calculating moments of the contour"""
        moments = self.contour.getMoments()
        self.assertIn('m00', moments)  # Ensure the moments dict has 'm00' key
        print("TESTING MOMENTS")
        print("Contour moments are:", moments)
        print("\n")

    def test_get_perimeter(self):
        """Test calculating perimeter of the contour"""
        perimeter = self.contour.getPerimeter()
        self.assertGreater(perimeter, 0)
        print("TESTING PERIMETER")
        print("Perimeter of the contour is:", perimeter)
        print("\n")

    def test_get_centroid(self):
        """Test calculating centroid"""
        centroid = self.contour.getCentroid()
        self.assertEqual(centroid, (150, 133))  # Centroid for the given triangle
        print("TESTING CENTROID")
        print("Centroid of the contour is:", centroid)
        print("Expected centroid is:", (150, 133))
        print("\n")

    def test_get_centroid_distance(self):
        """Test distance from centroid to a given point"""
        point = (200, 200)
        distance = self.contour.getCentroidDistance(point)
        expected_distance = np.sqrt((150 - 200) ** 2 + (133 - 200) ** 2)
        self.assertEqual(distance, expected_distance)
        print("TESTING CENTROID DISTANCE")
        print("Distance from centroid to point is:", distance)
        print("Expected distance is:", expected_distance)
        print("\n")

    def test_get_convex_hull(self):
        """Test getting convex hull of the contour"""
        convex_hull = self.contour.getConvexHull()
        self.assertIsInstance(convex_hull, np.ndarray)
        print("TESTING CONVEX HULL")
        print("Convex hull points are:", convex_hull)
        print("\n")

    def test_get_defects(self):
        defects = self.contour.getDefects()
        # Check if defects is None (valid for simple contours)
        if defects is not None:
            self.assertIsInstance(defects, np.ndarray)  # Should return defects if any
        else:
            self.assertIsNone(defects)  # It's fine if there are no defects
        print("TESTING CONVEXITY DEFECTS")
        print("Defects are:", defects)
        print("\n")

    def test_simplify(self):
        """Test simplifying the contour"""
        simplified_contour = self.contour.simplify(10.0)
        self.assertGreater(len(simplified_contour), 0)  # Should return a simplified version
        print("TESTING SIMPLIFY")
        print("Simplified contour points:", simplified_contour)
        print("\n")

    def test_smooth(self):
        """Test smoothing the contour"""
        smoothed_contour = self.contour.smooth(alpha=0.2)
        self.assertEqual(smoothed_contour.shape, self.contour.contour_points.shape)  # Same shape after smoothing
        print("TESTING SMOOTHING")
        print("Smoothed contour points:", smoothed_contour)
        print("\n")

    def test_match(self):
        """Test matching the contour with another contour"""
        other_contour_points = np.array([[[110, 110]], [[210, 110]], [[160, 210]]], dtype=np.int32)
        other_contour = Contour(other_contour_points)
        similarity = self.contour.match(other_contour.contour_points)
        self.assertIsInstance(similarity, float)  # It should return a similarity score
        print("TESTING CONTOUR MATCHING")
        print("Similarity score:", similarity)
        print("\n")

    def test_rotate(self):
        """Test rotating the contour"""
        original_contour = np.copy(self.contour.contour_points)
        self.contour.rotate(90, (150, 150))  # Rotate 90 degrees around centroid
        self.assertFalse(np.array_equal(self.contour.contour_points, original_contour))  # Should not be equal
        print("TESTING ROTATION")
        print("Original contour points:", original_contour)
        print("Rotated contour points:", self.contour.contour_points)
        print("Expected centroid after rotation:", (150, 150))
        print("\n")

    def test_translate(self):
        """Test translating the contour"""
        original_contour = np.copy(self.contour.contour_points)
        self.contour.translate(50, 50)  # Translate by (50, 50)
        self.assertFalse(np.array_equal(self.contour.contour_points, original_contour))  # Should be different
        print("TESTING TRANSLATION")
        print("Original contour points:", original_contour)
        print("Translated contour points:", self.contour.contour_points)
        print("Expected translation: (50, 50)")
        print("\n")

    def test_scale(self):
        """Test scaling the contour"""
        original_contour = np.copy(self.contour.contour_points)
        self.contour.scale(2)  # Scale by factor of 2
        self.assertFalse(np.array_equal(self.contour.contour_points, original_contour))  # Should be different
        print("TESTING SCALING")
        print("Original contour points:", original_contour)
        print("Scaled contour points:", self.contour.contour_points)
        print("\n")

    def test_draw(self):
        frame = np.zeros((200, 200, 3), dtype=np.uint8)  # Create a blank image (black)
        self.contour.draw(frame, color=(0, 255, 0), thickness=2)  # Use self.contour
        # After contour_editor the contour, check that the frame has been modified
        self.assertNotEqual(np.sum(frame), 0)
        print("TESTING DRAWING CONTOUR")
        print("Image frame after contour_editor contour:", frame)
        print("\n")

if __name__ == '__main__':
    unittest.main()

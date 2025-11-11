import unittest
import numpy as np
import cv2
from PLVision import Contouring


class TestContouring(unittest.TestCase):
    def setUp(self):
        self.image = np.zeros((100, 100), dtype=np.uint8)
        self.contour = np.array([[[10, 10]], [[10, 20]], [[20, 20]], [[20, 10]]])
        self.contours = [self.contour]
        self.hierarchy = np.array([[[0, 0, 0, 0]]])
        self.pivot = (15, 15)
        self.bbox = (5, 5, 25, 25)

    def test_findContours(self):
        contours, hierarchy = Contouring.findContours(self.image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        self.assertIsInstance(contours, tuple)
        self.assertIsInstance(hierarchy, np.ndarray)

    def test_rotateContour(self):
        result = Contouring.rotateContour(self.contour, 45, self.pivot)
        self.assertIsInstance(result, np.ndarray)

    def test_rotateContourAndChildren(self):
        Contouring.rotateContourAndChildren(self.contours, self.hierarchy, 45)
        self.assertIsInstance(self.contours[0], np.ndarray)

    def test_isContourWithinBbox(self):
        result = Contouring.isContourWithinBbox(self.contour, self.bbox)
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()

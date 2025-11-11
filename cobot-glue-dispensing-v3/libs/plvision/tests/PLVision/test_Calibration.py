"""
* File: test_Calibration.py
* Author: IlV
* Comments:
* Revision history:
* Date       Author      Description
* -----------------------------------------------------------------
** 070524     IlV         Initial release
* -----------------------------------------------------------------
*
"""

import unittest

import cv2
import numpy as np

from PLVision.Calibration import CameraCalibrator


class TestCameraCalibrator(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.calibrationPattern = cv2.imread("testData/calibration/calibration_chessboard.png")

    def setUp(self):
        """Set up the CameraCalibrator object for testing."""
        self.calibrator = CameraCalibrator(26, 15, 25)
        self.assertIsNotNone(self.calibrator)
        self.assertEqual(26, self.calibrator.chessboardWidth)
        self.assertEqual(15, self.calibrator.chessboardHeight)
        self.assertEqual(25, self.calibrator.chessboardSquaresSize)

    def test_calculateObjp(self):
        """Test if the _calculateObjp method returns a numpy array of the correct shape."""
        result = self.calibrator._calculateObjp()
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual((150, 3), result.shape)

    def test_findCorners(self):
        """Test if the findCorners method returns the correct types when given a grayscale image."""
        ret, corners = self.calibrator.findCorners(self.calibrationPattern)
        self.assertIsInstance(ret, bool)
        self.assertIsNotNone(corners)
        self.assertTrue(ret)
        # Assert that corners is a 3D numpy array
        self.assertEqual(len(corners.shape), 3)
        # Assert the width and height of the corners
        expected = self.calibrator.chessboardWidth * self.calibrator.chessboardHeight
        actual = corners.shape[0]

        self.assertEqual(actual,expected)

    def test_findCorners_wrong_chessboard_width(self):
        """Test if the findCorners method returns the correct types when given a grayscale image."""
        calibrator = CameraCalibrator(25, 15, 25)
        ret, corners = calibrator.findCorners(self.calibrationPattern)
        self.assertIsInstance(ret, bool)
        self.assertIsNone(corners)
        self.assertFalse(ret)

    def test_findCorners_wrong_chessboard_height(self):
        """Test if the findCorners method returns the correct types when given a grayscale image."""
        calibrator = CameraCalibrator(26, 14, 25)
        ret, corners = calibrator.findCorners(self.calibrationPattern)
        self.assertIsInstance(ret, bool)
        self.assertIsNone(corners)
        self.assertFalse(ret)

    def test_refineCorners(self):
        """Test if the refineCorners method returns a numpy array of the same shape as the input corners."""
        gray = cv2.cvtColor(self.calibrationPattern, cv2.COLOR_BGR2GRAY)
        corners = np.array([[[50, 50]]], dtype=np.float32)
        result = self.calibrator.refineCorners(gray, corners)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape, corners.shape)

    def test_calculateMeanError(self):
        """Test if the calculateMeanError method returns a float when given valid input parameters."""
        dist = np.zeros((5, 1), dtype=np.float32)
        mtx = np.eye(3, dtype=np.float32)
        rvecs = [np.zeros((3, 1), dtype=np.float32)]
        tvecs = [np.zeros((3, 1), dtype=np.float32)]
        meanError = self.calibrator.calculateMeanError(dist, mtx, rvecs, tvecs)
        self.assertIsInstance(meanError, float)

    def test_saveCalibrationData(self):
        """Test if the saveCalibrationData method correctly creates a file in the specified directory."""
        import os
        import tempfile

        mtx = np.eye(3, dtype=np.float32)
        dist = np.zeros((5, 1), dtype=np.float32)
        ppm = 1.0
        with tempfile.TemporaryDirectory() as tmpdirname:
            self.calibrator.saveCalibrationData(mtx, dist, ppm, tmpdirname)
            self.assertTrue(os.path.exists(os.path.join(tmpdirname, "camera_calibration.npz")))



if __name__ == '__main__':
    unittest.main()

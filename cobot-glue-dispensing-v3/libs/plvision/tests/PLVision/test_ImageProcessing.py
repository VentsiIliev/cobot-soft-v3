import unittest
import numpy as np
import cv2
from PLVision import ImageProcessing


class TestImageProcessing(unittest.TestCase):
    def setUp(self):
        """Set up a dummy image for testing."""
        self.image = np.zeros((100, 100, 3), dtype=np.uint8)

    def test_applyAffineTransformation(self):
        """Test if the affineTransform function works without raising an exception."""
        xOffset = 1
        yOffset = 0
        rotationAngle = 0
        xScale = 1
        yScale = 1
        try:
            ImageProcessing.applyAffineTransformation(self.image, xOffset, yOffset, rotationAngle, xScale, yScale)
        except Exception as e:
            self.fail(f"applyAffineTransformation method raised exception {e}")

    def test_undistortImage(self):
        """Test if the undistortImage function works without raising an exception."""
        mtx = np.eye(3, dtype=np.float32)
        dist = np.zeros((5, 1), dtype=np.float32)
        try:
            ImageProcessing.undistortImage(self.image, mtx, dist)
        except Exception as e:
            self.fail(f"undistortImage method raised exception {e}")

    def test_cropImage(self):
        """Test if the cropImage function works without raising an exception."""
        try:
            ImageProcessing.cropImage(self.image)
        except Exception as e:
            self.fail(f"cropImage method raised exception {e}")

    def test_grayscaleImage(self):
        """Test if the grayscaleImage function works without raising an exception and returns the correct shape."""
        try:
            grayscale = ImageProcessing.grayscaleImage(self.image)
            self.assertEqual(grayscale.shape, (100, 100))
        except Exception as e:
            self.fail(f"grayscaleImage method raised exception {e}")

    def test_zoom(self):
        """Test if the zoom function works without raising an exception."""
        try:
            ImageProcessing.zoom(self.image, 1)
        except Exception as e:
            self.fail(f"zoom method raised exception {e}")

    def test_cropImage_cropping(self):
        """Test if the cropImage function correctly crops the image."""
        cropped = ImageProcessing.cropImage(self.image, leftCrop=10, rightCrop=10, topCrop=20, bottomCrop=20, pad=False)
        self.assertEqual(cropped.shape, (60, 80, 3))

    def test_cropImage_padding(self):
        """Test if the cropImage function correctly pads the image after cropping."""
        cropped_padded = ImageProcessing.cropImage(self.image, leftCrop=10, rightCrop=10, topCrop=20, bottomCrop=20,
                                                   pad=True)
        self.assertEqual(cropped_padded.shape, (100, 100, 3))

    def test_cropImage_negative_left_crop(self):
        """Test if the cropImage function correctly handles negative cropping values."""
        with self.assertRaises(ValueError):
            ImageProcessing.cropImage(self.image, leftCrop=-10, rightCrop=0, topCrop=0, bottomCrop=0)

    def test_cropImage_negative_right_crop(self):
        """Test if the cropImage function correctly handles negative cropping values."""
        with self.assertRaises(ValueError):
            ImageProcessing.cropImage(self.image, leftCrop=0, rightCrop=-10, topCrop=0, bottomCrop=0)

    def test_cropImage_negative_top_crop(self):
        """Test if the cropImage function correctly handles negative cropping values."""
        with self.assertRaises(ValueError):
            ImageProcessing.cropImage(self.image, leftCrop=0, rightCrop=0, topCrop=-10, bottomCrop=0)

    def test_cropImage_negative_bottom_crop(self):
        """Test if the cropImage function correctly handles negative cropping values."""
        with self.assertRaises(ValueError):
            ImageProcessing.cropImage(self.image, leftCrop=0, rightCrop=0, topCrop=0, bottomCrop=-10)

    def test_cropImage_all_negative(self):
        """Test if the cropImage function correctly handles negative cropping values."""
        with self.assertRaises(ValueError):
            ImageProcessing.cropImage(self.image, leftCrop=-10, rightCrop=-10, topCrop=-10, bottomCrop=-10)

    def test_zoom_zoomIn(self):
        """Test if the zoom function correctly zooms in the image."""
        zoomed_in = ImageProcessing.zoom(self.image, 2)
        self.assertEqual(zoomed_in.shape, (100, 100, 3))

    def test_zoom_zoomOut(self):
        """Test if the zoom function correctly zooms out the image."""
        zoomed_out = ImageProcessing.zoom(self.image, 0.5)
        self.assertEqual(zoomed_out.shape, (100, 100, 3))

    # ...


if __name__ == '__main__':
    unittest.main()

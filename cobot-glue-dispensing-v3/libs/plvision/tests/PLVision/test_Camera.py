"""
* File: test_Camera.py
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
from PLVision.Camera import Camera


class TestCamera(unittest.TestCase):
    def setUp(self):
        """Set up the Camera object for testing."""
        self.camera = Camera(cameraIndex=0, width=1920, height=1080)
        self.assertIsNotNone(self.camera)
        self.assertEqual(0, self.camera.cameraIndex)
        self.assertEqual(1920, self.camera.width)
        self.assertEqual(1080, self.camera.height)

    def test_init_resolution_1280x720(self):
        """Test if the Camera object is created with the correct resolution when no width and height are given."""
        camera = Camera(cameraIndex=0, width=1280, height=720)
        self.assertEqual(0, camera.cameraIndex)
        self.assertEqual(1280, camera.width)
        self.assertEqual(720, camera.height)

    def test_setCameraIndex(self):
        """Test if the setCameraIndex method raises a ValueError when given a negative value."""
        with self.assertRaises(ValueError):
            self.camera.setCameraIndex(-1)

    def test_setCameraIndexValidIndex(self):
        """Test if the setCameraIndex method raises a ValueError when given a negative value."""
        self.camera.setCameraIndex(0)
        self.assertEqual(0, self.camera.cameraIndex)

    def test_setWidth(self):
        """Test if the setWidth method raises a ValueError when given a negative value."""
        with self.assertRaises(ValueError):
            self.camera.setWidth(-1)

    def test_setHeight(self):
        """Test if the setHeight method raises a ValueError when given a negative value."""
        with self.assertRaises(ValueError):
            self.camera.setHeight(-1)

    def test_capture(self):
        """Test if the capture method works without raising an exception."""
        try:
            self.camera.capture()
        except Exception as e:
            self.fail(f"capture method raised exception {e}")

    def test_captureImage(self):
        """Test if the captureImage method returns an image of the correct size."""
        image = self.camera.capture()
        self.assertEqual((1080, 1920, 3), image.shape)

    def test_stop(self):
        """Test if the stop method works without raising an exception."""
        try:
            self.camera.stopCapture()
        except Exception as e:
            self.fail(f"stopCapture method raised exception {e}")


if __name__ == '__main__':
    unittest.main()

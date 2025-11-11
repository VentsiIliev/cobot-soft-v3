"""
* File: Calibration.py
* Author: IlV
* Comments: This file contains calibration functions for the camera.
* Revision history:
* Date       Author      Description
* -----------------------------------------------------------------
* 070524     AtD/IlV         Initial release
* -----------------------------------------------------------------
*
"""
import cv2  # Import OpenCV
import numpy as np  # Import numpy

from libs.plvision.PLVision.Camera import Camera
import os


class CameraCalibrator:
    """
        A class for calibrating a camera using a chessboard pattern.

        Attributes:
            chessboardWidth (int): The number of inner corners per chessboard row.
            chessboardHeight (int): The number of inner corners per chessboard column.
            chessboardSquaresSize (float): The size of each chessboard square in real-world units.
            objp (np.ndarray): The object points in real-world space.
            objpoints (list): A list of object points in real-world space for all images.
            imgpoints (list): A list of corner points in image space for all images.
            winZone (tuple): The size of the search window at each pyramid level for corner refinement.
            zeroZone (tuple): The size of the dead region in the middle of the search zone over which the summation in
                          the formula below is not done. It is used to avoid possible singularities in the
                          autocorrelation matrix.
            criteriaMaxIterations (int): The maximum number of iterations for corner refinement algorithm
            criteriaAccuracy (float): The accuracy desired for corner refinement algorithm
    """

    def __init__(self, chessboardWidth, chessboardHeight, chessboardSquaresSize):
        """
            Initializes the CameraCalibrator with chessboard parameters.

            Parameters:
                chessboardWidth (int): Number of inner corners in chessboard rows.
                chessboardHeight (int): Number of inner corners in chessboard columns.
                chessboardSquaresSize (float): Size of each chessboard square.
        """
        self.chessboardWidth = chessboardWidth
        self.chessboardHeight = chessboardHeight
        self.chessboardSquaresSize = chessboardSquaresSize
        self.objp = self._calculateObjp()
        self.objpoints = []
        self.imgpoints = []

        self.winZone = (11, 11)
        self.zeroZone = (-1, -1)

        self.criteriaMaxIterations = 30
        self.criteriaAccuracy = 0.001

    def _calculateObjp(self):
        """
            Calculates the object points for the chessboard corners in the real-world space.

            Returns:
                np.ndarray: A numpy array of shape (N, 3) where N is the number of corners,
                            containing the (x, y, z) coordinates of each corner in real-world units.
        """
        objp = np.zeros((self.chessboardWidth * self.chessboardHeight, 3), np.float32)
        objp[:, :2] = np.mgrid[0:self.chessboardWidth, 0:self.chessboardHeight].T.reshape(-1,
                                                                                          2) * self.chessboardSquaresSize
        return objp

    def findCorners(self, gray):
        """
            Finds the corners in a grayscale image of the chessboard.

            Parameters:
                gray (np.ndarray): A grayscale image of the chessboard.

            Returns:
                tuple: A tuple containing a boolean value indicating if corners were successfully found,
                       and an array of detected corners in the image.
        """
        print("Finding corners of the chessboard ",self.chessboardWidth, self.chessboardHeight)
        return cv2.findChessboardCorners(gray, (self.chessboardWidth, self.chessboardHeight), None)

    def refineCorners(self, gray, corners):

        """
            Refines the detected corner locations in an image to sub-pixel accuracy.

            Parameters:
                gray (np.ndarray): A grayscale image of the chessboard.
                corners (np.ndarray): Initial coordinates of the detected corners in the image.

            Returns:
                np.ndarray: The refined corner locations in the image.
        """
        # define the criteria to stop. We stop it after a specified number of iterations
        # or a certain accuracy is achieved, whichever occurs first.
        criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, self.criteriaMaxIterations, self.criteriaMaxIterations)
        # Refine corner points
        return cv2.cornerSubPix(gray, corners, self.winZone, self.zeroZone, criteria)

    def drawCorners(self, frame, corners2, ret):
        """
            Draws the chessboard corners detected in an image.

            Parameters:
                frame (np.ndarray): The image on which to draw the corners.
                corners2 (np.ndarray): The corner points.
                ret (bool): Indicates whether the chessboard corners were found.
        """
        cv2.drawChessboardCorners(frame, (self.chessboardWidth, self.chessboardHeight), corners2, ret)

    def appendCorners(self, corners2):
        """
            Appends the detected corners and corresponding object points for camera calibration.

            Parameters:
                corners2 (np.ndarray): The corner points in the image.
        """
        self.imgpoints.append(corners2)
        self.objpoints.append(self.objp)

    def calculatePpm(self):
        """
        Calculates the pixels-per-metric ratio based on detected corners, considering both
        x and y distances between corners for a more accurate estimation.

        Returns:
            float: The average pixels-per-metric ratio for the detected squares.
        """
        squareSizesPx = []  # This will store the average square size for each image, in pixels.

        for i, points in enumerate(self.imgpoints):
            if points.shape[0] != self.chessboardWidth * self.chessboardHeight:
                continue  # Skip if not all corners are detected.

            # Reshape points for easier manipulation
            pointsReshaped = points.reshape((self.chessboardHeight, self.chessboardWidth, 2))
            # Calculate diffs along x and y directions for each square
            diffsX = np.diff(pointsReshaped, axis=1)[:, :-1, 0]  # Exclude the last diff which has no right neighbor
            diffsY = np.diff(pointsReshaped, axis=0)[:-1, :, 1]  # Exclude the last diff which has no bottom neighbor

            # Calculate the mean square size (in pixels) for this image
            meanSquareSizePx = np.mean([np.mean(diffsX), np.mean(diffsY)])
            squareSizesPx.append(meanSquareSizePx)

        # Calculate overall mean square size in pixels and convert to PPM
        squareSizePxMean = np.mean(squareSizesPx)
        ppm = squareSizePxMean / self.chessboardSquaresSize

        return ppm

    def calibrateCamera(self, image):
        """
           Performs camera calibration using the detected corners.

           Returns:
               tuple: The distortion coefficients, camera matrix, rotation vectors,
                      and translation vectors determined during calibration.
       """
        imageShape = image.shape[::-1]  # FIXME
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(self.objpoints, self.imgpoints, imageShape, None, None)
        return dist, mtx, rvecs, tvecs

    def calculateMeanError(self, dist, mtx, rvecs, tvecs):
        """
           Calculates the mean error of the reprojected points against the original detected corners.

           Parameters:
               dist (np.ndarray): The distortion coefficients.
               mtx (np.ndarray): The camera matrix.
               rvecs (list): List of rotation vectors.
               tvecs (list): List of translation vectors.

           Returns:
               float: The mean error across all calibration images.
       """
        meanError = 0.0
        for i in range(len(self.objpoints)):
            imgpoints2, _ = cv2.projectPoints(self.objpoints[i], rvecs[i], tvecs[i], mtx, dist)
            error = cv2.norm(self.imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            meanError += error
        return meanError

    def saveCalibrationData(self, mtx, dist, ppm, path):
        """
            Saves the calibration data to a file.

            Parameters:
                mtx (np.ndarray): The camera matrix.
                dist (np.ndarray): The distortion coefficients.
                ppm (float): The pixels-per-metric ratio.
                path: (str) Path to the directory where the calibration data is saved
        """

        filename = os.path.join(path, "camera_calibration.npz")
        np.savez(filename, mtx=mtx, dist=dist, ppm=ppm)

    def performCameraCalibration(self, image, path):

        """
        Perform camera calibration using the provided image.

        Parameters:
            path: (str) Path to the directory where the calibration data is saved
            image (np.ndarray): The input image for calibration.

        Returns:
            tuple: A tuple containing a boolean indicating if calibration was successful,
                   the calibration data (distortion coefficients, camera matrix, rotation vectors,
                   and translation vectors), the image and the coordinates of the detected corners.
        """
        if image is None:
            raise ValueError("Image is None")
        # Convert image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # cv2.imwrite("image.jpg", image)
        # Find corners in the grayscale image
        # cv2.imwrite("gray.jpg", gray)
        ret, corners = self.findCorners(gray)
        print(f"ret, corners = {ret} , {corners}")

        if not ret:
            # Corner detection failed
            print("Failed to find corners in the image.")
            return False, None, None, None

        # Refine corners for sub-pixel accuracy
        cornersRefined = self.refineCorners(gray, corners)

        # Draw refined corners on the image
        self.drawCorners(image, cornersRefined, ret)

        # Append corners for calibration
        self.appendCorners(cornersRefined)

        # Calculate pixels-per-metric ratio
        ppm = self.calculatePpm()

        # Calibrate camera
        dist, mtx, rvecs, tvecs = self.calibrateCamera(gray)

        # Calculate mean error
        meanError = self.calculateMeanError(dist, mtx, rvecs, tvecs)

        # Save calibration data
        self.saveCalibrationData(mtx, dist, ppm, path)

        # Return calibration success, calibration data, and image
        return True, (dist, mtx, rvecs, tvecs, ppm, meanError), image, corners


if __name__ == "__main__":
    camera = Camera(cameraIndex=0, width=1920, height=1080)

    calibrator = CameraCalibrator(10, 15, 25)
    calibrator.winZone = (12, 12)
    calibrator.zeroZone = (-2, -2)
    calibrator.criteriaAccuracy = 0.005
    calibrator.criteriaMaxIterations = 60

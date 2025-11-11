"""
* File: PIDController.py
* Author: IlV
* Comments:
* Revision history:
* Date       Author      Description
* -----------------------------------------------------------------
** 100624     IlV         Initial release
* -----------------------------------------------------------------
*
"""

import cv2
import numpy as np

from ..PID.PIDController import PIDController


class BrightnessController(PIDController):
    def __init__(self, Kp, Ki, Kd, setPoint):
        super().__init__(Kp, Ki, Kd, setPoint)

    def calculateBrightness(self, frame, roi_points=None):
        """
        Calculate the brightness of a frame, optionally within a specific region of interest.

        Args:
            frame (np.array): The frame to calculate the brightness of.
            roi_points (np.array, optional): Points defining the region of interest. 
                                           If None, calculates brightness of entire frame.

        Returns:
            float: The brightness of the frame or region.
        """
        # Convert the frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # If no ROI specified, calculate brightness of entire frame (backward compatibility)
        if roi_points is None:
            return cv2.mean(gray)[0]
        
        # Create mask for the region of interest
        mask = np.zeros(gray.shape[:2], dtype=np.uint8)
        
        # Convert points to proper format for fillPoly
        if len(roi_points.shape) == 3:
            # Already in (N, 1, 2) format
            roi_points_int = roi_points.astype(np.int32)
        else:
            # Convert (N, 2) to (N, 1, 2) format
            roi_points_int = roi_points.astype(np.int32).reshape((-1, 1, 2))
        
        # Fill the polygon area in the mask
        cv2.fillPoly(mask, [roi_points_int], 255)
        
        # Calculate mean brightness only within the masked region
        region_brightness = cv2.mean(gray, mask=mask)[0]
        
        return region_brightness

    def adjustBrightness(self, frame, adjustment, roi_points=None):
        """
        Adjust the brightness of a frame, optionally within a specific region of interest.

        Args:
            frame (np.array): The frame to adjust the brightness of.
            adjustment (float): The amount to adjust the brightness by.
            roi_points (np.array, optional): Points defining the region of interest. 
                                           If None, adjusts brightness of entire frame.

        Returns:
            np.array: The frame with adjusted brightness.
        """
        # Clip the adjustment to the range [-100, 100]
        adjustment = np.clip(adjustment, -100, 100)

        # If no ROI specified, adjust brightness of entire frame (backward compatibility)
        if roi_points is None:
            return cv2.convertScaleAbs(frame, alpha=1, beta=adjustment)
        
        # Region-based brightness adjustment - apply adjustment only to ROI
        adjusted_frame = frame.copy()
        
        # Create mask for the region of interest
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        
        # Convert points to proper format for fillPoly
        if len(roi_points.shape) == 3:
            # Already in (N, 1, 2) format
            roi_points_int = roi_points.astype(np.int32)
        else:
            # Convert (N, 2) to (N, 1, 2) format
            roi_points_int = roi_points.astype(np.int32).reshape((-1, 1, 2))
        
        # Fill the polygon area in the mask
        cv2.fillPoly(mask, [roi_points_int], 255)
        
        # Extract only the ROI region from the original frame
        roi_region = frame.copy()
        roi_region = np.where(mask[..., None], roi_region, 0)
        
        # Apply brightness adjustment only to the extracted ROI region
        roi_adjusted = cv2.convertScaleAbs(roi_region, alpha=1, beta=adjustment)
        
        # Apply the adjusted ROI back to the original frame using the mask
        adjusted_frame = np.where(mask[..., None], roi_adjusted, frame)
        
        return adjusted_frame
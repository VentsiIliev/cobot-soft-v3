import numpy as np
import cv2

def _isValid(sprayPatternList):
    """
  Check if the given spray pattern list is valid.

  Args:
      sprayPatternList (list): A list of spray pattern contours to be validated.

  Returns:
      bool: True if the spray pattern list is not empty and not None, False otherwise.
  """

    return sprayPatternList is not None and len(sprayPatternList) > 0

def _remove_contour(newContours, contour_to_remove):
    """
   Safely remove an exact matching contour from the newContours list.

   Args:
       newContours (list): List of contours from which the matching contour should be removed.
       contour_to_remove (array): The contour to be removed.

   Returns:
       None
   """

    for i, stored_contour in enumerate(newContours):
        if np.array_equal(stored_contour, contour_to_remove):
            del newContours[i]  # Remove the matching contour
            print(f"Removed Contour")
            return
    print(f"Error: Could not find an exact match to remove.")
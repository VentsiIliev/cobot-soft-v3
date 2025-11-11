"""
* File: arucoModule.py
* Author: IlV
* Comments:
* Revision history:
* Date       Author      Description
* -----------------------------------------------------------------
** 140524     IlV         Initial release
* -----------------------------------------------------------------
*
"""

import cv2


def get_corners(image, arucoIds, maxAttempts=10):
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    parameters = cv2.aruco.DetectorParameters()

    maxAttempts = maxAttempts
    found_markers = 0
    ids = None
    bboxes = None
    corners = [None, None, None, None]
    # FIND THE PROJECTION SCREEN COORDS
    while True:
        while maxAttempts > 0 and found_markers < len(arucoIds):
            detection_results = cv2.aruco.detectMarkers(image, aruco_dict, parameters=parameters)
            bboxes, ids, _ = detection_results
            if ids is None:
                continue
            for idx in ids:
                if idx in arucoIds:
                    found_markers += 1
                    print("Marker found", idx)
            maxAttempts -= 1

        all_detected = True
        for idx in arucoIds:
            if idx not in ids:
                all_detected = False

        if ids is not None and all_detected is True:
            # Match the detected markers with their respective IDs
            for bbox, marker_id in zip(bboxes, ids):
                if marker_id[0] == arucoIds[0]:  # Top left marker ID
                    corners[0] = bbox[0][0]

                elif marker_id[0] == arucoIds[1]:  # Top right marker ID
                    corners[1] = bbox[0][0]

                elif marker_id[0] == arucoIds[2]:  # Bottom right marker ID
                    corners[2] = bbox[0][0]

                elif marker_id[0] == arucoIds[3]:  # Bottom left marker ID
                    corners[3] = bbox[0][0]

            return [corners[0], corners[1], corners[2], corners[3]], ids
        else:
            print("not detected")
            return None, None

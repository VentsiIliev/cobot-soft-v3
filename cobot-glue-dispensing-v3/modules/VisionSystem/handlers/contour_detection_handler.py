import cv2
import numpy as np

from libs.plvision.PLVision import Contouring


def findContours(vision_system, imageParam):
    """
    Converts an image to grayscale, applies thresholding, performs dilation and erosion, and finds contours.
    """
    gray = cv2.cvtColor(imageParam, cv2.COLOR_BGR2GRAY)
    # print("applied gray")
    # Apply Gaussian blur if enabled
    if vision_system.camera_settings.get_gaussian_blur():
        # print(f"using blur")
        blur_kernel_size = vision_system.camera_settings.get_blur_kernel_size()
        # Ensure kernel size is odd
        if blur_kernel_size % 2 == 0:
            blur_kernel_size += 1
        blur = cv2.GaussianBlur(gray, (blur_kernel_size, blur_kernel_size), 0)
    else:
        blur = gray

    # Apply threshold with configurable type
    threshold_type = vision_system.camera_settings.get_threshold_type()
    threshold_types = {
        "binary": cv2.THRESH_BINARY,
        "binary_inv": cv2.THRESH_BINARY_INV,
        "trunc": cv2.THRESH_TRUNC,
        "tozero": cv2.THRESH_TOZERO,
        "tozero_inv": cv2.THRESH_TOZERO_INV
    }

    thresh_type = threshold_types.get(threshold_type, cv2.THRESH_BINARY_INV)

    threshold = vision_system.get_thresh_by_area(vision_system.threshold_by_area)

    # print(f"Using threshold {thresh_type} for area {self.threshold_by_area}")
    # print(f"Threshold = {threshold}")
    _, thresh = cv2.threshold(blur, threshold, 255, thresh_type)
    unique_vals = np.unique(thresh)
    # print("Unique pixel values in thresh:", unique_vals)

    vision_system.message_publisher.publish_thresh_image(thresh)
    # Apply dilation if enabled
    if vision_system.camera_settings.get_dilate_enabled():
        dilate_kernel_size = vision_system.camera_settings.get_dilate_kernel_size()
        dilate_iterations = vision_system.camera_settings.get_dilate_iterations()
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (dilate_kernel_size, dilate_kernel_size))
        thresh = cv2.dilate(thresh, kernel, iterations=dilate_iterations)

    # Apply erosion if enabled
    if vision_system.camera_settings.get_erode_enabled():
        erode_kernel_size = vision_system.camera_settings.get_erode_kernel_size()
        erode_iterations = vision_system.camera_settings.get_erode_iterations()
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (erode_kernel_size, erode_kernel_size))
        thresh = cv2.erode(thresh, kernel, iterations=erode_iterations)

    # Find contours on the processed image
    # cv2.imwrite("debug_thresh.png", thresh)

    # contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # print("Found contours:", len(contours))

    return contours

def approxContours(vision_system, contours):
    """
    Approximates contours using the Ramer-Douglas-Pucker algorithm.
    """
    # return contours
    approx = []
    for cnt in contours:
        epsilon = vision_system.camera_settings.get_epsilon() * cv2.arcLength(cnt, True)
        approx_contour = cv2.approxPolyDP(cnt, epsilon, True)
        approx.append(approx_contour)
    return approx

def filter_contours_by_area(vision_system, contours):
    """
    Filters contours based on minimum and maximum area settings.
    """
    filteredContours = [cnt for cnt in contours if
                        cv2.contourArea(cnt) > vision_system.camera_settings.get_min_contour_area()]
    filteredContours = [cnt for cnt in filteredContours if
                        cv2.contourArea(cnt) < vision_system.camera_settings.get_max_contour_area()]
    return filteredContours

# Squared distance function
def sq_dist(p1, p2):
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2

def all_inside_spray_area(vision_system, contour):
    for pt in contour:
        if cv2.pointPolygonTest(
            vision_system.data_manager.sprayAreaPoints.astype(np.float32),
            (float(pt[0][0]), float(pt[0][1])),
            False
        ) < 0:
            return False
    return True

def sort_contours_by_proximity(contours, start_point):
    sorted_contours = []
    current_point = start_point
    remaining_contours = contours.copy()

    while remaining_contours:
        # Find the contour with the closest centroid to the current point
        next_contour = min(
            remaining_contours,
            key=lambda cnt: sq_dist(Contouring.calculateCentroid(cnt), current_point)
        )
        sorted_contours.append(next_contour)
        current_point = Contouring.calculateCentroid(next_contour)
        remaining_contours.remove(next_contour)

    return sorted_contours

def handle_contour_detection(vision_system,sort=False):
    """
    Detect, filter, and sort contours in the image.
    Returns (sorted_contours, corrected_image, None)
    """
    # --- Step 1: Calibration handling ---
    if vision_system.isSystemCalibrated:
        vision_system.correctedImage = vision_system.correctImage(vision_system.image.copy())
    else:
        cv2.putText(
            vision_system.image,
            "System is not calibrated",
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
        )
        vision_system.correctedImage = vision_system.image

    # --- Step 2: Find and filter contours ---
    contours = findContours(vision_system, vision_system.correctedImage)
    approx_contours = approxContours(vision_system, contours)
    filtered_contours = filter_contours_by_area(vision_system, approx_contours)

    contours_inside_spray_area = []
    for cnt in filtered_contours:

        if all_inside_spray_area(vision_system, cnt):
            contours_inside_spray_area.append(cnt)

    if not contours_inside_spray_area:
        return None, vision_system.correctedImage, None

    final_contours = None
    if sort is True:
        # --- Step 3: Sort contours by proximity (using helper) ---
        top_left = (0, 0)
        contours_sorted = sort_contours_by_proximity(contours_inside_spray_area, start_point=top_left)
        final_contours = contours_sorted
    else:
        final_contours = contours_inside_spray_area

    # --- Step 4: Optional visualization ---
    if vision_system.camera_settings.get_draw_contours():
        cv2.drawContours(vision_system.correctedImage, final_contours, -1, (0, 255, 0), 1)

    # --- Step 5: Publish latest image ---
    vision_system.message_publisher.publish_latest_image(vision_system.correctedImage)

    return final_contours, vision_system.correctedImage, None



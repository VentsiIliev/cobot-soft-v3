import cv2

from src.backend.GlueDispensingApplication.utils.custom_logging import log_if_enabled, LoggingLevel
from libs.plvision.PLVision.arucoModule import ArucoDictionary, ArucoDetector


def detect_aruco_markers(vision_system,log_enabled,logger, flip=False, image=None):
    """
    Detect ArUco markers in the image.
    """
    # Use settings value if flip not specified
    if image is None:
        log_if_enabled(enabled=log_enabled,
                       logger=logger,
                       level=LoggingLevel.INFO,
                       message="Image is None in detectArucoMarkers:",
                       broadcast_to_ui=False)

    if flip is None:
        flip = vision_system.camera_settings.get_aruco_flip_image()

    # Check if ArUco detection is enabled
    # if not self.camera_settings.get_aruco_enabled():
    #     return None, None, None

    enableContourDrawingAfterDetection = vision_system.camera_settings.get_draw_contours()
    if vision_system.camera_settings.get_draw_contours():
        vision_system.camera_settings.set_draw_contours(False)

    if image is None:
        skip = 30
        while skip > 0:
            image = vision_system.correctedImage
            skip -= 1

    if flip is True:
        image = cv2.flip(image, 1)

    # Get ArUco dictionary from settings
    aruco_dict_name = vision_system.camera_settings.get_aruco_dictionary()

    aruco_dict = getattr(ArucoDictionary, aruco_dict_name, ArucoDictionary.DICT_4X4_1000)

    arucoDetector = ArucoDetector(arucoDict=aruco_dict)
    try:
        arucoCorners, arucoIds = arucoDetector.detectAll(image)
        log_if_enabled(enabled=log_enabled,
                       logger=logger,
                       level=LoggingLevel.INFO,
                       message=f"Detected {len(arucoIds)} ArUco markers",
                       broadcast_to_ui=False)
    except Exception as e:
        print(e)
        return None, None, None

    if enableContourDrawingAfterDetection:
        vision_system.camera_settings.set_draw_contours(True)

    return arucoCorners, arucoIds, image

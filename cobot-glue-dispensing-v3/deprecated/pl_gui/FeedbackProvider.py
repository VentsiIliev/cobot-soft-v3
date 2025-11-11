import os
from FeedbackWindow import FeedbackWindow
from FeedbackWindow import INFO_MESSAGE,WARNING_MESSAGE,ERROR_MESSAGE

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources","pl_ui_icons","messages")
PLACE_CHESSBOARD_ICON = os.path.join(RESOURCE_DIR,  "PLACE_CALIBRATION_PATTERN.png")
MOVE_CHESSBOARD_ICON = os.path.join(RESOURCE_DIR,  "MOVE_CALIBRATION_PATTERN.png")

class FeedbackProvider:
    def __init__(self):
        pass


    @staticmethod
    def showPlaceCalibrationPattern():
        feedbackWindow = FeedbackWindow(PLACE_CHESSBOARD_ICON,INFO_MESSAGE)
        feedbackWindow.show_feedback()

    @staticmethod
    def showMessage(message):
        feedbackWindow = FeedbackWindow(message = message, message_type =INFO_MESSAGE)
        feedbackWindow.show_feedback()
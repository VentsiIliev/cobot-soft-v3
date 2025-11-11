import os
import sys

from PyQt6.QtWidgets import QApplication

from modules.shared.localization.enums.Message import Message
from src.frontend.pl_ui.localization.container import get_app_translator
from src.frontend.pl_ui.ui.widgets.FeedbackWindow import FeedbackWindow, INFO_MESSAGE, WARNING_MESSAGE, ERROR_MESSAGE

from src.frontend.pl_ui.utils.IconLoader import PLACE_CHESSBOARD_ICON
from src.frontend.pl_ui.utils.IconLoader import MOVE_CHESSBOARD_ICON

class FeedbackProvider:
    def __init__(self):
        pass


    @staticmethod
    def showPlaceCalibrationPattern():
        feedbackWindow = FeedbackWindow(PLACE_CHESSBOARD_ICON,INFO_MESSAGE)
        feedbackWindow.show_feedback()

    @staticmethod
    def showMessage(message):
        # check if message is simple string
        if type(message) is str:
            feedbackWindow = FeedbackWindow(message = message, message_type =INFO_MESSAGE)
            feedbackWindow.show_feedback()
        else:
            if not isinstance(message,Message):
                raise TypeError("message must be of type str or Message Enum")
            # translate the message and display it
            translator = get_app_translator()
            translator.tr(message.value)
            # pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    FeedbackProvider.showPlaceCalibrationPattern()
    FeedbackProvider.showMessage("This is an information message.")
    sys.exit(app.exec_())
import sys

from PyQt6.QtWidgets import QApplication

from deprecated.pl_gui.MainWindow import MainWindow
from deprecated.pl_gui.dashboard.DashboardContent import MainContent
#
from .LoginWindow import LoginWindow
import os

DEFAULT_SCREEN_WIDTH = 1280
DEFAULT_SCREEN_HEIGHT = 720
SHOW_FULLSCREEN = True
WINDOW_TITLE = "PL Project"
SETTINGS_STYLESHEET = os.path.join("pl_gui","styles.qss")
class PlGui:

    def __init__(self, controller=None):
        self.controller = controller
        self.requires_login = True
        self.window = None



    def start(self):
        app = QApplication(sys.argv)
        # Load stylesheet from file
        try:
            with open(SETTINGS_STYLESHEET, "r") as file:
                app.setStyleSheet(file.read())
                print("Stylesheets applied")
        except FileNotFoundError:
            print("Stylesheet file not found. Using default styles.")


        dashboardContent = MainContent(screenWidth=DEFAULT_SCREEN_WIDTH,controller=self.controller)

        self.window = MainWindow(dashboardContent,self.controller)
        dashboardContent.parent = self.window

        self.window.setWindowTitle(WINDOW_TITLE)
        self.window.setMinimumSize(DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT)
        self.window.setGeometry(100, 100, DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT)
        self.window.setContentsMargins(0, 0, 0, 0)

        dashboardContent.screenWidth = self.window.screen_width
        dashboardContent.drawer.callback = self.window.logout
        self.window.main_content = dashboardContent
        if SHOW_FULLSCREEN:
            self.window.showFullScreen()
        else:
            self.window.show()

        if self.requires_login:
            self.window.setEnabled(False)
            login = LoginWindow(self.controller,onLogEventCallback=self.window.onLogEvent,header=self.window.header)
            login.showFullScreen()  # show fullscreen but non-blocking
            if login.exec():  # This now blocks until login accepted/rejected
                from datetime import datetime
                login_timestamp = datetime.now()
                print(f"Logged in successfully at {login_timestamp}")

                self.window.setEnabled(True)
            else:
                print("Login failed or cancelled")
                return  # Instead of sys.exit(0), we just return and do not proceed

        sys.exit(app.exec())  # Only call this once after everything is set up


# if __name__ == "__main__":
#     gui = PlGui()
#     gui.start()
import sys

from PyQt6.QtWidgets import QApplication

#
from deprecated.pl_gui.main_application.login.LoginWindow import LoginWindow

from deprecated.pl_gui.main_application.NewMainWindow import ApplicationMainWindow

CONFIG_FILE = "pl_gui/pl_gui_config.json"

SHOW_FULLSCREEN = False
WINDOW_TITLE = "PL Project"


# SETTINGS_STYLESHEET = os.path.join("pl_gui","styles.qss")
class PlGui:

    def __init__(self, controller=None):
        self.controller = controller
        self.requires_login = True

    def start(self):
        app = QApplication(sys.argv)
        # app.setStyle('Fusion')

        gui = ApplicationMainWindow(self.controller)

        if SHOW_FULLSCREEN:
            gui.showFullScreen()
        else:
            gui.show()

        if self.requires_login:
            gui.lock()
            login = LoginWindow(self.controller, onLogEventCallback=gui.onLogEvent, header=gui.header)
            login.showFullScreen()  # show fullscreen but non-blocking
            if login.exec():  # This now blocks until login accepted/rejected
                from datetime import datetime
                login_timestamp = datetime.now()
                print(f"Logged in successfully at {login_timestamp}")

                gui.unlock()
            else:
                print("Login failed or cancelled")
                return  # Instead of sys.exit(0), we just return and do not proceed

        sys.exit(app.exec())  # Only call this once after everything is set up

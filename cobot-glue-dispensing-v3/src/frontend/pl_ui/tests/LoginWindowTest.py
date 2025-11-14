import sys

from PyQt6.QtWidgets import QApplication


from frontend.pl_ui.tests.mocks import MockController
from frontend.pl_ui.ui.windows.login.LoginWindow import LoginWindow


def on_log_event():
    print("Login successful!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = MockController()
    login_window = LoginWindow(controller, on_log_event, header=None)
    login_window.exec()

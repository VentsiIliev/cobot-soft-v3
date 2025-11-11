
import os
from datetime import datetime
from PyQt6.QtCore import QSize, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, QSizePolicy, QWidget, QApplication, QMainWindow
)
from PyQt6.QtGui import QIcon
from API.shared.user.Session import SessionManager
from API.localization.enums.Message import Message
from API.localization.LanguageResourceLoader import LanguageResourceLoader
from deprecated.pl_gui.customWidgets.Drawer import Drawer


class SessionInfoWidget(Drawer):
    RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
    LOGOUT_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "LOGOUT_BUTTON_SQUARE.png")
    logout_requested = pyqtSignal()

    def __init__(self, parent=None, onLogoutCallback=None):
        super().__init__(parent)
        self.callback = onLogoutCallback
        self.langLoader = LanguageResourceLoader()
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setStyleSheet("""
            QFrame#mainFrame {
                background-color: white;
                border-radius: 12px;
                border: 2px solid #905BA9;
            }
            QLabel {
                font-size: 16px;
                background: transparent;
            }
            QGroupBox {
                background: transparent;
                font-weight: bold;
                font-size: 18px;
                margin-top: 10px;
            }
            QPushButton#logoutButton {
                border: none;
                background: white;
            }
        """)
        self.initUI()
        self.update_info()

    def initUI(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.main_frame)

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.user_group = QGroupBox("")
        self.user_layout = QVBoxLayout()
        self.user_group.setLayout(self.user_layout)

        self.session_group = QGroupBox("")
        self.session_layout = QVBoxLayout()
        self.session_group.setLayout(self.session_layout)

        self.id_label = QLabel(self.langLoader.get_message(Message.ID))
        self.first_name_label = QLabel(self.langLoader.get_message(Message.FIRST_NAME))
        self.last_name_label = QLabel(self.langLoader.get_message(Message.LAST_NAME))
        self.role_label = QLabel(self.langLoader.get_message(Message.ROLE))

        self.login_time_label = QLabel(self.langLoader.get_message(Message.LOGIN_TIME))
        self.session_duration_label = QLabel(self.langLoader.get_message(Message.SESSION_DURATION))

        self.user_layout.addWidget(self.id_label)
        self.user_layout.addWidget(self.first_name_label)
        self.user_layout.addWidget(self.last_name_label)
        self.user_layout.addWidget(self.role_label)

        self.session_layout.addWidget(self.login_time_label)
        self.session_layout.addWidget(self.session_duration_label)

        layout.addWidget(self.user_group)
        layout.addWidget(self.session_group)
        layout.addStretch()

        logout_container = QWidget()
        logout_layout = QHBoxLayout()
        logout_layout.setContentsMargins(0, 0, 0, 0)
        logout_container.setLayout(logout_layout)

        self.logout_button = QPushButton()
        self.logout_button.setObjectName("logoutButton")
        icon = QIcon(self.LOGOUT_BUTTON_ICON_PATH)
        self.logout_button.setIcon(icon)
        self.logout_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.logout_button.setMinimumWidth(100)
        self.logout_button.setIconSize(QSize(48, 48))
        self.logout_button.clicked.connect(self.on_logout_clicked)

        logout_layout.addWidget(self.logout_button)
        layout.addWidget(logout_container)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.user_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.session_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def on_logout_clicked(self):
        self.logout_requested.emit()
        print("Logout button clicked")
        if self.callback:
            self.callback()
        else:
            print("Logout callback is None")

    def update_info(self):
        user = SessionManager.get_current_user()
        session = SessionManager._current_session

        if user:
            self.id_label.setText(f"{self.langLoader.get_message(Message.ID)}: {user.id}")
            self.first_name_label.setText(f"{self.langLoader.get_message(Message.FIRST_NAME)}: {user.firstName}")
            self.last_name_label.setText(f"{self.langLoader.get_message(Message.LAST_NAME)}: {user.lastName}")
            self.role_label.setText(f"{self.langLoader.get_message(Message.ROLE)}: {user.role.value}")
        else:
            self.id_label.setText(f"{self.langLoader.get_message(Message.ID)}: -")
            self.first_name_label.setText(f"{self.langLoader.get_message(Message.FIRST_NAME)}: -")
            self.last_name_label.setText(f"{self.langLoader.get_message(Message.LAST_NAME)}: -")
            self.role_label.setText(f"{self.langLoader.get_message(Message.ROLE)}: -")

        if session:
            login_time = session.login_time.strftime("%Y-%m-%d %H:%M:%S")
            self.login_time_label.setText(f"{self.langLoader.get_message(Message.LOGIN_TIME)}: {login_time}")

            now = datetime.now()
            duration = now - session.login_time
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.session_duration_label.setText(
                f"{self.langLoader.get_message(Message.SESSION_DURATION)}: {hours}h {minutes}m {seconds}s"
            )
        else:
            self.login_time_label.setText(f"{self.langLoader.get_message(Message.LOGIN_TIME)}: -")
            self.session_duration_label.setText(f"{self.langLoader.get_message(Message.SESSION_DURATION)}: -")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        icon_size = max(24, min(128, width // 5))
        self.logout_button.setIconSize(QSize(icon_size, icon_size))

# --- Test MainWindow for demonstration ---

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    # Mock user and session data
    class MockRole:
        value = "Admin"

    class MockUser:
        id = 2
        firstName = "John"
        lastName = "Doe"
        role = MockRole()

    class MockSession:
        login_time = datetime.now()

    # Patch SessionManager for mock data
    SessionManager.get_current_user = staticmethod(lambda: MockUser())
    SessionManager._current_session = MockSession()

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Session Info Example")
            self.setGeometry(100, 100, 400, 300)
            self.session_info_drawer = SessionInfoWidget(self)
            self.session_info_drawer.setFixedWidth(300)
            toggle_btn = QPushButton("Toggle Session Drawer", self)
            toggle_btn.clicked.connect(self.session_info_drawer.toggle)
            self.setCentralWidget(toggle_btn)

        def resizeEvent(self, event):
            super().resizeEvent(event)
            self.session_info_drawer.resize_to_parent_height()

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
"""
SessionInfoWidget migrated to use the new localization system.
This is an example of how to convert existing widgets.

BEFORE (old system):
- Manual import of LanguageResourceLoader and Message
- Creating langLoader instance in __init__
- Manual MessageBroker subscription for language changes
- Calling langLoader.get_message() throughout the code
- No automatic updates on language changes

AFTER (new system):
- Single import from pl_ui.localization
- Using TranslatableMixin for translation capabilities
- Automatic language change handling
- Clean tr() calls with organized keys
- No manual broker subscriptions needed
"""

import os
from datetime import datetime
from PyQt6.QtCore import QSize, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton, QSizePolicy, QWidget
)
from PyQt6.QtGui import QIcon

from modules.shared.shared.user.Session import SessionManager
from src.frontend.pl_ui.ui.widgets.Drawer import Drawer
from src.frontend.pl_ui.utils.IconLoader import LOGOUT_BUTTON_ICON_PATH

# Update the import
from src.frontend.pl_ui.localization import TranslationKeys, TranslatableDrawer


class SessionInfoWidget(TranslatableDrawer):

    def __init__(self, parent=None, onLogoutCallback=None):
        # Initialize TranslatableDrawer (handles both Drawer and translation setup)
        super().__init__(parent)

        self.callback = onLogoutCallback

        # Initialize UI elements
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

        # Initialize translations after UI is created (one line!)
        self.init_translations()

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

        # Create labels without text - text set in retranslate()
        self.id_label = QLabel()
        self.first_name_label = QLabel()
        self.last_name_label = QLabel()
        self.role_label = QLabel()

        self.login_time_label = QLabel()
        self.session_duration_label = QLabel()

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
        icon = QIcon(LOGOUT_BUTTON_ICON_PATH)
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

    def retranslate(self):
        """
        NEW: Automatic translation updates.
        Called automatically when language changes - no manual subscription needed!
        """
        # Update all static text labels with organized translation keys
        self.id_label.setText(self.tr(TranslationKeys.User.ID))
        self.first_name_label.setText(self.tr(TranslationKeys.User.FIRST_NAME))
        self.last_name_label.setText(self.tr(TranslationKeys.User.LAST_NAME))
        self.role_label.setText(self.tr(TranslationKeys.User.ROLE))

        self.login_time_label.setText(self.tr(TranslationKeys.User.LOGIN_TIME))
        self.session_duration_label.setText(self.tr(TranslationKeys.User.SESSION_DURATION))

        # Update with current data
        self.update_info()

    def on_logout_clicked(self):
        print("Logout button clicked")
        if self.callback:
            self.callback()
        else:
            print("Logout callback is None")

    def update_info(self):
        """Update session information with current data."""
        user = SessionManager.get_current_user()
        session = SessionManager._current_session

        if user:
            # NEW: Clean translation calls with organized keys
            self.id_label.setText(f"{self.tr(TranslationKeys.User.ID)}: {user.id}")
            self.first_name_label.setText(f"{self.tr(TranslationKeys.User.FIRST_NAME)}: {user.firstName}")
            self.last_name_label.setText(f"{self.tr(TranslationKeys.User.LAST_NAME)}: {user.lastName}")
            self.role_label.setText(f"{self.tr(TranslationKeys.User.ROLE)}: {user.role.value}")
        else:
            self.id_label.setText(f"{self.tr(TranslationKeys.User.ID)}: -")
            self.first_name_label.setText(f"{self.tr(TranslationKeys.User.FIRST_NAME)}: -")
            self.last_name_label.setText(f"{self.tr(TranslationKeys.User.LAST_NAME)}: -")
            self.role_label.setText(f"{self.tr(TranslationKeys.User.ROLE)}: -")

        if session:
            login_time = session.login_time.strftime("%Y-%m-%d %H:%M:%S")
            self.login_time_label.setText(f"{self.tr(TranslationKeys.User.LOGIN_TIME)}: {login_time}")

            now = datetime.now()
            duration = now - session.login_time
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.session_duration_label.setText(
                f"{self.tr(TranslationKeys.User.SESSION_DURATION)}: {hours}h {minutes}m {seconds}s"
            )
        else:
            self.login_time_label.setText(f"{self.tr(TranslationKeys.User.LOGIN_TIME)}: -")
            self.session_duration_label.setText(f"{self.tr(TranslationKeys.User.SESSION_DURATION)}: -")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        icon_size = max(24, min(128, width // 5))
        self.logout_button.setIconSize(QSize(icon_size, icon_size))

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    main_window = QMainWindow()
    drawer = SessionInfoWidget(parent=main_window)
    main_window.setCentralWidget(drawer)
    main_window.resize(400, 600)
    main_window.show()
    sys.exit(app.exec())
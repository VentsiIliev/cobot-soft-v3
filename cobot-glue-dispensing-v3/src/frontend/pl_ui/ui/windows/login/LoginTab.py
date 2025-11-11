from typing import Callable

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout
)

from src.frontend.pl_ui.ui.widgets.virtualKeyboard.VirtualKeyboard import FocusLineEdit
from src.frontend.pl_ui.utils.IconLoader import LOGIN_BUTTON
from src.frontend.pl_ui.localization import TranslationKeys, TranslatableWidget
from src.frontend.pl_ui.ui.widgets.MaterialButton import MaterialButton
from src.frontend.pl_ui.utils.styles.globalStyles import FONT,MATERIAL_BUTTON_PRIMARY_COLOR

class LoginTab(TranslatableWidget):
    """Standard username/password login tab"""

    login_requested = pyqtSignal(str, str)

    def __init__(self, on_login_callback: Callable[[str, str], None], parent=None) -> None:
        super().__init__(parent, auto_retranslate=False)
        self.on_login_callback = on_login_callback
        self.font: QFont = QFont(FONT, 16, QFont.Weight.Bold)
        self.label: QLabel
        self.username_input: FocusLineEdit
        self.password_input: FocusLineEdit
        self.login_button: QPushButton
        self.setup_ui()
        
        # Initialize translations after UI is created
        self.init_translations()

    def setup_ui(self) -> None:
        layout: QVBoxLayout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Create labels without text - text will be set in retranslate()
        self.label = QLabel()
        self.label.setFont(self.font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        layout.addStretch(1)

        # Username input
        self.username_input = FocusLineEdit(parent=self)
        self.username_input.setFixedHeight(40)
        self.username_input.setStyleSheet("""
            border-radius: 10px;
            border: 2px solid purple;
            color: black;
            font-family: Arial;
            font-size: 14px;
            text-transform: uppercase;
        """)
        layout.addWidget(self.username_input)

        # Password input
        self.password_input = FocusLineEdit(parent=self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(40)
        self.password_input.setStyleSheet("""
            border-radius: 10px;
            border: 2px solid purple;
            color: black;
            font-family: Arial;
            font-size: 14px;
            text-transform: uppercase;
        """)
        layout.addWidget(self.password_input)

        layout.addStretch(2)

        # Login button
        button_layout: QHBoxLayout = QHBoxLayout()
        # self.login_button = QPushButton()
        self.login_button = MaterialButton(
            text=self.tr(TranslationKeys.Auth.LOGIN))
        self.login_button.clicked.connect(self.handle_field_login)
        button_layout.addWidget(self.login_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def handle_field_login(self) -> None:
        """Handle login when button is pressed"""
        import time
        timestamp = time.time()
        print(f"=== LoginTab.handle_field_login() called at {timestamp} ===")
        username: str = self.username_input.text()
        password: str = self.password_input.text()
        print(f"=== About to call callback with {username} at {timestamp} ===")
        # Using direct callback instead of signal emission
        self.on_login_callback(username, password)
        print(f"=== Callback completed at {timestamp} ===")

    def retranslate(self) -> None:
        """Update all text labels for language changes - called automatically"""
        self.label.setText(self.tr(TranslationKeys.Auth.LOGIN))
        self.username_input.setPlaceholderText(self.tr(TranslationKeys.Auth.ID))
        self.password_input.setPlaceholderText(self.tr(TranslationKeys.Auth.PASSWORD))
        self.login_button.setText(self.tr(TranslationKeys.Auth.LOGIN))
    def resize_elements(self, window_width: int, window_height: int) -> None:
        """Handle responsive design for button sizing"""
        button_width: int = max(160, min(int(window_width * 0.3), 300))
        button_height: int = max(70, min(int(window_height * 0.15), 120))
        icon_size: QSize = QSize(
            max(60, min(int(window_width * 0.12), 100)),
            max(60, min(int(window_width * 0.12), 100))
        )

        self.login_button.setFixedSize(button_width, button_height)
        self.login_button.setIconSize(icon_size)

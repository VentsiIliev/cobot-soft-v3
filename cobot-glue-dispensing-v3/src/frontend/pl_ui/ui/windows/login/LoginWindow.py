import os
import warnings
from typing import Any, Callable, Optional

from PyQt6.QtCore import Qt, QSize, QEvent
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QStackedLayout, QWidget,
    QTabWidget, QLabel, QDialog
)

from frontend.pl_ui.localization import TranslationKeys, TranslatableDialog

from frontend.pl_ui.ui.widgets.CustomFeedbackDialog import CustomFeedbackDialog, DialogType
from frontend.pl_ui.ui.widgets.Header import Header
from frontend.pl_ui.ui.widgets.ToastWidget import ToastWidget
from frontend.pl_ui.ui.windows.login.LoginController import LoginController
from frontend.pl_ui.ui.windows.login.LoginTab import LoginTab
from frontend.pl_ui.ui.windows.login.QRLoginTab import QRLoginTab
from frontend.pl_ui.ui.windows.login.SetupStepsWidget import SetupStepsWidget
from frontend.pl_ui.utils.IconLoader import LOGIN_BUTTON, LOGIN_QR_BUTTON, LOGO
from modules.shared.utils.jsonUtils import load_json_file

# Suppress specific DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning, message="sipPyTypeDict() is deprecated")
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))

# Resolve the base directory of this file
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SETTINGS_PATH = os.path.join(BASE_DIR, "loginWindowConfig.json")


class LoginWindow(TranslatableDialog):
    def __init__(self, controller: Any, onLogEventCallback: Callable[[], None], header: Optional[Header] = None) -> None:
        super().__init__(auto_retranslate=False)
        self._allow_close = False
        self.ui_settings: dict[str, Any] = self.load_ui_settings()
        self.onLogEventCallback: Callable[[], None] = onLogEventCallback
        self.header: Header = Header(self.width(), self.height(), None, None)

        self.controller: Any = controller
        self.loginController: LoginController = LoginController(self.controller)
        self.font: QFont = QFont("Arial", 16, QFont.Weight.Bold)
        self.font_small: QFont = QFont("Arial", 14)

        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("background-color: white;")
        self.setup_ui()
        
        # Initialize translations after UI is created
        self.init_translations()
        from modules.shared.MessageBroker import MessageBroker
        broker = MessageBroker()
        broker.publish("vison-auto-brightness","stop")

    def setup_ui(self) -> None:
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.header.menu_button.setVisible(False)
        self.header.dashboardButton.setVisible(False)
        self.header.power_toggle_button.setVisible(False)
        outer_layout.addWidget(self.header)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Logo container
        logo_container = self.create_logo_container()
        main_layout.addWidget(logo_container, 1)

        # Right side with stacked layout
        self.right_stack = QStackedLayout()

        # Create setup steps widget (now using new localization system)
        self.step_widget: SetupStepsWidget = SetupStepsWidget(
            self.controller,
            parent=self
        )

        # Create tabs widget
        self.tabs_widget: QTabWidget = self.create_tabs_widget()
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # Add widgets to stack
        self.right_stack.addWidget(self.step_widget)
        self.right_stack.addWidget(self.tabs_widget)

        right_container = QWidget()
        right_container.setLayout(self.right_stack)
        main_layout.addWidget(right_container, 2)

        outer_layout.addLayout(main_layout)
        self.setLayout(outer_layout)

    def on_tab_changed(self) -> None:
        """Handle switching to QR tab"""
        if self.tabs.currentIndex() == 1:
            warning_dialog = CustomFeedbackDialog(
                parent=self,
                dialog_type=DialogType.WARNING,
                # 👈 key addition: use one of ['warning', 'info', 'success', 'error', 'feedback']
                title=self.tr(TranslationKeys.Warning.WARNING),
                message=self.tr(TranslationKeys.Warning.THE_ROBOT_WILL_START_MOVING_TO_THE_LOGIN_POSITION),
                info_text=self.tr(TranslationKeys.Warning.PLEASE_ENSURE_THE_AREA_IS_CLEAR_BEFORE_PROCEEDING),
                ok_text="OK",  # optional
                cancel_text=self.tr(TranslationKeys.Warning.CANCEL)  # optional
            )

            result = warning_dialog.exec()
            if result == QDialog.DialogCode.Accepted:
                self.controller.handleLoginPos()
            else:
                self.tabs.setCurrentIndex(0)
                print("Cancelled switching to QR login tab")

        else:
            print("Switched to normal login tab")

    def create_logo_container(self) -> QWidget:
        """Create the logo container widget"""
        logo_container = QWidget()
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.logo_label = QLabel()
        pixmap = QPixmap(LOGO)
        self.original_logo_pixmap: QPixmap = pixmap
        self.logo_label.setPixmap(
            pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(self.logo_label)
        logo_container.setLayout(logo_layout)
        logo_container.setStyleSheet("""
            background: qlineargradient(
                x1: 0, y1: 0,
                x2: 1, y2: 1,
                stop: 0 #d5c6f6,
                stop: 1 #b8b5e0
            );
        """)
        return logo_container

    def create_tabs_widget(self) -> QTabWidget:
        """Create the tabs widget with login and QR tabs"""
        self.tabs = QTabWidget()
        self.tabs.setIconSize(QSize(40, 40))

        self.login_tab: LoginTab = LoginTab(self.handle_login, parent=self)
        # Signal connection removed - already connected via constructor callback
        # QRLoginTab now using new localization system
        self.qr_tab: QRLoginTab = QRLoginTab(self.controller, self.handle_login, parent=self)

        self.tabs.addTab(self.login_tab, QIcon(LOGIN_BUTTON), "")
        self.tabs.addTab(self.qr_tab, QIcon(LOGIN_QR_BUTTON), "")

        default_login: str = self.ui_settings.get("DEFAULT_LOGIN", "NORMAL").upper()
        if default_login == "QR":
            self.tabs.setCurrentIndex(1)
        else:
            self.tabs.setCurrentIndex(0)

        return self.tabs

    def retranslate(self) -> None:
        """Update all text labels for language changes - called automatically"""
        self.setWindowTitle(self.tr(TranslationKeys.Auth.LOGIN))

    def load_ui_settings(self) -> dict[str, Any]:
        """Load UI settings from JSON file"""
        return load_json_file(SETTINGS_PATH, {}, debug=True)


    def resizeEvent(self, event: QEvent) -> None:
        """Handle window resize events"""
        new_width = self.width()
        new_height = self.height()

        logo_max_width = int(new_width * 0.2)
        logo_max_height = int(new_height * 0.4)
        logo_size = QSize(logo_max_width, logo_max_height)

        if hasattr(self, "original_logo_pixmap"):
            scaled_pixmap = self.original_logo_pixmap.scaled(
                logo_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)

        # self.login_tab.resize_elements(new_width, new_height)
        self.qr_tab.resize_elements(new_width, new_height)

        tab_icon_size = QSize(
            max(30, min(int(new_width * 0.08), 80)),
            max(30, min(int(new_width * 0.08), 80))
        )
        self.tabs.setIconSize(tab_icon_size)

        super().resizeEvent(event)

    def handle_login(self, username: str, password: str) -> None:
        """Handle login process for both tabs"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] === LOGIN ATTEMPT for user: {username} ===")
        result, message = self.loginController.handle_login(username, password)
        print(f"[{timestamp}] LoginController result: {result}, Message: {message}")
        if result is True:
            print(f"[{timestamp}] Login successful, stopping QR scanning and completing login...")
            
            # CRITICAL: Stop QR scanning immediately upon ANY successful login
            if hasattr(self, 'qr_tab') and self.qr_tab:
                print(f"[{timestamp}] Calling force_stop_scanning() on QR tab...")
                self.qr_tab.force_stop_scanning()
            
            print(f"[{timestamp}] Calling onLogEventCallback()...")
            self.onLogEventCallback()
            print(f"[{timestamp}] Callback completed, calling accept()...")
            self._allow_close = True
            self.accept()
            print(f"[{timestamp}] accept() completed")
        else:
            print(f"[{timestamp}] Login failed: {message}")
            toast = ToastWidget(self, message, 2)
            toast.show()

    def keyPressEvent(self, event):
        """Override to prevent ESC from closing the login window"""
        if event.key() == Qt.Key.Key_Escape:
            # Ignore ESC key - do nothing
            event.ignore()
            return

        # For all other keys, use default behavior
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """Prevent accidental window closing"""
        if not self._allow_close:
            event.ignore()
            return
        super().closeEvent(event)

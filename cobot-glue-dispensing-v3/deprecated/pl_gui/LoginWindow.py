from PyQt6.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QTabWidget, QWidget, QStackedLayout
)

from pl_ui.ui.widgets.CustomWarningDialog import CustomWarningDialog
from pl_ui.ui.widgets.virtualKeyboard.VirtualKeyboard import FocusLineEdit
from pl_ui.ui.widgets.CameraFeed import CameraFeed
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer
from pl_ui.ui.widgets.ToastWidget import ToastWidget
from API import Constants
import warnings
import os
import json
from API.localization.enums.Language import Language
from API.localization.LanguageResourceLoader import LanguageResourceLoader
from API.localization.enums.Message import Message
from pl_ui.ui.widgets.Header import Header
from API.MessageBroker import MessageBroker
from pl_ui.Endpoints import *


# Suppress specific DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning, message="sipPyTypeDict() is deprecated")
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
BACKGROUND = os.path.join(RESOURCE_DIR, "Background_&_Logo.png")
LOGIN_BUTTON = os.path.join(RESOURCE_DIR, "pl_ui_icons", "LOGIN_BUTTON_SQUARE.png")
LOGIN_QR_BUTTON = os.path.join(RESOURCE_DIR, "pl_ui_icons", "QR_CODE_BUTTON_SQUARE.png")
# MACHINE_BUTTONS_IMAGE = os.path.join(RESOURCE_DIR, "pl_ui_icons", "MACHINE_BUTTONS.png")
COBOT_IMAGE  = os.path.join(RESOURCE_DIR, "pl_ui_icons", "COBOT_IMAGE.png")
MACHINE_BUTTONS_IMAGE = os.path.join(RESOURCE_DIR, "pl_ui_icons", "MACHINE_BUTTONS_1.png")
LOGO = os.path.join(RESOURCE_DIR, "pl_ui_icons", "logo.ico")

# Resolve the base directory of this file
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SETTINGS_PATH = os.path.join(BASE_DIR, "system", "storage", "ui_settings", "ui_settings.json")


class LoginTab(QWidget):
    """Standard username/password login tab"""

    def __init__(self, controller, lang_loader, on_login_callback):
        super().__init__()
        self.controller = controller
        self.lang_loader = lang_loader
        self.on_login_callback = on_login_callback
        self.font = QFont("Arial", 16, QFont.Weight.Bold)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        self.label = QLabel(self.lang_loader.get_message(Message.LOGIN))
        self.label.setFont(self.font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        layout.addStretch(1)

        # self.username_input = QLineEdit()
        self.username_input = FocusLineEdit(parent=self)
        self.username_input.setPlaceholderText(self.lang_loader.get_message(Message.ID))
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

        self.password_input = FocusLineEdit(parent=self)
        self.password_input.setPlaceholderText(self.lang_loader.get_message(Message.PASSWORD))
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

        layout.addStretch(1)

        button_layout = QHBoxLayout()
        self.login_button = QPushButton("")
        self.login_button.setIcon(QIcon(LOGIN_BUTTON))
        self.login_button.setStyleSheet("border: none; background: transparent;")
        self.login_button.clicked.connect(self.handle_field_login)
        button_layout.addWidget(self.login_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def handle_field_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        self.on_login_callback(username, password)

    def update_labels(self,message = None):
        """Update all text labels for language changes"""
        self.label.setText(self.lang_loader.get_message(Message.LOGIN))
        self.username_input.setPlaceholderText(self.lang_loader.get_message(Message.ID))
        self.password_input.setPlaceholderText(self.lang_loader.get_message(Message.PASSWORD))

    def resize_elements(self, window_width, window_height):
        """Handle responsive design for button sizing"""
        button_width = max(160, min(int(window_width * 0.3), 300))
        button_height = max(70, min(int(window_height * 0.15), 120))
        icon_size = QSize(max(60, min(int(window_width * 0.12), 100)),
                          max(60, min(int(window_width * 0.12), 100)))

        self.login_button.setFixedSize(button_width, button_height)
        self.login_button.setIconSize(icon_size)


class QRLoginTab(QWidget):
    """QR code login tab"""

    def __init__(self, controller, lang_loader, on_login_callback):
        super().__init__()
        self.controller = controller
        self.lang_loader = lang_loader
        self.on_login_callback = on_login_callback
        self.font_small = QFont("Arial", 14)
        self.setup_ui()

    def setup_ui(self):
        # Stop contour detection when initializing QR tab
        self.controller.handle(STOP_CONTOUR_DETECTION)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        self.qr_label = QLabel(self.lang_loader.get_message(Message.SCAN_QR_TO_LOGIN))
        self.qr_label.setFont(self.font_small)
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.qr_label)

        layout.addStretch(1)

        # Add CameraFeed widget
        self.camera_feed = CameraFeed(updateCallback=self.get_camera_frame, toggleCallback=None)
        layout.addWidget(self.camera_feed, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(1)

        self.qr_button = QPushButton("")
        self.qr_button.setIcon(QIcon(LOGIN_QR_BUTTON))
        self.qr_button.setStyleSheet("border: none; background: transparent;")
        self.qr_button.clicked.connect(self.handle_qr_code)
        layout.addWidget(self.qr_button, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(2)
        self.setLayout(layout)

    def get_camera_frame(self):
        """Get camera frame for the camera feed"""
        # print("login feed update")
        return self.controller.handle(UPDATE_CAMERA_FEED)

    def handle_qr_code(self):
        """Handle QR code scanning and login"""
        self.controller.handle(START_CONTOUR_DETECTION)

        response = self.controller.handle(QR_LOGIN)
        if response is None:
            print("handle_qr_code response is None")
            return

        if response.status == Constants.RESPONSE_STATUS_SUCCESS:
            user_data = response.data
            user_id = user_data.get("id")
            password = user_data.get("password")
            self.on_login_callback(user_id, password)
        else:
            print("Failed to retrieve QR code data:", response)

    def update_labels(self):
        """Update all text labels for language changes"""
        self.qr_label.setText(self.lang_loader.get_message(Message.SCAN_QR_TO_LOGIN))

    def resize_elements(self, window_width, window_height):
        """Handle responsive design for button sizing"""
        button_width = max(160, min(int(window_width * 0.3), 300))
        button_height = max(70, min(int(window_height * 0.15), 120))
        icon_size = QSize(max(60, min(int(window_width * 0.12), 100)),
                          max(60, min(int(window_width * 0.12), 100)))

        self.qr_button.setFixedSize(button_width, button_height)
        self.qr_button.setIconSize(icon_size)


class SetupStepsWidget(QWidget):
    """Initial setup steps widget"""

    def __init__(self, controller, lang_loader, on_language_change_callback):
        super().__init__()
        self.controller = controller
        self.lang_loader = lang_loader
        self.on_language_change_callback = on_language_change_callback
        self.font = QFont("Arial", 16, QFont.Weight.Bold)
        self.font_small = QFont("Arial", 14)
        self.setStyleSheet("background-color: white;")
        self.setup_ui()
        broker = MessageBroker()
        broker.subscribe("Language",self.update_labels)

    def setup_ui(self):
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(20, 20, 20, 20)

        # Top layout with language selector
        top_layout = QHBoxLayout()
        top_layout.addStretch()

        outer_layout.addLayout(top_layout)

        # Add expanding spacer to center the label vertically
        outer_layout.addStretch()

        # Center content - just the label
        self.image_label = QLabel()
        self.image_label.setPixmap(QPixmap(MACHINE_BUTTONS_IMAGE).scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio,
                                                                         Qt.TransformationMode.SmoothTransformation))
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add a text label under the image
        self.instructions = QLabel(self.lang_loader.get_message(Message.SETUP_FIRST_STEP))
        self.instructions.setFont(self.font_small)
        self.instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(self.instructions, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add another expanding spacer to keep label centered
        outer_layout.addStretch()

        # Bottom buttons layout - always at the bottom
        bottom_buttons_layout = QHBoxLayout()
        bottom_buttons_layout.setContentsMargins(0, 0, 0, 20)  # Add some margin from the very bottom

        # Create Next button
        self.confirm_blue_button = QPushButton(self.lang_loader.get_message(Message.NEXT))
        self.confirm_blue_button.setFixedSize(200, 60)
        self.confirm_blue_button.setStyleSheet("""
            QPushButton {
                background-color: #905BA9;
                color: white;
                font-family: Arial;
                font-size: 16px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #905BA9;
            }
        """)
        self.confirm_blue_button.clicked.connect(self.user_confirmed_blue_button)

        bottom_buttons_layout.addWidget(self.confirm_blue_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Add bottom buttons layout to outer layout
        outer_layout.addLayout(bottom_buttons_layout)

        self.setLayout(outer_layout)



    def user_confirmed_blue_button(self):
        """Handle confirmation of blue button press"""
        # Directly switch to login after confirming first step
        parent = self.parentWidget()
        while parent and not isinstance(parent, LoginWindow):
            parent = parent.parentWidget()
        if parent and hasattr(parent, "right_stack") and hasattr(parent, "tabs_widget"):
            parent.right_stack.setCurrentWidget(parent.tabs_widget)

    def check_physical_button(self):
        """Check for physical button press"""
        if self.controller.is_blue_button_pressed():
            self.instructions.setText(Message.SETUP_FIRST_STEP)
            self.home_button.setVisible(True)
        else:
            # Keep checking every 500ms
            QTimer.singleShot(500, self.check_physical_button)

    def update_labels(self,mesasge=None):
        """Update all text labels for language changes"""
        self.instructions.setText(self.lang_loader.get_message(Message.SETUP_FIRST_STEP))
        self.confirm_blue_button.setText(self.lang_loader.get_message(Message.NEXT))
        # self.language_selector.update()


class LoginWindow(QDialog):
    def __init__(self, controller, onLogEventCallback,header):
        super().__init__()
        self.ui_settings = self.load_ui_settings()
        self.onLogEventCallback = onLogEventCallback
        self.header = Header(self.width(),self.height(),None,None)
        self.langLoader = LanguageResourceLoader()
        self.controller = controller
        self.dragging = False
        self.offset = QPoint()
        self.font = QFont("Arial", 16, QFont.Weight.Bold)
        self.font_small = QFont("Arial", 14)

        self.setWindowTitle(self.langLoader.get_message(Message.LOGIN))
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("background-color: white;")
        self.setup_ui()
        broker = MessageBroker()
        broker.subscribe("Language",self.updateLabels)

    def setup_ui(self):
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.header.hideMenuButton()
        self.header.hidePowerButton()
        self.header.hideDashboardButton()
        outer_layout.addWidget(self.header)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Logo container
        logo_container = self.create_logo_container()
        main_layout.addWidget(logo_container, 1)

        # Right side with stacked layout
        self.right_stack = QStackedLayout()

        # Create setup steps widget
        self.step_widget = SetupStepsWidget(
            self.controller,
            self.langLoader,
            self.handle_language_change,
        )

        # Create tabs widget
        self.tabs_widget = self.create_tabs_widget()
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # Add widgets to stack
        self.right_stack.addWidget(self.step_widget)
        self.right_stack.addWidget(self.tabs_widget)

        right_container = QWidget()
        right_container.setLayout(self.right_stack)
        main_layout.addWidget(right_container, 2)

        outer_layout.addLayout(main_layout)
        self.setLayout(outer_layout)

    def on_tab_changed(self):
        """Handle switching to QR tab"""
        if self.tabs.currentIndex() == 1:
            # Create custom warning dialog
            warning_dialog = CustomWarningDialog(
                parent=self,
                title="WARNING",
                message="THE ROBOT WILL START MOVING TO THE LOGIN POSITION.",
                info_text="Please ensure the area is clear before proceeding."
            )

            result = warning_dialog.exec()
            if warning_dialog.get_result() == "OK":
                self.controller.handle(GO_TO_LOGIN_POS)
            else:
                # Switch back to the previous tab if cancelled
                self.tabs.setCurrentIndex(0)
                print("Cancelled switching to QR login tab")
        else:
            print("Switched to normal login tab")

    def create_logo_container(self):
        """Create the logo container widget"""
        logo_container = QWidget()
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.logo_label = QLabel()
        pixmap = QPixmap(LOGO)
        self.original_logo_pixmap = pixmap
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

    def create_tabs_widget(self):
        """Create the tabs widget with login and QR tabs"""
        self.tabs = QTabWidget()
        self.tabs.setIconSize(QSize(40, 40))

        # Create tab instances
        self.login_tab = LoginTab(self.controller, self.langLoader, self.handle_login)
        self.qr_tab = QRLoginTab(self.controller, self.langLoader, self.handle_login)

        # Add tabs to widget
        self.tabs.addTab(self.login_tab, QIcon(LOGIN_BUTTON), "")
        self.tabs.addTab(self.qr_tab, QIcon(LOGIN_QR_BUTTON), "")

        # Set default tab based on settings
        default_login = self.ui_settings.get("DEFAULT_LOGIN", "NORMAL").upper()
        if default_login == "QR":
            self.tabs.setCurrentIndex(1)  # QR tab
        else:
            self.tabs.setCurrentIndex(0)  # Normal login tab

        return self.tabs

    def load_ui_settings(self):
        """Load UI settings from JSON file"""
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print("data", data)
                return data
        except Exception as e:
            print(f"Failed to load setting: {e}")
            return {}

    def handle_language_change(self, language: Language):
        """Handle language change event"""
        print(f"Selected Language Enum: {language.name}")
        self.updateLabels()

    def updateLabels(self,message= None):
        """Update all labels for language changes"""
        self.langLoader = LanguageResourceLoader()  # reload language resources if needed

        # Update window title
        self.setWindowTitle(self.langLoader.get_message(Message.LOGIN))

        # Update tab labels
        self.login_tab.update_labels()
        self.qr_tab.update_labels()
        self.step_widget.update_labels()

    def resizeEvent(self, event):
        """Handle window resize events"""
        new_width = self.width()
        new_height = self.height()

        # Calculate new size for logo
        logo_max_width = int(new_width * 0.2)
        logo_max_height = int(new_height * 0.4)
        logo_size = QSize(logo_max_width, logo_max_height)

        # Scale original pixmap to new size, keep aspect ratio
        if hasattr(self, "original_logo_pixmap"):
            scaled_pixmap = self.original_logo_pixmap.scaled(
                logo_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)

        # Resize tab elements
        self.login_tab.resize_elements(new_width, new_height)
        self.qr_tab.resize_elements(new_width, new_height)

        # Responsive icon size for tabs
        tab_icon_size = QSize(
            max(30, min(int(new_width * 0.08), 80)),
            max(30, min(int(new_width * 0.08), 80))
        )
        self.tabs.setIconSize(tab_icon_size)

        super().resizeEvent(event)

    def handle_login(self, username, password):
        """Handle login process for both tabs"""
        print("User", username)
        print("pass", password)

        if not username or not password:  # Check if either is None or empty
            toast = ToastWidget(self, self.langLoader.get_message(Message.ENTER_ID_AND_PASSWORD), 2)
            toast.show()
            return

        if not username.isdigit():  # Check if username is a number
            toast = ToastWidget(self, self.langLoader.get_message(Message.INVALID_LOGIN_ID), 2)
            toast.show()
            return

        message = self.controller.handleLogin(username, password)
        if message == "1":
            self.controller.handle(START_CONTOUR_DETECTION)
            self.accept()
            self.onLogEventCallback()
        elif message == "0":
            toast = ToastWidget(self, self.langLoader.get_message(Message.INCORRECT_PASSWORD), 2)
            toast.show()
        elif message == "-1":
            toast = ToastWidget(self, self.langLoader.get_message(Message.USER_NOT_FOUND), 2)
            toast.show()

    def handle_home_robot_result(self, result):
        """Handle the result from home robot operation"""
        print(f"Received home robot result: {result}")

        # Always switch to tabs widget
        self.right_stack.setCurrentWidget(self.tabs_widget)

        # Show toast message if there was an error
        if result != Constants.RESPONSE_STATUS_SUCCESS:
            toast = ToastWidget(self, self.langLoader.get_message(Message.ERROR_HOMING), 3)
            toast.show()

    def mousePressEvent(self, event):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging"""
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.offset)

    def mouseReleaseEvent(self, event):
        """Handle mouse release for window dragging"""
        self.dragging = False









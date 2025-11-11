import os
from typing import Callable, Optional

from PyQt6.QtCore import QSize, Qt, QEvent, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout, QPushButton, QFrame
)
from src.frontend.pl_ui.utils.styles.ComboBoxStyle import ComboBoxStyle
from src.frontend.pl_ui.utils.IconLoader import ACCOUNT_BUTTON_SQUARE

from modules.shared.MessageBroker import MessageBroker
from src.frontend.pl_ui.ui.widgets.LanguageSelectorWidget import LanguageSelectorWidget

# Resource paths
RESOURCE_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
MENU_ICON_PATH: str = os.path.join(RESOURCE_DIR, "pl_ui_icons", "SANDWICH_MENU.png")
LOGO_ICON_PATH: str = os.path.join(RESOURCE_DIR, "pl_ui_icons", "logo.ico")
ON_ICON_PATH: str = os.path.join(RESOURCE_DIR, "pl_ui_icons", "POWER_ON_BUTTON.png")
OFF_ICON_PATH: str = os.path.join(RESOURCE_DIR, "pl_ui_icons", "POWER_OFF_BUTTON.png")
DASHBOARD_BUTTON_ICON_PATH: str = os.path.join(RESOURCE_DIR, "pl_ui_icons", "DASHBOARD_BUTTON_SQUARE.png")


class Header(QFrame):
    user_account_clicked = pyqtSignal()
    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        toggle_menu_callback: Optional[Callable[[], None]],
        dashboard_button_callback: Optional[Callable[[], None]],
    ) -> None:
        super().__init__()
        self.broker: MessageBroker = MessageBroker()
        self.setContentsMargins(0, 0, 0, 0)
        self.screen_width: int = screen_width
        self.screen_height: int = screen_height
        self.setStyleSheet("background-color: white;")

        self.header_layout: QHBoxLayout = QHBoxLayout(self)
        self.header_layout.setContentsMargins(10, 0, 10, 0)
        self.header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Dashboard Button



        self.dashboardButton: QPushButton = QPushButton()
        self.dashboardButton.setIcon(QIcon(DASHBOARD_BUTTON_ICON_PATH))
        self.dashboardButton.clicked.connect(
            dashboard_button_callback if dashboard_button_callback else lambda: print("dashboard_button_callback is none")
        )
        self.dashboardButton.setStyleSheet("border: none; background: transparent; padding: 0px;")
        self.header_layout.addWidget(self.dashboardButton)

        # Menu Button
        self.menu_button: QPushButton = QPushButton()
        self.menu_button.setIcon(QIcon(MENU_ICON_PATH))
        self.menu_button.clicked.connect(
            toggle_menu_callback if toggle_menu_callback else lambda: print("toggle_menu_callback is none")
        )
        self.menu_button.setStyleSheet("border: none; background: transparent; padding: 0px;")
        self.header_layout.addWidget(self.menu_button)

        # Left stretch
        self.header_layout.addStretch()

        # Language Selector (centered)
        self.language_selector: LanguageSelectorWidget = LanguageSelectorWidget()
        self.language_selector.setObjectName("language_selector_combo")
        self.language_selector.languageChanged.connect(self.handle_language_change)
        self.language_selector.setFixedWidth(200)

        combo_style = ComboBoxStyle().generate_stylesheet("language_selector_combo")
        self.language_selector.setStyleSheet(combo_style)

        self.header_layout.addWidget(self.language_selector)

        # Right stretch
        self.header_layout.addStretch()

        # Power Toggle Button
        self.power_toggle_button: QPushButton = QPushButton()
        self.power_toggle_button.setIcon(QIcon(OFF_ICON_PATH))
        self.power_toggle_button.setToolTip("Power Off")
        self.power_toggle_button.setStyleSheet("border: none; background: white; padding: 0px;")
        self.power_toggle_button.clicked.connect(self.toggle_power)
        self.header_layout.addSpacing(20)
        self.header_layout.addWidget(self.power_toggle_button)

        self.power_on: bool = False  # Power state

        self.userAccountButton: QPushButton = QPushButton()
        self.userAccountButton.setIcon(QIcon(ACCOUNT_BUTTON_SQUARE))
        self.userAccountButton.setStyleSheet("border: none; background: transparent; padding: 0px;")
        self.userAccountButton.clicked.connect(self.on_user_account_clicked)
        self.userAccountButton.setVisible(False)
        self.header_layout.addWidget(self.userAccountButton)

        self.setMinimumHeight(int(self.screen_height * 0.08))
        self.setMaximumHeight(100)

    def on_user_account_clicked(self):
        self.user_account_clicked.emit()

    def toggle_power(self) -> None:
        self.power_on = not self.power_on
        icon: QIcon = QIcon(ON_ICON_PATH) if self.power_on else QIcon(OFF_ICON_PATH)
        tooltip: str = "Power On" if self.power_on else "Power Off"
        self.power_toggle_button.setIcon(icon)
        self.power_toggle_button.setToolTip(tooltip)
        print(f"Power turned {'ON' if self.power_on else 'OFF'}")

    def resizeEvent(self, event: QEvent) -> None:
        new_width: int = self.width()
        icon_size: int = int(new_width * 0.05)

        self.menu_button.setIconSize(QSize(icon_size, icon_size))
        self.power_toggle_button.setIconSize(QSize(icon_size, icon_size))
        self.dashboardButton.setIconSize(QSize(icon_size, icon_size))
        self.userAccountButton.setIconSize(QSize(icon_size, icon_size))
        super().resizeEvent(event)

    def handle_language_change(self, message: str) -> None:
        self.broker.publish("Language", "Change")
        # print("Language changed")




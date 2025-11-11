import os
import sys
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QPushButton, QFrame
)

from deprecated.pl_gui.customWidgets.LanguageSelectorWidget import LanguageSelectorWidget
from API.MessageBroker import MessageBroker
# Resource paths
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
MENU_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "SANDWICH_MENU.png")
LOGO_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "logo.ico")
ON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "POWER_ON_BUTTON.png")
OFF_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "POWER_OFF_BUTTON.png")
DASHBOARD_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "DASHBOARD_BUTTON_SQUARE.png")

class Header(QFrame):
    def __init__(self, screen_width, screen_height, toggle_menu_callback, dashboard_button_callback):
        super().__init__()
        self.broker = MessageBroker()
        self.setContentsMargins(0, 0, 0, 0)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.setStyleSheet("background-color: white;")

        self.header_layout = QHBoxLayout(self)
        self.header_layout.setContentsMargins(10, 0, 10, 0)
        self.header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Dashboard Button
        self.dashboardButton = QPushButton()
        self.dashboardButton.setIcon(QIcon(DASHBOARD_BUTTON_ICON_PATH))
        self.dashboardButton.clicked.connect(dashboard_button_callback if dashboard_button_callback else lambda: print("dashboard_button_callback is none"))
        self.dashboardButton.setStyleSheet("border: none; background: transparent; padding: 0px;")
        self.header_layout.addWidget(self.dashboardButton)

        # Menu Button
        self.menu_button = QPushButton()
        self.menu_button.setIcon(QIcon(MENU_ICON_PATH))
        self.menu_button.clicked.connect(toggle_menu_callback if toggle_menu_callback else lambda: print("toggle_menu_callback is none"))
        self.menu_button.setStyleSheet("border: none; background: transparent; padding: 0px;")
        self.header_layout.addWidget(self.menu_button)

        # Left stretch
        self.header_layout.addStretch()

        # Language Selector (centered)
        self.language_selector = LanguageSelectorWidget()
        self.language_selector.languageChanged.connect(self.handle_language_change)
        self.language_selector.setFixedWidth(200)
        self.header_layout.addWidget(self.language_selector)

        # Right stretch
        self.header_layout.addStretch()

        # Power Toggle Button
        self.power_toggle_button = QPushButton()
        self.power_toggle_button.setIcon(QIcon(OFF_ICON_PATH))
        self.power_toggle_button.setToolTip("Power Off")
        self.power_toggle_button.setStyleSheet("border: none; background: white; padding: 0px;")
        self.power_toggle_button.clicked.connect(self.toggle_power)
        self.header_layout.addSpacing(20)
        self.header_layout.addWidget(self.power_toggle_button)

        self.power_on = False  # Power state

        self.setMinimumHeight(int(self.screen_height * 0.08))
        self.setMaximumHeight(100)

    def showLanguageSelector(self):
        self.language_selector.setVisible(True)

    def hideLanguageSelector(self):
        self.language_selector.setVisible(False)

    def hideMenuButton(self):
        self.menu_button.setVisible(False)

    def showMenuButton(self):
        self.menu_button.setVisible(True)

    def hideDashboardButton(self):
        self.dashboardButton.setVisible(False)

    def showDashboardButton(self):
        self.dashboardButton.setVisible(True)

    def showPowerButton(self):
        self.power_toggle_button.setVisible(True)

    def  hidePowerButton(self):
        self.power_toggle_button.setVisible(False)

    def toggle_power(self):
        self.power_on = not self.power_on
        icon = QIcon(ON_ICON_PATH) if self.power_on else QIcon(OFF_ICON_PATH)
        tooltip = "Power On" if self.power_on else "Power Off"
        self.power_toggle_button.setIcon(icon)
        self.power_toggle_button.setToolTip(tooltip)
        print(f"Power turned {'ON' if self.power_on else 'OFF'}")

    def resizeEvent(self, event):
        new_width = self.width()
        icon_size = int(new_width * 0.05)

        self.menu_button.setIconSize(QSize(icon_size, icon_size))
        self.power_toggle_button.setIconSize(QSize(icon_size, icon_size))
        self.dashboardButton.setIconSize(QSize(icon_size, icon_size))

        super().resizeEvent(event)

    def handle_language_change(self,message):
        self.broker.publish("Language","Change")
        # print("Language changed")

# For test/demo
if __name__ == "__main__":
    app = QApplication(sys.argv)
    screen_size = app.primaryScreen().size()
    header = Header(screen_size.width(), screen_size.height(), lambda: print("Menu toggled"), lambda: print("Dashboard clicked"))
    header.show()
    sys.exit(app.exec())

import os

from PyQt6 import QtCore
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter
# import QSizePolicy
from PyQt6.QtWidgets import QVBoxLayout
from frontend.pl_ui.ui.windows.settings.RobotConfigUI import RobotConfigController, RobotConfigUI
from frontend.pl_ui.ui.widgets.CustomWidgets import CustomTabWidget, BackgroundTabPage
from .CameraSettingsTabLayout import CameraSettingsTabLayout
from .GlueSettingsTabLayout import GlueSettingsTabLayout
from PyQt6.QtWidgets import QVBoxLayout, QSizePolicy

#
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
BACKGROUND = os.path.join(RESOURCE_DIR, "Background_&_Logo.png")
CAMERA_SETTINGS_ICON_PATH = os.path.join(RESOURCE_DIR, "CAMERA_SETTINGS_BUTTON.png")
CONTOUR_SETTINGS_ICON_PATH = os.path.join(RESOURCE_DIR, "CONTOUR_SETTINGS_BUTTON_SQUARE.png")
ROBOT_SETTINGS_ICON_PATH = os.path.join(RESOURCE_DIR, "ROBOT_SETTINGS_BUTTON_SQUARE.png")
GLUE_SETTINGS_ICON_PATH = os.path.join(RESOURCE_DIR, "glue_qty.png")


class BackgroundWidget(CustomTabWidget):
    def __init__(self):
        super().__init__()

        # Load the background image
        self.background = QPixmap(BACKGROUND)  # Update with your image path
        if self.background.isNull():
            print("Error: Background image not loaded correctly!")

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background.isNull():
            painter.drawPixmap(self.rect(), self.background)  # Scale image to widget size
        else:
            print("Background image not loaded")
        super().paintEvent(event)  # Call the base class paintEvent to ensure proper widget rendering


class SettingsContent(BackgroundWidget):
    # Action signals
    update_camera_feed_requested = QtCore.pyqtSignal()
    raw_mode_requested = QtCore.pyqtSignal(bool)
    
    # Settings change signal - replaces callback pattern
    setting_changed = QtCore.pyqtSignal(str, object, str)  # key, value, component_type

    def __init__(self, controller=None):
        super().__init__()

        # Keep minimal controller reference only for RobotConfigController
        # All other operations should be handled via signals
        self.controller = controller

        self.setStyleSheet(""" 
            QTabWidget {
                background-color: white; 
                padding: 10px; 
            }
            QTabBar::tab { 
                background: transparent; 
                border: none; 
            } 
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.cameraSettingsTab = BackgroundTabPage()
        self.robotSettingsTab = BackgroundTabPage()
        # self.contourSettingsTab = BackgroundTabPage()
        self.glueSettingsTab = BackgroundTabPage()

        self.addTab(self.cameraSettingsTab, "")
        self.addTab(self.robotSettingsTab, "")
        # self.addTab(self.contourSettingsTab, "")
        self.addTab(self.glueSettingsTab, "")

        # Set icons for tabs (Initial)
        self.update_tab_icons()

        # Tab content layouts - CREATE THEM FIRST
        self.cameraSettingsTabLayout = CameraSettingsTabLayout(self.cameraSettingsTab)
        self.connectCameraSettingSignals()
        self.cameraSettingsTabLayout.update_camera_feed_signal.connect(lambda: self.update_camera_feed_requested.emit())


        # Create robot settings (still needs controller for now due to RobotConfigUI design)
        robotConfigController = RobotConfigController(self.controller.requestSender)
        self.robotSettingsTabLayout = RobotConfigUI(self, robotConfigController)
        
        # Create glue settings without initial data - will be populated externally
        self.glueSettingsTabLayout = GlueSettingsTabLayout(self.glueSettingsTab, None)

        # *** ADD THIS: Set the layouts to the tab pages ***
        self.cameraSettingsTab.setLayout(self.cameraSettingsTabLayout)
        
        # For RobotConfigUI widget, we need to add it as a widget, not set it as layout
        robot_tab_layout = QVBoxLayout()
        robot_tab_layout.addWidget(self.robotSettingsTabLayout)
        self.robotSettingsTab.setLayout(robot_tab_layout)
        
        # self.contourSettingsTab.setLayout(self.contourSettingsTabLayout)
        self.glueSettingsTab.setLayout(self.glueSettingsTabLayout)

        # Connect unified signals to settings callback
        self._connect_settings_signals()
        # self.hide()  # Hide settings content initially

    def _connect_settings_signals(self):
        """
        Connect all settings tab signals to emit the unified setting_changed signal.
        This replaces the old callback pattern with clean signal emission.
        """
        # Connect glue settings value changes
        self.glueSettingsTabLayout.value_changed_signal.connect(self._emit_setting_change)
        
        # Connect camera settings value changes
        self.cameraSettingsTabLayout.value_changed_signal.connect(self._emit_setting_change)
        
        # Note: RobotConfigUI uses a different pattern - would need separate handling if required
    
    def _emit_setting_change(self, key: str, value, component_type: str):
        """
        Emit the unified setting_changed signal and maintain backward compatibility.
        
        Args:
            key: The setting key
            value: The new value
            component_type: The component class name
        """
        # Emit the new signal for modern signal-based handling
        self.setting_changed.emit(key, value, component_type)
    
    def clean_up(self):
        """Clean up resources when closing the settings content"""
        self.cameraSettingsTabLayout.clean_up()
        # self.robotSettingsTabLayout.clean_up()
        # self.glueSettingsTabLayout.clean_up()

    def updateCameraFeed(self, frame):
        """Update the camera feed in the camera settings tab."""
        self.cameraSettingsTabLayout.update_camera_feed(frame)

    def connectCameraSettingSignals(self):
        print("Connecting camera settings signals")
        self.cameraSettingsTabLayout.star_camera_requested.connect(self.onStartCameraRequested)
        self.cameraSettingsTabLayout.raw_mode_requested.connect(self.onRawModeRequested)

    def onStartCameraRequested(self):
        print("Camera start requested")

    def onRawModeRequested(self, state):
        print("Raw mode requested")
        # Emit a signal to update the camera feed
        self.raw_mode_requested.emit(state)

    def update_tab_icons(self):
        """Dynamically update tab icons based on window width"""
        tab_icon_size = int(self.width() * 0.05)  # 5% of new window width for tabs
        self.setTabIcon(0, QIcon(CAMERA_SETTINGS_ICON_PATH))
        self.setTabIcon(1, QIcon(ROBOT_SETTINGS_ICON_PATH))
        self.setTabIcon(2, QIcon(GLUE_SETTINGS_ICON_PATH))
        # self.setTabIcon(3, QIcon(CONTOUR_SETTINGS_ICON_PATH))
        self.tabBar().setIconSize(QSize(tab_icon_size, tab_icon_size))

    def resizeEvent(self, event):
        """Resize the tab widget dynamically on window resize"""
        new_width = self.width()

        # Resize the tab widget to be responsive to the window size
        self.setMinimumWidth(int(new_width * 0.3))  # 30% of the window width
        self.update_tab_icons()

        super().resizeEvent(event)

    def updateCameraSettings(self, cameraSettings):
        print("Updating camera settings in SettingsContent: ", cameraSettings)
        self.cameraSettingsTabLayout.updateValues(cameraSettings)

    def updateRobotSettings(self, robotSettings):
        # self.robotSettingsTabLayout.updateValues(robotSettings)
        pass

    def updateContourSettings(self, contourSettings):
        return
        # self.contourSettingsTabLayout.updateValues(contourSettings)

    def updateGlueSettings(self, glueSettings):
        self.glueSettingsTabLayout.updateValues(glueSettings)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QSizePolicy

    app = QApplication(sys.argv)
    window = SettingsContent()
    window.show()
    sys.exit(app.exec())

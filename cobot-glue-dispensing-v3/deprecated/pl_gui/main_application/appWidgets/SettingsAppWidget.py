from deprecated.pl_gui.Endpoints import RAW_MODE_ON, RAW_MODE_OFF
from deprecated.pl_gui.main_application.appWidgets.AppWidget import AppWidget
from deprecated.pl_gui.main_application.helpers.Endpoints import GET_SETTINGS, UPDATE_CAMERA_FEED, UPDATE_SETTINGS


class SettingsAppWidget(AppWidget):
    """Specialized widget for User Management application"""

    def __init__(self, parent=None, controller=None):
        self.controller = controller
        super().__init__("Settings", parent)

    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button
        self.setStyleSheet("""
                   QWidget {
                       background-color: #f8f9fa;
                       font-family: 'Segoe UI', Arial, sans-serif;
                       color: #000000;  /* Force black text */
                   }
                   
               """)
        # Replace the content with actual SettingsContent if available
        try:
            from deprecated.pl_gui.settings_view.SettingsContent import SettingsContent
            # Remove the placeholder content
            def updateSettingsCallback(key, value, className):
                # self.controller.updateSettings(key,value,className)
                print("Update Settings Callback called with key:", key, "value:", value, "className:", className)
                self.controller.handle(UPDATE_SETTINGS, key, value, className)

            def updateCameraFeedCallback():

                frame = self.controller.handle(UPDATE_CAMERA_FEED)
                self.content_widget.updateCameraFeed(frame)

            def onRawModeRequested(state):
                if state:
                    print("Raw mode requested SettingsAppWidget")
                    self.controller.handle(RAW_MODE_ON)
                else:
                    print("Raw mode off requested SettingsAppWidget")
                    self.controller.handle(RAW_MODE_OFF)

            self.content_widget = SettingsContent(updateSettingsCallback=updateSettingsCallback)
            self.content_widget.update_camera_feed_requested.connect(lambda: updateCameraFeedCallback())
            self.content_widget.raw_mode_requested.connect(lambda state: onRawModeRequested(state))
            print("Controller:", self.controller)
            if self.controller is None:
                raise ValueError("Controller is not set for SettingsAppWidget")
            cameraSettings, robotSettings, glueSettings = self.controller.handle(GET_SETTINGS)
            self.content_widget.updateCameraSettings(cameraSettings)
            self.content_widget.updateRobotSettings(robotSettings)
            self.content_widget.updateContourSettings(cameraSettings)
            self.content_widget.updateGlueSettings(glueSettings)

            # content_widget.show()
            print("SettingsContent loaded successfully")
            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(self.content_widget)
        except ImportError:
            # Keep the placeholder if the UserManagementWidget is not available
            print("SettingsContent not available, using placeholder")

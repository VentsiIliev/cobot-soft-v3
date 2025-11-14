from frontend.pl_ui.Endpoints import UPDATE_SETTINGS, UPDATE_CAMERA_FEED, RAW_MODE_ON, RAW_MODE_OFF, GET_SETTINGS
from frontend.pl_ui.ui.windows.mainWindow.appWidgets.AppWidget import AppWidget
from frontend.pl_ui.ui.windows.settings.SettingsContent import SettingsContent


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

            try:
                self.content_widget = SettingsContent(updateSettingsCallback=updateSettingsCallback,controller=self.controller)
                self.content_widget.update_camera_feed_requested.connect(lambda: updateCameraFeedCallback())
                self.content_widget.raw_mode_requested.connect(lambda state: onRawModeRequested(state))
            except Exception as e:
                import traceback
                traceback.print_exc()
                # If content widget creation fails, we cannot proceed
                raise e
            print("Controller:", self.controller)
            if self.controller is None:
                raise ValueError("Controller is not set for SettingsAppWidget")
            try:
                cameraSettings, robotSettings, glueSettings = self.controller.handle(GET_SETTINGS)
                self.content_widget.updateCameraSettings(cameraSettings)
                self.content_widget.updateRobotSettings(robotSettings)
                self.content_widget.updateContourSettings(cameraSettings)
                self.content_widget.updateGlueSettings(glueSettings)
            except Exception as e:
                import traceback
                traceback.print_exc()

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
    def clean_up(self):
        self.content_widget.clean_up()
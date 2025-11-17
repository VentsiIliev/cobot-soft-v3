from frontend.pl_ui.ui.windows.mainWindow.appWidgets.AppWidget import AppWidget
from frontend.pl_ui.ui.windows.settings.SettingsContent import SettingsContent
from modules.shared.v1.endpoints import settings_endpoints,camera_endpoints
from frontend.pl_ui.services.ControllerService import ControllerService

class SettingsAppWidget(AppWidget):
    """Settings application widget using clean service pattern"""

    def __init__(self, parent=None, controller=None, controller_service=None):
        self.controller = controller  # Keep for backward compatibility
        self.controller_service = controller_service or ControllerService(controller)
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

            # Remove the placeholder content - no more callback needed!
            # Settings will be handled via signals using the clean service pattern

            def updateCameraFeedCallback():

                frame = self.controller.handle(camera_endpoints.UPDATE_CAMERA_FEED)
                self.content_widget.updateCameraFeed(frame)

            def onRawModeRequested(state):
                if state:
                    print("Raw mode requested SettingsAppWidget")
                    self.controller.handle(camera_endpoints.CAMERA_ACTION_RAW_MODE_ON)
                else:
                    print("Raw mode off requested SettingsAppWidget")
                    self.controller.handle(camera_endpoints.CAMERA_ACTION_RAW_MODE_OFF)

            try:
                # Create SettingsContent without callback - it will emit signals instead
                self.content_widget = SettingsContent(controller=self.controller)
                
                # Connect to the new unified signal for settings changes
                self.content_widget.setting_changed.connect(self._handle_setting_change)
                
                # Connect action signals
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
                # Use the clean service pattern for loading settings
                settings_result = self.controller_service.settings.get_all_settings()
                
                if settings_result:
                    settings_data = settings_result.data
                    self.content_widget.updateCameraSettings(settings_data["camera"])
                    self.content_widget.updateRobotSettings(settings_data["robot"])
                    self.content_widget.updateContourSettings(settings_data["camera"])
                    self.content_widget.updateGlueSettings(settings_data["glue"])
                    print(f"✅ Settings loaded successfully: {settings_result.message}")
                else:
                    print(f"❌ Failed to load settings: {settings_result.message}")
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
    def _handle_setting_change(self, key: str, value, component_type: str):
        """
        Handle setting changes using the clean service pattern.
        This replaces the old callback approach with signal-based handling.
        
        Args:
            key: The setting key
            value: The new value
            component_type: The component class name
        """
        print(f"🔧 Setting change signal received: {component_type}.{key} = {value}")
        
        # Use the clean service pattern
        result = self.controller_service.settings.update_setting(key, value, component_type)
        
        if result:
            print(f"✅ Settings update successful: {result.message}")
            # Could show success toast here
        else:
            print(f"❌ Settings update failed: {result.message}")
            # Could show error dialog here
    
    def clean_up(self):
        """Clean up resources when widget is destroyed"""
        if hasattr(self, 'content_widget') and self.content_widget:
            self.content_widget.clean_up()
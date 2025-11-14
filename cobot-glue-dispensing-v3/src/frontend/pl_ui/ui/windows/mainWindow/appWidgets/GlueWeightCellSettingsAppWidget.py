from frontend.pl_ui.Endpoints import UPDATE_SETTINGS, UPDATE_CAMERA_FEED, RAW_MODE_ON, RAW_MODE_OFF, GET_SETTINGS
from frontend.pl_ui.ui.windows.mainWindow.appWidgets.AppWidget import AppWidget
from frontend.pl_ui.ui.windows.settings.LoadCellsSettingsTabLayout import LoadCellsSettingsTabLayout


class GlueWeightCellSettingsAppWidget(AppWidget):
    """Specialized widget for User Management application"""

    def __init__(self, parent=None, controller=None):
        self.controller = controller
        self.parent = parent
        super().__init__("Settings", parent)
        print("GlueWeightCellSettingsAppWidget initialized with parent:", self.parent)

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
            from PyQt6.QtWidgets import QWidget

            def settingsChangeCallback(key, value, className):
                print(f"Settings changed in {className}: {key} = {value}")

            try:
                # LoadCellsSettingsTabLayout is now a QVBoxLayout, so wrap it in a QWidget
                # like the calibration app does
                self.content_widget = QWidget(self.parent)
                self.content_layout = LoadCellsSettingsTabLayout()
                self.content_layout.connectValueChangeCallbacks(settingsChangeCallback)
                self.content_widget.setLayout(self.content_layout)
            except Exception as e:
                import traceback
                traceback.print_exc()
                # If content widget creation fails, we cannot proceed
                raise e



            # content_widget.show()
            print("LoadCellsSettingsTabLayout loaded successfully")
            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(self.content_widget)
        except ImportError:
            # Keep the placeholder if the UserManagementWidget is not available
            print("LoadCellsSettingsTabLayout not available, using placeholder")

    def clean_up(self):
        """Clean up resources when the widget is closed"""
        print("Cleaning up GlueWeightCellSettingsAppWidget")
        try:
            if hasattr(self, 'content_layout') and self.content_layout:
                # Call the cleanup method on the LoadCellsSettingsTabLayout
                if hasattr(self.content_layout, '_cleanup_message_broker'):
                    self.content_layout._cleanup_message_broker()
        except Exception as e:
            print(f"Error during GlueWeightCellSettingsAppWidget cleanup: {e}")
        super().clean_up() if hasattr(super(), 'clean_up') else None

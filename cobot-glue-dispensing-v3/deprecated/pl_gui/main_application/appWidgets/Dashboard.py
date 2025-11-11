from PyQt6.QtCore import pyqtSignal

from deprecated.pl_gui.main_application.appWidgets.AppWidget import AppWidget
from deprecated.pl_gui.main_application.dashboard.DashboardWidget import DashboardWidget

class DashboardAppWidget(AppWidget):
    """Specialized widget for User Management application"""
    # define logout signal
    LOGOUT_REQUEST = pyqtSignal()
    start_requested = pyqtSignal()
    def __init__(self, parent=None,controller=None):
        self.controller = controller
        super().__init__("Dashboard", parent)
    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button

        # Replace the content with actual UserManagementWidget if available
        try:
            from deprecated.pl_gui.dashboard.DashboardContent import MainContent
            # from pl_gui.dashboard.NewDashboardWidget import GlueDashboardWidget
            from deprecated.pl_gui.Endpoints import UPDATE_CAMERA_FEED
            # Remove the placeholder content
            self.content_widget = DashboardWidget(updateCameraFeedCallback=lambda: self.controller.handle(UPDATE_CAMERA_FEED))
            self.content_widget.start_requested.connect(self.start_requested.emit)
            self.content_widget.glue_type_changed_signal.connect(self.on_glue_type_changed)
            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(self.content_widget)
        except ImportError:
            import traceback
            traceback.print_exc()
            # Keep the placeholder if the UserManagementWidget is not available
            print("Dashboard not available, using placeholder")

    def onLogOut(self):
        print("Logout requested from Dashboard")
        self.LOGOUT_REQUEST.emit()

    def on_glue_type_changed(self, index,glue_type):
        print(f"Glue type of {index} changed to: {glue_type} ")
        from GlueDispensingApplication.tools.GlueCell import GlueCellsManagerSingleton
        manager = GlueCellsManagerSingleton.get_instance()
        manager.updateGlueTypeById(index,glue_type)

    def clean_up(self):
        """Clean up resources when the widget is closed"""
        # Perform any necessary cleanup here
        print("Cleaning up DashboardAppWidget")
        self.content_widget.clean_up()
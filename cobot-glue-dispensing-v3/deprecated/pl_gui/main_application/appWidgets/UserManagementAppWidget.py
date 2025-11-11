import os

from deprecated.pl_gui.main_application.appWidgets.AppWidget import AppWidget

# Navigate up to project root, then down to API/shared/user/users.csv
base_dir = os.path.dirname(os.path.abspath(__file__))  # pl_gui/
project_root = os.path.abspath(os.path.join(base_dir, ".."))  # move up one level
csv_file_path = os.path.join(project_root, "API", "shared", "user", "users.csv")


class UserManagementAppWidget(AppWidget):
    """Specialized widget for User Management application"""

    def __init__(self, parent=None):
        super().__init__("User Management", parent)

    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button

        # Replace the content with actual UserManagementWidget if available
        try:
            from API.shared.user.UserDashboard import UserManagementWidget
            # Remove the placeholder content
            content_widget = UserManagementWidget(csv_file_path=csv_file_path)

            from API.MessageBroker import MessageBroker
            broker = MessageBroker()
            broker.subscribe("Language", content_widget.update_language)

            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(content_widget)
        except ImportError:
            import traceback
            traceback.print_exc()
            # Keep the placeholder if the UserManagementWidget is not available
            print("UserManagementWidget not available, using placeholder")



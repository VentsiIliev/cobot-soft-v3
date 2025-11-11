from deprecated.pl_gui.main_application.appWidgets.AppWidget import AppWidget


class ContourEditorAppWidget(AppWidget):
    """Specialized widget for User Management application"""

    def __init__(self, parent=None,controller=None):
        self.controller = controller
        self.parent = parent
        self.content_widget = None
        super().__init__("Contour Editor", parent)
    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button

        # Replace the content with actual UserManagementWidget if available
        try:
            from deprecated.pl_gui.contour_editor.ContourEditor import MainApplicationFrame
            # Remove the placeholder content
            self.content_widget = MainApplicationFrame(parent=self.parent)

            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(self.content_widget)
        except ImportError:
            import traceback
            traceback.print_exc()
            print("Contour Editor not available, using placeholder")

    def set_image(self,image):
        """Set the image to be displayed in the contour editor"""
        try:
            self.content_widget.set_image(image)
            print("Set image in Contour Editor")
        except AttributeError:
            import traceback
            traceback.print_exc()
            print("Contour Editor widget does not support set_image method")

    def init_contours(self,contours_by_layer):
        """Initialize contours in the contour editor"""
        try:
            print("content_widget type:", type(self.content_widget))
            self.content_widget.init_contours(contours_by_layer)
        except AttributeError:
            # print the actual error
            import traceback
            traceback.print_exc()
            print("Contour Editor widget does not support init_contours method")

    def set_create_workpiece_for_on_submit_callback(self, callback):
        """Set the callback for when the create workpiece button is clicked"""
        try:
            print("Setting create workpiece callback")
            self.content_widget.set_create_workpiece_for_on_submit_callback(callback)
        except AttributeError:
            print("Contour Editor widget does not support set_create_workpiece_for_on_submit_callback method")

    def to_wp_data(self):
        return self.content_widget.contourEditor.manager.to_wp_data()
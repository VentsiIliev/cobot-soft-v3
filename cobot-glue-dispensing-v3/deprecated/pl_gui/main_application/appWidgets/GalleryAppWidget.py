from API.MessageBroker import MessageBroker
from deprecated.pl_gui.Endpoints import WORPIECE_GET_ALL
from deprecated.pl_gui.main_application.appWidgets.AppWidget import AppWidget


class GalleryAppWidget(AppWidget):
    """Specialized widget for User Management application"""

    def __init__(self, parent=None,controller=None,onApplyCallback=None,thumbnails=None):
        self.controller = controller
        self.thumbnails = thumbnails
        self.onApplyCallback = onApplyCallback
        super().__init__("Gallery", parent)

    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button

        # Replace the content with actual UserManagementWidget if available
        try:
            workpieces = self.controller.handle(WORPIECE_GET_ALL)

            def onApply(selectedWorkpieces):
                if len(selectedWorkpieces) == 0:
                    return
                workpieces = self.controller.handle(WORPIECE_GET_ALL)
                selected = selectedWorkpieces[0]

                selectedWp = None
                for wp in workpieces:
                    if str(wp.workpieceId) == str(selected):
                        selectedWp = wp
                        break
                print("Selected Workpiece:", selectedWp.sprayPattern)
                self.controller.handleExecuteFromGallery(selectedWp)

            from deprecated.pl_gui.gallery.GalleryContent import GalleryContent
            # Remove the placeholder content

            if self.onApplyCallback is None:
                self.onApplyCallback = onApply

            content_widget = GalleryContent(workpieces = workpieces,thumbnails=self.thumbnails, onApplyCallback=self.onApplyCallback)
            broker = MessageBroker()
            broker.subscribe("Language", content_widget.updateLanguage)

            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(content_widget)
        except ImportError:
            # Keep the placeholder if the UserManagementWidget is not available
            print("Gallery not available, using placeholder")
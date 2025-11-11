from PyQt6.QtCore import pyqtSignal

from modules.shared.MessageBroker import MessageBroker
from src.frontend.pl_ui.Endpoints import WORPIECE_GET_ALL
from src.frontend.pl_ui.ui.windows.mainWindow.appWidgets.AppWidget import AppWidget


class GalleryAppWidget(AppWidget):
    """Specialized widget for User Management application"""
    apply_button_clicked = pyqtSignal()
    edit_requested = pyqtSignal(str)
    def __init__(self, parent=None, controller=None, onApplyCallback=None, thumbnails=None):
        self.controller = controller
        self.thumbnails = thumbnails
        self.onApplyCallback = onApplyCallback
        super().__init__("Gallery", parent)

    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button

        try:
            workpieces = self.controller.handle(WORPIECE_GET_ALL)

            def onApply(filename):
                if not filename:
                    print("❌ No filename provided")
                    return

                self.controller.handleSetPreselectedWorkpiece(filename)



            from src.frontend.pl_ui.ui.windows.gallery.GalleryContent import GalleryContent
            # Remove the placeholder content

            if self.onApplyCallback is None:
                self.onApplyCallback = onApply

            content_widget = GalleryContent(workpieces=workpieces, thumbnails=self.thumbnails,
                                            onApplyCallback=self.onApplyCallback,controller=self.controller)
            content_widget.edit_requested.connect(lambda workpiece_id: self.edit_requested.emit(workpiece_id))
            # broker = MessageBroker()
            # broker.subscribe("Language", content_widget.updateLanguage)

            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(content_widget)
        except ImportError:
            # Keep the placeholder if the UserManagementWidget is not available
            print("Gallery not available, using placeholder")

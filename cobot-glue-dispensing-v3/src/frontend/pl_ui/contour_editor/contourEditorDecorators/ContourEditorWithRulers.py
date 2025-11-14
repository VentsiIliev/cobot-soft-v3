from PyQt6.QtCore import Qt, QEvent, pyqtSignal
from PyQt6.QtWidgets import QWidget, QGridLayout

from frontend.pl_ui.contour_editor.Ruler import Ruler
from frontend.pl_ui.contour_editor.Ruler import Ruler
from frontend.pl_ui.contour_editor.contourEditorDecorators.ContourEditor import ContourEditor


class ContourEditorWithRulers(QWidget):
    update_camera_feed_requested = pyqtSignal()

    def __init__(self, visionSystem, image_path=None, contours=None, workpiece=None):
        super().__init__()
        # Inner editor widget (actual painter / logic)
        self.editor = ContourEditor(visionSystem, image_path=image_path, contours=contours, workpiece=workpiece)
        self.editor.update_camera_feed_requested.connect(self.update_camera_feed_requested)

        # Create rulers
        self.h_ruler = Ruler(Qt.Orientation.Horizontal)
        self.v_ruler = Ruler(Qt.Orientation.Vertical)

        # Grid layout: top-left spacer, top horizontal ruler, left vertical ruler, editor in bottom-right
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(QWidget(), 0, 0)         # spacer
        layout.addWidget(self.h_ruler, 0, 1)      # top ruler
        layout.addWidget(self.v_ruler, 1, 0)      # left ruler
        layout.addWidget(self.editor, 1, 1)       # editor viewport
        self.setLayout(layout)

        # Keep rulers in sync after the editor repaints or updates
        self.editor.installEventFilter(self)
        try:
            # also update when points change (signal provided by editor)
            self.editor.pointsUpdated.connect(self._update_rulers)
        except Exception:
            pass

    def _update_rulers(self):
        """Update rulers to reflect editor transform."""
        self.h_ruler.update_view(self.editor.scale_factor, self.editor.translation)
        self.v_ruler.update_view(self.editor.scale_factor, self.editor.translation)

    def eventFilter(self, obj, event):
        # After editor paint, refresh rulers
        if obj is self.editor and event.type() == QEvent.Type.Paint:
            self._update_rulers()
        return super().eventFilter(obj, event)

    def __getattr__(self, name):
        # Forward unknown attribute access to inner editor for compatibility
        return getattr(self.editor, name)

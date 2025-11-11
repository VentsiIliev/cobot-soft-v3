from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QGridLayout

from src.frontend.pl_ui.contour_editor.constants import EDIT_MODE, DRAG_MODE
from src.frontend.pl_ui.contour_editor.contourEditorDecorators.ContourEditorWithRulers import ContourEditorWithRulers
from src.frontend.pl_ui.contour_editor.widgets.BottomToolBar import BottomToolBar


class ContourEditorWithBottomToolBar(QWidget):
    """Decorator that wraps ContourEditorWithRulers and adds zoom controls at bottom center"""
    update_camera_feed_requested = pyqtSignal()
    def __init__(self, visionSystem, image_path=None, contours=None, workpiece=None):
        super().__init__()

        # Create the editor with rulers
        self.editor_with_rulers = ContourEditorWithRulers(visionSystem, image_path=image_path, contours=contours,
                                                          workpiece=workpiece)
        self.editor_with_rulers.update_camera_feed_requested.connect(self.update_camera_feed_requested)

        # Create zoom controls
        self.bottom_toolbar = BottomToolBar(self)

        # Connect zoom controls to viewport controller methods
        self.bottom_toolbar.zoom_in_requested.connect(self.editor_with_rulers.editor.viewport_controller.zoom_in)
        self.bottom_toolbar.zoom_out_requested.connect(self.editor_with_rulers.editor.viewport_controller.zoom_out)
        self.bottom_toolbar.reset_zoom_requested.connect(self.editor_with_rulers.editor.viewport_controller.reset_zoom)
        self.bottom_toolbar.pan_mode_toggle_requested.connect(self.toggle_pan_mode)
        self.bottom_toolbar.show_points_requested.connect(self.show_points)
        self.bottom_toolbar.hide_points_requested.connect(self.hide_points)

        # Setup layout
        self.setupLayout()

    def toggle_pan_mode(self):
        """Handle pan mode toggle from zoom controls widget"""
        # Toggle the mode in the actual editor
        current_mode = getattr(self.editor_with_rulers.editor, 'current_mode', EDIT_MODE)
        new_mode = EDIT_MODE if current_mode == DRAG_MODE else DRAG_MODE
        self.editor_with_rulers.editor.set_cursor_mode(new_mode)

        # Update the zoom controls button state to match editor state
        self.bottom_toolbar.is_drag_mode = (new_mode == DRAG_MODE)

    def show_points(self):
        """Show anchor and control points"""
        from pl_ui.contour_editor import constants
        constants.SHOW_ANCHOR_POINTS = True
        constants.SHOW_CONTROL_POINTS = True
        # Trigger repaint to update the display
        self.editor_with_rulers.editor.update()

    def hide_points(self):
        """Hide anchor and control points"""
        from pl_ui.contour_editor import constants
        constants.SHOW_ANCHOR_POINTS = False
        constants.SHOW_CONTROL_POINTS = False
        # Trigger repaint to update the display
        self.editor_with_rulers.editor.update()

    def set_zoom_controls_visible(self, visible):
        """Toggle visibility of zoom controls"""
        self.bottom_toolbar.set_zoom_controls_visible(visible)

    def set_pan_controls_visible(self, visible):
        """Toggle visibility of pan/edit toggle button"""
        self.bottom_toolbar.set_pan_controls_visible(visible)

    def are_zoom_controls_visible(self):
        """Check if zoom controls are visible"""
        return self.bottom_toolbar.are_zoom_controls_visible()

    def are_pan_controls_visible(self):
        """Check if pan controls are visible"""
        return self.bottom_toolbar.are_pan_controls_visible()

    def setupLayout(self):
        # Create main layout
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add editor with rulers to fill most of the space
        main_layout.addWidget(self.editor_with_rulers, 0, 0, 1, 3)  # row 0, col 0-2, spans 1 row, 3 cols

        # Add zoom controls at bottom center
        main_layout.addWidget(QWidget(), 1, 0)  # spacer left
        main_layout.addWidget(self.bottom_toolbar, 1, 1)  # zoom controls center
        main_layout.addWidget(QWidget(), 1, 2)  # spacer right

        # Set column stretch to center the zoom controls
        main_layout.setColumnStretch(0, 1)  # left spacer gets extra space
        main_layout.setColumnStretch(1, 0)  # zoom controls fixed size
        main_layout.setColumnStretch(2, 1)  # right spacer gets extra space

        # Set row stretch to keep zoom controls at bottom
        main_layout.setRowStretch(0, 1)  # editor gets most space
        main_layout.setRowStretch(1, 0)  # zoom controls fixed height

    def __getattr__(self, name):
        # Forward unknown attribute access to the editor for compatibility
        return getattr(self.editor_with_rulers, name)

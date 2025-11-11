from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter

from src.frontend.pl_ui.contour_editor.rendering.renderer import (
    draw_ruler, draw_rectangle_selection, draw_pickup_point,
    draw_selection_status, draw_segments, draw_drag_crosshair, 
    draw_highlighted_line_segment
)


class EditorRenderer:
    def __init__(self, editor):
        self.editor = editor

    def render(self, painter, event):
        """Main render method called from paintEvent"""
        if not painter.isActive():
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.editor.rect(), Qt.GlobalColor.white)
        
        # Apply transformation for image space rendering
        painter.translate(self.editor.translation)
        painter.scale(self.editor.scale_factor, self.editor.scale_factor)
        painter.drawImage(0, 0, self.editor.image)

        # Draw all image-space elements
        draw_ruler(self.editor, painter)
        draw_segments(self.editor, painter, self.editor.manager)
        draw_rectangle_selection(self.editor, painter)
        draw_pickup_point(self.editor, painter)
        draw_selection_status(self.editor, painter)

        # Draw highlighted line segment with measurements (in image space)
        if self.editor.highlighted_line_segment:
            draw_highlighted_line_segment(self.editor, painter)

        # Reset transform for screen-space rendering
        painter.resetTransform()

        # Draw drag crosshair (helps with touchscreen - shows above finger)
        # Only draw when actually dragging (mouse has moved), not just on press-and-hold
        if (hasattr(self.editor.mode_manager, 'drag_mode') and 
            self.editor.mode_manager.drag_mode.is_actually_dragging and 
            self.editor.current_cursor_pos is not None):
            draw_drag_crosshair(self.editor, painter, self.editor.current_cursor_pos)
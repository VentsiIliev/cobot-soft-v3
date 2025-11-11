# pl_ui/contour_editor/EditorStateMachine/Modes/RectangleSelectMode.py
from PyQt6.QtCore import Qt, QPointF, QRectF
from src.frontend.pl_ui.contour_editor.EditorStateMachine.Modes.BaseMode import BaseMode
from src.frontend.pl_ui.contour_editor.utils.coordinate_utils import map_to_image_space

class RectangleSelectMode(BaseMode):
    name = "rectangle_select"

    def __init__(self):
        super().__init__()
        # Rectangle selection state
        self.selection_start = None  # QPointF - starting point in image space
        self.selection_end = None    # QPointF - ending point in image space
        self.is_selecting = False    # Flag indicating if user is currently dragging

    def mousePress(self, editor, event):
        """Start rectangle selection"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Convert screen position to image space
            pos_img = map_to_image_space(event.position(), editor.translation, editor.scale_factor)

            self.selection_start = pos_img
            self.selection_end = pos_img
            self.is_selecting = True

            print(f"Rectangle selection started at: {pos_img}")
            editor.update()

    def mouseMove(self, editor, event):
        """Update rectangle as user drags"""
        if self.is_selecting:
            # Convert screen position to image space
            pos_img = map_to_image_space(event.position(), editor.translation, editor.scale_factor)

            self.selection_end = pos_img
            editor.update()  # Redraw to show selection rectangle

    def mouseRelease(self, editor, event):
        """Finalize selection and select all points within rectangle"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            # Convert screen position to image space
            pos_img = map_to_image_space(event.position(), editor.translation, editor.scale_factor)

            self.selection_end = pos_img
            self.is_selecting = False

            # Create rectangle from start and end points
            rect = QRectF(self.selection_start, self.selection_end).normalized()

            print(f"Rectangle selection finished: {rect}")

            # Find all points within the rectangle
            self._select_points_in_rectangle(editor, rect)

            # Clear the selection rectangle
            self.selection_start = None
            self.selection_end = None

            editor.update()

    def _select_points_in_rectangle(self, editor, rect):
        """Select all points (anchors and controls) that fall within the rectangle"""
        selected_count = 0

        # Iterate through all segments
        for seg_index, segment in enumerate(editor.manager.get_segments()):
            # Check anchor points
            for point_index, point in enumerate(segment.points):
                if rect.contains(point):
                    # Add to selection
                    editor.selection_manager.toggle_point_selection(
                        ('anchor', seg_index, point_index)
                    )
                    selected_count += 1
                    print(f"Selected anchor point: segment {seg_index}, index {point_index}")

            # Check control points
            for ctrl_index, ctrl in enumerate(segment.controls):
                if ctrl is not None and rect.contains(ctrl):
                    # Add to selection
                    editor.selection_manager.toggle_point_selection(
                        ('control', seg_index, ctrl_index)
                    )
                    selected_count += 1
                    print(f"Selected control point: segment {seg_index}, index {ctrl_index}")

        print(f"Rectangle selection: {selected_count} points selected")

    def get_selection_rect(self):
        """Get the current selection rectangle (for rendering)"""
        if self.is_selecting and self.selection_start and self.selection_end:
            return QRectF(self.selection_start, self.selection_end).normalized()
        return None

    def clear(self):
        """Clear rectangle selection state"""
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
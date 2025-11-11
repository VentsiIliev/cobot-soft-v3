from PyQt6.QtCore import QPointF, QTimer

# from pl_ui.contour_editor.ContourEditorWithRulers import ContourEditorWithRulers
from src.frontend.pl_ui.contour_editor.EditorStateMachine.Modes.BaseMode import BaseMode
from src.frontend.pl_ui.contour_editor.utils.coordinate_utils import map_to_image_space

class PointDragMode(BaseMode):
    name = "drag_point"
    def __init__(self, editor):
        super().__init__()
        self.editor = editor

        # Drag state variables (moved from ContourEditor)
        self.dragging_point = None  # (role, seg_index, point_index)
        self.initial_drag_point_pos = None  # QPointF - original point position
        self.initial_drag_mouse_pos = None  # QPointF - original mouse position
        self.drag_threshold = 10  # pixels - minimum movement to trigger drag
        self.pending_drag_update = False  # flag for throttled updates
        self.point_to_crosshair_offset = None  # Offset from crosshair to point
        self.is_actually_dragging = False  # True only when mouse has moved significantly

    def mousePress(self, editor, event, drag_target=None):
        """
        Initialize dragging for a specific target.
        Store the initial point position and crosshair position for delta calculation.
        """
        if not drag_target:
            return

        self.dragging_point = drag_target
        self.is_actually_dragging = False  # Not dragging yet, just pressed
        role, seg_index, idx = drag_target

        # Set this point as selected (for deletion via remove button)
        editor.selection_manager.set_single_selection(drag_target)
        print(f"Point selected: {drag_target}")

        # Hide point info overlay when dragging starts
        if hasattr(editor, 'point_info_overlay'):
            editor.point_info_overlay.hide()

        # Get current point position in image space
        if role == "anchor":
            self.initial_drag_point_pos = QPointF(editor.manager.segments[seg_index].points[idx])
        else:
            self.initial_drag_point_pos = QPointF(editor.manager.segments[seg_index].controls[idx])

        # Calculate initial crosshair position in image space (50 pixels above cursor)
        crosshair_offset_y = -50
        crosshair_screen_pos = QPointF(
            event.position().x(),
            event.position().y() + crosshair_offset_y
        )
        self.initial_drag_mouse_pos = map_to_image_space(crosshair_screen_pos, editor.translation, editor.scale_factor)

        print(f"Initial point pos: {self.initial_drag_point_pos}, Initial crosshair pos: {self.initial_drag_mouse_pos}")

        editor.manager.save_state()

    def mouseMove(self, editor, event):
        if not self.dragging_point:
            return

        # Mark that we're actually dragging (mouse has moved)
        self.is_actually_dragging = True

        # Calculate current crosshair position in image space (50 pixels above cursor)
        crosshair_offset_y = -50
        crosshair_screen_pos = QPointF(
            event.position().x(),
            event.position().y() + crosshair_offset_y
        )

        # Convert current crosshair position to image space
        current_crosshair_pos = map_to_image_space(crosshair_screen_pos, editor.translation, editor.scale_factor)

        # Place the point directly at the crosshair position
        # This ensures the point is exactly where the crosshair shows
        role, seg_index, idx = self.dragging_point
        new_pos = current_crosshair_pos

        editor.manager.move_point(role, seg_index, idx, new_pos, suppress_save=True)
        self.pending_drag_update = True

        # Autoscroll if near edges
        margin = 50
        scroll_speed = 10
        x, y = event.position().x(), event.position().y()

        if x < margin:
            editor.translation += QPointF(scroll_speed, 0)
        elif x > editor.width() - margin:
            editor.translation -= QPointF(scroll_speed, 0)

        if y < margin:
            editor.translation += QPointF(0, scroll_speed)
        elif y > editor.height() - margin:
            editor.translation -= QPointF(0, scroll_speed)

        if not self.editor.drag_timer.isActive():
            self.editor.drag_timer.start()

    def mouseRelease(self):
        """Clear drag state"""
        self.dragging_point = None
        self.initial_drag_point_pos = None
        self.initial_drag_mouse_pos = None
        self.point_to_crosshair_offset = None
        self.is_actually_dragging = False

    # def perform_drag_update(self):
    #     if self.pending_drag_update:
    #         self.editor.update()
    #         print(f"Dragged point to new position.")
    #         self.pending_drag_update = False
    #     else:
    #         self.drag_timer.stop()

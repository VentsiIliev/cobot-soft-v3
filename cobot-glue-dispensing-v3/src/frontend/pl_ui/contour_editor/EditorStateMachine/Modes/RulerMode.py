# contour_editor/modes/ruler_mode.py
from PyQt6.QtCore import Qt
from src.frontend.pl_ui.contour_editor.EditorStateMachine.Modes.BaseMode import BaseMode
from src.frontend.pl_ui.contour_editor.utils.coordinate_utils import map_to_image_space, calculate_distance

class RulerMode(BaseMode):
    name = "ruler"

    def __init__(self):
        super().__init__()
        # Ruler state variables (moved from ContourEditor)
        self.ruler_start = None  # QPointF - first measurement point
        self.ruler_end = None  # QPointF - second measurement point
        self.dragging_ruler_point = None  # None, "start" or "end"
        self.ruler_hit_radius = 10  # pixels in screen-space for hit detection

    def enter(self, editor):
        editor.setCursor(Qt.CursorShape.CrossCursor)
        self.ruler_start = None
        self.ruler_end = None
        self.dragging_ruler_point = None
        print("Entered Ruler Mode")

    def exit(self, editor):
        self.dragging_ruler_point = None
        editor.update()

    def mousePress(self, editor, event):

        pos_img = map_to_image_space(event.position(), editor.translation, editor.scale_factor)

        # Check if near start or end point
        def near(p):
            if p is None: return False
            dist = calculate_distance(pos_img, p)
            return dist * editor.scale_factor < self.ruler_hit_radius

        if near(self.ruler_start):
            self.dragging_ruler_point = "start"
            return
        elif near(self.ruler_end):
            self.dragging_ruler_point = "end"
            return

        # Otherwise, set points
        if self.ruler_start is None:
            self.ruler_start = pos_img
        elif self.ruler_end is None:
            self.ruler_end = pos_img
        else:
            # Both points already set; reset start to new click
            self.ruler_start = pos_img
            self.ruler_end = None

        editor.update()

    def mouseMove(self, editor, event):
        if not self.dragging_ruler_point:
            return
        pos_img = map_to_image_space(event.position(), editor.translation, editor.scale_factor)
        if self.dragging_ruler_point == "start":
            self.ruler_start = pos_img
        elif self.dragging_ruler_point == "end":
            self.ruler_end = pos_img
        editor.update()

    def mouseRelease(self):
        """Clear dragging state"""
        self.dragging_ruler_point = None

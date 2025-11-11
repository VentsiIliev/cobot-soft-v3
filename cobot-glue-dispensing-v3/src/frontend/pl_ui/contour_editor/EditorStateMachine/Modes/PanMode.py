# pl_ui/contour_editor/EditorStateMachine/Modes/PanMode.py
from PyQt6.QtCore import Qt
from src.frontend.pl_ui.contour_editor.EditorStateMachine.Modes.BaseMode import BaseMode

class PanMode(BaseMode):
    name = "pan"

    def __init__(self):
        super().__init__()
        # Pan state variables (moved from ContourEditor)
        self.last_drag_pos = None  # QPointF - last mouse position during panning

    def mousePress(self, editor, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_drag_pos = event.position()
            editor.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMove(self, editor, event):
        if self.last_drag_pos is None:
            return
        delta = event.position() - self.last_drag_pos
        editor.translation += delta
        self.last_drag_pos = event.position()
        editor.update()

    def mouseRelease(self):
        """Clear pan state"""
        self.last_drag_pos = None

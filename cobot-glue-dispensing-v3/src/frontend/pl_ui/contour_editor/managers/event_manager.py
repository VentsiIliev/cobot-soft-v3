from PyQt6.QtCore import QEvent

from frontend.pl_ui.contour_editor.handlers.gesture_handler import handle_gesture_event
from frontend.pl_ui.contour_editor.handlers.mouse_event_handler import (
    mousePressEvent, mouseMoveEvent, mouseReleaseEvent, mouseDoubleClickEvent
)


class EventManager:
    def __init__(self, editor):
        self.editor = editor
        
        # Event state management
        self.current_cursor_pos = None  # Screen-space position for drag crosshair
        self.last_drag_pos = None  # Used for zooming gestures

    def handle_mouse_press(self, event):
        """Handle mouse press events"""
        mousePressEvent(self.editor, event)

    def handle_mouse_double_click(self, event):
        """Handle mouse double click events"""
        mouseDoubleClickEvent(self.editor, event)
        # Note: Original code had super().mouseMoveEvent(event) which seems like a bug
        # Keeping it for backward compatibility but this should probably be removed

    def handle_mouse_move(self, event):
        """Handle mouse move events"""
        mouseMoveEvent(self.editor, event)

    def handle_mouse_release(self, event):
        """Handle mouse release events"""
        mouseReleaseEvent(self.editor, event)

    def handle_wheel(self, event):
        """Handle mouse wheel events (zoom)"""
        self.editor.viewport_controller.handle_zoom(event)

    def handle_general_event(self, event):
        """Handle general Qt events (like gestures)"""
        if event.type() == QEvent.Type.Gesture:
            return self.handle_gesture_event(event)
        return False

    def handle_gesture_event(self, event):
        """Handle gesture events"""
        handle_gesture_event(self.editor, event)
        return True

    def update_cursor_position(self, pos):
        """Update the current cursor position for drag crosshair"""
        self.current_cursor_pos = pos

    def get_cursor_position(self):
        """Get the current cursor position"""
        return self.current_cursor_pos

    def update_drag_position(self, pos):
        """Update the last drag position for gesture handling"""
        self.last_drag_pos = pos

    def get_drag_position(self):
        """Get the last drag position"""
        return self.last_drag_pos

    def reset_event_state(self):
        """Reset event-related state"""
        self.current_cursor_pos = None
        self.last_drag_pos = None
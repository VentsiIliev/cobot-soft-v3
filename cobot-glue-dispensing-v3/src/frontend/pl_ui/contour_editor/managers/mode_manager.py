from PyQt6.QtCore import Qt

from frontend.pl_ui.contour_editor.constants import EDIT_MODE, RECTANGLE_SELECT_MODE, DRAG_MODE, PICKUP_POINT_MODE, MULTI_SELECT_MODE
from frontend.pl_ui.contour_editor.EditorStateMachine.Modes.MultiPointSelectMode import MultiPointSelectMode
from frontend.pl_ui.contour_editor.EditorStateMachine.Modes.PanMode import PanMode
from frontend.pl_ui.contour_editor.EditorStateMachine.Modes.PointDragMode import PointDragMode


class ModeManager:
    def __init__(self, editor):
        self.editor = editor
        
        # Mode state - now owned by ModeManager
        self.current_mode = EDIT_MODE
        self.pan_mode_active = False
        self.pickup_point_mode_active = False
        self.multi_select_mode_active = False
        
        # Mode objects
        self.pan_mode = PanMode()
        self.drag_mode = PointDragMode(editor)
        self.multi_select_mode = MultiPointSelectMode()

    def set_cursor_mode(self, mode):
        """Set the current cursor mode and update all related state"""
        self.current_mode = mode
        self.pan_mode_active = (mode == DRAG_MODE)
        self.pickup_point_mode_active = (mode == PICKUP_POINT_MODE)
        self.multi_select_mode_active = (mode == MULTI_SELECT_MODE)
        
        # Update cursor based on mode
        if mode == DRAG_MODE:
            self.editor.setCursor(Qt.CursorShape.OpenHandCursor)
        elif mode == EDIT_MODE:
            self.editor.setCursor(Qt.CursorShape.ArrowCursor)
        elif mode == PICKUP_POINT_MODE:
            self.editor.setCursor(Qt.CursorShape.CrossCursor)
        elif mode == MULTI_SELECT_MODE:
            self.editor.setCursor(Qt.CursorShape.PointingHandCursor)
        elif mode == RECTANGLE_SELECT_MODE:
            self.editor.setCursor(Qt.CursorShape.CrossCursor)

    def toggle_multi_select_mode(self):
        """Toggle multi-selection mode on/off"""
        if self.multi_select_mode_active:
            # Exit multi-select mode
            self.multi_select_mode_active = False
            self.editor.selection_manager.clear_all_selections()
            self.set_cursor_mode(EDIT_MODE)
            print("Multi-selection mode deactivated")
        else:
            # Enter multi-select mode
            self.multi_select_mode_active = True
            self.set_cursor_mode(MULTI_SELECT_MODE)
            print("Multi-selection mode activated")

        self.editor.update()
        return self.multi_select_mode_active

    def _should_draw_all_points(self):
        """Decide whether to draw all points based on current zoom level."""
        return self.editor.scale_factor > self.editor.min_point_display_scale
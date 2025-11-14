from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QCursor

from frontend.pl_ui.contour_editor.constants import EDIT_MODE, RECTANGLE_SELECT_MODE
from frontend.pl_ui.contour_editor.utils.coordinate_utils import map_to_image_space
from frontend.pl_ui.contour_editor.widgets.ToolsPopup import ToolsPopup
from frontend.pl_ui.contour_editor.widgets.MagnifierWidget import MagnifierWidget
from frontend.pl_ui.contour_editor.EditorStateMachine.Modes.RulerMode import RulerMode
from frontend.pl_ui.contour_editor.EditorStateMachine.Modes.RectangleSelectMode import RectangleSelectMode

class ToolManager:
    def __init__(self, editor):
        self.editor = editor
        
        # Tool state - now owned by ToolManager
        self.ruler_mode_active = False
        self.magnifier_active = False
        self.rectangle_select_mode_active = False
        
        # Tool mode objects
        self.ruler_mode = RulerMode()
        self.rectangle_select_mode = RectangleSelectMode()
        
        # Magnifier widget
        self.magnifier = MagnifierWidget(editor)
        self.magnifier.hide()

    def show_tools_menu(self):
        """Show the compact Material Design tools popup (using reusable ToolsPopup)."""
        # Build a dictionary of current active tool states
        active_states = {
            "ruler": self.ruler_mode_active,
            "magnifier": self.magnifier_active,
            "rectangle_select": self.rectangle_select_mode_active
        }

        print(f"Current active states: {active_states}")

        # Create popup instance - use only the Qt signal, not the callback
        popup = ToolsPopup(
            parent=self.editor,
            active_states=active_states
        )

        # Connect to the Qt signal
        # bind the editor so the slot receives (editor, tool_name)
        popup.toolSelected.connect(lambda tool_name: self.handle_tool_selection(tool_name))

        # Show centered popup
        popup.show_centered()

    def handle_tool_selection(self, tool_name: str):
        """Handle tool selection from ToolsPopup."""
        print(f"Tool selected: {tool_name}")

        # Map tool names to actions
        if tool_name == "Ruler":
            self.toggle_ruler_mode()
        elif tool_name == "Magnifier":
            self.toggle_magnifier()
        elif tool_name == "Rectangle Select":
            self.enable_rectangle_select_mode()
        else:
            print(f"Unknown tool: {tool_name}")

    def enable_rectangle_select_mode(self):
        """Toggle rectangle selection mode on/off"""
        if self.rectangle_select_mode_active:
            # Exit rectangle select mode
            self.rectangle_select_mode_active = False
            self.editor.selection_manager.clear_all_selections()
            self.rectangle_select_mode.clear()  # Clear any in-progress selection
            self.editor.set_cursor_mode(EDIT_MODE)
            print("Rectangle selection mode deactivated")
        else:
            # Enter rectangle select mode
            self.rectangle_select_mode_active = True
            self.editor.set_cursor_mode(RECTANGLE_SELECT_MODE)
            print("Rectangle selection mode activated")

        self.editor.update()
        return self.rectangle_select_mode_active

    def toggle_ruler_mode(self):
        """Toggle distance measurement (ruler) mode."""
        self.ruler_mode_active = not self.ruler_mode_active
        self.ruler_mode.ruler_start = None
        self.ruler_mode.ruler_end = None
        self.editor.setCursor(Qt.CursorShape.CrossCursor if self.ruler_mode_active else Qt.CursorShape.ArrowCursor)
        print(f"Ruler mode {'enabled' if self.ruler_mode_active else 'disabled'}.")
        self.editor.update()

    def toggle_magnifier(self):
        """Toggle the magnifier window on/off"""
        self.magnifier_active = not self.magnifier_active

        if self.magnifier_active:
            try:
                # Get current mouse position
                global_pos = QCursor.pos()
                widget_pos = self.editor.mapFromGlobal(global_pos)
                # Convert to QPointF to avoid mixing QPoint and QPointF
                widget_pos = QPointF(widget_pos.x(), widget_pos.y())
                image_pos = map_to_image_space(widget_pos, self.editor.viewport_controller.translation, self.editor.viewport_controller.scale_factor)

                # Set cursor position without triggering update yet
                self.magnifier.cursor_pos = image_pos

                # Show the window first
                self.magnifier.show()
                self.magnifier.raise_()

                # Now position it (this will trigger paint, but window is already shown)
                self.magnifier.update_position(widget_pos, image_pos)

                print("Magnifier activated - move mouse to see zoomed view")
            except Exception as e:
                print(f"Error activating magnifier: {e}")
                import traceback
                traceback.print_exc()
                self.magnifier_active = False
                return False
        else:
            self.magnifier.hide()
            print("Magnifier deactivated")

        return self.magnifier_active


# Legacy functions for backward compatibility - delegate to tool manager
def enable_rectangle_select_mode(editor):
    """Toggle rectangle selection mode on/off"""
    if editor.rectangle_select_mode_active:
        # Exit rectangle select mode
        editor.rectangle_select_mode_active = False
        editor.selection_manager.clear_all_selections()
        editor.rectangle_select_mode.clear()  # Clear any in-progress selection
        editor.set_cursor_mode(EDIT_MODE)
        print("Rectangle selection mode deactivated")
    else:
        # Enter rectangle select mode
        editor.rectangle_select_mode_active = True
        editor.set_cursor_mode(RECTANGLE_SELECT_MODE)
        print("Rectangle selection mode activated")

    editor.update()
    return editor.rectangle_select_mode_active

def toggle_ruler_mode(editor):
    """Toggle distance measurement (ruler) mode."""
    editor.ruler_mode_active = not getattr(editor, "ruler_mode_active", False)
    editor.ruler_mode.ruler_start = None
    editor.ruler_mode.ruler_end = None
    editor.setCursor(Qt.CursorShape.CrossCursor if editor.ruler_mode_active else Qt.CursorShape.ArrowCursor)
    print(f"Ruler mode {'enabled' if editor.ruler_mode_active else 'disabled'}.")
    editor.update()

def toggle_magnifier(editor):
    """Toggle the magnifier window on/off"""
    editor.magnifier_active = not editor.magnifier_active

    if editor.magnifier_active:
        try:
            # Get current mouse position
            from PyQt6.QtGui import QCursor
            global_pos = QCursor.pos()
            widget_pos = editor.mapFromGlobal(global_pos)
            # Convert to QPointF to avoid mixing QPoint and QPointF
            widget_pos = QPointF(widget_pos.x(), widget_pos.y())
            image_pos = map_to_image_space(widget_pos, editor.translation, editor.scale_factor)

            # Set cursor position without triggering update yet
            editor.magnifier.cursor_pos = image_pos

            # Show the window first
            editor.magnifier.show()
            editor.magnifier.raise_()

            # Now position it (this will trigger paint, but window is already shown)
            editor.magnifier.update_position(widget_pos, image_pos)

            print("Magnifier activated - move mouse to see zoomed view")
        except Exception as e:
            print(f"Error activating magnifier: {e}")
            import traceback
            traceback.print_exc()
            editor.magnifier_active = False
            return False
    else:
        editor.magnifier.hide()
        print("Magnifier deactivated")

    return editor.magnifier_active

def handle_tool_selection(editor, tool_name: str):
    """Handle tool selection from ToolsPopup."""
    print(f"Tool selected: {tool_name}")

    # Map tool names to actions
    if tool_name == "Ruler":
        toggle_ruler_mode(editor)
    elif tool_name == "Magnifier":
        toggle_magnifier(editor)
    elif tool_name == "Rectangle Select":
        enable_rectangle_select_mode(editor)
    else:
        print(f"Unknown tool: {tool_name}")

def show_tools_menu(editor):
    """Show the compact Material Design tools popup (using reusable ToolsPopup)."""

    # Build a dictionary of current active tool states
    active_states = {
        "ruler": getattr(editor, "ruler_mode_active", False),
        "magnifier": getattr(editor, "magnifier_active", False),
        "rectangle_select": getattr(editor, "rectangle_select_mode_active", False)
    }

    print(f"Current active states: {active_states}")

    # Create popup instance - use only the Qt signal, not the callback
    popup = ToolsPopup(
        parent=editor,
        active_states=active_states
    )

    # Connect to the Qt signal
    # bind the editor so the slot receives (editor, tool_name)
    popup.toolSelected.connect(lambda tool_name, editor=editor: handle_tool_selection(editor, tool_name))

    # Show centered popup
    popup.show_centered()

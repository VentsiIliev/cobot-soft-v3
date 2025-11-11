from PyQt6.QtCore import Qt, QPointF

from src.frontend.pl_ui.contour_editor.EditorStateMachine.Modes.MultiPointSelectMode import MultiPointSelectMode
from src.frontend.pl_ui.contour_editor.EditorStateMachine.Modes.PointDragMode import PointDragMode
from src.frontend.pl_ui.contour_editor.utils.coordinate_utils import map_to_image_space, calculate_distance
from src.frontend.pl_ui.contour_editor.EditorStateMachine.Modes.RulerMode import RulerMode
from src.frontend.pl_ui.contour_editor.EditorStateMachine.Modes.PanMode import PanMode




def mousePressEvent(contour_editor, event):
    # Check if point info overlay is visible - if so, deselect the point and consume the event
    if hasattr(contour_editor, 'point_info_overlay') and contour_editor.point_info_overlay.isVisible():
        contour_editor.selection_manager.clear_all_selections()
        contour_editor.point_info_overlay.hide()
        contour_editor.update()
        return

    # Check if segment click overlay is visible - if so, hide it and consume the event
    if hasattr(contour_editor, 'segment_click_overlay') and contour_editor.segment_click_overlay.isVisible():
        contour_editor.segment_click_overlay.hide()
        return

    if contour_editor.viewport_controller.is_zooming:
        contour_editor.last_drag_pos = event.position()
        return

    if contour_editor.pan_mode_active:
        contour_editor.pan_mode.mousePress(contour_editor, event)
        return

    if not contour_editor.is_within_image(event.position()):
        print(f"Position out of image: {event.position()}")
        return

    pos = map_to_image_space(event.position(), contour_editor.translation, contour_editor.scale_factor)
    # Screen-space hit radius
    min_px_hit = 10  # pixels on screen
    # Convert to image-space for detection
    hit_radius_img = min_px_hit / contour_editor.scale_factor
    print("Mouse pressed at image coords:", pos)

    # --- RULER MODE ---

    if getattr(contour_editor, "ruler_mode_active", False):
        contour_editor.ruler_mode.mousePress(contour_editor,event)
        return

    # Right-click handling
    if event.button() == Qt.MouseButton.RightButton:
        if contour_editor.manager.remove_control_point_at(pos):
            contour_editor.handle_right_mouse_click(contour_editor)
            return

    elif event.button() == Qt.MouseButton.LeftButton:
        # Handle rectangle selection mode
        if getattr(contour_editor, 'rectangle_select_mode_active', False):
            contour_editor.rectangle_select_mode.mousePress(contour_editor, event)
            return

        # Handle pickup point mode
        if contour_editor.pickup_point_mode_active:
            contour_editor.pickup_point = pos
            print(f"Pickup point set at: {pos}")
            contour_editor.update()
            return

        candidates = contour_editor.manager.find_all_drag_targets(pos, threshold=hit_radius_img)

        if candidates:
            if contour_editor.multi_select_mode_active:
                # Delegate to MultiPointSelectMode
                contour_editor.multi_select_mode.mousePress(contour_editor, event, candidates)
                contour_editor.update()  # Refresh UI to show selection
                return

            # Not multi-select: delegate to PointDragMode
            drag_target = candidates[0]  # pick first if not cycling for now
            contour_editor.drag_mode.mousePress(contour_editor, event, drag_target)
            print(f"Dragging existing point (PointDragMode): {drag_target}")

            # Start timer for press-and-hold to show point info overlay
            contour_editor.press_hold_start_pos = event.position()
            contour_editor.point_info_timer.start()
            return



        else:
            if contour_editor.multi_select_mode_active:
                # Clicked empty space in multi-select mode: do nothing
                print("Multi-select mode: clicked empty space, no point added")
                return

            # Not multi-select: attempt to add a control point
            result = contour_editor._handle_add_control_point(pos)
            if result:
                print(f"Added control point at {pos}")
                return

        # Clear all selections if clicking empty area without multi-select
        contour_editor.selection_manager.clear_all_selections()

        # Check again for adding control point if segment exists
        result = contour_editor._handle_add_control_point(pos)
        if result:
            print(f"_handle_add_control_point return result: {result}")
            return

        # Fallback: add new anchor point
        contour_editor.manager.add_point(pos)
        contour_editor.update()
        contour_editor.pointsUpdated.emit()

def mouseMoveEvent(contour_editor, event):
    # Track cursor position for drag crosshair (helps with touchscreen)
    contour_editor.current_cursor_pos = event.position()

    # Cancel press-and-hold timer if mouse moves significantly (indicating drag, not hold)
    if contour_editor.point_info_timer.isActive() and contour_editor.press_hold_start_pos is not None:
        # Calculate movement distance
        dx = event.position().x() - contour_editor.press_hold_start_pos.x()
        dy = event.position().y() - contour_editor.press_hold_start_pos.y()
        distance = (dx * dx + dy * dy) ** 0.5

        # If moved more than 5 pixels, cancel timer (it's a drag, not a hold)
        if distance > 5:
            contour_editor.point_info_timer.stop()
            contour_editor.press_hold_start_pos = None

    # Update magnifier if active
    if getattr(contour_editor, 'magnifier_active', False):
        # When dragging, show magnifier at crosshair position (50px above cursor)
        if contour_editor.drag_mode.dragging_point:
            crosshair_offset_y = -50
            crosshair_screen_pos = QPointF(
                event.position().x(),
                event.position().y() + crosshair_offset_y
            )
            image_pos = map_to_image_space(crosshair_screen_pos, contour_editor.translation, contour_editor.scale_factor)
            contour_editor.magnifier.update_position(crosshair_screen_pos, image_pos)
        else:
            # Normal mode - show magnifier at cursor position
            screen_pos = event.position()
            image_pos = map_to_image_space(screen_pos, contour_editor.translation, contour_editor.scale_factor)
            contour_editor.magnifier.update_position(screen_pos, image_pos)

    # --- Rectangle selection mode ---
    if getattr(contour_editor, 'rectangle_select_mode_active', False):
        contour_editor.rectangle_select_mode.mouseMove(contour_editor, event)
        return

    # --- Dragging a point ---
    # --- RULER MODE ---
    if getattr(contour_editor, "ruler_mode_active", False) and contour_editor.ruler_mode.dragging_ruler_point:
        contour_editor.ruler_mode.mouseMove(contour_editor, event)
        return

    if contour_editor.drag_mode.dragging_point:
        contour_editor.drag_mode.mouseMove(contour_editor, event)
        return

    # --- Panning the background ---
    if contour_editor.pan_mode_active:
        contour_editor.pan_mode.mouseMove(contour_editor, event)
        return


def mouseDoubleClickEvent(contour_editor, event):
    pos = event.position()
    target = contour_editor.manager.find_drag_target(pos)

    if target and target[0] == 'control':
        role, seg_index, ctrl_idx = target
        contour_editor.manager.reset_control_point(seg_index, ctrl_idx)
        contour_editor.update()
        contour_editor.pointsUpdated.emit()

def mouseReleaseEvent(contour_editor, event):

    # Stop press-and-hold timer on release
    if contour_editor.point_info_timer.isActive():
        contour_editor.point_info_timer.stop()
    contour_editor.press_hold_start_pos = None

    # --- Rectangle selection mode ---
    if getattr(contour_editor, 'rectangle_select_mode_active', False):
        contour_editor.rectangle_select_mode.mouseRelease(contour_editor, event)
        return

    # --- RULER MODE ---
    if getattr(contour_editor, "ruler_mode_active", False):
        contour_editor.ruler_mode.mouseRelease()

    # Clear drag mode state
    contour_editor.drag_mode.mouseRelease()

    # Handle zooming mode release
    if contour_editor.viewport_controller.is_zooming:
        contour_editor.last_drag_pos = None
        contour_editor.update()
        return

    if contour_editor.pan_mode_active:
        contour_editor.setCursor(Qt.CursorShape.OpenHandCursor)
        contour_editor.pan_mode.mouseRelease()

    contour_editor.update()

def handle_right_mouse_click(contour_editor):
    contour_editor.selection_manager.selected_point_info = None
    contour_editor.update()
    contour_editor.pointsUpdated.emit()


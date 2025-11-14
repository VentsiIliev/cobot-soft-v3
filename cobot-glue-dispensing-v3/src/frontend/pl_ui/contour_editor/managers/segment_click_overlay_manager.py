from frontend.pl_ui.contour_editor.widgets.SegmentClickOverlay import SegmentClickOverlay


def setup_segment_click_overlay(editor):
    # Segment click overlay for choosing between control point and anchor point
    try:
        segment_click_overlay = SegmentClickOverlay(editor)
        segment_click_overlay.hide()
        segment_click_overlay.disconnect_line_requested.connect(lambda: on_disconnect_line_requested(editor))
        segment_click_overlay.control_point_requested.connect(lambda: on_add_control_point_requested(editor))
        segment_click_overlay.anchor_point_requested.connect(lambda: on_add_anchor_point_requested(editor))
        segment_click_overlay.delete_segment_requested.connect(lambda: on_delete_segment_requested(editor))
        print(f"Segment click overlay set up for editor {editor}")
        return segment_click_overlay

    except:
        import traceback
        traceback.print_exc()
        return None

def on_disconnect_line_requested(editor):
    """Called when user clicks 'Disconnect Line' in the overlay"""

    # Disconnect the line segment
    result = editor.segment_action_controller.on_disconnect_line_requested(editor.pending_segment_click_pos, editor.pending_segment_click_index)

    if result:
        # Update and emit signals only if successful
        editor.update()
        editor.pointsUpdated.emit()
    else:
        print(f"Failed to disconnect line segment in segment {editor.pending_segment_click_index}")

    # Clear pending data
    editor.pending_segment_click_pos = None
    editor.pending_segment_click_index = None

def on_add_control_point_requested(editor):
    """Called when user clicks 'Add Control Point' in the overlay"""
    if editor.pending_segment_click_pos is None or editor.pending_segment_click_index is None:
        return

    pos = editor.pending_segment_click_pos
    seg_index = editor.pending_segment_click_index
    result = editor.segment_action_controller.on_add_control_point_requested(pos, seg_index)

    # If the result is False, that means adding the control point was prevented (e.g., due to layer being locked)
    if result:
        # Update and emit signals if control point is successfully added
        editor.update()
        editor.pointsUpdated.emit()

    # Clear pending data
    editor.pending_segment_click_pos = None
    editor.pending_segment_click_index = None

def on_delete_segment_requested(editor):
    """Called when user clicks 'Delete Segment' in the overlay"""
    if editor.pending_segment_click_index is None:
        return

    seg_index = editor.pending_segment_click_index

    # Delete the segment
    editor.segment_action_controller.on_delete_segment_requested(seg_index)
    # Update and emit signals
    editor.update()
    editor.pointsUpdated.emit()

    # Clear pending data
    editor.pending_segment_click_pos = None
    editor.pending_segment_click_index = None

def on_add_anchor_point_requested(editor):
    """Called when user clicks 'Add Anchor Point' in the overlay"""
    if editor.pending_segment_click_pos is None or editor.pending_segment_click_index is None:
        return

    pos = editor.pending_segment_click_pos
    seg_index = editor.pending_segment_click_index

    # Insert anchor point at the clicked position
    result = editor.segment_action_controller.on_add_anchor_point_requested(pos, seg_index)
    if result:
        # Update and emit signals if anchor point is successfully added
        editor.update()
        editor.pointsUpdated.emit()

    # Clear pending data
    editor.pending_segment_click_pos = None
    editor.pending_segment_click_index = None
from PyQt6.QtCore import QEventLoop, QPointF
from PyQt6.QtWidgets import QDialog

from frontend.pl_ui.contour_editor import constants
from frontend.pl_ui.contour_editor.widgets.PointInfoOverlay import PointInfoOverlay

def setup_point_info_overlay(editor):
        point_info_overlay = PointInfoOverlay(editor)
        point_info_overlay.hide()
        point_info_overlay.delete_requested.connect(lambda: remove_selected_points(editor))
        point_info_overlay.line_segment_clicked.connect(lambda seg_index, line_index: on_line_segment_clicked(editor, seg_index, line_index))
        point_info_overlay.set_length_requested.connect(lambda seg_index, line_index:on_set_length_requested(editor, seg_index, line_index))
        return point_info_overlay

def remove_selected_points(editor):
        """Remove currently selected points - handles both single and multi-selection"""
        from PyQt6.QtWidgets import QMessageBox
        from collections import defaultdict

        # Get selected points
        selected_points_list = getattr(editor.selection_manager, 'selected_points_list', [])
        selected_point_info = getattr(editor.selection_manager, 'selected_point_info', None)

        if not selected_points_list and not selected_point_info:
            QMessageBox.information(None, "No Selection",
                "Please select one or more points first.\n\n" +
                "Tip: In multi-select mode, click points to select/deselect.")
            return

        # Handle multi-selection
        if selected_points_list:
            points_count = len(selected_points_list)

            # Ask for confirmation when deleting multiple points
            if points_count > 1:
                reply = QMessageBox.question(
                    None,
                    "Delete Multiple Points",
                    f"Are you sure you want to delete {points_count} selected points?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Group points by segment to handle index shifts correctly
            points_by_segment = defaultdict(list)
            for point_info in selected_points_list:
                seg_index = point_info['seg_index']
                points_by_segment[seg_index].append(point_info)

            # Sort segments in reverse order
            sorted_segments = sorted(points_by_segment.keys(), reverse=True)

            print(f"Deleting {points_count} points from {len(sorted_segments)} segment(s)")

            # Save state once for the entire operation
            editor.manager.save_state()

            # Process each segment independently
            for seg_index in sorted_segments:
                segment_points = points_by_segment[seg_index]

                # Sort points within segment by index in reverse order
                sorted_points = sorted(segment_points, key=lambda x: x['point_index'], reverse=True)

                segments = editor.manager.get_segments()
                if seg_index < 0 or seg_index >= len(segments):
                    print(f"Warning: Skipping invalid segment index: {seg_index}")
                    continue

                segment = segments[seg_index]

                # Check if layer is locked
                if segment.layer and segment.layer.locked:
                    print(f"Warning: Cannot delete points from locked layer '{segment.layer.name}'")
                    continue

                # Delete points in reverse order
                for point_info in sorted_points:
                    role = point_info['role']
                    point_index = point_info['point_index']

                    if role not in ['anchor', 'control']:
                        print(f"Warning: Skipping unknown point type: {role}")
                        continue

                    try:
                        if role == 'anchor':
                            if 0 <= point_index < len(segment.points):
                                del segment.points[point_index]
                                # Also remove corresponding control point
                                if point_index < len(segment.controls):
                                    del segment.controls[point_index]
                                print(f"Deleted anchor point at segment {seg_index}, index {point_index}")
                            else:
                                print(f"Warning: Anchor index {point_index} out of bounds")

                        elif role == 'control':
                            if 0 <= point_index < len(segment.controls):
                                segment.controls[point_index] = None
                                print(f"Cleared control point at segment {seg_index}, index {point_index}")
                            else:
                                print(f"Warning: Control index {point_index} out of bounds")

                    except Exception as e:
                        print(f"Error deleting point at seg {seg_index}, idx {point_index}: {e}")

            # Clear selections
            editor.selection_manager.clear_all_selections()
            print(f"Successfully deleted {points_count} points")

        # Handle single selection (backward compatibility)
        elif selected_point_info:
            try:
                role, seg_index, point_index = selected_point_info

                if role not in ['anchor', 'control']:
                    QMessageBox.warning(None, "Invalid Selection", f"Unknown point type: {role}")
                    return

                # Use manager's remove_point method (handles undo/redo)
                editor.manager.remove_point(role, seg_index, point_index)
                editor.selection_manager.clear_all_selections()
                print(f"Deleted {role} point {point_index} from segment {seg_index}")

            except Exception as e:
                QMessageBox.critical(None, "Delete Point Failed", f"Error: {str(e)}")
                print(f"Error in remove_selected_points: {e}")

        # Refresh UI
        editor.update()
        if hasattr(editor, 'point_manager_widget') and editor.point_manager_widget:
            editor.point_manager_widget.refresh_points()

def on_line_segment_clicked(editor, seg_index, line_index):
    """Handle line segment button click in point info overlay"""
    if line_index == -1:
        # Deselect
        editor.highlighted_line_segment = None
    else:
        # Highlight this line segment
        editor.highlighted_line_segment = (seg_index, line_index)

    # Redraw to show/hide the highlighted line
    editor.update()

def on_set_length_requested(editor, seg_index, line_index):
        """Handle set length and angle request for a line segment"""
        import math
        from pl_ui.contour_editor.utils.coordinate_utils import calculate_distance
        from pl_ui.contour_editor.widgets.SetLengthAndAngleDialog import SetLengthAndAngleDialog

        # Get the segment
        segments = editor.manager.get_segments()
        if seg_index < 0 or seg_index >= len(segments):
            print(f"Invalid segment index: {seg_index}")
            return

        segment = segments[seg_index]
        points = segment.points

        # line_index represents the line from points[line_index] to points[line_index + 1]
        if line_index < 0 or line_index >= len(points) - 1:
            print(f"Invalid line index: {line_index}")
            return

        p1 = points[line_index]
        p2 = points[line_index + 1]

        # Calculate current length
        current_length_px = calculate_distance(p1, p2)
        current_length_mm = current_length_px / constants.PIXELS_PER_MM

        # Calculate current angle (in degrees, relative to positive X axis)
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        current_angle_rad = math.atan2(dy, dx)
        current_angle_deg = math.degrees(current_angle_rad)

        # Show dialog with current angle
        dialog = SetLengthAndAngleDialog(current_length_mm, current_angle_deg, editor)
        dialog.show()
        loop = QEventLoop()
        dialog.finished.connect(loop.quit)  # Once finished, quit the event loop
        loop.exec()  # Block until the user closes the dialog

        if dialog.result() != QDialog.DialogCode.Accepted:
            print("Set length/angle dialog cancelled")
            return


        new_length_mm = dialog.get_length()
        new_angle_deg = dialog.get_angle()

        if new_length_mm is None or new_length_mm <= 0:
            return

        print(f"Setting line {line_index} from {current_length_mm:.2f}mm @ {current_angle_deg:.1f}° to {new_length_mm:.2f}mm @ {new_angle_deg if new_angle_deg is not None else current_angle_deg:.1f}°")

        # Convert to pixels
        new_length_px = new_length_mm * constants.PIXELS_PER_MM

        # Determine the angle to use
        if new_angle_deg is not None:
            # Use the new angle
            angle_rad = math.radians(new_angle_deg)
            unit_x = math.cos(angle_rad)
            unit_y = math.sin(angle_rad)
        else:
            # Keep current angle, only change length
            if current_length_px == 0:
                print("Cannot set length: current length is zero")
                return

            unit_x = dx / current_length_px
            unit_y = dy / current_length_px

        # Calculate new position for p2
        new_p2 = QPointF(
            p1.x() + unit_x * new_length_px,
            p1.y() + unit_y * new_length_px
        )

        # Save state for undo
        editor.manager.save_state()

        # Move the point
        points[line_index + 1] = new_p2

        # Update and redraw
        editor.update()
        editor.pointsUpdated.emit()

        print(f"Moved point from ({p2.x():.2f}, {p2.y():.2f}) to ({new_p2.x():.2f}, {new_p2.y():.2f})")

def update_point_info_overlay(editor):
    """Show or hide the point info overlay based on current selection"""
    # Only show for single-point selection (not multi-select)
    selected_point_info = getattr(editor.selection_manager, 'selected_point_info', None)
    selected_points_list = getattr(editor.selection_manager, 'selected_points_list', [])

    # Hide if multi-select (more than 1 point) or no selection
    if len(selected_points_list) > 1 or not selected_point_info:
        editor.point_info_overlay.hide()
        return

    # Single point is selected
    role, seg_index, point_index = selected_point_info

    # Get the point's position in image space
    segments = editor.manager.get_segments()
    if seg_index < 0 or seg_index >= len(segments):
        editor.point_info_overlay.hide()
        return

    segment = segments[seg_index]

    # Get point position based on role
    if role == "anchor":
        if point_index < 0 or point_index >= len(segment.points):
            editor.point_info_overlay.hide()
            return
        point_pos = segment.points[point_index]
    elif role == "control":
        if point_index < 0 or point_index >= len(segment.controls):
            editor.point_info_overlay.hide()
            return
        point_pos = segment.controls[point_index]
        if point_pos is None:
            editor.point_info_overlay.hide()
            return
    else:
        editor.point_info_overlay.hide()
        return

    # Convert point position to screen space
    screen_pos = editor.translation + QPointF(
        point_pos.x() * editor.scale_factor,
        point_pos.y() * editor.scale_factor
    )

    # Convert to global coordinates for the overlay
    global_pos = editor.mapToGlobal(screen_pos.toPoint())

    # Determine connected line segments
    connected_line_segments = []

    if role == "anchor":
        # For anchor points, show the line segments they connect to
        # If point_index is 0, it's only connected to line 0 (to next point)
        # If point_index is last, it's only connected to the previous line
        # Otherwise, it's connected to two lines (before and after)

        num_points = len(segment.points)

        # Line segment before this point (this point is the end)
        if point_index > 0:
            connected_line_segments.append(point_index - 1)

        # Line segment after this point (this point is the start)
        if point_index < num_points - 1:
            connected_line_segments.append(point_index)

    elif role == "control":
        # For control points, show the line segment they belong to
        connected_line_segments.append(point_index)

    # Update and show the overlay
    editor.point_info_overlay.set_point_info(role, seg_index, point_index, connected_line_segments)
    editor.point_info_overlay.show_at(global_pos)
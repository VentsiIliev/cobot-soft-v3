from PyQt6.QtCore import QTimer

from frontend.pl_ui.contour_editor import constants
from frontend.pl_ui.contour_editor.managers.point_info_overlay_manager import remove_selected_points, setup_point_info_overlay, update_point_info_overlay
from frontend.pl_ui.contour_editor.managers.segment_click_overlay_manager import setup_segment_click_overlay


class OverlayManager:
    def __init__(self, editor):
        self.editor = editor
        
        # Overlay state
        self.pending_segment_click_pos = None  # Store the clicked position
        self.pending_segment_click_index = None  # Store the segment index
        self.press_hold_start_pos = None  # Track where press started
        
        # Initialize overlays
        self.setup_overlays()
        self.setup_overlay_timers()
    
    def setup_overlays(self):
        """Initialize all overlay components"""
        # Segment click overlay for choosing between control point and anchor point
        try:
            self.segment_click_overlay = setup_segment_click_overlay(self.editor)
        except:
            import traceback
            traceback.print_exc()

        # Point info overlay for showing info and quick actions on selected point
        self.point_info_overlay = setup_point_info_overlay(self.editor)
    
    def setup_overlay_timers(self):
        """Setup timers for overlay functionality"""
        # Timer for press-and-hold to show point info overlay
        self.point_info_timer = QTimer(self.editor)
        self.point_info_timer.setSingleShot(True)
        self.point_info_timer.setInterval(constants.POINT_INFO_HOLD_DURATION_MS)  # Hold time to show overlay
        self.point_info_timer.timeout.connect(self._show_point_info_on_hold)
    
    def remove_selected_points(self):
        """Remove selected points using the point info overlay manager"""
        remove_selected_points(self.editor)
    
    def _show_point_info_on_hold(self):
        """Callback when press-and-hold timer fires - show point info overlay"""
        # Timer only fires if mouse hasn't moved > 5px (checked in mouseMoveEvent)
        # So if we're here, user is holding still - show the overlay
        update_point_info_overlay(self.editor)
    
    def handle_add_control_point(self, pos):
        """Smart segment click handling - shows overlay only if no control point exists"""
        # Get the segment info at the position
        segment_info = self.editor.manager.find_segment_at(pos)
        if segment_info:
            seg_index, line_index = segment_info
            segment = self.editor.manager.get_segments()[seg_index]

            # Check if this line segment already has a control point
            has_control_point = (
                line_index < len(segment.controls) and
                segment.controls[line_index] is not None
            )

            if has_control_point:
                # Control point already exists - directly add anchor point to split segment
                print(f"Control point already exists at line {line_index}, adding anchor point instead")
                result = self.editor.manager.insert_anchor_point(seg_index, pos)
                if result:
                    self.editor.update()
                    self.editor.pointsUpdated.emit()
                return True
            else:
                # No control point - show overlay to let user choose
                self.pending_segment_click_pos = pos
                self.pending_segment_click_index = seg_index

                # Show the overlay at the cursor position
                from PyQt6.QtGui import QCursor
                global_pos = QCursor.pos()
                self.segment_click_overlay.show_at(global_pos)

                return True

        return False
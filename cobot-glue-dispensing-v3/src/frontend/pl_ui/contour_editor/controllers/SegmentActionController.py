class SegmentActionController:
    def __init__(self,bezier_manager):
        self.bezier_manager = bezier_manager

    def add_new_segment(self, layer_name="Contour"):
        """Add a new segment to the workpiece"""
        print("New segment started.")
        new_segment = self.bezier_manager.start_new_segment(layer_name)

        print("Current segments:", self.bezier_manager.get_segments())  # Debug print


        return new_segment

    def on_disconnect_line_requested(self,pending_segment_click_pos,pending_segment_click_index):
        """Called when user clicks 'Disconnect Line' in the overlay"""
        if pending_segment_click_index is None or pending_segment_click_pos is None:
            return

        seg_index = pending_segment_click_index
        pos = pending_segment_click_pos

        # Find which line segment was clicked to get the line index
        segment_info = self.bezier_manager.find_segment_at(pos)
        if not segment_info:
            print("No segment line found at click position")
            return

        found_seg_index, line_index = segment_info

        # Verify this matches our expected segment
        if found_seg_index != seg_index:
            print(f"Warning: Found segment {found_seg_index} but expected {seg_index}")
            seg_index = found_seg_index  # Use the found segment index

        # Disconnect the line segment
        result = self.bezier_manager.disconnect_line_segment(seg_index, line_index)
        return result

    def on_add_control_point_requested(self,pending_segment_click_pos,pending_segment_click_index):
        """Called when user clicks 'Add Control Point' in the overlay"""
        if pending_segment_click_pos is None or pending_segment_click_index is None:
            return

        pos = pending_segment_click_pos
        seg_index = pending_segment_click_index

        segment = self.bezier_manager.get_segments()[seg_index]
        segment_info = self.bezier_manager.find_segment_at(pos)

        result = False
        if segment_info:
            _, line_index = segment_info

            # Always add/update control point (allows replacing existing control points)
            result = self.bezier_manager.add_control_point(seg_index, pos)

        return result

    def on_delete_segment_requested(self,pending_segment_click_index):
        """Called when user clicks 'Delete Segment' in the overlay"""
        if pending_segment_click_index is None:
            return

        seg_index = pending_segment_click_index

        # Delete the segment
        self.bezier_manager.delete_segment(seg_index)

    def on_add_anchor_point_requested(self,pending_segment_click_pos,pending_segment_click_index):
        """Called when user clicks 'Add Anchor Point' in the overlay"""
        if pending_segment_click_pos is None or pending_segment_click_index is None:
            return

        pos = pending_segment_click_pos
        seg_index = pending_segment_click_index

        # Insert anchor point at the clicked position
        result = self.bezier_manager.insert_anchor_point(seg_index, pos)
        return result

    def delete_segment(self, seg_index):
        """Delete a segment from the workpiece"""
        self.bezier_manager.delete_segment(seg_index)

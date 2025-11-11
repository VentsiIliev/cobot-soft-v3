class SelectionManager:
    def __init__(self):
        self.selected_points_list = []
        self.selected_point_info = None


    def toggle_point_selection(self, drag_target):
        """Toggle selection state of a point for multi-selection"""
        if not drag_target:
            return

        role, seg_index, point_index = drag_target
        selection_dict = {
            'role': role,
            'seg_index': seg_index,
            'point_index': point_index
        }

        # Check if this point is already selected
        for i, selected in enumerate(self.selected_points_list):
            if (selected['role'] == role and
                    selected['seg_index'] == seg_index and
                    selected['point_index'] == point_index):
                # Point is selected, remove it
                del self.selected_points_list[i]
                print(f"Deselected point: {selection_dict}")
                return

        # Point is not selected, add it
        self.selected_points_list.append(selection_dict)
        print(f"Selected point: {selection_dict}")

    def set_single_selection(self, drag_target):
        """Set a single point selection (clears others)"""
        self.clear_all_selections()
        if drag_target:
            role, seg_index, point_index = drag_target
            self.selected_point_info = drag_target  # Maintain backward compatibility
            self.selected_points_list.append({
                'role': role,
                'seg_index': seg_index,
                'point_index': point_index
            })
            print(f"Single selection set: {drag_target}")

    def clear_all_selections(self):
        """Clear all point selections"""
        self.selected_points_list.clear()
        self.selected_point_info = None
        print("Cleared all selections")


    def is_point_selected(self, role, seg_index, point_index):
        """Check if a specific point is selected"""
        for selected in self.selected_points_list:
            if (selected['role'] == role and
                    selected['seg_index'] == seg_index and
                    selected['point_index'] == point_index):
                return True
        return False

    def set_single_selection_from_dict(self, point_info):
        """Set a single point selection from a selection dictionary (clears others)"""
        self.clear_all_selections()
        if point_info:
            role = point_info['role']
            seg_index = point_info['seg_index']
            point_index = point_info['point_index']
            self.selected_point_info = (role, seg_index, point_index)  # Maintain backward compatibility
            self.selected_points_list.append(point_info)
            print(f"Single selection set from dict: {point_info}")
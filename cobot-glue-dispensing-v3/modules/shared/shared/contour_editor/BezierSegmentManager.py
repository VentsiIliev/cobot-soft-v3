from __future__ import annotations

import math

import numpy as np
from PyQt6.QtCore import QPointF
import copy
from src.frontend.pl_ui.contour_editor.widgets.SegmentSettingsWidget import default_settings

class Segment:
    def __init__(self, layer=None,settings=None):
        self.points: list[QPointF] = []
        self.controls: list[QPointF | None] = []
        self.visible = True
        self.layer = layer
        if settings == None:
            self.settings = default_settings
            print("Setting default settings:", self.settings)
        else:
            self.settings = settings

    def set_settings(self, settings: dict):
        """Set the settings for the segment."""
        self.settings = settings
        print("Segment settings updated:", self.settings)

    def add_point(self, point: QPointF):
        self.points.append(point)
        if len(self.points) > 1:
            self.controls.append(None)

    def remove_point(self, index: int):
        if 0 <= index < len(self.points):
            del self.points[index]
            if index < len(self.controls):
                del self.controls[index]

    def add_control_point(self, index: int, point: QPointF):
        if 0 <= index < len(self.controls):
            self.controls[index] = point
        else:
            self.controls.append(point)

    def set_layer(self, layer):
        self.layer = layer

    def get_external_layer(self):
        return self.layer if self.layer else None

    def get_contour_layer(self):
        return self.layer if self.layer else None

    def get_fill_layer(self):
        return self.layer if self.layer else None

    def __str__(self):
        return f"Segment(points={self.points}, controls={self.controls}, visible={self.visible}, layer={self.layer})"


class Layer:
    def __init__(self, name, locked=False, visible=True):
        self.name = name
        self.locked = locked
        self.visible = visible
        self.segments: list[Segment] = []

    def add_segment(self, segment: Segment):
        self.segments.append(segment)

    def remove_segment(self, index: int):
        if 0 <= index < len(self.segments):
            del self.segments[index]

    def __str__(self):
        return f"Layer(name={self.name}, locked={self.locked}, visible={self.visible}, segments={self.segments})"


class BezierSegmentManager:
    def __init__(self):
        self.active_segment_index = 0
        self.undo_stack = []
        self.redo_stack = []
        self.external_layer = Layer("Workpiece", False, True)
        self.contour_layer = Layer("Contour", False, True)
        self.fill_layer = Layer("Fill", False, True)
        self.segments: list[Segment] = [Segment(layer=self.contour_layer)]

    def undo(self):
        if not self.undo_stack:
            raise Exception("Nothing to undo.")
        self.redo_stack.append(copy.deepcopy(self.segments))
        self.segments = self.undo_stack.pop()

    def redo(self):
        if not self.redo_stack:
            raise Exception("Nothing to redo.")
        self.undo_stack.append(copy.deepcopy(self.segments))
        self.segments = self.redo_stack.pop()

    def save_state(self, max_stack_size=100):
        print("Saving state...")
        self.undo_stack.append(copy.deepcopy(self.segments))
        if len(self.undo_stack) > max_stack_size:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def set_active_segment(self, seg_index):
        if 0 <= seg_index < len(self.segments):
            segment = self.segments[seg_index]
            layer_name = getattr(segment, 'layer', None)

            # Check if the segment has a layer and if it's locked
            if layer_name:
                if ((layer_name == "Workpiece" and self.external_layer.locked) or
                        (layer_name == "Contour" and self.contour_layer.locked) or
                        (layer_name == "Fill" and self.fill_layer.locked)):
                    print(f"Cannot activate segment {seg_index}: Layer '{layer_name}' is locked.")
                    return

            print(f"Updating segment: {seg_index}")
            self.active_segment_index = seg_index

    def create_segment(self, points, layer_name="Contour"):
        # Select the correct layer object
        if layer_name == "Workpiece":
            layer = self.external_layer
        elif layer_name == "Contour":
            layer = self.contour_layer
        elif layer_name == "Fill":
            layer = self.fill_layer
        else:
            raise ValueError(f"Invalid layer name: {layer_name}")

        # Create the segment and add points
        segment = Segment(layer=layer)
        for pt in points:
            segment.add_point(pt)
        return segment

    def start_new_segment(self, layer=None):
        print("Existing segments before creation:", len(self.segments))
        print("Starting new segment...")

        # Existing segment checking
        if len(self.segments) > 0:
            print("Existing segment:", self.segments[0])

        # Lock check logic and segment creation
        if layer:
            # print(f"Layer {layer} check...")
            if layer == "Workpiece" and self.external_layer.locked:
                # print(f"Cannot start new segment: Layer '{layer}' is locked.")
                return None, False
            elif layer == "Contour" and self.contour_layer.locked:
                # print(f"Cannot start new segment: Layer '{layer}' is locked.")
                return None, False
            elif layer == "Fill" and self.fill_layer.locked:
                # print(f"Cannot start new segment: Layer '{layer}' is locked.")
                return None,False

        if layer == "Workpiece":
            layer = self.external_layer
        elif layer == "Contour":
            layer = self.contour_layer
        elif layer == "Fill":
            layer = self.fill_layer
        else:
            raise ValueError(f"Invalid layer name: {layer}")

        # Create the segment
        new_segment = Segment(layer=layer)
        # print(f"Created new segment: {new_segment}")
        self.segments.append(new_segment)
        # print("Segments after creation:", len(self.segments))
        self.active_segment_index = len(self.segments) - 1
        # print("Active segment index set to:", self.active_segment_index)
        return new_segment ,True

    def assign_segment_layer(self, seg_index, layer_name):

        segment = self.segments[seg_index]
        if segment.layer.locked:
            print(f"Cannot assign layer: Layer '{segment.layer.name}' is locked.")
            return

        if 0 <= seg_index < len(self.segments):
            if layer_name == "Workpiece":
                segment.layer = self.external_layer
            elif layer_name == "Contour":
                segment.layer = self.contour_layer
            elif layer_name == "Fill":
                segment.layer = self.fill_layer
            else:
                print(f"Invalid layer name: {layer_name}")
                return

    def add_point(self, pos: QPointF):
        if 0 <= self.active_segment_index < len(self.segments):
            self.save_state()
            active_segment = self.segments[self.active_segment_index]

            if active_segment.layer is None:
                print("Cannot add point: Segment layer is not set.")
                return

            # Check if the layer is locked
            if active_segment.layer.locked:
                print(f"Cannot add point: Layer '{active_segment.layer.name}' is locked.")
                return  # Exit the function if the layer is locked

            active_segment.add_point(pos)  # Corrected the syntax here
            print(f"Added point {pos} to segment {self.active_segment_index}")
        else:
            print(f"Invalid active segment index: {self.active_segment_index}")

    def get_segments(self):
        return self.segments

    def to_wp_data(self, samples_per_segment=5):
        path_points = {
            "Workpiece": [],
            "Contour": [],
            "Fill": []
        }

        def is_cp_effective(p0, cp, p1, threshold=1.0):
            dx, dy = p1.x() - p0.x(), p1.y() - p0.y()
            if dx == dy == 0:
                return False
            distance = abs(dy * cp.x() - dx * cp.y() + p1.x() * p0.y() - p1.y() * p0.x()) / ((dx ** 2 + dy ** 2) ** 0.5)
            return distance > threshold

        def to_opencv_contour(path):
            """Convert list of [x, y] points to OpenCV-style contour array"""
            if not path or not all(isinstance(pt, (list, tuple)) and len(pt) == 2 for pt in path):
                print("⚠️ Skipping invalid path:", path)
                return None
            return np.array(path, dtype=np.float32).reshape(-1, 1, 2)

        # Process each segment individually
        for segment in self.segments:
            print("Processing segment with layer name:", segment.layer.name)
            raw_path = []
            points = segment.points
            controls = segment.controls

            # Add the first point
            if points:
                raw_path.append([points[0].x(), points[0].y()])

            # Build the path for this segment
            for i in range(1, len(points)):
                p0, p1 = points[i - 1], points[i]
                if i - 1 < len(controls) and controls[i - 1] is not None and is_cp_effective(p0, controls[i - 1], p1):
                    # For Bezier curves, skip t=0 (which is p0, already added) and include t=1 (which is p1)
                    for t in [j / samples_per_segment for j in range(1, samples_per_segment + 1)]:
                        x = (1 - t) ** 2 * p0.x() + 2 * (1 - t) * t * controls[i - 1].x() + t ** 2 * p1.x()
                        y = (1 - t) ** 2 * p0.y() + 2 * (1 - t) * t * controls[i - 1].y() + t ** 2 * p1.y()
                        raw_path.append([x, y])
                else:
                    # For straight lines, only add p1 (p0 is already in the path)
                    raw_path.append([p1.x(), p1.y()])
            print(f"    BezierSegmentManager: to_opencv_contour: raw_path = {raw_path}")
            # Convert to OpenCV contour format
            contour = to_opencv_contour(raw_path)
            print(f"    BezierSegmentManager: to_opencv_contour: to_opencv_contour result = {contour}")
            if contour is not None:
                # Append a new contour-settings pair for this segment
                path_points[segment.layer.name].append({
                    "contour": contour,
                    "settings": dict(segment.settings)
                })

        # Add placeholders for layers that have no segments
        for layer_name in ["Workpiece", "Contour", "Fill"]:
            if not path_points[layer_name]:
                path_points[layer_name].append({
                    "contour": np.empty((0, 1, 2), dtype=np.float32),
                    "settings": {}
                })

        print("path_points in to_wp_data:", path_points)
        return path_points

    # Example implementation for BezierSegmentManager
    def get_active_segment(self):
        if self.active_segment_index is not None and 0 <= self.active_segment_index < len(self.segments):
            return self.segments[self.active_segment_index]
        return None

    def disconnect_line_segment(self, seg_index, line_index):
        """
        Disconnect a line segment by splitting it into two separate segments.
        
        Args:
            seg_index: Index of the segment to split
            line_index: Index of the line within the segment (between points[line_index] and points[line_index + 1])
        """
        self.save_state()  # Save state before making changes
        
        if seg_index < 0 or seg_index >= len(self.segments):
            print(f"Invalid segment index: {seg_index}")
            return False
            
        segment = self.segments[seg_index]
        
        # Check if the segment layer is locked
        if segment.layer.locked:
            print(f"Cannot disconnect line segment: Layer '{segment.layer.name}' is locked.")
            return False
            
        # Check if line_index is valid
        if line_index < 0 or line_index >= len(segment.points) - 1:
            print(f"Invalid line index: {line_index}")
            return False
            
        # Can't disconnect if there are only 2 points (would result in empty segments)
        if len(segment.points) <= 2:
            print("Cannot disconnect: Segment has only 2 points")
            return False
            
        print(f"Disconnecting line {line_index} in segment {seg_index}")
        print(f"Original segment has {len(segment.points)} points creating {len(segment.points)-1} lines")
        
        # We need to create up to 3 segments:
        # 1. Everything BEFORE the disconnected line (if line_index > 0)
        # 2. The disconnected line itself (always)
        # 3. Everything AFTER the disconnected line (if there are more lines)
        
        segments_to_insert = []
        insertion_index = seg_index
        
        # 1. Create segment for everything BEFORE the disconnected line (if any)
        if line_index > 0:
            before_segment = Segment(layer=segment.layer, settings=segment.settings)
            
            # Add points from start up to (but not including) the start of disconnected line
            for i in range(line_index + 1):  # From 0 to line_index (inclusive)
                before_segment.points.append(segment.points[i])
                
            # Add corresponding control points
            for i in range(line_index):  # Control points from 0 to line_index-1
                if i < len(segment.controls):
                    before_segment.controls.append(segment.controls[i])
                else:
                    before_segment.controls.append(None)
                    
            segments_to_insert.append(before_segment)
            print(f"Before segment: {len(before_segment.points)} points, {len(before_segment.controls)} controls")
        
        # 2. Create segment for the disconnected line itself (always)
        disconnected_segment = Segment(layer=segment.layer, settings=segment.settings)
        
        # Add the two points of the disconnected line
        disconnected_segment.points.append(segment.points[line_index])      # Start point
        disconnected_segment.points.append(segment.points[line_index + 1])  # End point
        
        # Add the control point for the disconnected line (if any)
        if line_index < len(segment.controls):
            disconnected_segment.controls.append(segment.controls[line_index])
        else:
            disconnected_segment.controls.append(None)
            
        segments_to_insert.append(disconnected_segment)
        print(f"Disconnected segment: {len(disconnected_segment.points)} points, {len(disconnected_segment.controls)} controls")
        
        # 3. Create segment for everything AFTER the disconnected line (if any)
        if line_index + 2 < len(segment.points):  # If there are points after the disconnected line
            after_segment = Segment(layer=segment.layer, settings=segment.settings)
            
            # Add points from after the disconnected line to the end
            for i in range(line_index + 1, len(segment.points)):
                after_segment.points.append(segment.points[i])
                
            # Add corresponding control points
            for i in range(line_index + 1, len(segment.controls)):
                after_segment.controls.append(segment.controls[i])
                
            # Ensure proper control points list length
            while len(after_segment.controls) < len(after_segment.points) - 1:
                after_segment.controls.append(None)
                
            segments_to_insert.append(after_segment)
            print(f"After segment: {len(after_segment.points)} points, {len(after_segment.controls)} controls")
        
        # Remove the original segment
        del self.segments[seg_index]
        
        # Insert the new segments at the original position
        for i, new_segment in enumerate(segments_to_insert):
            self.segments.insert(seg_index + i, new_segment)
            
        # Update active segment index if necessary
        if self.active_segment_index == seg_index:
            # Set active to the disconnected line segment
            self.active_segment_index = seg_index + (1 if line_index > 0 else 0)
        elif self.active_segment_index > seg_index:
            # Shift the active segment index due to insertions
            self.active_segment_index += len(segments_to_insert) - 1
            
        print(f"Successfully disconnected line segment. Created {len(segments_to_insert)} segments from 1.")
        
        return True

    def get_robot_path(self, samples_per_segment=5):
        path_points = []

        def is_cp_effective(p0, cp, p1, threshold=1.0):
            dx, dy = p1.x() - p0.x(), p1.y() - p0.y()
            if dx == dy == 0:
                return False
            distance = abs(dy * cp.x() - dx * cp.y() + p1.x() * p0.y() - p1.y() * p0.x()) / ((dx ** 2 + dy ** 2) ** 0.5)
            return distance > threshold

        for segment in self.segments:
            points = segment.points
            controls = segment.controls
            for i in range(1, len(points)):
                p0, p1 = points[i - 1], points[i]
                if i - 1 < len(controls) and controls[i - 1] is not None and is_cp_effective(p0, controls[i - 1], p1):
                    for t in [j / samples_per_segment for j in range(samples_per_segment + 1)]:
                        x = (1 - t) ** 2 * p0.x() + 2 * (1 - t) * t * controls[i - 1].x() + t ** 2 * p1.x()
                        y = (1 - t) ** 2 * p0.y() + 2 * (1 - t) * t * controls[i - 1].y() + t ** 2 * p1.y()
                        path_points.append(QPointF(x, y))
                else:
                    path_points.extend([p0, p1])

        return path_points

    def delete_segment(self, seg_index):
        print(f"[DEBUG] delete_segment called for segment {seg_index}")
        if 0 <= seg_index < len(self.segments):
            segment = self.segments[seg_index]
            print(f"[DEBUG] Segment layer: {segment.layer.name}")
            print(f"[DEBUG] Segment layer locked: {segment.layer.locked}")
            print(f"[DEBUG] Manager external_layer.locked: {self.external_layer.locked}")
            print(f"[DEBUG] Manager contour_layer.locked: {self.contour_layer.locked}")
            print(f"[DEBUG] Manager fill_layer.locked: {self.fill_layer.locked}")

            if segment.layer.locked:
                print(f"Cannot delete segment {seg_index}: Layer '{segment.layer.name}' is locked.")
                return
            # # Check if the segment has a layer and if it's locked
            # layer_name = getattr(segment, 'layer', None)
            # if layer_name:
            #     if ((layer_name == "External" and self.external_layer.locked) or
            #             (layer_name == "Contour" and self.contour_layer.locked) or
            #             (layer_name == "Fill" and self.fill_layer.locked)):
            #         print(f"Cannot delete segment {seg_index}: Layer '{layer_name}' is locked.")
            #         return

            del self.segments[seg_index]
            if not self.segments:
                self.active_segment_index = -1
            elif self.active_segment_index == seg_index:
                self.active_segment_index = len(self.segments) - 1
            elif self.active_segment_index > seg_index:
                self.active_segment_index -= 1

    def set_segment_visibility(self, seg_index, visible):
        if 0 <= seg_index < len(self.segments):
            self.segments[seg_index].visible = visible

    def is_segment_visible(self, seg_index):
        if 0 <= seg_index < len(self.segments):
            return self.segments[seg_index].visible
        return False

    def has_control_points(self, seg_index):
        if 0 <= seg_index < len(self.segments):
            return len(self.segments[seg_index].controls) > 0
        return False

    def find_all_drag_targets(self, pos, threshold=5.0):
        """Return all points under the cursor, using Euclidean distance for better accuracy."""
        targets = []
        for seg_idx, segment in enumerate(self.segments):
            for idx, pt in enumerate(segment.points):
                dx = pt.x() - pos.x()
                dy = pt.y() - pos.y()
                distance = math.hypot(dx, dy)
                if distance <= threshold:
                    targets.append(("anchor", seg_idx, idx))
            for idx, ctrl in enumerate(segment.controls):
                if ctrl is None:
                    continue
                dx = ctrl.x() - pos.x()
                dy = ctrl.y() - pos.y()
                distance = math.hypot(dx, dy)
                if distance <= threshold:
                    targets.append(("control", seg_idx, idx))
        return targets

    def find_drag_target(self, pos, threshold=10):
        for seg_index, seg in enumerate(self.segments):

            # if segment is not active, skip
            if seg_index != self.active_segment_index:
                continue

            # segment is locked continue
            if seg.layer.locked:
                continue

            # Check control points
            for i, pt in enumerate(seg.controls):
                if pt is None:
                    continue  # Skip placeholder controls
                if (pt - pos).manhattanLength() < threshold:
                    return 'control', seg_index, i

            # Check anchor points
            for i, pt in enumerate(seg.points):
                if (pt - pos).manhattanLength() < threshold:
                    return 'anchor', seg_index, i

        return None

    def reset_control_point(self, seg_index, ctrl_idx):
        self.save_state()
        segment = self.segments[seg_index]

        # Sanity check
        if 0 <= ctrl_idx < len(segment.controls) and ctrl_idx < len(segment.points):
            segment.controls[ctrl_idx] = QPointF(segment.points[ctrl_idx])

    def move_point(self, role, seg_index, idx, new_pos, suppress_save=False):
        if not suppress_save:
            self.save_state()

        segment = self.segments[seg_index]

        if segment.layer.locked:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            parent = QApplication.activeWindow()
            QMessageBox.warning(parent, "Layer Locked",
                                f"Cannot move point: Layer '{segment.layer.name}' is locked.")
            return

        points = segment.points  # Access the 'points' attribute
        controls = segment.controls  # Access the 'controls' attribute

        if role == 'anchor':
            old_pos = points[idx]
            delta = new_pos - old_pos
            points[idx] = new_pos

            if idx > 0 and idx - 1 < len(controls):
                p0, ctrl = points[idx - 1], controls[idx - 1]
                if self.is_on_line(p0, ctrl, old_pos):
                    controls[idx - 1] = (p0 + new_pos) / 2

            if idx < len(points) - 1 and idx < len(controls):
                p1, ctrl = points[idx + 1], controls[idx]
                if self.is_on_line(old_pos, ctrl, p1):
                    controls[idx] = (new_pos + p1) / 2

        elif role == 'control':
            controls[idx] = new_pos

    def remove_control_point_at(self, pos, threshold=10):
        self.save_state()
        for seg in self.segments:

            if seg.layer is None:
                print("Cannot remove control point: Segment layer is not set.")
                return False

            if seg.layer.locked:
                print(f"Cannot remove control point: Layer '{seg.layer.name}' is locked.")
                return False

            for i, pt in enumerate(seg.controls):  # Access the 'controls' attribute
                if pt is None:  # Skip placeholder controls
                    continue
                if (pt - pos).manhattanLength() < threshold:
                    seg.remove_point(i)  # Access 'remove_point' method
                    # del seg.controls[i]  # Access 'controls' and delete the control point
                    if i + 1 < len(seg.points):  # Access 'points' and delete the corresponding point
                        del seg.points[i + 1]
                    return True
        return False

    def remove_point(self, role, seg_index, idx):
        self.save_state()
        segment = self.segments[seg_index]

        # Check if the segment has a layer and if it's locked
        layer_name = getattr(segment, 'layer', None)
        if layer_name:
            if ((layer_name == "Workpiece" and self.external_layer.locked) or
                    (layer_name == "Contour" and self.contour_layer.locked) or
                    (layer_name == "Fill" and self.fill_layer.locked)):
                print(f"Cannot remove point: Layer '{layer_name}' is locked.")
                return

        if role == 'anchor':
            del segment.points[idx]  # Access the 'points' attribute
        elif role == 'control':
            del segment.controls[idx]  # Access the 'controls' attribute
        else:
            raise ValueError("Role must be 'anchor' or 'control'")

    @staticmethod
    def is_on_line(p0, cp, p1, threshold=1.0):
        if cp is None:
            return False

        dx = p1.x() - p0.x()
        dy = p1.y() - p0.y()

        if dx == 0 and dy == 0:
            return False

        # Vector from p0 to cp
        v1x = cp.x() - p0.x()
        v1y = cp.y() - p0.y()

        # Vector from p0 to p1
        v2x = dx
        v2y = dy

        # Dot product to check if cp is within the segment projection
        dot = v1x * v2x + v1y * v2y
        len_sq = v2x * v2x + v2y * v2y

        if dot < 0 or dot > len_sq:
            return False  # cp lies outside the segment

        # Perpendicular distance from cp to line p0-p1
        distance = abs(dy * cp.x() - dx * cp.y() + p1.x() * p0.y() - p1.y() * p0.x()) / ((dx ** 2 + dy ** 2) ** 0.5)

        return distance < threshold

    def add_control_point(self, segment_index, pos):
        self.save_state()  # Save the state before any changes

        # Retrieve the segment and check if it has a layer
        segment = self.segments[segment_index]

        if segment.layer.locked:
            print(f"Cannot add control point: Layer '{segment.layer.name}' is locked.")
            return False  # Return early if layer is locked

        # Proceed with finding the segment at the position and adding control point
        segment_info = self.find_segment_at(pos)
        if not segment_info:
            print("No segment line clicked.")
            return False

        seg_index, line_index = segment_info
        p0 = segment.points[line_index]
        p1 = segment.points[line_index + 1]

        midpoint = (p0 + p1) * 0.5
        print(f"Adding control point at midpoint {midpoint} between {p0} and {p1}")
        print(f"Segment layer locked: ", segment.layer.locked)
        if line_index < len(segment.controls):
            segment.controls[line_index] = midpoint
        else:
            # Ensure the controls list matches the number of line segments
            while len(segment.controls) < line_index:
                segment.controls.append(None)
            segment.controls.append(midpoint)

        return True

    def insert_anchor_point(self, segment_index, pos):
        """
        Insert a new anchor point at the specified position on a segment line.
        This splits the segment at the clicked position.

        Args:
            segment_index: Index of the segment to modify
            pos: Position where the anchor should be inserted

        Returns:
            bool: True if successful, False otherwise
        """
        self.save_state()  # Save the state before any changes

        # Retrieve the segment and check if it has a layer
        segment = self.segments[segment_index]

        if segment.layer.locked:
            print(f"Cannot insert anchor point: Layer '{segment.layer.name}' is locked.")
            return False

        # Find which line segment the position is on
        segment_info = self.find_segment_at(pos)
        if not segment_info:
            print("No segment line clicked.")
            return False

        seg_index, line_index = segment_info
        if seg_index != segment_index:
            print("Position is on a different segment.")
            return False

        # Get the two anchor points that define the line segment
        p0 = segment.points[line_index]
        p1 = segment.points[line_index + 1]

        # Calculate the exact position on the line (project pos onto the line)
        dx = p1.x() - p0.x()
        dy = p1.y() - p0.y()
        segment_length_squared = dx * dx + dy * dy

        if segment_length_squared == 0:
            print("Cannot insert anchor on zero-length segment.")
            return False

        # Vector from p0 to pos
        px = pos.x() - p0.x()
        py = pos.y() - p0.y()

        # Projection scalar (where along the line the point should be)
        t = (px * dx + py * dy) / segment_length_squared
        t = max(0.0, min(1.0, t))  # Clamp to [0, 1]

        # Calculate the insertion point (projected onto the line)
        insert_x = p0.x() + t * dx
        insert_y = p0.y() + t * dy
        insert_point = QPointF(insert_x, insert_y)

        print(f"Inserting anchor point at {insert_point} between {p0} and {p1}")

        # Insert the new anchor point after line_index
        segment.points.insert(line_index + 1, insert_point)

        # Handle control points:
        # If there was a control point for this segment, we need to split it into two
        # Otherwise, add None for both new segments
        if line_index < len(segment.controls):
            old_control = segment.controls[line_index]

            if old_control is not None:
                # Calculate new control points for the two new segments
                # First segment: p0 -> insert_point
                ctrl1 = QPointF(
                    p0.x() + t * (old_control.x() - p0.x()),
                    p0.y() + t * (old_control.y() - p0.y())
                )

                # Second segment: insert_point -> p1
                ctrl2 = QPointF(
                    insert_point.x() + (1 - t) * (old_control.x() - p0.x()),
                    insert_point.y() + (1 - t) * (old_control.y() - p0.y())
                )

                # Replace the old control with the first new control
                segment.controls[line_index] = ctrl1
                # Insert the second control
                segment.controls.insert(line_index + 1, ctrl2)
            else:
                # No control point existed, add None for the new segment
                segment.controls.insert(line_index + 1, None)
        else:
            # No control point in the list for this segment, add None
            segment.controls.insert(line_index + 1, None)

        print(f"Anchor point inserted. Segment now has {len(segment.points)} points and {len(segment.controls)} controls.")
        return True

    def find_segment_at(self, pos, threshold=10):
        for seg_index, segment in enumerate(self.segments):
            points = segment.points
            for i in range(1, len(points)):
                p0 = points[i - 1]
                p1 = points[i]

                if self.is_on_segment(p0, pos, p1, threshold):
                    return seg_index, i - 1

        return None

    @staticmethod
    def is_on_segment(p0, test_pt, p1, threshold=5.0):
        if test_pt is None:
            return False

        dx = p1.x() - p0.x()
        dy = p1.y() - p0.y()
        segment_length_squared = dx * dx + dy * dy
        if segment_length_squared == 0:
            return False

        # Vector from p0 to test_pt
        px = test_pt.x() - p0.x()
        py = test_pt.y() - p0.y()

        # Projection scalar
        t = (px * dx + py * dy) / segment_length_squared

        if t < 0.0 or t > 1.0:
            return False

        # Projection point on the segment
        proj_x = p0.x() + t * dx
        proj_y = p0.y() + t * dy

        # Distance from test point to projection
        dist = ((test_pt.x() - proj_x) ** 2 + (test_pt.y() - proj_y) ** 2) ** 0.5

        return dist <= threshold

    def set_layer_locked(self, layer_name, locked):
        print(f"[DEBUG] set_layer_locked called: {layer_name} -> {locked}")
        if layer_name == "Workpiece":
            print(f"[DEBUG] Before: external_layer.locked = {self.external_layer.locked}")
            self.external_layer.locked = locked
            print(f"[DEBUG] After: external_layer.locked = {self.external_layer.locked}")
        elif layer_name == "Contour":
            print(f"[DEBUG] Before: contour_layer.locked = {self.contour_layer.locked}")
            self.contour_layer.locked = locked
            print(f"[DEBUG] After: contour_layer.locked = {self.contour_layer.locked}")
        elif layer_name == "Fill":
            print(f"[DEBUG] Before: fill_layer.locked = {self.fill_layer.locked}")
            self.fill_layer.locked = locked
            print(f"[DEBUG] After: fill_layer.locked = {self.fill_layer.locked}")

        # Fix segments with stale layer references
        self._fix_segment_layer_references()
        print("Layer lock state updated:", layer_name, locked)

    def _fix_segment_layer_references(self):
        """Fix segments that have stale layer references after undo/redo or deep copy operations"""
        print("[DEBUG] Fixing segment layer references...")
        for i, segment in enumerate(self.segments):
            if segment.layer and segment.layer.name == "Workpiece" and segment.layer is not self.external_layer:
                print(f"[DEBUG] Fixing segment {i}: Workpiece layer reference")
                segment.layer = self.external_layer
            elif segment.layer and segment.layer.name == "Contour" and segment.layer is not self.contour_layer:
                print(f"[DEBUG] Fixing segment {i}: Contour layer reference")
                segment.layer = self.contour_layer
            elif segment.layer and segment.layer.name == "Fill" and segment.layer is not self.fill_layer:
                print(f"[DEBUG] Fixing segment {i}: Fill layer reference")
                segment.layer = self.fill_layer

    def isLayerLocked(self, layer_name):
        if layer_name == "Workpiece":
            return self.external_layer.locked
        elif layer_name == "Contour":
            return self.contour_layer.locked
        elif layer_name == "Fill":
            return self.fill_layer.locked
        return

    def get_significant_points(self, points, num_points):
        """
        Reduce a list of points to the most 'significant' ones based on curvature.

        Args:
            points (list[QPointF]): Input points.
            num_points (int): Maximum number of points to keep.

        Returns:
            list[QPointF]: Reduced list of significant points.
        """
        if len(points) <= num_points:
            return points.copy()

        # Compute curvature as angle between consecutive segments
        curvatures = []
        for i in range(1, len(points) - 1):
            p0, p1, p2 = points[i - 1], points[i], points[i + 1]
            v1 = np.array([p1.x() - p0.x(), p1.y() - p0.y()])
            v2 = np.array([p2.x() - p1.x(), p2.y() - p1.y()])
            if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
                angle = 0.0
            else:
                cos_theta = np.clip(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1, 1)
                angle = np.arccos(cos_theta)
            curvatures.append((i, angle))

        # Always include first and last points
        selected_indices = {0, len(points) - 1}

        # Pick points with highest curvature until we reach num_points
        curvatures.sort(key=lambda x: x[1], reverse=True)
        for idx, _ in curvatures:
            if len(selected_indices) >= num_points:
                break
            selected_indices.add(idx)

        # Return points sorted in original order
        return [points[i] for i in sorted(selected_indices)]

    def contour_to_bezier(self, contour, num_points=None, control_point_ratio=0.5, close_contour=True, settings=None,
                          straight_threshold=0.5):
        """
        Converts a contour to a Segment with Bezier control points,
        selecting the most significant points and avoiding unnecessary controls.

        Args:
            contour (list or numpy array): OpenCV-style contour [[x, y]].
            num_points (int, optional): Max number of anchor points. If None, use all.
            control_point_ratio (float): Where to place the control point between two anchor points.
            close_contour (bool): Whether to close the contour.
            straight_threshold (float): Max perpendicular distance to consider a segment straight.

        Returns:
            list[Segment]: Segment with anchor and control points.
        """
        if len(contour) < 2:
            return []

        # Close contour if requested
        if close_contour:
            start_pt = contour[0][0]
            end_pt = contour[-1][0]
            if not np.allclose(start_pt, end_pt):
                contour = np.vstack([contour, [contour[0]]])

        points = [QPointF(pt[0][0], pt[0][1]) for pt in contour]

        # Reduce points based on significance if requested
        if num_points is not None and num_points < len(points):
            points = self.get_significant_points(points, num_points)

        # Create segment
        self.external_layer.locked = False
        segment = Segment(self.external_layer, settings)
        self.external_layer.locked = True

        # Add anchor points
        for pt in points:
            segment.add_point(pt)

        # Add control points **only if the line is not straight**
        for i in range(len(segment.points) - 1):
            p0 = segment.points[i]
            p1 = segment.points[i + 1]

            # Compute candidate control point
            control_x = (1 - control_point_ratio) * p0.x() + control_point_ratio * p1.x()
            control_y = (1 - control_point_ratio) * p0.y() + control_point_ratio * p1.y()
            control_pt = QPointF(control_x, control_y)

            # Check deviation from straight line
            # Check deviation from straight line
            dx = p1.x() - p0.x()
            dy = p1.y() - p0.y()

            denom = math.hypot(dx, dy)
            if denom == 0:
                dist = 0.0
            else:
                dist = abs(dy * control_pt.x() - dx * control_pt.y() + p1.x() * p0.y() - p1.y() * p0.x()) / denom

            if dist > straight_threshold:
                segment.add_control_point(i, control_pt)
            else:
                segment.add_control_point(i, None)  # Skip control point if line is almost straight

        return [segment]

    def clear_all_segments(self):
        self.segments.clear()
        self.active_segment_index = -1


import os
import sys

from deprecated.pl_gui.contour_editor.SpacingDialog import SpacingDialog

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import cv2
from PyQt6.QtCore import QTimer
from matplotlib import pyplot as plt

from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QSize, QRectF
from PyQt6.QtGui import QPainter, QImage, QPen, QBrush, QPainterPath
from PyQt6.QtWidgets import QFrame, QDialog
from PyQt6.QtGui import QColor

from API.shared.contour_editor.BezierSegmentManager import BezierSegmentManager

from PyQt6.QtCore import QPointF
import numpy as np
LAYER_COLORS = {
    "External": QColor("#FF0000"),  # Red
    "Contour": QColor("#00FFFF"),  # Cyan
    "Fill": QColor("#00FF00"),  # Green
}

DRAG_MODE = "drag"
EDIT_MODE = "edit"


class ContourEditor(QFrame):
    pointsUpdated = pyqtSignal()

    def __init__(self, visionSystem, image_path=None, contours=None):
        super().__init__()
        self.setWindowTitle("Editable Bezier Curves")
        self.setGeometry(100, 100, 640, 360)
        self.visionSystem = visionSystem
        self.manager = BezierSegmentManager()
        self.dragging_point = None

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setAutoFillBackground(False)
        self.image = self.load_image(image_path)
        self.selected_point_info = None

        self.scale_factor = 1.0
        self.translation = QPointF(0, 0)
        self.grabGesture(Qt.GestureType.PinchGesture)
        self.is_zooming = False

        self.drag_mode_active = False
        self.last_drag_pos = None
        self.contours = None

        self.drag_threshold = 10  # Set a threshold for movement

        self.dragging_point = None
        self.last_drag_pos = None
        self.drag_threshold = 10
        self.drag_timer = QTimer(self)
        self.drag_timer.setInterval(16)  # Limit updates to ~60 FPS
        self.drag_timer.timeout.connect(self.perform_drag_update)
        self.pending_drag_update = False

        self.initContour(contours)

    def zoom_in(self):
        self._apply_centered_zoom(1.25)

    def zoom_out(self):
        self._apply_centered_zoom(0.8)

    def _apply_centered_zoom(self, factor):
        # Center of the widget in screen space
        center_screen = QPointF(self.width() / 2, self.height() / 2)

        # Convert screen center to image space
        center_img_space = (center_screen - self.translation) / self.scale_factor

        # Apply the zoom factor
        self.scale_factor *= factor

        # Calculate new screen position of image center after scaling
        new_center_screen_pos = center_img_space * self.scale_factor + self.translation

        # Adjust translation so that the zoom is centered on the widget center
        self.translation += center_screen - new_center_screen_pos

        self.update()

    def reset_zoom(self):
        self.scale_factor = 1.0

        # Center image in widget
        frame_width = self.width()
        frame_height = self.height()
        img_width = self.image.width()
        img_height = self.image.height()

        x = (frame_width - img_width) / 2
        y = (frame_height - img_height) / 2
        self.translation = QPointF(x, y)

        self.update()

    def set_cursor_mode(self, mode):
        self.current_mode = mode
        self.drag_mode_active = (mode == DRAG_MODE)

        if mode == DRAG_MODE:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif mode == EDIT_MODE:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def initContour(self, contours_by_layer):
        """
        Initialize contours from a dictionary: { layer_name: [contour1, contour2, ...] }
        """
        print("in contoureditor.py")
        from API.shared.contour_editor.BezierSegmentManager import Layer
        if not contours_by_layer:
            return

        self.contours = contours_by_layer  # store the dict instead of a flat list

        for layer_name, contours in contours_by_layer.items():
            if contours is None or len(contours) == 0:
                continue

            for cnt in contours:

                bezier_segments = self.manager.contour_to_bezier(cnt)
                for segment in bezier_segments:
                    # Optional: attach layer info to the segment
                    segment.layer = Layer(layer_name,locked=True,visible=True)

                    self.manager.segments.append(segment)

        self.pointsUpdated.emit()

    def toggle_zooming(self):
        self.is_zooming = not self.is_zooming
        if self.is_zooming:
            self.grabGesture(Qt.GestureType.PinchGesture)
            print("Zooming and pinch gesture enabled.")
        else:
            self.ungrabGesture(Qt.GestureType.PinchGesture)
            print("Zooming and pinch gesture disabled.")

    def reset_zoom_flag(self):
        self.is_zooming = False

    def load_image(self, path):
        if path:
            image = QImage(path)
            if image.isNull():
                # print(f"Failed to load image from: {path}")
                image = QImage(1280, 720, QImage.Format.Format_RGB32)
        else:
            image = QImage(1280, 720, QImage.Format.Format_RGB32)
        image.fill(Qt.GlobalColor.white)
        return image

    def handle_gesture_event(self, event):
        # gesture = event.gesture(Qt.GestureType.PinchGesture)
        gesture = event.gesture(Qt.GestureType.PinchGesture)
        if gesture:
            if gesture.robotState() == Qt.GestureState.GestureStarted:
                self._initial_scale = self.scale_factor  # Optional: save original scale
            elif gesture.robotState() == Qt.GestureState.GestureUpdated:
                pinch = gesture
                scale_factor = pinch.scaleFactor()
                center = pinch.centerPoint()  # Midpoint of the fingers

                # Save the point under the fingers in image coordinates (before zoom)
                old_scale = self.scale_factor
                image_point_under_fingers = (center - self.translation) / old_scale

                # Apply new scale factor
                self.scale_factor *= scale_factor
                self.scale_factor = max(0.1, min(self.scale_factor, 20.0))  # Optional clamp

                # Update translation to keep image point under fingers
                self.translation = center - image_point_under_fingers * self.scale_factor

                self.update()
            elif gesture.robotState() == Qt.GestureState.GestureFinished:
                # Optional: snap or log final zoom level
                pass

    def update_image(self, image_input):
        if isinstance(image_input, str):
            image = QImage(image_input)
            if image.isNull():
                # print(f"Failed to load image from path: {image_input}")
                return
            self.image = image
        elif isinstance(image_input, QImage):
            self.image = image_input
        else:
            print("Unsupported image input type.")
            return
        self.update()

    def event(self, event):
        if event.type() == QEvent.Type.Gesture:
            self.handle_gesture_event(event)
            return True
        return super().event(event)

    def delete_segment(self, seg_index):
        self.manager.delete_segment(seg_index)

    def wheelEvent(self, event):
        self._handle_zoom(event)

    def _handle_zoom(self, event):
        angle = event.angleDelta().y()
        factor = 1.25 if angle > 0 else 0.8

        cursor_pos = event.position()
        cursor_img_pos = (cursor_pos - self.translation) / self.scale_factor

        self.scale_factor *= factor

        # Update translation to zoom towards cursor
        new_cursor_screen_pos = cursor_img_pos * self.scale_factor + self.translation
        self.translation += cursor_pos - new_cursor_screen_pos

        self.update()

    def mousePressEvent(self, event):
        if self.is_zooming:
            self.last_drag_pos = event.position()
            return

        if self.drag_mode_active and event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.last_drag_pos = event.position()
            return

        if not self.is_within_image(event.position()):
            return

        pos = self.map_to_image_space(event.position())

        # Right-click handling
        if event.button() == Qt.MouseButton.RightButton:
            if self.manager.remove_control_point_at(pos):
                self._handle_right_mouse_click()
                return

        elif event.button() == Qt.MouseButton.LeftButton:
            # ✅ First, check if the click is on an existing anchor or control point
            drag_target = self.manager.find_drag_target(pos)
            if drag_target:
                self._handle_left_mouse_dragging(drag_target, pos)
                return

            # ✅ Only if not dragging an existing point, check for segment to add control point

            result = self._handle_add_control_point(pos)
            if result:
                return  # Control point added successfully

            # ✅ If not dragging or adding control point, check if it's a new anchor point
            # Fallback: add new anchor point
            self.manager.add_point(pos)
            self.selected_point_info = None
            self.update()
            self.pointsUpdated.emit()

    def _handle_add_control_point(self, pos):
        # Get the segment info at the position
        segment_info = self.manager.find_segment_at(pos)
        if segment_info:
            seg_index, line_index = segment_info
            segment = self.manager.get_segments()[seg_index]

            # Check if the line already has a control point, if not, add one
            if line_index >= len(segment.controls) or segment.controls[line_index] is None:
                result = self.manager.add_control_point(seg_index, pos)

                # If the result is False, that means adding the control point was prevented (e.g., due to layer being locked)
                if not result:
                    return False

                # Update and emit signals if control point is successfully added
                self.update()
                self.pointsUpdated.emit()
                return True

        return False

    def _handle_right_mouse_click(self):
        self.selected_point_info = None
        self.update()
        self.pointsUpdated.emit()

    def _handle_left_mouse_dragging(self, drag_target, pos):
        self.dragging_point = drag_target
        self.selected_point_info = drag_target
        self.initial_drag_pos = pos
        self.manager.save_state()
        self.update()

    def set_layer_visibility(self, layer_name, visible):

        if layer_name == "External":
            layer = self.manager.external_layer
        elif layer_name == "Contour":
            layer = self.manager.contour_layer
        elif layer_name == "Fill":
            layer = self.manager.fill_layer
        else:
            print("Invalid layer: ", layer_name)
            return

        layer.visible = visible

        for idx, segment in enumerate(self.manager.get_segments()):
            if segment.layer.name == layer.name:
                self.manager.set_segment_visibility(idx, visible)

        self.update()  # Redraw after visibility change

    def mouseDoubleClickEvent(self, event):
        pos = event.position()
        target = self.manager.find_drag_target(pos)

        if target and target[0] == 'control':
            role, seg_index, ctrl_idx = target
            self.manager.reset_control_point(seg_index, ctrl_idx)
            self.update()
            self.pointsUpdated.emit()

    #

    def mouseMoveEvent(self, event):
        if self.drag_mode_active and self.last_drag_pos is not None:
            delta = event.position() - self.last_drag_pos
            self.translation += delta
            self.last_drag_pos = event.position()
            self.pending_drag_update = True
            if not self.drag_timer.isActive():
                self.drag_timer.start()
            return

        if self.dragging_point:
            current_pos = self.map_to_image_space(event.position())
            if not self.is_within_image(event.position()):
                return

            delta = current_pos - self.initial_drag_pos
            if abs(delta.x()) > self.drag_threshold or abs(delta.y()) > self.drag_threshold:
                role, seg_index, idx = self.dragging_point
                self.manager.move_point(role, seg_index, idx, self.initial_drag_pos + delta, suppress_save=True)
                self.pending_drag_update = True
                if not self.drag_timer.isActive():
                    self.drag_timer.start()

    def perform_drag_update(self):
        if self.pending_drag_update:
            self.update()
            self.pending_drag_update = False
        else:
            self.drag_timer.stop()

    def mouseReleaseEvent(self, event):
        self.dragging_point = None
        if self.drag_mode_active:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.last_drag_pos = None

        self.update()

    def addNewSegment(self, layer_name="Contour"):
        print("New segment started.")
        newSegment = self.manager.start_new_segment(layer_name)

        print("Current segments:", self.manager.get_segments())  # Debug print
        self.update()
        self.pointsUpdated.emit()

    def set_image(self, image):
        if image is None:
            return
        height, width, channels = image.shape
        bytes_per_line = channels * width
        fmt = QImage.Format.Format_RGB888 if channels == 3 else QImage.Format.Format_RGBA888
        qimage = QImage(image.data, width, height, bytes_per_line, fmt)
        self.update_image(qimage)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_N:
            self.addNewSegment()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.save_robot_path_to_txt("robot_path.txt", samples_per_segment=5)
            self.plot_robot_path()
            # from temp import testTransformPoints
        elif key == Qt.Key.Key_Space:
            print("Capturing image from vision system...")
            image = self.visionSystem.captureImage()
            contours = self.visionSystem.contours

            if image is None:
                image = cv2.imread("imageDebug2.png")
                # image = cv2.imread("imageDebug.png")
                print("Image capture failed.")
                # return

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            thresh = ~thresh
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # approx
            contours = [cv2.approxPolyDP(cnt, 3, True) for cnt in contours]

            if contours is not None:
                self.initContour(contours)

            self.set_image(image)

            # height, width, channels = image.shape
            # bytes_per_line = channels * width
            # fmt = QImage.Format.Format_RGB888 if channels == 3 else QImage.Format.Format_RGBA888
            # qimage = QImage(image.data, width, height, bytes_per_line, fmt)
            # self.update_image(qimage)

    def map_to_image_space(self, pos):
        return (pos - self.translation) / self.scale_factor

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        # Apply transformation
        painter.translate(self.translation)
        painter.scale(self.scale_factor, self.scale_factor)

        painter.drawImage(0, 0, self.image)

        for segment in self.manager.get_segments():
            if segment.visible:
                # if segment.get("visible", True):  # Default to True if missing
                self.draw_bezier_segment(painter, segment)

        painter.end()

    def get_active_segment_rect(self):
        segment = self.manager.get_active_segment()
        if not segment or not segment.visible:
            return None

        points = segment.points + [pt for pt in segment.controls if pt is not None]
        if not points:
            return None

        min_x = min(p.x() for p in points)
        max_x = max(p.x() for p in points)
        min_y = min(p.y() for p in points)
        max_y = max(p.y() for p in points)

        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)

    def draw_bezier_segment(self, painter, segment):
        points = segment.points
        controls = segment.controls

        # Check if this is the active segment
        is_active = (self.manager.segments.index(segment) == self.manager.active_segment_index)

        if len(points) >= 2:
            # Start path at the first point
            path = QPainterPath()
            path.moveTo(points[0])

            # Loop over the points and controls to create the path
            for i in range(1, len(points)):
                if i - 1 < len(controls) and controls[i - 1] is not None:  # If we have a control point for this segment
                    path.quadTo(controls[i - 1], points[i])  # Draw a quadratic Bézier curve
                else:
                    # If no control points, draw a straight line (this is the fallback)
                    path.lineTo(points[i])

            # Set the color for the path based on the layer (inactive segments will have reduced opacity)
            layer = segment.layer
            color = LAYER_COLORS.get(layer.name, QColor("black"))  # Default layer color

            # Set thickness and opacity based on whether the segment is active or not
            if is_active:
                pen = QPen(color, 2)  # Active segment will have a thicker line
            else:
                # Inactive segments: thinner line and with reduced opacity
                pen = QPen(color, 1)
                pen.setColor(color.lighter(150))  # Slightly lighter color for inactive segments (reduce opacity)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)  # Smooth ends
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)  # Smooth joins

            # Apply the pen settings
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

        # Draw anchor points (points on the curve)
        painter.setPen(QPen(Qt.PenStyle.NoPen))  # No outline for the points
        for i, pt in enumerate(points):
            is_selected = (
                    self.selected_point_info == ('anchor', self.manager.segments.index(segment), i)
            )

            # Set color and size for selected points
            color = Qt.GlobalColor.green if is_selected else Qt.GlobalColor.blue
            # size = 8 if is_selected else 5
            size = 5 if is_selected else 5
            painter.setBrush(QBrush(color))
            painter.drawEllipse(pt, size, size)

        # Draw control points (if available)
        for i, pt in enumerate(controls):
            if pt is None:
                continue  # Skip invalid control points
            is_selected = (
                    self.selected_point_info == ('control', self.manager.segments.index(segment), i)
            )
            # Set color and size for selected control points
            color = Qt.GlobalColor.green if is_selected else Qt.GlobalColor.red
            size = 8 if is_selected else 5
            painter.setBrush(QBrush(color))
            painter.drawEllipse(pt, size, size)

        # Optionally, draw lines connecting anchor points to control points (debugging or visualization)
        painter.setPen(QPen(Qt.GlobalColor.gray, 1, Qt.PenStyle.DashLine))
        for i in range(1, len(points)):
            if i - 1 < len(controls):
                ctrl = controls[i - 1]
                if ctrl is not None:
                    painter.drawLine(points[i - 1], ctrl)
                    painter.drawLine(ctrl, points[i])

    def save_robot_path_dict_to_txt(self, filename="robot_path_dict.txt", samples_per_segment=5):
        robot_path_dict = self.manager.to_wp_data(samples_per_segment)
        try:
            with open(filename, 'w') as f:
                for segment_name, path in robot_path_dict.items():
                    f.write(f"Segment: {segment_name}\n")
                    for pt in path:
                        f.write(f"{pt.x():.3f}, {pt.y():.3f}\n")
                    f.write("\n")  # Add a blank line between segments
            print(f"Saved path to {filename}")
        except Exception as e:
            print(f"Error saving path: {e}")

        return robot_path_dict

    def save_robot_path_to_txt(self, filename="robot_path.txt", samples_per_segment=5):
        path = self.manager.get_robot_path(samples_per_segment)
        try:
            with open(filename, 'w') as f:
                for pt in path:
                    f.write(f"{pt.x():.3f}, {pt.y():.3f}\n")
            print(f"Saved path to {filename}")
        except Exception as e:
            print(f"Error saving path: {e}")

    def plot_robot_path(self, filename="robot_path.txt"):
        try:
            with open(filename, 'r') as f:
                coords = [tuple(map(float, line.strip().split(','))) for line in f if ',' in line]

            # Remove duplicate points
            unique_coords = list(set(coords))
            unique_coords.sort(key=coords.index)  # Preserve the original order

            x_vals, y_vals = zip(*unique_coords)
            total_points = len(unique_coords)  # Count the total number of unique points

            plt.figure(figsize=(12.8, 7.2))
            plt.plot(x_vals, y_vals, 'b-', label="Robot Path")  # Plot the path
            plt.scatter(x_vals, y_vals, color='red', label=f"Points ({total_points})")  # Plot the points
            plt.gca().invert_yaxis()
            plt.xlim(0, self.width())
            plt.ylim(self.height(), 0)
            plt.title(f"Robot Path Visualization (Total Points: {total_points})")  # Include total points in the title
            plt.xlabel("X")
            plt.ylabel("Y")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print(f"Failed to plot path: {e}")

    def is_within_image(self, pos: QPointF) -> bool:
        image_width = self.image.width()
        image_height = self.image.height()
        img_pos = self.map_to_image_space(pos)
        return 0 <= img_pos.x() < image_width and 0 <= img_pos.y() < image_height

    def set_layer_locked(self, layer_name, locked):
        self.manager.set_layer_locked(layer_name, locked)
        print("Layer lock state updated:", layer_name, locked)


import sys
import threading
from PyQt6.QtWidgets import (
    QFrame, QWidget, QHBoxLayout, QVBoxLayout, QApplication
)
from PyQt6.QtCore import QFile, QTextStream

from GlueDispensingApplication.vision.VisionService import VisionServiceSingleton
from deprecated.pl_gui.contour_editor.PointManagerWidget import PointManagerWidget
# from NewContourEditor.PointManager import PointManagerWidget
from deprecated.pl_gui.CreateWorkpieceForm import CreateWorkpieceForm
from .TopbarWidget import TopBarWidget


class MainApplicationFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.visionSystem = VisionServiceSingleton.get_instance()

        # State management
        self.current_view = "point_manager"  # "point_manager" or "create_workpiece"

        # Start the vision system thread
        threading.Thread(target=self.runCameraFeed, daemon=True).start()

        self.initUI()

    def runCameraFeed(self):
        while True:
            self.visionSystem.run()

    def initUI(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # Bezier editor on the left
        self.contourEditor = ContourEditor(self.visionSystem, image_path="imageDebug.png")

        # Top bar widget
        self.topbar = TopBarWidget(self.contourEditor, None,zigzag_callback=self.generateLineGridPattern,offset_callback=self.shrink)
        mainLayout.addWidget(self.topbar)

        # Horizontal layout for the main content
        horizontal_widget = QWidget()
        horizontalLayout = QHBoxLayout(horizontal_widget)
        horizontalLayout.setContentsMargins(0, 0, 0, 0)

        horizontalLayout.addWidget(self.contourEditor, stretch=4)

        # Create the right panel widgets
        self.pointManagerWidget = PointManagerWidget(self.contourEditor)
        self.topbar.point_manager = self.pointManagerWidget
        self.pointManagerWidget.setFixedWidth(600)

        self.createWorkpieceForm = CreateWorkpieceForm(parent=self)
        # self.createWorkpieceForm.apply_stylesheet()
        self.createWorkpieceForm.setFixedWidth(350)
        self.createWorkpieceForm.hide()  # Initially hidden

        # Add point manager to layout (initially visible)
        horizontalLayout.addWidget(self.pointManagerWidget, stretch=1)
        horizontalLayout.addWidget(self.createWorkpieceForm, stretch=1)

        # Set up save button callback to switch views
        self.topbar.set_save_button_callback(self.on_first_save_clicked)
        self.topbar.onStartCallback = self.onStart
        # Add the horizontal widget to the main layout
        mainLayout.addWidget(horizontal_widget)

    def set_create_workpiece_for_on_submit_callback(self, callback):
        """
        Set the callback for when the create workpiece button is clicked.
        This allows the main application to handle the creation of a workpiece.
        """
        self.createWorkpieceForm.onSubmitCallBack = callback
        print("Set create workpiece callback in main application frame.")

    def shrink(self):
        from deprecated.pl_gui.contour_editor.utils import shrink_contour_points
        dialog = SpacingDialog(self)
        dialog.setWindowTitle("Shrink Amount")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            print("Shrink cancelled by user.")
            return

        shrink_amount = dialog.get_spacing()
        if shrink_amount <= 0:
            print("Shrink amount must be positive.")
            return

        external_segments = [s for s in self.contourEditor.manager.get_segments() if
                             getattr(s.layer, "name", "") == "External"]
        if not external_segments:
            print("No external contour found.")
            return

        contour = external_segments[0]
        contour_points = np.array([(pt.x(), pt.y()) for pt in contour.points])
        if contour_points.size == 0:
            print("External contour has no points.")
            return
        if contour_points.shape[0] < 3:
            print("Contour has fewer than 3 points — can't shrink properly.")
            return

        new_contour_points = shrink_contour_points(contour_points, shrink_amount)
        if new_contour_points is None or len(new_contour_points) < 2:
            print("Shrink amount too large — polygon disappeared or invalid result!")
            return

        for i in range(len(new_contour_points) - 1):
            p1 = new_contour_points[i]
            p2 = new_contour_points[i + 1]
            qpoints = [QPointF(p1[0], p1[1]), QPointF(p2[0], p2[1])]
            segment = self.contourEditor.manager.create_segment(qpoints, layer_name="Contour")
            self.contourEditor.manager.segments.append(segment)

        self.contourEditor.update()
        self.pointManagerWidget.refresh_points()
        print(f"Added shrunk contour inward by {shrink_amount} units as new segments.")

    def generateLineGridPattern(self):
        """
        Generate zig-zag lines aligned to the external contour using minimum area bounding box orientation.
        """
        from PyQt6.QtWidgets import QInputDialog
        from PyQt6.QtCore import QPointF
        import numpy as np
        from deprecated.pl_gui.contour_editor.utils import zigZag

        # def zigZag(contour, spacing):
        #     # Convert contour to a Shapely polygon
        #     contour_poly = Polygon(contour.squeeze())
        #     if not contour_poly.is_valid:
        #         contour_poly = contour_poly.buffer(0)  # Fix self-intersections if any
        #
        #     # Get rotated bounding box
        #     bbox = cv2.minAreaRect(contour)
        #     box = cv2.boxPoints(bbox)
        #     center = np.mean(box, axis=0)
        #     width, height = bbox[1]
        #     angle = bbox[2]
        #
        #     if width < height:
        #         shorter_dim = width
        #         longer_dim = height
        #         vertical = True
        #     else:
        #         shorter_dim = height
        #         longer_dim = width
        #         vertical = False
        #
        #     # Generate zigzag lines in the bbox's local frame (unrotated)
        #     lines = []
        #     for i in range(0, int(shorter_dim), spacing):
        #         if vertical:
        #             x = -shorter_dim / 2 + i
        #             pt1 = [x, -longer_dim / 2]
        #             pt2 = [x, longer_dim / 2]
        #         else:
        #             y = -shorter_dim / 2 + i
        #             pt1 = [-longer_dim / 2, y]
        #             pt2 = [longer_dim / 2, y]
        #         lines.append((pt1, pt2))
        #
        #     # Rotate and translate lines to match the actual bbox orientation
        #     theta = np.radians(angle)
        #     rot_matrix = np.array([
        #         [np.cos(theta), -np.sin(theta)],
        #         [np.sin(theta), np.cos(theta)]
        #     ])
        #
        #     final_coords = []
        #     for pt1, pt2 in lines:
        #         # Rotate
        #         pt1_rot = rot_matrix @ np.array(pt1) + center
        #         pt2_rot = rot_matrix @ np.array(pt2) + center
        #
        #         # Clip line with actual contour
        #         line = LineString([pt1_rot, pt2_rot])
        #         clipped = line.intersection(contour_poly)
        #
        #         # Add resulting points or line segments
        #         if clipped.is_empty:
        #             continue
        #         elif clipped.geom_type == "LineString":
        #             final_coords.extend(list(clipped.coords))
        #         elif clipped.geom_type == "MultiLineString":
        #             for part in clipped:
        #                 final_coords.extend(list(part.coords))
        #
        #     return np.array(final_coords)

        # Ask user for spacing
        spacing, ok = QInputDialog.getInt(self, "ZigZag Spacing", "Enter spacing in pixels:", value=20, min=1, max=1000)
        if not ok:
            print("Zig-zag pattern generation cancelled by user.")
            return

        # Get external contour
        external_segments = [s for s in self.contourEditor.manager.get_segments() if
                             getattr(s.layer, "name", "") == "External"]
        if not external_segments:
            print("No external contour found.")
            return

        contour = external_segments[0]
        contour_points = np.array([(pt.x(), pt.y()) for pt in contour.points])
        if contour_points.size == 0:
            print("External contour has no points.")
            return

        # Ensure contour is not empty and convert to float32 for OpenCV
        if contour_points.shape[0] < 3:
            print("Contour has fewer than 3 points — can't compute minAreaRect.")
            return

        contour_points = contour_points.astype(np.float32)

        # Generate zig-zag points
        zigzag_points = zigZag(contour_points, spacing)

        # Create line segments
        # Create line segments with alternating directions (left-right, right-left)
        for i in range(0, len(zigzag_points) - 1, 2):
            p1 = zigzag_points[i]
            p2 = zigzag_points[i + 1]
            if (i // 2) % 2 == 0:
                qpoints = [QPointF(p1[0], p1[1]), QPointF(p2[0], p2[1])]
            else:
                qpoints = [QPointF(p2[0], p2[1]), QPointF(p1[0], p1[1])]
            segment = self.contourEditor.manager.create_segment(qpoints, layer_name="Contour")
            self.contourEditor.manager.segments.append(segment)

        self.contourEditor.update()
        self.pointManagerWidget.refresh_points()
        print("Generated zig-zag grid aligned to external contour.")

    def on_first_save_clicked(self):
        """Handle the first save button click - switch from point manager to create workpiece form"""
        if self.current_view == "point_manager":
            # Hide point manager and show create workpiece form
            self.pointManagerWidget.hide()
            # self.createWorkpieceForm.show()
            # self.createWorkpieceForm.raise_()
            self.createWorkpieceForm.toggle()
            # Update the save button callback to handle workpiece saving
            self.topbar.set_save_button_callback(self.on_workpiece_save_clicked)
            self.current_view = "create_workpiece"

            print("Switched to Create Workpiece form")

    def onStart(self):
        from GlueDispensingApplication.workpiece.Workpiece import Workpiece,WorkpieceField


        mock_data = {
            WorkpieceField.WORKPIECE_ID.value: "WP123",
            WorkpieceField.NAME.value: "Test Workpiece",
            WorkpieceField.DESCRIPTION.value: "Sample description",
            WorkpieceField.OFFSET.value: "10,20,30",
            WorkpieceField.HEIGHT.value: "50",
            WorkpieceField.GLUE_QTY.value: "100",
            WorkpieceField.SPRAY_WIDTH.value: "5",
            WorkpieceField.TOOL_ID.value: "0",
            WorkpieceField.GRIPPER_ID.value: "0",
            WorkpieceField.GLUE_TYPE.value: "Type A",
            WorkpieceField.PROGRAM.value: "Trace",
            WorkpieceField.MATERIAL.value: "Material1",
            WorkpieceField.CONTOUR_AREA.value: "1000",
        }

        wp_contours_data = self.contourEditor.manager.to_wp_data(samples_per_segment=5)
        print("Workpiece contours data:", wp_contours_data)
        sprayPatternsDict = {
            "Contour": [],
            "Fill": []
        }

        sprayPatternsDict['Contour'] = wp_contours_data.get('Contour')
        sprayPatternsDict['Fill'] = wp_contours_data.get('Fill')


        mock_data[WorkpieceField.SPRAY_PATTERN.value] = sprayPatternsDict
        mock_data[WorkpieceField.CONTOUR.value] = wp_contours_data.get('External')
        wp = Workpiece.fromDict(mock_data)
        print("Workpiece created:", wp)
        print("Start button pressed: CONTOUR EDITOR " )
        self.parent.controller.handleExecuteFromGallery(wp)

    def on_workpiece_save_clicked(self):
        """Handle the second save button click - save the workpiece"""
        # Call the workpiece form's submit method
        self.createWorkpieceForm.onSubmit()
        print("Workpiece saved!")

        # Optionally, you could reset back to point manager or keep the form
        # For now, we'll keep the create workpiece form visible

    def set_image(self, image):
        self.contourEditor.set_image(image)

    def init_contours(self, contours):
        print("in contour editor.py")
        self.contourEditor.initContour(contours)

    def resizeEvent(self, event):
        """Resize content and side menu dynamically."""
        super().resizeEvent(event)
        new_width = self.width()

        # Adjust icon sizes of the sidebar buttons
        icon_size = int(new_width * 0.05)  # 5% of the new window width
        for button in self.topbar.buttons:
            button.setIconSize(QSize(icon_size, icon_size))

        if hasattr(self.createWorkpieceForm, 'buttons'):
            for button in self.createWorkpieceForm.buttons:
                button.setIconSize(QSize(icon_size, icon_size))

        # Resize the icons in the labels
        if hasattr(self.createWorkpieceForm, 'icon_widgets'):
            for label, original_pixmap in self.createWorkpieceForm.icon_widgets:
                scaled_pixmap = original_pixmap.scaled(
                    int(icon_size / 2), int(icon_size / 2),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                label.setPixmap(scaled_pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load and apply stylesheet
    stylesheetPath = "D:/GitHub/Cobot-Glue-Nozzle/pl_gui/styles.qss"
    file = QFile(stylesheetPath)
    if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
        stream = QTextStream(file)
        stylesheet = stream.readAll()
        file.close()
        app.setStyleSheet(stylesheet)

    main_window = QWidget()
    layout = QVBoxLayout(main_window)
    app_frame = MainApplicationFrame()
    layout.addWidget(app_frame)
    main_window.setGeometry(100, 100, 1600, 800)
    main_window.setWindowTitle("Glue Dispensing Application")
    main_window.show()
    sys.exit(app.exec())
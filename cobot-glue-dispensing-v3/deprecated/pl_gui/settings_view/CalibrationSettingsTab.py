import cv2
import numpy as np
from PyQt6 import QtCore
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (QSizePolicy, QScrollArea, QPushButton,
                             QTextEdit, QProgressBar)
from API.MessageBroker import MessageBroker
from deprecated.pl_gui.settings_view.BaseSettingsTabLayout import BaseSettingsTabLayout
from PyQt6.QtWidgets import QScroller
from deprecated.pl_gui.robotManualControl.RobotJogWidget import RobotJogWidget
from deprecated.pl_gui.virtualKeyboard.VirtualKeyboard import FocusDoubleSpinBox
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel


class ClickableLabel(QLabel):
    clicked = pyqtSignal(int, int)  # Emits x, y coordinates of click
    corner_dragged = pyqtSignal(int, int, int)  # Emits corner_index, x, y coordinates

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dragging = False
        self.drag_corner_index = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.corner_positions = {}  # Will store corner positions in label coordinates
        self.corner_radius = 15  # Clickable radius around corners
        self.parent_widget = None

    def set_parent_widget(self, parent_widget):
        self.parent_widget = parent_widget

    def update_corner_positions(self, corners_image_coords, image_to_label_scale):
        """Update corner positions in label coordinates for hit testing"""
        self.corner_positions = {}
        if len(corners_image_coords) == 4:
            for i, (img_x, img_y) in enumerate(corners_image_coords):
                # Convert image coordinates to label coordinates
                label_x = img_x / image_to_label_scale
                label_y = img_y / image_to_label_scale
                self.corner_positions[i + 1] = (label_x, label_y)

    def get_corner_at_position(self, x, y):
        """Check if click position is near any corner"""
        for corner_index, (corner_x, corner_y) in self.corner_positions.items():
            distance = ((x - corner_x) ** 2 + (y - corner_y) ** 2) ** 0.5
            if distance <= self.corner_radius:
                return corner_index
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            y = event.position().y()

            # Check if we're clicking near a corner
            corner_at_pos = self.get_corner_at_position(x, y)

            if corner_at_pos is not None:
                # Start dragging this corner
                self.dragging = True
                self.drag_corner_index = corner_at_pos
                corner_x, corner_y = self.corner_positions[corner_at_pos]
                self.drag_offset_x = x - corner_x
                self.drag_offset_y = y - corner_y

                # Set this corner as selected
                if self.parent_widget:
                    self.parent_widget.set_selected_corner(corner_at_pos)

                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            else:
                # Regular click - emit clicked signal
                self.clicked.emit(int(x), int(y))

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging and self.drag_corner_index is not None:
            x = event.position().x()
            y = event.position().y()

            # Calculate new corner position (compensate for drag offset)
            new_x = x - self.drag_offset_x
            new_y = y - self.drag_offset_y

            # Emit drag signal
            self.corner_dragged.emit(self.drag_corner_index, int(new_x), int(new_y))
        else:
            # Check if we're hovering over a corner
            x = event.position().x()
            y = event.position().y()
            corner_at_pos = self.get_corner_at_position(x, y)

            if corner_at_pos is not None:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            self.drag_corner_index = None
            self.setCursor(Qt.CursorShape.ArrowCursor)

        super().mouseReleaseEvent(event)


from PyQt6.QtWidgets import QHBoxLayout

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout, QGroupBox
from PyQt6.QtCore import Qt


class ClickableRow(QWidget):
    def __init__(self, index, label_text, x_spin, y_spin, callback):
        super().__init__()
        self.index = index
        self.callback = callback

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # small margins
        layout.setHorizontalSpacing(2)
        layout.setVerticalSpacing(0)

        self.label = QLabel(label_text)
        self.label.setFixedWidth(100)  # optional, keeps labels aligned

        layout.addWidget(self.label, 0, 0)
        layout.addWidget(x_spin, 0, 1)
        layout.addWidget(y_spin, 0, 2)

        self.setLayout(layout)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback(self.index)


class CalibrationServiceTabLayout(BaseSettingsTabLayout, QVBoxLayout):
    # Robot movement signals
    jogRequested = QtCore.pyqtSignal(str, str, str, float)
    update_camera_feed_signal = QtCore.pyqtSignal()
    move_to_pickup_requested = QtCore.pyqtSignal()
    move_to_calibration_requested = QtCore.pyqtSignal()
    save_point_requested = QtCore.pyqtSignal()

    # Image capture signals
    capture_image_requested = QtCore.pyqtSignal()
    save_images_requested = QtCore.pyqtSignal()

    # Calibration process signals
    calibrate_camera_requested = QtCore.pyqtSignal()
    detect_markers_requested = QtCore.pyqtSignal()
    compute_homography_requested = QtCore.pyqtSignal()
    auto_calibrate_requested = QtCore.pyqtSignal()
    test_calibration_requested = QtCore.pyqtSignal()
    save_work_area_requested = QtCore.pyqtSignal(list)

    # Debug and testing signals
    show_debug_view_requested = QtCore.pyqtSignal(bool)

    def __init__(self, parent_widget=None, calibration_service=None):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)
        print(f"Initializing {self.__class__.__name__} with parent widget: {parent_widget}")

        self.parent_widget = parent_widget
        self.calibration_service = calibration_service
        self.debug_mode_active = False
        self.calibration_in_progress = False

        # Store the original image for overlay drawing
        self.original_image = None
        self.image_scale_factor = 1.0
        self.image_to_label_scale = 1.0  # Scale factor from image coords to label coords

        # Create main content with new layout
        self.create_main_content()

        self.updateFrequency = 30  # in milliseconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.update_camera_feed_signal.emit())
        self.timer.start(self.updateFrequency)

        # Connect to parent widget resize events if possible
        if self.parent_widget:
            self.parent_widget.resizeEvent = self.on_parent_resize

        self.selected_corner_index = None

        broker = MessageBroker()
        broker.subscribe("vision-system/calibration-feedback", self.addLog)
        broker.subscribe("vision-system/calibration_image_captured", self.addLog)

    def addLog(self, message):
        print("Message received in addLog:", message)
        """Add a log message to the output area"""
        if hasattr(self, 'log_output'):
            self.log_output.append(message)
            self.log_output.ensureCursorVisible()

    def update_camera_preview_from_cv2(self, cv2_image):
        if hasattr(self, 'calibration_preview_label'):
            # Store the original image
            self.original_image = cv2_image.copy()

            # Draw work area overlay on the image
            overlay_image = self.draw_work_area_overlay(cv2_image)

            rgb_image = overlay_image[:, :, ::-1] if len(overlay_image.shape) == 3 else overlay_image
            height, width = rgb_image.shape[:2]
            bytes_per_line = 3 * width if len(rgb_image.shape) == 3 else width

            img_bytes = rgb_image.tobytes()

            if len(rgb_image.shape) == 3:
                q_image = QImage(img_bytes, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            else:
                q_image = QImage(img_bytes, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)

            pixmap = QPixmap.fromImage(q_image)
            self.update_calibration_preview(pixmap)

            # Update corner positions for drag detection
            self.update_corner_positions_for_dragging()

    def draw_work_area_overlay(self, cv2_image):
        """Draw work area corners and lines on the camera image"""
        if cv2_image is None:
            return cv2_image

        overlay_image = cv2_image.copy()

        # Get corner coordinates
        corners = []
        for i in range(1, 5):
            x_spin = self.corner_fields.get(f"corner{i}_x")
            y_spin = self.corner_fields.get(f"corner{i}_y")
            if x_spin and y_spin:
                x = int(x_spin.value())
                y = int(y_spin.value())
                corners.append((x, y))

        if len(corners) == 4:
            # Define colors
            line_color = (0, 255, 0)  # Green for lines
            corner_color = (255, 0, 0)  # Red for corners
            selected_corner_color = (0, 0, 255)  # Blue for selected corner
            fill_color = (0, 255, 0, 50)  # Semi-transparent green for fill

            # Draw filled work area (semi-transparent)
            points = np.array(corners, np.int32)

            # Create overlay for transparency
            overlay = overlay_image.copy()
            cv2.fillPoly(overlay, [points], (0, 255, 0))
            cv2.addWeighted(overlay_image, 0.8, overlay, 0.2, 0, overlay_image)

            # Draw lines connecting corners
            line_thickness = 2
            for i in range(4):
                start_point = corners[i]
                end_point = corners[(i + 1) % 4]  # Connect to next corner (wrap around)
                cv2.line(overlay_image, start_point, end_point, line_color, line_thickness)

        return overlay_image

    def update_corner_positions_for_dragging(self):
        """Update corner positions in label coordinates for drag detection"""
        if not hasattr(self, 'calibration_preview_label') or self.original_image is None:
            return

        # Get corner coordinates in image space
        corners = []
        for i in range(1, 5):
            x_spin = self.corner_fields.get(f"corner{i}_x")
            y_spin = self.corner_fields.get(f"corner{i}_y")
            if x_spin and y_spin:
                x = x_spin.value()
                y = y_spin.value()
                corners.append((x, y))

        if len(corners) == 4:
            # Calculate the scale factor from image to label coordinates
            label_size = self.calibration_preview_label.size()
            img_height, img_width = self.original_image.shape[:2]

            # Calculate scaling to fit image in label while maintaining aspect ratio
            scale_x = label_size.width() / img_width
            scale_y = label_size.height() / img_height
            scale = min(scale_x, scale_y)  # Use smaller scale to maintain aspect ratio

            self.image_to_label_scale = 1.0 / scale  # Store inverse for easy conversion

            # Update corner positions in the clickable label
            self.calibration_preview_label.update_corner_positions(corners, self.image_to_label_scale)

    def update_corner_positions_for_dragging(self):
        """Update corner positions in label coordinates for drag detection"""
        if not hasattr(self, 'calibration_preview_label') or self.original_image is None:
            return

        # Get corner coordinates in image space
        corners = []
        for i in range(1, 5):
            x_spin = self.corner_fields.get(f"corner{i}_x")
            y_spin = self.corner_fields.get(f"corner{i}_y")
            if x_spin and y_spin:
                x = x_spin.value()
                y = y_spin.value()
                corners.append((x, y))

        if len(corners) == 4:
            # Calculate the scale factor from image to label coordinates
            label_size = self.calibration_preview_label.size()
            img_height, img_width = self.original_image.shape[:2]

            # Calculate scaling to fit image in label while maintaining aspect ratio
            scale_x = label_size.width() / img_width
            scale_y = label_size.height() / img_height
            scale = min(scale_x, scale_y)  # Use smaller scale to maintain aspect ratio

            self.image_to_label_scale = 1.0 / scale  # Store inverse for easy conversion

            # Update corner positions in the clickable label
            self.calibration_preview_label.update_corner_positions(corners, self.image_to_label_scale)

    def update_work_area_visualization(self):
        """Update the work area visualization when corner values change"""
        if self.original_image is not None:
            self.update_camera_preview_from_cv2(self.original_image)

    def update_camera_feed(self, frame):
        try:
            if frame is not None:
                self.update_camera_preview_from_cv2(frame)
            else:
                return
        except Exception as e:
            print(f"Exception occurred: {e}")
        finally:
            pass

    def create_calibration_preview_section(self):
        """Create the calibration preview section with preview and controls"""
        preview_widget = QWidget()
        preview_widget.setFixedWidth(500)
        preview_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
        """)

        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(20, 20, 20, 20)
        preview_layout.setSpacing(15)

        # Calibration preview area
        self.calibration_preview_label = ClickableLabel("Calibration Preview")
        self.calibration_preview_label.clicked.connect(self.on_preview_clicked)
        self.calibration_preview_label.corner_dragged.connect(self.on_corner_dragged)
        self.calibration_preview_label.set_parent_widget(self)

        self.calibration_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.calibration_preview_label.setStyleSheet("""
            QLabel {
                background-color: #333;
                color: white;
                font-size: 16px;
                border: 1px solid #666;
                border-radius: 4px;
            }
        """)
        self.calibration_preview_label.setMinimumSize(460, 259)
        self.calibration_preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self.calibration_preview_label.setScaledContents(False)
        preview_layout.addWidget(self.calibration_preview_label)

        # Progress bar for calibration
        self.calibration_progress = QProgressBar()
        self.calibration_progress.setVisible(False)
        self.calibration_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 3px;
            }
        """)
        preview_layout.addWidget(self.calibration_progress)

        # Control buttons grid - UPDATED SECTION
        button_grid = QGridLayout()
        button_grid.setSpacing(10)

        # Row 0: Robot movement buttons
        self.move_to_pickup_button = QPushButton("Move to Pickup")
        self.move_to_calibration_button = QPushButton("Move to Calibration")

        movement_buttons = [self.move_to_pickup_button, self.move_to_calibration_button]
        for i, btn in enumerate(movement_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 0, i)

        # Row 1: Image capture buttons
        # self.save_images_button = QPushButton("Save Images")

        self.save_workarea_button = QPushButton("Save Work Area")
        self.save_workarea_button.setMinimumHeight(40)
        button_grid.addWidget(self.save_workarea_button, 1, 0, 1, 2)

        self.capture_image_button = QPushButton("Capture Image")
        self.capture_image_button.setMinimumHeight(40)
        button_grid.addWidget(self.capture_image_button, 2, 0, 1, 2)

        # Row 2: Calibration process buttons
        # self.calibrate_camera_button = QPushButton("Calibrate Camera")
        # self.detect_markers_button = QPushButton("Detect Markers")

        # calibration_buttons = [self.detect_markers_button]
        # for i, btn in enumerate(calibration_buttons):
        #     btn.setMinimumHeight(40)
        #     button_grid.addWidget(btn, 2, i)

        # Row 3: Compute homography (spans both columns)

        self.calibrate_camera_button = QPushButton("Calibrate Camera")
        self.calibrate_camera_button.setMinimumHeight(40)
        button_grid.addWidget(self.calibrate_camera_button, 3, 0, 1, 2)

        self.compute_homography_button = QPushButton("Calibrate Robot")
        self.compute_homography_button.setMinimumHeight(40)
        button_grid.addWidget(self.compute_homography_button, 4, 0, 1, 2)  # Span 2 columns

        self.auto_calibrate = QPushButton("Camera and Robot Calibration")
        self.auto_calibrate.setMinimumHeight(40)
        button_grid.addWidget(self.auto_calibrate, 5, 0, 1, 2)  # Span 2 columns

        self.test_calibration_button = QPushButton("Test Calibration")
        self.test_calibration_button.setMinimumHeight(40)
        button_grid.addWidget(self.test_calibration_button, 6, 0, 1, 2)  # Span 2 columns

        preview_layout.addLayout(button_grid)

        # Log output area
        self.log_output = QTextEdit()
        self.log_output.setMaximumHeight(120)
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Logs")
        preview_layout.addWidget(self.log_output)

        preview_layout.addStretch()

        self.connect_default_callbacks()

        for btn in movement_buttons + [self.compute_homography_button,
                                       self.auto_calibrate]:
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        return preview_widget

    def on_corner_dragged(self, corner_index, label_x, label_y):
        """Handle corner dragging"""
        print(f"Corner {corner_index} dragged to label coordinates: ({label_x}, {label_y})")

        if self.original_image is not None:
            # Convert label coordinates to image coordinates
            actual_x = int(label_x * self.image_to_label_scale)
            actual_y = int(label_y * self.image_to_label_scale)

            # Ensure coordinates are within image bounds
            img_height, img_width = self.original_image.shape[:2]
            actual_x = max(0, min(actual_x, img_width - 1))
            actual_y = max(0, min(actual_y, img_height - 1))
        else:
            actual_x, actual_y = label_x, label_y

        # Update the corresponding spinboxes
        corner_x_spin = self.corner_fields[f"corner{corner_index}_x"]
        corner_y_spin = self.corner_fields[f"corner{corner_index}_y"]

        # Temporarily disconnect signals to avoid recursive updates
        corner_x_spin.valueChanged.disconnect()
        corner_y_spin.valueChanged.disconnect()

        corner_x_spin.setValue(actual_x)
        corner_y_spin.setValue(actual_y)

        # Reconnect signals
        corner_x_spin.valueChanged.connect(self.update_work_area_visualization)
        corner_y_spin.valueChanged.connect(self.update_work_area_visualization)

        print(f"Corner {corner_index} updated to image coordinates: ({actual_x}, {actual_y})")

        # Update the visualization
        self.update_work_area_visualization()

    def on_preview_clicked(self, x, y):
        print(f"Camera preview clicked at: ({x}, {y})")
        if self.selected_corner_index is not None:
            # Calculate the actual image coordinates based on scaling
            label_size = self.calibration_preview_label.size()
            if self.original_image is not None:
                img_height, img_width = self.original_image.shape[:2]

                # Calculate scaling factor
                scale_x = img_width / label_size.width()
                scale_y = img_height / label_size.height()

                # Use the larger scale to maintain aspect ratio
                scale = max(scale_x, scale_y)

                # Calculate actual image coordinates
                actual_x = int(x * scale)
                actual_y = int(y * scale)

                # Ensure coordinates are within image bounds
                actual_x = max(0, min(actual_x, img_width - 1))
                actual_y = max(0, min(actual_y, img_height - 1))
            else:
                actual_x, actual_y = x, y

            corner_x_spin = self.corner_fields[f"corner{self.selected_corner_index}_x"]
            corner_y_spin = self.corner_fields[f"corner{self.selected_corner_index}_y"]

            corner_x_spin.setValue(actual_x)
            corner_y_spin.setValue(actual_y)
            print(f"Corner {self.selected_corner_index} updated to ({actual_x}, {actual_y})")

            # Update the visualization
            self.update_work_area_visualization()

    def update_calibration_preview(self, pixmap):
        """Update the calibration preview with a new frame, maintaining aspect ratio"""
        if hasattr(self, 'calibration_preview_label'):
            label_size = self.calibration_preview_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.calibration_preview_label.setPixmap(scaled_pixmap)
            self.calibration_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.calibration_preview_label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )

    def update_calibration_preview_from_cv2(self, cv2_image):
        """Update preview from OpenCV image"""
        if hasattr(self, 'calibration_preview_label'):
            rgb_image = cv2_image[:, :, ::-1] if len(cv2_image.shape) == 3 else cv2_image
            height, width = rgb_image.shape[:2]
            bytes_per_line = 3 * width if len(rgb_image.shape) == 3 else width

            img_bytes = rgb_image.tobytes()

            if len(rgb_image.shape) == 3:
                q_image = QImage(img_bytes, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            else:
                q_image = QImage(img_bytes, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)

            pixmap = QPixmap.fromImage(q_image)
            self.update_calibration_preview(pixmap)

    def clear_log(self):
        """Clear the log output"""
        if hasattr(self, 'log_output'):
            self.log_output.clear()

    def on_parent_resize(self, event):
        """Handle parent widget resize events"""
        if hasattr(super(QWidget, self.parent_widget), 'resizeEvent'):
            super(QWidget, self.parent_widget).resizeEvent(event)

    def update_layout_for_screen_size(self):
        """Update layout based on current screen size"""
        self.clear_layout()
        self.create_main_content()

    def clear_layout(self):
        """Clear all widgets from the layout"""
        while self.count():
            child = self.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def create_main_content(self):
        """Create the main content with camera preview on left, settings in middle, and robot jog on right"""
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setSpacing(2)
        main_horizontal_layout.setContentsMargins(0, 0, 0, 0)

        # --- Left: Camera Preview ---
        preview_widget = self.create_calibration_preview_section()
        # Set minimum width to prevent excessive shrinking
        # preview_widget.setMinimumWidth(400)

        # --- Middle: Settings scroll area ---
        settings_scroll_area = QScrollArea()
        settings_scroll_area.setWidgetResizable(True)
        settings_scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        settings_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        settings_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # SOLUTION 1: Set minimum width for settings area
        settings_scroll_area.setMinimumWidth(200)  # Prevent squashing below this width

        # SOLUTION 2: Set preferred size
        settings_scroll_area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        QScroller.grabGesture(settings_scroll_area.viewport(), QScroller.ScrollerGestureType.TouchGesture)

        settings_content_widget = QWidget()
        settings_content_layout = QVBoxLayout(settings_content_widget)
        settings_content_layout.setSpacing(2)
        settings_content_layout.setContentsMargins(0, 0, 0, 0)

        # Add all the settings groups to the middle section
        self.add_settings_to_layout(settings_content_layout)

        settings_scroll_area.setWidget(settings_content_widget)

        # --- Right: Robot Jog Widget ---
        robot_jog_widget = QWidget()
        robot_jog_widget.setMinimumWidth(400)  # Prevent excessive shrinking
        robot_jog_layout = QVBoxLayout(robot_jog_widget)
        robot_jog_layout.setSpacing(2)
        robot_jog_layout.setContentsMargins(0, 0, 0, 0)

        self.robotManualControlWidget = RobotJogWidget(self.parent_widget)
        self.robotManualControlWidget.jogRequested.connect(lambda command, axis, direction, value:
                                                           self.jogRequested.emit(command, axis, direction, value))
        self.robotManualControlWidget.save_point_requested.connect(lambda: self.save_point_requested.emit())
        robot_jog_layout.addWidget(self.robotManualControlWidget, 1)
        # robot_jog_layout.addStretch()

        # SOLUTION 3: Use different stretch factors
        # Give middle section higher priority to maintain its space
        main_horizontal_layout.addWidget(preview_widget, 1)  # Left - stretch factor 1
        main_horizontal_layout.addWidget(settings_scroll_area, 2)  # Middle - stretch factor 2 (more space priority)
        main_horizontal_layout.addWidget(robot_jog_widget, 1)  # Right - stretch factor 1
        # --- Wrap inside QWidget ---
        main_widget = QWidget()
        main_widget.setLayout(main_horizontal_layout)

        # SOLUTION 5: Set minimum width for the entire main widget
        main_widget.setMinimumWidth(1200)  # Ensure window doesn't get too narrow

        self.addWidget(main_widget)

    def add_settings_to_layout(self, parent_layout):
        """Add all settings groups to the layout in vertical arrangement"""
        # --- Work area corners group ---
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        work_area_group = self.create_work_area_group()
        parent_layout.addWidget(work_area_group)
        # First row of settings
        first_row = QHBoxLayout()
        first_row.setSpacing(2)
        first_row.addWidget(work_area_group)
        parent_layout.addLayout(first_row)

        # Second row of settings
        second_row = QHBoxLayout()
        second_row.setSpacing(2)
        second_row.addWidget(spacer)
        parent_layout.addLayout(second_row)

        # Third row of settings
        third_row = QHBoxLayout()
        third_row.setSpacing(2)
        third_row.addWidget(spacer)
        parent_layout.addLayout(third_row)

    def connect_default_callbacks(self):
        """Connect default button callbacks"""
        # Robot movement controls
        self.move_to_pickup_button.clicked.connect(lambda: self.move_to_pickup_requested.emit())
        self.move_to_calibration_button.clicked.connect(lambda: self.move_to_calibration_requested.emit())

        # Image capture controls
        self.capture_image_button.clicked.connect(lambda: self.capture_image_requested.emit())
        # self.save_images_button.clicked.connect(lambda: self.save_images_requested.emit())

        # Calibration process controls
        self.calibrate_camera_button.clicked.connect(lambda: self.calibrate_camera_requested.emit())
        # self.detect_markers_button.clicked.connect(lambda: self.detect_markers_requested.emit())
        self.compute_homography_button.clicked.connect(lambda: self.compute_homography_requested.emit())
        self.auto_calibrate.clicked.connect(lambda: self.auto_calibrate_requested.emit())
        self.test_calibration_button.clicked.connect(lambda: self.test_calibration_requested.emit())
        self.save_workarea_button.clicked.connect(lambda: self.onSaveWorkAreaRequested())

    def onSaveWorkAreaRequested(self):
        """Handle save work area request"""
        corners = []
        for i in range(1, 5):
            x_spin = self.corner_fields.get(f"corner{i}_x")
            y_spin = self.corner_fields.get(f"corner{i}_y")
            if x_spin and y_spin:
                x = float(x_spin.value())
                y = float(y_spin.value())
                corners.append([x, y])

        if len(corners) != 4:
            print("Error: Not enough corners defined to save work area.")
            return

        self.save_work_area_requested.emit(corners)

    def create_work_area_group(self):
        group_box = QGroupBox("Work Area Corners")

        layout = QVBoxLayout()  # stack rows vertically
        layout.setSpacing(0)  # reduce space between rows
        layout.setContentsMargins(0, 0, 0, 0)
        self.corner_fields = {}
        self.corner_rows = {}

        for i in range(1, 5):
            # x_spin = QDoubleSpinBox()
            x_spin = FocusDoubleSpinBox()
            x_spin.setRange(0, 10000)
            x_spin.setDecimals(2)

            y_spin = FocusDoubleSpinBox()
            y_spin.setRange(0, 10000)
            y_spin.setDecimals(2)

            x_spin.setFixedWidth(60)
            y_spin.setFixedWidth(60)

            # Connect value change signals to update visualization
            x_spin.valueChanged.connect(self.update_work_area_visualization)
            y_spin.valueChanged.connect(self.update_work_area_visualization)

            row_widget = ClickableRow(i, f"Corner {i}:", x_spin, y_spin, self.set_selected_corner)
            row_widget.setFixedHeight(30)  # adjust to taste

            layout.addWidget(row_widget)

            self.corner_fields[f"corner{i}_x"] = x_spin
            self.corner_fields[f"corner{i}_y"] = y_spin
            self.corner_rows[i] = row_widget

        group_box.setLayout(layout)
        return group_box

    def set_selected_corner(self, index):
        for i, row in self.corner_rows.items():
            row.setStyleSheet("")
        self.corner_rows[index].setStyleSheet("background-color: lightblue;")
        self.selected_corner_index = index
        print(f"Selected corner {index}")

        # Update visualization to show selected corner
        self.update_work_area_visualization()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget

    app = QApplication(sys.argv)
    main_widget = QWidget()
    layout = CalibrationServiceTabLayout(main_widget)
    main_widget.setLayout(layout)
    main_widget.show()
    sys.exit(app.exec())
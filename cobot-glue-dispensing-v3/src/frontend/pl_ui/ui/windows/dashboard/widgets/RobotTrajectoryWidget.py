import os
import time
import threading
from collections import deque

import cv2
import numpy as np
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QSizePolicy

from frontend.pl_ui.utils.IconLoader import LOGO
from frontend.pl_ui.utils.IconLoader import CAMERA_PREVIEW_PLACEHOLDER


class CompactTimeMetric(QWidget):
    """Compact time metric with horizontal layout"""

    def __init__(self, title, value="0.00 s", color="#1976D2", parent=None):
        super().__init__(parent)
        self.color = color
        self.init_ui(title, value)

    def init_ui(self, title, value):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Title label (smaller)
        self.title_label = QLabel(title + ":")
        self.title_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
        self.title_label.setStyleSheet(f"color: {self.color}; font-weight: 500;")

        # Value label (compact)
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.value_label.setStyleSheet("color: #212121; font-weight: 600;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def update_value(self, value):
        self.value_label.setText(value)


class TrajectoryManager:
    def __init__(self):
        self.trajectory_points = deque()
        self.current_position = None
        self.last_position = None
        self._lock = threading.Lock()  # Add thread lock for thread safety
        
        # Trail settings
        self.trail_length = 100
        self.trail_thickness = 2
        self.trail_fade = False
        self.show_current_point = True
        self.interpolate_motion = True

        # Colors (BGR) - Material Design colors
        self.trail_color = (156, 39, 176)  # Purple 500
        self.current_point_color = (0, 0, 128)  # Navy Blue

        # Performance tracking
        self.start_time = time.time() * 1000
        self.update_count = 0
        self.is_running = True
        
        # Trajectory break tracking
        self.trajectory_break_pending = False



    def add_interpolated_points(self, start_pos, end_pos, num_interpolated=3):
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        current_time = time.time()

        distance = np.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)

        with self._lock:
            if distance > 5:
                for i in range(1, num_interpolated + 1):
                    t = i / (num_interpolated + 1)
                    interp_x = int(start_x + t * (end_x - start_x))
                    interp_y = int(start_y + t * (end_y - start_y))
                    self.trajectory_points.append((interp_x, interp_y, current_time, False))  # False = not a break

            self.trajectory_points.append((end_x, end_y, current_time, False))  # False = not a break

    def update_position(self, position):
        # If a trajectory break is pending, reset last position to avoid connecting
        if self.trajectory_break_pending:
            self.last_position = None
            self.trajectory_break_pending = False
            # print("🔀 TRAJECTORY: Break applied - starting new trajectory segment")
        else:
            self.last_position = self.current_position
            
        self.current_position = position

        if self.last_position is not None and self.interpolate_motion:
            self.add_interpolated_points(self.last_position, self.current_position)
        else:
            with self._lock:
                is_break_start = self.last_position is None  # True if this is the start of a new segment
                self.trajectory_points.append((*position, time.time(), is_break_start))
    
    def break_trajectory(self):
        """Signal that the next position update should start a new trajectory segment"""
        # print("🔀 TRAJECTORY: Break requested - next trajectory point will start new segment")
        self.trajectory_break_pending = True

    def clear_trail(self):
        with self._lock:
            self.trajectory_points.clear()
            self.current_position = None
            self.last_position = None
    
    def get_trajectory_copy(self):
        """Thread-safe method to get a copy of trajectory points"""
        with self._lock:
            return list(self.trajectory_points)




def draw_icon_at_position(icon, image, position):
    """Draw icon at given position with improved error handling"""
    if icon is None:
        raise ValueError("Logo icon is None")

    if image is None:
        raise ValueError("Image is None")

    if position is None:
        raise ValueError("Current position is None")

    image_width = image.shape[1]
    image_height = image.shape[0]

    x, y = position
    h, w = icon.shape[:2]
    x1, y1 = x - w // 2, y - h // 2
    x2, y2 = x1 + w, y1 + h

    if x1 >= 0 and y1 >= 0 and x2 <= image_width and y2 <= image_height:
        if len(icon.shape) == 3 and icon.shape[2] == 4:
            alpha_logo = icon[:, :, 3] / 255.0
            alpha_bg = 1.0 - alpha_logo
            for c in range(0, 3):
                image[y1:y2, x1:x2, c] = (
                        alpha_logo * icon[:, :, c] +
                        alpha_bg * image[y1:y2, x1:x2, c]
                ).astype(np.uint8)
        else:
            image[y1:y2, x1:x2] = icon
    else:
        pass
        # print(f"Warning: Icon position out of bounds: ({x1}, {y1}) to ({x2}, {y2})")

def draw_smooth_trail(image, trajectory_points_with_breaks):
    """Draw trajectory trail respecting break markers"""
    if len(trajectory_points_with_breaks) < 2:
        return

    image_width = image.shape[1]
    image_height = image.shape[0]
    
    # Split trajectory into separate segments based on break markers
    segments = []
    current_segment = []
    
    for point_data in trajectory_points_with_breaks:
        if len(point_data) >= 4:  # New format: (x, y, time, is_break)
            x, y, timestamp, is_break = point_data[:4]
            if is_break and current_segment:
                # Start of new segment - save current segment and start fresh
                if len(current_segment) > 1:
                    segments.append(current_segment)
                current_segment = [(x, y)]
            else:
                current_segment.append((x, y))
        else:  # Old format: (x, y, time) - treat as continuous
            x, y = point_data[:2]
            current_segment.append((x, y))
    
    # Add the last segment
    if len(current_segment) > 1:
        segments.append(current_segment)
    
    # print(f"🎨 TRAJECTORY: Drawing {len(segments)} separate trajectory segments")
    
    # Draw each segment separately
    for segment_idx, segment in enumerate(segments):
        if len(segment) < 2:
            continue
            
        # Convert to numpy array for processing
        segment_points = np.array(segment, dtype=np.float32)
        
        # Apply smoothing to this segment
        smoothed_points = []
        kernel_size = 3  # Reduced for better responsiveness
        
        for i in range(len(segment_points)):
            start = max(0, i - kernel_size + 1)
            avg_x = np.mean(segment_points[start:i + 1, 0])
            avg_y = np.mean(segment_points[start:i + 1, 1])
            smoothed_points.append((int(avg_x), int(avg_y)))
        
        # Draw lines within this segment only
        total = len(smoothed_points)
        
        for i in range(total - 1):
            progress = (i + 1) / total
            if progress < 0.3:
                fade_factor = progress / 0.3
                color = (
                    int(200 * fade_factor),
                    int(100 * fade_factor),
                    int(50 * fade_factor)
                )
            elif progress < 0.7:
                fade_factor = (progress - 0.3) / 0.4
                color = (
                    int(156 + (100 * fade_factor)),
                    int(39 + (50 * fade_factor)),
                    int(176 + (79 * fade_factor))
                )
            else:
                fade_factor = (progress - 0.7) / 0.3
                color = (
                    int(255 * fade_factor),
                    int(89 * fade_factor),
                    int(255 * fade_factor)
                )

            thickness = max(1, int(2 + (progress * 4)))
            p1 = smoothed_points[i]
            p2 = smoothed_points[i + 1]

            if (0 <= p1[0] < image_width and 0 <= p1[1] < image_height and
                    0 <= p2[0] < image_width and 0 <= p2[1] < image_height):
                cv2.line(image, p1, p2, color, thickness, lineType=cv2.LINE_AA)

        # Highlight recent points within this segment
        if len(smoothed_points) > 5:
            recent_points = smoothed_points[-5:]
            for i in range(len(recent_points) - 1):
                p1 = recent_points[i]
                p2 = recent_points[i + 1]
                if (0 <= p1[0] < image_width and 0 <= p1[1] < image_height and
                        0 <= p2[0] < image_width and 0 <= p2[1] < image_height):
                    cv2.line(image, p1, p2, (255, 200, 255), 6, lineType=cv2.LINE_AA)
                    cv2.line(image, p1, p2, (255, 100, 255), 2, lineType=cv2.LINE_AA)

def load_logo_icon():
    """Load logo icon with error handling"""
    if not os.path.exists(LOGO):
        print(f"ERROR: Logo file does not exist at {LOGO}")
        return
    try:
        from PIL import Image
        pil_image = Image.open(LOGO).convert('RGBA')
        logo = np.array(pil_image)
        logo = cv2.cvtColor(logo, cv2.COLOR_RGBA2BGRA)
        logo_icon = cv2.resize(logo, (36, 36), interpolation=cv2.INTER_AREA)
        return logo_icon
    except Exception as e:
        print(f"Failed to load logo: {e}")


class RobotTrajectoryWidget(QWidget):
    def __init__(self, image_width=640, image_height=360):
        super().__init__()

        # Store image dimensions
        self.image_width = image_width
        self.image_height = image_height

        # External data
        self.estimated_time_value = 0.0
        self.time_left_value = 0.0

        # Frame and trajectory storage
        self.base_frame = None
        self.current_frame = None
        self.trajectory_manager = TrajectoryManager()

        self.init_ui()

        # FIXED: Improved logo loading with better error handling and debugging
        self.logo_icon = load_logo_icon()

        # Load placeholder image after UI is initialized
        self.load_placeholder_image()
        self.drawing_enabled = False
        # Timer to refresh display
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(30)  # 30 FPS



    def init_ui(self):
        self.setWindowTitle("Trajectory Tracker")

        # Metrics widgets
        self.estimated_metric = CompactTimeMetric("Est. Time", "0.00 s", "#1976D2")
        self.time_left_metric = CompactTimeMetric("Time Left", "0.00 s", "#388E3C")


        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)
        metrics_layout.addWidget(self.estimated_metric)
        metrics_layout.addWidget(self.time_left_metric)
        metrics_layout.addStretch()
        metrics_widget = QWidget()
        metrics_widget.setLayout(metrics_layout)
        metrics_widget.setVisible(False)

        # Image
        self.image_label = QLabel()
        self.image_label.setFixedSize(self.image_width, self.image_height)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #F5F5F5;
                border-radius: 6px;
                border: 1px solid #E0E0E0;
            }
        """)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Container layout
        container_layout = QVBoxLayout()
        container_layout.setSpacing(12)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.addWidget(metrics_widget)
        container_layout.addWidget(self.image_label)

        # Container frame
        container_frame = QFrame()
        container_frame.setLayout(container_layout)
        container_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.addWidget(container_frame)

        # Set size policy to allow expansion while maintaining aspect ratio
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(self.image_width + 48, self.image_height + 100)  # Add padding for metrics and margins

    def load_placeholder_image(self):
        """Load and set placeholder image"""
        try:
            placeholder_image = cv2.imread(CAMERA_PREVIEW_PLACEHOLDER)
            placeholder_image = cv2.resize(placeholder_image, (self.image_width, self.image_height))
            self.base_frame = placeholder_image.copy()
            self.current_frame = placeholder_image.copy()
            self._update_label_from_frame()
        except Exception as e:
            raise ValueError(f"Error loading placeholder image: {e}")

    def update(self, message=None):
        if message is None:
            return

        x, y = message.get("x", 0), message.get("y", 0)
        # print(f"📍 Widget received: ({x}, {y}) - Widget size: {self.image_width}x{self.image_height}")
        # print(self.get_image_dimensions())
        screen_x = int(x)
        screen_y = int(y)

        self.trajectory_manager.update_position((screen_x, screen_y))
    
    def break_trajectory(self):
        """Request a trajectory break for the next position update"""
        self.trajectory_manager.break_trajectory()

    def update_display(self):
        if self.base_frame is None:
            return

        self.current_frame = self.base_frame.copy()

        # Use the thread-safe method to get trajectory points
        trajectory_points_copy = self.trajectory_manager.get_trajectory_copy()

        if self.drawing_enabled == True:
            if trajectory_points_copy:
                try:
                    # Pass the trajectory points with break information directly
                    draw_smooth_trail(image=self.current_frame, trajectory_points_with_breaks=trajectory_points_copy)
                except (IndexError, ValueError):
                    # Handle any remaining issues with point extraction
                    pass

        # if self.trajectory_manager.current_position is not None and self.trajectory_manager.show_current_point:
        #     draw_icon_at_position(self.logo_icon, self.current_frame,
        #                           self.trajectory_manager.current_position)

        self._update_label_from_frame()
        self.trajectory_manager.update_count += 1

        # Update time displays
        self.estimated_metric.update_value(f"{self.estimated_time_value:.2f} s")
        self.time_left_metric.update_value(f"{self.time_left_value:.2f} s")

    def _update_label_from_frame(self):
        if self.current_frame is None:
            return

        rgb_image = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        q_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888)

        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)

    def enable_drawing(self,message):

        self.drawing_enabled = True

    def disable_drawing(self,message):
        print("Stopping trajectory updates and clearing trail")
        self.drawing_enabled = False
        self.trajectory_manager.clear_trail()

    def set_image(self, message=None):
        # print("Updating image from external source")
        """Receive an external image from outside."""
        if message is None or "image" not in message:
            return

        frame = message.get("image")
        if frame is None:
            self.load_placeholder_image()
            return

        try:
            frame = cv2.resize(frame, (self.image_width, self.image_height))
            self.base_frame = frame.copy()
            self.trajectory_manager.clear_trail()
        except Exception as e:
            print(f"Error setting image: {e}")
            self.load_placeholder_image()

    def get_image_dimensions(self):
        """Return the configured image dimensions"""
        return self.image_width, self.image_height

    def closeEvent(self, event):
        self.trajectory_manager.is_running = False
        self.timer.stop()
        event.accept()

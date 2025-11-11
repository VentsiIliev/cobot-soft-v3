import os
import sys
import time
import math
import threading
import numpy as np
import cv2
from collections import deque
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QSizePolicy
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QImage, QPixmap, QPalette, QPainter, QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from API.MessageBroker import MessageBroker

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "resources")
CAMERA_PREVIEW_PLACEHOLDER = os.path.join(RESOURCE_DIR, "pl_ui_icons", "Background_&_Logo_white.png")
print(f"Using placeholder image from: {CAMERA_PREVIEW_PLACEHOLDER}")
LOGO = os.path.join(RESOURCE_DIR, "pl_ui_icons", "logo.ico")


class CompactCard(QFrame):
    """Compact card component with minimal padding"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: none;
            }
        """)
        # Reduced shadow for compact design
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(1)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)


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


class SmoothTrajectoryWidget(QWidget):
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

        # Trajectory tracking
        self.trajectory_points = deque()
        self.current_position = None
        self.last_position = None

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

        self.init_ui()

        # FIXED: Improved logo loading with better error handling and debugging
        self.logo_icon = None
        self.load_logo_icon()

        # Load placeholder image after UI is initialized
        self.load_placeholder_image()

        # Timer to refresh display
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(33)  # 30 FPS

    def load_logo_icon(self):
        """Load logo icon with improved error handling and debugging"""
        print(f"Attempting to load logo from: {LOGO}")

        # Check if file exists
        if not os.path.exists(LOGO):
            print(f"ERROR: Logo file does not exist at {LOGO}")
            return

        try:
            # Try different approaches to load .ico file
            # Method 1: Direct OpenCV load
            logo = cv2.imread(LOGO, cv2.IMREAD_UNCHANGED)

            if logo is None:
                print("Method 1 failed: cv2.imread returned None")

                # Method 2: Try loading as PNG (some .ico files are actually PNG)
                try:
                    from PIL import Image
                    pil_image = Image.open(LOGO)
                    pil_image = pil_image.convert('RGBA')
                    logo = np.array(pil_image)
                    # Convert RGBA to BGRA for OpenCV
                    logo = cv2.cvtColor(logo, cv2.COLOR_RGBA2BGRA)
                    print("Method 2 successful: Loaded via PIL")
                except ImportError:
                    print("PIL not available, trying alternative method")
                except Exception as e:
                    print(f"Method 2 failed: {e}")

                    # Method 3: Try loading without alpha channel
                    logo = cv2.imread(LOGO, cv2.IMREAD_COLOR)
                    if logo is not None:
                        print("Method 3 successful: Loaded without alpha channel")
            else:
                print("Method 1 successful: Direct OpenCV load")

            if logo is not None:
                print(f"Logo loaded successfully. Shape: {logo.shape}, dtype: {logo.dtype}")

                # Resize to appropriate size (make it larger so it's more visible)
                target_size = 36  # Increased from 32 to make it more visible
                self.logo_icon = cv2.resize(logo, (target_size, target_size), interpolation=cv2.INTER_AREA)
                print(f"Logo resized to: {self.logo_icon.shape}")

                # Debug: Save the resized logo to verify it's correct
                debug_path = "debug_logo.png"
                cv2.imwrite(debug_path, self.logo_icon)
                print(f"Debug logo saved to: {debug_path}")
            else:
                print("ERROR: Failed to load logo with all methods")

        except Exception as e:
            print(f"Exception while loading logo: {e}")
            import traceback
            traceback.print_exc()

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
        self.image_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

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

        # === Dynamically compute total widget size ===
        total_width = container_frame.sizeHint().width() + main_layout.contentsMargins().left() + main_layout.contentsMargins().right()
        total_height = container_frame.sizeHint().height() + main_layout.contentsMargins().top() + main_layout.contentsMargins().bottom()
        self.setFixedSize(total_width, total_height)

    def load_placeholder_image(self):
        """Load and set placeholder image"""
        try:
            placeholder_image = cv2.imread(CAMERA_PREVIEW_PLACEHOLDER)

            if placeholder_image is not None:
                placeholder_image = cv2.resize(placeholder_image, (self.image_width, self.image_height))
                self.base_frame = placeholder_image.copy()
                self.current_frame = placeholder_image.copy()
                self._update_label_from_frame()
            else:
                self.create_fallback_placeholder()

        except Exception as e:
            print(f"Error loading placeholder image: {e}")
            self.create_fallback_placeholder()

    def create_fallback_placeholder(self):
        """Create a simple fallback placeholder when image file is not available"""
        placeholder = np.full((self.image_height, self.image_width, 3), (64, 64, 64), dtype=np.uint8)

        font = cv2.FONT_HERSHEY_SIMPLEX
        text = "Camera Feed"
        font_scale = 1.0
        color = (200, 200, 200)
        thickness = 2

        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
        x = (self.image_width - text_width) // 2
        y = (self.image_height + text_height) // 2

        cv2.putText(placeholder, text, (x, y), font, font_scale, color, thickness)
        cv2.rectangle(placeholder, (10, 10), (self.image_width - 10, self.image_height - 10), (100, 100, 100), 2)

        self.base_frame = placeholder.copy()
        self.current_frame = placeholder.copy()
        self._update_label_from_frame()

    def update(self, message=None):
        if message is None:
            return

        x, y = message.get("x", 0), message.get("y", 0)
        print(f"📍 Widget received: ({x}, {y}) - Widget size: {self.image_width}x{self.image_height}")
        print(self.get_image_dimensions())
        screen_x = int(x)
        screen_y = int(y)

        self.last_position = self.current_position
        self.current_position = (screen_x, screen_y)

        if self.last_position is not None and self.interpolate_motion:
            self._add_interpolated_points(self.last_position, self.current_position)
        else:
            self.trajectory_points.append((screen_x, screen_y, time.time()))

    def _add_interpolated_points(self, start_pos, end_pos, num_interpolated=3):
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        current_time = time.time()

        distance = np.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)

        if distance > 5:
            for i in range(1, num_interpolated + 1):
                t = i / (num_interpolated + 1)
                interp_x = int(start_x + t * (end_x - start_x))
                interp_y = int(start_y + t * (end_y - start_y))
                self.trajectory_points.append((interp_x, interp_y, current_time))

        self.trajectory_points.append((end_x, end_y, current_time))

    def update_display(self):
        if self.base_frame is None:
            return

        self.current_frame = self.base_frame.copy()

        # # Clean up old trajectory points
        # current_time = time.time()
        # while self.trajectory_points and current_time - self.trajectory_points[0][2] > 10:
        #     self.trajectory_points.popleft()
        #
        # while len(self.trajectory_points) > self.trail_length:
        #     self.trajectory_points.popleft()

        self._draw_smooth_trail()

        # FIXED: Improved logo drawing with better bounds checking and debugging
        if self.current_position is not None and self.show_current_point:
            self._draw_logo_at_position()

        self._update_label_from_frame()
        self.update_count += 1

        # Update time displays
        self.estimated_metric.update_value(f"{self.estimated_time_value:.2f} s")
        self.time_left_metric.update_value(f"{self.time_left_value:.2f} s")

    def _draw_logo_at_position(self):
        """Draw logo at current position with improved error handling"""
        if self.logo_icon is None:
            # print("Logo icon is None, drawing fallback circle")
            # Fallback: draw a simple circle if logo is not available
            x, y = self.current_position
            if 0 <= x < self.image_width and 0 <= y < self.image_height:
                cv2.circle(self.current_frame, (x, y), 15, (0, 255, 255), 3)  # Yellow circle
                cv2.circle(self.current_frame, (x, y), 8, (0, 0, 255), -1)  # Red filled center
            return

        x, y = self.current_position
        h, w = self.logo_icon.shape[:2]

        # Calculate position (center the logo on the point)
        x1, y1 = x - w // 2, y - h // 2
        x2, y2 = x1 + w, y1 + h

        # print(f"Drawing logo at position ({x}, {y}), logo size: {w}x{h}, bounds: ({x1},{y1}) to ({x2},{y2})")
        # print(f"Frame size: {self.current_frame.shape[1]}x{self.current_frame.shape[0]}")

        # Check bounds with some tolerance
        if x1 >= 0 and y1 >= 0 and x2 <= self.current_frame.shape[1] and y2 <= self.current_frame.shape[0]:
            try:
                if len(self.logo_icon.shape) == 3 and self.logo_icon.shape[2] == 4:
                    # Logo has alpha channel
                    # print("Drawing logo with alpha blending")
                    alpha_logo = self.logo_icon[:, :, 3] / 255.0
                    alpha_bg = 1.0 - alpha_logo

                    for c in range(0, 3):
                        self.current_frame[y1:y2, x1:x2, c] = (
                                alpha_logo * self.logo_icon[:, :, c] +
                                alpha_bg * self.current_frame[y1:y2, x1:x2, c]
                        ).astype(np.uint8)
                    # print("Alpha blending completed")
                else:
                    # No alpha channel, direct paste
                    # print("Drawing logo without alpha")
                    self.current_frame[y1:y2, x1:x2] = self.logo_icon
                    # print("Direct paste completed")

            except Exception as e:
                # print(f"Error drawing logo: {e}")
                # Fallback to circle
                cv2.circle(self.current_frame, (x, y), 15, (0, 255, 0), 3)
        else:
            # print(f"Logo position out of bounds, drawing at edge")
            # Still draw something visible at the edge
            safe_x = max(15, min(x, self.image_width - 15))
            safe_y = max(15, min(y, self.image_height - 15))
            cv2.circle(self.current_frame, (safe_x, safe_y), 10, (255, 0, 255), 2)

    def _draw_smooth_trail(self):
        if len(self.trajectory_points) < 2:
            return

        points = np.array([(p[0], p[1]) for p in self.trajectory_points], dtype=np.float32)
        smoothed_points = []
        kernel_size = 5

        for i in range(len(points)):
            start = max(0, i - kernel_size + 1)
            avg_x = np.mean(points[start:i + 1, 0])
            avg_y = np.mean(points[start:i + 1, 1])
            smoothed_points.append((int(avg_x), int(avg_y)))

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

            if (0 <= p1[0] < self.image_width and 0 <= p1[1] < self.image_height and
                    0 <= p2[0] < self.image_width and 0 <= p2[1] < self.image_height):
                cv2.line(self.current_frame, p1, p2, color, thickness, lineType=cv2.LINE_AA)

        # Glow effect for recent points
        if len(smoothed_points) > 10:
            recent_points = smoothed_points[-10:]
            for i in range(len(recent_points) - 1):
                p1 = recent_points[i]
                p2 = recent_points[i + 1]

                if (0 <= p1[0] < self.image_width and 0 <= p1[1] < self.image_height and
                        0 <= p2[0] < self.image_width and 0 <= p2[1] < self.image_height):
                    cv2.line(self.current_frame, p1, p2, (255, 200, 255), 8, lineType=cv2.LINE_AA)
                    cv2.line(self.current_frame, p1, p2, (255, 100, 255), 3, lineType=cv2.LINE_AA)

    def _update_label_from_frame(self):
        if self.current_frame is None:
            return

        rgb_image = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        q_image = QImage(rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888)

        pixmap = QPixmap.fromImage(q_image)
        self.image_label.setPixmap(pixmap)

    def set_image(self, message=None):
        print("Updating image from external source")
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
            self.clear_trail()
        except Exception as e:
            print(f"Error setting image: {e}")
            self.load_placeholder_image()

    def set_placeholder_image(self, image_path=None):
        """Set a custom placeholder image"""
        if image_path is None:
            image_path = CAMERA_PREVIEW_PLACEHOLDER

        try:
            placeholder = cv2.imread(image_path)
            if placeholder is not None:
                placeholder = cv2.resize(placeholder, (self.image_width, self.image_height))
                self.base_frame = placeholder.copy()
                self.current_frame = placeholder.copy()
                self._update_label_from_frame()
                return True
        except Exception as e:
            print(f"Error setting placeholder image: {e}")

        self.create_fallback_placeholder()
        return False

    def set_estimated_time(self, time_value):
        """Update estimated time value"""
        self.estimated_time_value = time_value

    def set_time_left(self, time_value):
        """Update time left value"""
        self.time_left_value = time_value

    def clear_trail(self):
        self.trajectory_points.clear()
        self.current_position = None
        self.last_position = None

    def get_image_dimensions(self):
        """Return the configured image dimensions"""
        return self.image_width, self.image_height

    def set_image_dimensions(self, width, height):
        """Update image dimensions and adjust widget accordingly"""
        self.image_width = width
        self.image_height = height

        widget_width = width + 32
        widget_height = height + 80
        self.setFixedSize(widget_width, widget_height)

        self.image_label.setFixedSize(width, height)
        self.clear_trail()
        self.load_placeholder_image()

    def closeEvent(self, event):
        self.is_running = False
        self.timer.stop()
        event.accept()


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Space-Optimized Trajectory Tracker")
        self.setGeometry(50, 50, 800, 600)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.camera_widget = SmoothTrajectoryWidget(image_width=640, image_height=360)
        self.camera_widget.set_image(np.zeros((1280, 720, 3), dtype=np.uint8))
        self.camera_widget.estimated_time_value = 5.0
        self.camera_widget.time_left_value = 3.0

        broker = MessageBroker()
        broker.subscribe("robot/trajectory/point", self.camera_widget.update)
        broker.subscribe("robot/trajectory/updateImage", self.camera_widget.set_image)

        layout.addWidget(self.camera_widget)
        self.setLayout(layout)
        self.start_smooth_trajectory_thread()

    def start_smooth_trajectory_thread(self):
        def generate_smooth_trajectory():
            broker = MessageBroker()
            t = 0.0
            dt = 0.02
            while True:
                x = 80 * math.cos(t * 2)
                y = 80 * math.sin(t * 2)
                broker.publish("robot/trajectory/point", {"x": x, "y": y})

                t += dt
                time.sleep(dt)

        threading.Thread(target=generate_smooth_trajectory, daemon=True).start()


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
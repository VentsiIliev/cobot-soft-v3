from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ThumbnailWidget(QWidget):
    """Custom widget to display a thumbnail image, file name, and last modified date."""

    # Add signal definitions
    clicked = pyqtSignal()
    long_pressed = pyqtSignal()  # New signal for long press

    def __init__(self, filename, pixmap, timestamp, parent=None, workpieceId=None):
        super().__init__(parent)

        # Store data for potential use in signal handlers
        self.filename = filename
        self.timestamp = timestamp
        self.original_pixmap = pixmap
        self.workpieceId = workpieceId  # Store workpiece ID for deletion

        # Long press timer setup
        self.long_press_timer = QTimer()
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self._on_long_press_timeout)
        self.long_press_duration = 1000  # 1000ms for touch-friendly long press
        self.press_start_pos = None
        self.is_pressed = False
        self.original_stylesheet = None  # Store original style for feedback

        # Set fixed size for consistent layout
        self.setFixedSize(140, 180)
        self.setStyleSheet("""
            ThumbnailWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                margin: 2px;
            }
            ThumbnailWidget:hover {
                border: 2px solid #0078d4;
                background-color: #f5f5f5;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # Small margins inside the widget
        layout.setSpacing(3)  # Minimal spacing between elements
        self.setLayout(layout)

        # Add thumbnail image with fixed size
        image_label = QLabel()
        image_label.setFixedSize(120, 120)
        image_label.setPixmap(
            pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("border: 1px solid #ddd; background-color: #f9f9f9;")
        layout.addWidget(image_label)

        # Add file name (truncate if too long)
        filename_display = filename if len(filename) <= 20 else filename[:17] + "..."
        filename_label = QLabel(filename_display)
        filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        filename_label.setWordWrap(True)
        filename_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(filename_label)

        # Add last modified date
        date_label = QLabel(f"Modified: {timestamp}")
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(8)
        date_label.setFont(font)
        date_label.setStyleSheet("color: #666;")
        # layout.addWidget(date_label)

    def mousePressEvent(self, event):
        """Handle mouse press events for both click and long press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_pressed = True
            self.press_start_pos = event.position().toPoint()

            # Store original style and apply pressed feedback
            self.original_stylesheet = self.styleSheet()
            self.setStyleSheet("""
                ThumbnailWidget {
                    border: 3px solid #0078d4;
                    border-radius: 5px;
                    background-color: #e3f2fd;
                    margin: 2px;
                    transform: scale(0.98);
                }
            """)

            # Start long press timer
            self.long_press_timer.start(self.long_press_duration)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_pressed:
            self.is_pressed = False

            # Restore original stylesheet
            if self.original_stylesheet is not None:
                self.setStyleSheet(self.original_stylesheet)

            # Stop long press timer
            if self.long_press_timer.isActive():
                self.long_press_timer.stop()
                # If timer was still active, it's a normal click
                self.clicked.emit()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events to cancel long press if mouse moves too far."""
        if self.is_pressed and self.press_start_pos is not None:
            # Calculate distance moved
            current_pos = event.position().toPoint()
            distance = (current_pos - self.press_start_pos).manhattanLength()

            # Cancel long press if moved too far (more than 15 pixels for touch-friendly)
            if distance > 15 and self.long_press_timer.isActive():
                self.long_press_timer.stop()
                self.is_pressed = False
                # Restore original stylesheet
                if self.original_stylesheet is not None:
                    self.setStyleSheet(self.original_stylesheet)
        super().mouseMoveEvent(event)

    def _on_long_press_timeout(self):
        """Called when long press timer expires."""
        if self.is_pressed:
            self.is_pressed = False
            self.long_pressed.emit()
            print(f"Long press detected on thumbnail: {self.filename}")

    def leaveEvent(self, event):
        """Handle mouse leave events to cancel long press."""
        if self.long_press_timer.isActive():
            self.long_press_timer.stop()
        self.is_pressed = False
        # Restore original stylesheet
        if self.original_stylesheet is not None:
            self.setStyleSheet(self.original_stylesheet)
        super().leaveEvent(event)
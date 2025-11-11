from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ThumbnailWidget(QWidget):
    """Custom widget to display a thumbnail image, file name, and last modified date."""

    # Add the clicked signal definition
    clicked = pyqtSignal()

    def __init__(self, filename, pixmap, timestamp, parent=None):
        super().__init__(parent)

        # Store data for potential use in signal handlers
        self.filename = filename
        self.timestamp = timestamp
        self.original_pixmap = pixmap

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
        layout.addWidget(date_label)

    def mousePressEvent(self, event):
        """Handle mouse press events to emit clicked signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
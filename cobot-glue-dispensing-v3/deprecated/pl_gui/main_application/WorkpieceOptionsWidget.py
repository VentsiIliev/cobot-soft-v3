import os
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSizePolicy)
from PyQt6.QtGui import QPixmap

# Assuming your resource directory structure
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
print("Resource directory:", RESOURCE_DIR)
CAMERA_ICON_PATH = os.path.join(RESOURCE_DIR, "createWorkpieceOptions", "camera.png")
# D:\GitHub\cobot-soft-v2\cobot-soft-glue-dispencing-v2\pl_gui\main_application\resources\createWorkpieceOptions
print("Camera icon path:", CAMERA_ICON_PATH)
DXF_ICON_PATH = os.path.join(RESOURCE_DIR, "createWorkpieceOptions", "dxf_file.png")


class ResponsiveWorkpieceOptionButton(QPushButton):
    """Responsive custom button for workpiece options with large icon and text"""

    def __init__(self, icon_path, text, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self.text = text
        self.base_width = 200
        self.base_height = 180
        self.setup_button()

    def setup_button(self):
        # Set minimum size but allow growth
        self.setMinimumSize(150, 120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 2px solid #d0d0d0;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
                color: #333;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #b0b0b0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
                border-color: #a0a0a0;
            }
        """)

        # Create layout for icon and text
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon label
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Text label
        if self.text is not None and self.text != "":
            self.text_label = QLabel(self.text)
            self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.text_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
            self.text_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

            layout.addWidget(self.text_label, 0)  # Text takes minimal space
        layout.addWidget(self.icon_label, 1)  # Give icon more space

        self.update_icon()

    def update_icon(self):
        """Update icon size based on current button size"""
        button_size = self.size()
        # Calculate icon size as percentage of button size
        icon_size = min(button_size.width() * 0.4, button_size.height() * 0.5, 100)
        icon_size = max(icon_size, 40)  # Minimum icon size

        if os.path.exists(self.icon_path):
            pixmap = QPixmap(self.icon_path)
            scaled_pixmap = pixmap.scaled(
                int(icon_size), int(icon_size),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.icon_label.setPixmap(scaled_pixmap)
        else:
            # Fallback colored rectangle
            self.icon_label.setFixedSize(int(icon_size), int(icon_size))
            self.icon_label.setStyleSheet(f"""
                background-color: #4CAF50;
                border-radius: {int(icon_size * 0.125)}px;
            """)

    def resizeEvent(self, event):
        """Handle resize events to update icon size"""
        super().resizeEvent(event)
        self.update_icon()


class WorkpieceOptionsWidget(QWidget):
    """Responsive widget with two large option buttons for creating workpieces"""

    # Signals
    create_workpiece_camera_selected = pyqtSignal()
    create_workpiece_dxf_selected = pyqtSignal()

    def __init__(self, parent=None, controller=None):
        self.controller = controller
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the responsive user interface"""
        # Remove fixed size - make it fully responsive
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(400, 250)

        # Main container for centering
        main_container = QWidget()
        main_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Outer layout for centering the main container
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.addStretch(1)  # Top stretch

        # Horizontal centering layout
        h_center_layout = QHBoxLayout()
        h_center_layout.addStretch(1)  # Left stretch
        h_center_layout.addWidget(main_container, 0)  # Don't stretch the content
        h_center_layout.addStretch(1)  # Right stretch

        outer_layout.addLayout(h_center_layout, 0)  # Don't stretch vertically
        outer_layout.addStretch(1)  # Bottom stretch

        # Main content layout
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Title
        self.title_label = QLabel("Create Workpiece")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        """)

        # Buttons container
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(30)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Camera button
        self.camera_button = ResponsiveWorkpieceOptionButton(CAMERA_ICON_PATH, "")
        self.camera_button.clicked.connect(self.on_camera_selected)
        self.camera_button.setMaximumSize(250, 200)  # Limit maximum size

        # DXF button
        self.dxf_button = ResponsiveWorkpieceOptionButton(DXF_ICON_PATH, "")
        self.dxf_button.clicked.connect(self.on_dxf_selected)
        self.dxf_button.setMaximumSize(250, 200)  # Limit maximum size

        buttons_layout.addWidget(self.camera_button)
        buttons_layout.addWidget(self.dxf_button)

        # Add to main layout
        # main_layout.addWidget(self.title_label)
        main_layout.addWidget(buttons_container)

        # Widget styling
        main_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 15px;
            }
        """)

        # Set a preferred size for the main container
        main_container.setMinimumSize(400, 320)
        main_container.setMaximumSize(600, 400)

    def resizeEvent(self, event):
        """Handle resize events for responsive text sizing"""
        super().resizeEvent(event)
        self.update_text_sizes()

    def update_text_sizes(self):
        """Update text sizes based on widget size"""
        widget_width = self.width()

        # Scale font sizes based on widget width
        if widget_width < 500:
            title_size = 20
        elif widget_width < 700:
            title_size = 24
        else:
            title_size = 28

        self.title_label.setStyleSheet(f"""
            font-size: {title_size}px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        """)



    def on_camera_selected(self):
        """Handle camera button click"""
        self.create_workpiece_camera_selected.emit()
        print("Camera option selected")

    def on_dxf_selected(self):
        """Handle DXF button click"""
        self.create_workpiece_dxf_selected.emit()
        print("DXF option selected")


# Alternative responsive compact inline version
class ResponsiveCompactWorkpieceOptions(QWidget):
    """Responsive compact version that can be embedded inline"""

    camera_selected = pyqtSignal()
    dxf_selected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup responsive compact UI"""
        # Main centering layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.addStretch(1)

        # Horizontal centering layout for buttons
        h_layout = QHBoxLayout()
        h_layout.addStretch(1)

        # Buttons container
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(20)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Camera button
        self.camera_button = ResponsiveWorkpieceOptionButton(CAMERA_ICON_PATH, "Camera")
        self.camera_button.setMinimumSize(120, 100)
        self.camera_button.setMaximumSize(180, 150)
        self.camera_button.clicked.connect(self.camera_selected.emit)

        # DXF button
        self.dxf_button = ResponsiveWorkpieceOptionButton(DXF_ICON_PATH, "DXF Upload")
        self.dxf_button.setMinimumSize(120, 100)
        self.dxf_button.setMaximumSize(180, 150)
        self.dxf_button.clicked.connect(self.dxf_selected.emit)

        buttons_layout.addWidget(self.camera_button)
        buttons_layout.addWidget(self.dxf_button)

        h_layout.addWidget(buttons_container)
        h_layout.addStretch(1)

        main_layout.addLayout(h_layout)
        main_layout.addStretch(1)

        self.setStyleSheet("background: transparent;")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = WorkpieceOptionsWidget()
    widget.show()
    sys.exit(app.exec())
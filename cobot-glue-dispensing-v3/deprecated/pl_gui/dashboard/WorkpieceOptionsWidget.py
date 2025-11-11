import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QDialog, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QPixmap, QIcon


class WorkpieceOptionsWidget(QDialog):
    # Signals to emit when options are selected
    camera_selected = pyqtSignal()
    dxf_selected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Workpiece")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.setupUI()

    def setupUI(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Title section
        title_layout = QVBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("Create Workpiece")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel("Choose how you'd like to create your workpiece")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666666; margin-bottom: 10px;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        # Options section
        options_layout = QVBoxLayout()
        options_layout.setSpacing(15)

        # Camera option button
        self.camera_btn = self.create_option_button(
            "📷", "Camera Capture",
            "Take a photo of your workpiece",
            "#3B82F6"
        )
        self.camera_btn.clicked.connect(self.on_camera_selected)

        # DXF upload option button
        self.dxf_btn = self.create_option_button(
            "📁", "DXF Upload",
            "Upload a DXF file",
            "#10B981"
        )
        self.dxf_btn.clicked.connect(self.on_dxf_selected)

        options_layout.addWidget(self.camera_btn)
        options_layout.addWidget(self.dxf_btn)

        # Add to main layout
        main_layout.addLayout(title_layout)
        main_layout.addLayout(options_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

        # Apply overall styling
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                border-radius: 10px;
            }
        """)

    def create_option_button(self, icon, title, description, color):
        """Create a styled option button with icon, title and description"""
        button = QPushButton()
        button.setFixedHeight(80)
        button.setCursor(Qt.CursorShape.PointingHandCursor)

        # Create button layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(20, 15, 20, 15)
        button_layout.setSpacing(15)

        # Icon label
        icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(24)
        icon_label.setFont(icon_font)
        icon_label.setFixedSize(50, 50)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 25px;
                color: white;
            }}
        """)

        # Text section
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)

        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #666666; font-size: 12px;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)

        # Create a widget to hold the layout
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.addWidget(icon_label)
        content_layout.addLayout(text_layout)
        content_layout.addStretch()
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Set the widget as button's layout (this is a workaround)
        button_inner_layout = QHBoxLayout(button)
        button_inner_layout.addWidget(content_widget)
        button_inner_layout.setContentsMargins(0, 0, 0, 0)

        # Style the button
        button.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid #E5E7EB;
                border-radius: 10px;
                background-color: white;
                text-align: left;
            }}
            QPushButton:hover {{
                border-color: {color};
                background-color: #F9FAFB;
            }}
            QPushButton:pressed {{
                background-color: #F3F4F6;
            }}
        """)

        return button

    def on_camera_selected(self):
        """Handle camera option selection"""
        self.camera_selected.emit()
        self.accept()  # Close dialog

    def on_dxf_selected(self):
        """Handle DXF upload option selection"""
        self.dxf_selected.emit()
        self.accept()  # Close dialog


# Example usage and integration with your main class
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout()

        # Example button to trigger the workpiece creation
        create_btn = QPushButton("Create Workpiece")
        create_btn.clicked.connect(self.onCreateWorkpiece)

        layout.addWidget(create_btn)
        self.setLayout(layout)
        self.setWindowTitle("Main Application")
        self.resize(300, 200)

    def onCreateWorkpiece(self):
        """Your main method - shows the options widget"""
        dialog = WorkpieceOptionsWidget(self)

        # Connect signals to your methods
        dialog.camera_selected.connect(self.onCameraCapture)
        dialog.dxf_selected.connect(self.onDxfUpload)

        dialog.exec()

    def onCameraCapture(self):
        """Handle camera capture functionality"""
        print("Camera capture selected!")
        # Add your camera capture code here

    def onDxfUpload(self):
        """Handle DXF file upload functionality"""
        print("DXF upload selected!")
        # Add your DXF upload code here


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect,
    QFrame
)


class CustomWarningDialog(QDialog):
    """Custom modern warning dialog to replace QMessageBox"""

    def __init__(self, parent=None, title="Warning", message="", info_text=""):
        super().__init__(parent)
        self.result_value = None
        self.setup_dialog(title, message, info_text)

    def setup_dialog(self, title, message, info_text):
        """Setup the custom dialog styling and layout"""
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(500, 300)

        # Remove window frame for custom styling
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create main container with rounded corners
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 2px solid #d3d3d3;
            }
        """)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(0, 0, 0, 100))
        container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        container_layout.setSpacing(20)

        # Header with warning icon and title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        # Warning icon (using emoji for simplicity)
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                color: #905BA9;
            }
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 24px;
                font-weight: bold;
                color: #333;
            }
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        container_layout.addLayout(header_layout)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("""
            QFrame {
                background-color: #d3d3d3;
                border: none;
                height: 1px;
            }
        """)
        container_layout.addWidget(line)

        # Main message
        message_label = QLabel(message)
        message_label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 10px 0;
            }
        """)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(message_label)

        # Info text (if provided)
        if info_text:
            info_label = QLabel(info_text)
            info_label.setStyleSheet("""
                QLabel {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 14px;
                    color: #666;
                    padding: 5px 0;
                }
            """)
            info_label.setWordWrap(True)
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(info_label)

        container_layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedSize(120, 45)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #666;
                border: 2px solid #d3d3d3;
                border-radius: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #905BA9;
                color: #905BA9;
            }
            QPushButton:pressed {
                background-color: #e8e8e8;
            }
        """)
        self.cancel_button.clicked.connect(self.reject_dialog)

        # OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.setFixedSize(120, 45)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #905BA9, stop:1 #7A4D96);
                color: white;
                border: none;
                border-radius: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #A16BB7, stop:1 #905BA9);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7A4D96, stop:1 #6A4386);
            }
        """)
        self.ok_button.clicked.connect(self.accept_dialog)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        container_layout.addLayout(button_layout)

        main_layout.addWidget(container)
        self.setLayout(main_layout)

        # Center the dialog on parent
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

    def accept_dialog(self):
        """Handle OK button click"""
        self.result_value = "OK"
        self.accept()

    def reject_dialog(self):
        """Handle Cancel button click"""
        self.result_value = "Cancel"
        self.reject()

    def get_result(self):
        """Get the result after dialog closes"""
        return self.result_value
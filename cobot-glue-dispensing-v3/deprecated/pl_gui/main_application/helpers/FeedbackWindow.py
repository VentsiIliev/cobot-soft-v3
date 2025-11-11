from PyQt6.QtWidgets import (
    QApplication, QDialog, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize
import os

INFO_MESSAGE = "info"
WARNING_MESSAGE = "warning"
ERROR_MESSAGE = "error"

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources","pl_ui_icons","messages")


class FeedbackWindow(QDialog):
    def __init__(self, image_path=None, message="", message_type="info"):
        super().__init__()

        self.setWindowTitle("Feedback")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.resize(360, 360)
        self.setMinimumSize(280, 280)
        self.setMaximumSize(500, 500)

        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.setGeometry(x, y, self.width(), self.height())
        self.setStyleSheet("background:#f5f5f5;")

        icon_paths = {
            "info": os.path.join(RESOURCE_DIR, "DESCRIPTION_ICON.png"),
            "warning": os.path.join(RESOURCE_DIR, "POP_UP_NOTIFICATION_ICON.png"),
            "error": os.path.join(RESOURCE_DIR, "DESCRIPTION_ICON.png"),
        }

        # === Top icon
        top_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_pixmap = QPixmap(icon_paths.get(message_type, icon_paths["info"]))
        icon_label.setPixmap(icon_pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        top_layout.addWidget(icon_label)
        top_layout.addStretch()

        # === Main content (image or message)
        content_widget = QLabel()
        content_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_widget.setWordWrap(True)

        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            content_widget.setPixmap(
                pixmap.scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        elif message:
            content_widget.setText(message)
            content_widget.setStyleSheet("font-size: 16px; color: #333;")
        else:
            content_widget.setText("No content to display.")
            content_widget.setStyleSheet("font-size: 16px; color: #999;")

        # === OK button
        ok_button = QPushButton()
        ok_button.setIcon(QIcon(os.path.join(RESOURCE_DIR, "ACCEPT_BUTTON.png")))
        ok_button.setIconSize(QSize(64, 64))
        ok_button.setStyleSheet("border:none;")
        ok_button.setFixedSize(64, 64)
        ok_button.clicked.connect(self.accept)

        # === Layout
        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(content_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

    def show_feedback(self):
        self.exec()

import os
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QParallelAnimationGroup, \
    QPoint
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QColor, QPixmap, QIcon
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QSize

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), 'resources')
MENU_ICON_PATH = os.path.join(RESOURCES_DIR, 'menu_icon.png')


class FloatingFolderIcon(QPushButton):
    """Material Design floating action button for folder icon"""

    clicked_signal = pyqtSignal()

    def __init__(self, folder_name, parent=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.setFixedSize(80, 80)  # Material Design FAB size
        self.setup_ui()

    def setup_ui(self):
        """Setup Material Design floating action button"""
        self.setStyleSheet("""
            QPushButton {
                background: #6750A4;
                border: none;
                border-radius: 40px;
                font-size: 20px;
                font-weight: 500;
                color: white;
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                padding: 12px;
            }
            QPushButton:hover {
                background: #7965AF;
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background: #5A3D99;
                transform: scale(0.95);
            }
        """)

        # Scale icon to fit with padding - much smaller than button size
        icon_size = 48  # Leaves 16px padding on each side (80 - 48 = 32, divided by 2 = 16px padding)

        # Create properly sized icon
        if os.path.exists(MENU_ICON_PATH):
            pixmap = QPixmap(MENU_ICON_PATH)
            if not pixmap.isNull():
                # Scale pixmap maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    icon_size, icon_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setIcon(QIcon(scaled_pixmap))
            else:
                # Fallback to text if image fails to load
                self.setText("☰")
        else:
            # Fallback to text if file doesn't exist
            self.setText("☰")

        # Set icon size for the button
        self.setIconSize(QSize(icon_size, icon_size))

        # Clear any text if icon loaded successfully
        if not self.icon().isNull():
            self.setText("")

        self.setToolTip(f"Open {self.folder_name} folder")

        # Material Design elevation shadow
        try:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(24)
            shadow.setColor(QColor(0, 0, 0, 60))  # Material Design shadow
            shadow.setOffset(0, 8)
            self.setGraphicsEffect(shadow)
        except Exception as e:
            print(f"Shadow effect failed: {e}")

        self.clicked.connect(self.clicked_signal.emit)

    def show_with_animation(self):
        """Material Design scale-in animation"""
        self.show()
        self.raise_()

        start_pos = self.pos() + QPoint(0, 16)
        end_pos = self.pos()

        start_size = QSize(0, 0)
        end_size = self.size()

        start_rect = QRect(start_pos, start_size)
        end_rect = QRect(end_pos, end_size)

        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(300)  # Material Design timing
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)  # Material easing

        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(300)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(self.anim)
        self.anim_group.addAnimation(self.fade_anim)
        self.anim_group.start()

    def hide_with_animation(self):
        """Material Design scale-out animation"""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = QWidget()
    window.setStyleSheet("""
        QWidget {
            background-color: #f5f5f5;
        }
    """)
    layout = QVBoxLayout(window)

    folder_icon = FloatingFolderIcon("Test Folder")
    folder_icon.clicked_signal.connect(lambda: print("Folder icon clicked!"))
    layout.addWidget(folder_icon)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    window.setWindowTitle("Floating Folder Icon Example")
    window.resize(300, 200)
    window.show()

    sys.exit(app.exec())
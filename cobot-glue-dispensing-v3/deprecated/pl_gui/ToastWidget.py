from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint
from PyQt6.QtGui import QFontMetrics

class ToastWidget(QWidget):
    def __init__(self, parent=None, message="", duration=3000):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.ToolTip |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.message = message
        self.duration = duration  # milliseconds

        self.label = QLabel(message, self)
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                padding: 20px 40px;          /* Increased padding */
                background-color: rgba(50, 50, 50, 220);
                border-radius: 15px;         /* Slightly larger radius */
                font-size: 18pt;             /* Larger font */
                font-weight: bold;
            }
        """)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.adjustSize()

        # Calculate size based on text and padding
        fm = QFontMetrics(self.label.font())
        text_width = fm.horizontalAdvance(message)
        text_height = fm.height()

        width = text_width + 80   # padding left+right (40*2)
        height = text_height + 40 # padding top+bottom (20*2)
        self.resize(width, height)
        self.label.resize(width, height)

        self.animation = QPropertyAnimation(self)
        self.animation.setDuration(800)

    def show(self):
        if self.parent():
            parent = self.parent()
            x = (parent.width() - self.width()) // 2
            y = (parent.height() - self.height()) // 2  # vertically center
            self.move(parent.mapToGlobal(parent.rect().topLeft()) + QPoint(x, y))
        super().show()

        self.setWindowOpacity(1.0)

        QTimer.singleShot(self.duration, self.fade_out)

    def fade_out(self):
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.close)
        self.animation.start()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QMainWindow
    import sys

    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.resize(600, 400)
    main_window.show()

    toast = ToastWidget(parent=main_window, message="Hello, this is a larger centered toast!", duration=3000)
    toast.show()

    sys.exit(app.exec())

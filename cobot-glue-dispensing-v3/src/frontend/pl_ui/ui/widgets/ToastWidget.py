from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QWidget, QLabel


class ToastWidget(QWidget):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        message: str = "",
        duration: int = 3000,
    ) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.ToolTip
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.message: str = message
        self.duration: int = duration  # milliseconds

        self.label: QLabel = QLabel(message, self)
        self.label.setStyleSheet(
            """
            QLabel {
                color: white;
                padding: 20px 40px;          /* Increased padding */
                background-color: rgba(50, 50, 50, 220);
                border-radius: 15px;         /* Slightly larger radius */
                font-size: 18pt;             /* Larger font */
                font-weight: bold;
            }
        """
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.adjustSize()

        # Calculate size based on text and padding
        fm: QFontMetrics = QFontMetrics(self.label.font())
        text_width: int = fm.horizontalAdvance(message)
        text_height: int = fm.height()

        width: int = text_width + 80   # padding left+right (40*2)
        height: int = text_height + 40 # padding top+bottom (20*2)
        self.resize(width, height)
        self.label.resize(width, height)

        self.animation: QPropertyAnimation = QPropertyAnimation(self)
        self.animation.setDuration(800)

    def show(self) -> None:  # type: ignore[override]
        if self.parent():
            parent: QWidget = self.parentWidget()
            x: int = (parent.width() - self.width()) // 2
            y: int = (parent.height() - self.height()) // 2  # vertically center
            self.move(parent.mapToGlobal(parent.rect().topLeft()) + QPoint(x, y))
        super().show()

        self.setWindowOpacity(1.0)
        QTimer.singleShot(self.duration, self.fade_out)

    def fade_out(self) -> None:
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.close)
        self.animation.start()





from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QPropertyAnimation, QPoint, QEasingCurve

class Drawer(QWidget):
    def __init__(self, parent=None, animation_duration=300, side="right"):
        super().__init__(parent)
        self.animation_duration = animation_duration
        self.side = side  # 'left' or 'right'
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(self.animation_duration)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.is_open = False
        self.heightOffset = 0  # Offset for height adjustment if needed


    def toggle(self):
        """Animate drawer open/close from left or right, respecting heightOffset"""
        if not self.parent:
            return

        parent_rect = self.parent().rect()
        drawer_width = self.width()
        y = self.heightOffset

        if self.side == "right":
            start_x = parent_rect.width() - drawer_width if self.is_open else parent_rect.width()
            end_x = parent_rect.width() if self.is_open else parent_rect.width() - drawer_width
        else:  # left
            start_x = 0 if self.is_open else -drawer_width
            end_x = -drawer_width if self.is_open else 0

        target_pos = QPoint(end_x, y)

        self.setVisible(True)
        self.animation.stop()
        self.animation.setStartValue(QPoint(start_x, y))
        self.animation.setEndValue(target_pos)
        self.animation.start()
        self.is_open = not self.is_open

        if self.is_open:
            self.raise_()

    def resize_to_parent_height(self):
        """Adjust height and position based on parent size and drawer side, respecting heightOffset"""
        if not self.parent():
            return

        parent_height = self.parent().height()
        y = self.heightOffset
        self.setFixedHeight(parent_height - y)

        if self.side == "right":
            x = self.parent().width() - self.width() if self.is_open else self.parent().width()
        else:
            x = 0 if self.is_open else -self.width()

        self.move(x, y)
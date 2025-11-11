
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt, QPointF

class Ruler(QWidget):
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(parent)
        self.orientation = orientation
        self.scale_factor = 1.0
        self.translation = QPointF(0, 0)
        self.ruler_color = QColor(245, 245, 245)
        self.text_color = QColor(40, 40, 40)
        self.tick_color = QColor(100, 100, 100)
        self.font = QFont("Arial", 8)
        if orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(20)
        else:
            self.setFixedWidth(30)

    def update_view(self, scale_factor, translation):
        self.scale_factor = scale_factor
        self.translation = translation
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.ruler_color)
        painter.setPen(QPen(self.tick_color, 1))
        painter.setFont(self.font)

        step = 50  # base logical unit (in image pixels)
        step_screen = step * self.scale_factor
        if step_screen < 25:
            step *= 2
            step_screen = step * self.scale_factor
        elif step_screen > 100:
            step /= 2
            step_screen = step * self.scale_factor

        if self.orientation == Qt.Orientation.Horizontal:
            self.draw_horizontal(painter, step)
        else:
            self.draw_vertical(painter, step)

    def draw_horizontal(self, painter, step):
        height = self.height()
        width = self.width()
        start_x = -self.translation.x() % (step * self.scale_factor)
        base_value = int(-self.translation.x() / self.scale_factor // step * step)
        for i in range(int(width / (step * self.scale_factor)) + 3):
            x = start_x + i * step * self.scale_factor
            value = base_value + i * step
            painter.drawLine(int(x), height, int(x), height - 8)
            painter.drawText(int(x) + 2, height - 2, f"{int(value)}")

    def draw_vertical(self, painter, step):
        height = self.height()
        width = self.width()
        start_y = -self.translation.y() % (step * self.scale_factor)
        base_value = int(-self.translation.y() / self.scale_factor // step * step)
        for i in range(int(height / (step * self.scale_factor)) + 3):
            y = start_y + i * step * self.scale_factor
            value = base_value + i * step
            painter.drawLine(width, int(y), width - 8, int(y))
            painter.save()
            painter.translate(width - 2, int(y) - 2)
            painter.rotate(-90)
            painter.drawText(0, 0, f"{int(value)}")
            painter.restore()
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QLabel, QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, \
    QApplication
from PyQt6.QtGui import QPen, QPainter
from PyQt6.QtCore import Qt, QLineF
import sys


class DrawingCanvas(QGraphicsView):
    def __init__(self, scene, coord_label):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene = scene
        self.coord_label = coord_label
        self.start_point = None
        self.setMouseTracking(True)
        self.draw_axes()

        # These will be used to update the lines dynamically
        self.horizontal_line = None
        self.vertical_line = None
        self.line_to_x_ruler = None
        self.line_to_y_ruler = None

    def draw_axes(self):
        pen = QPen(Qt.GlobalColor.gray, 0.5, Qt.PenStyle.DashLine)

        # Draw X-axis at top (increasing to the right)
        self.scene.addLine(0, 0, 1000, 0, pen)  # X-axis (horizontal, top)

        # Draw Y-axis at left (increasing downward)
        self.scene.addLine(0, 0, 0, 600, pen)  # Y-axis (vertical, left)

    def draw_cursor_lines(self, x, y):
        # Remove previous horizontal line
        if self.horizontal_line:
            self.scene.removeItem(self.horizontal_line)
        # Draw new horizontal line
        self.horizontal_line = self.scene.addLine(0, y, 1000, y, QPen(Qt.GlobalColor.red))

        # Remove previous vertical line
        if self.vertical_line:
            self.scene.removeItem(self.vertical_line)
        # Draw new vertical line
        self.vertical_line = self.scene.addLine(x, 0, x, 600, QPen(Qt.GlobalColor.red))

        # Remove previous line to X ruler
        if self.line_to_x_ruler:
            self.scene.removeItem(self.line_to_x_ruler)
        # Draw line connecting cursor to X ruler
        self.line_to_x_ruler = self.scene.addLine(x, 0, x, y, QPen(Qt.GlobalColor.blue))

        # Remove previous line to Y ruler
        if self.line_to_y_ruler:
            self.scene.removeItem(self.line_to_y_ruler)
        # Draw line connecting cursor to Y ruler
        self.line_to_y_ruler = self.scene.addLine(0, y, x, y, QPen(Qt.GlobalColor.blue))

    def mouseMoveEvent(self, event):
        point = self.mapToScene(event.pos())

        # Update the cursor label with scene coordinates.
        self.coord_label.setText(f"Cursor: ({point.x():.1f}, {point.y():.1f})")

        # Draw lines indicating cursor position
        self.draw_cursor_lines(point.x(), point.y())


class AxisWidget(QWidget):
    def __init__(self, axis_type='x', parent=None):
        super().__init__(parent)
        self.axis_type = axis_type
        self.setFixedHeight(50 if axis_type == 'x' else 600)  # X-axis is horizontal, Y-axis is vertical
        self.setFixedWidth(1000 if axis_type == 'x' else 50)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(Qt.GlobalColor.black))

        if self.axis_type == 'x':  # X-axis (horizontal)
            for x in range(0, 1001, 100):
                painter.drawText(x, 20, str(x))  # Draw X values
            painter.drawLine(0, 0, 1000, 0)  # X-axis line

        elif self.axis_type == 'y':  # Y-axis (vertical)
            for y in range(0, 601, 100):  # Adjust for the scene height
                painter.drawText(5, y + 10, str(y))  # Y values increase downward
            painter.drawLine(0, 0, 0, 600)  # Y-axis line


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D Vector Drawing with Axis Widgets")
        self.resize(800, 600)

        self.scene = QGraphicsScene(0, 0, 800, 600)
        self.coord_label = QLabel("Cursor: (0, 0)")
        self.canvas = DrawingCanvas(self.scene, self.coord_label)

        # Create axis widgets
        self.x_axis_widget = AxisWidget(axis_type='x')
        self.y_axis_widget = AxisWidget(axis_type='y')

        # Layouts
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        # Arrange layout
        top_layout.addWidget(self.y_axis_widget)  # Y-axis widget on the left
        top_layout.addWidget(self.canvas)  # Drawing canvas in the center

        main_layout.addWidget(self.x_axis_widget)  # X-axis widget on top
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.coord_label)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

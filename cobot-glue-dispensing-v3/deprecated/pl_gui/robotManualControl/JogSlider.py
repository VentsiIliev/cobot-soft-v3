from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider


class JogSlider(QWidget):
    """Custom slider for jog step size"""

    def __init__(self, label_text="Step", parent=None):
        super().__init__(parent)
        self.initUI(label_text)

    def initUI(self, label_text):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Label
        self.label = QLabel(label_text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(self.label)

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(1, 50)
        self.slider.setValue(5)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(10)
        layout.addWidget(self.slider)

        # Value label
        self.value_label = QLabel("5 mm")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.value_label)

        # Connect slider to label update
        self.slider.valueChanged.connect(self.updateValueLabel)

        self.setLayout(layout)

    def updateValueLabel(self, value):
        """Update the value display label"""
        self.value_label.setText(f"{value} mm")

    def value(self):
        """Get current slider value"""
        return self.slider.value()

    def setValue(self, value):
        """Set slider value"""
        self.slider.setValue(value)
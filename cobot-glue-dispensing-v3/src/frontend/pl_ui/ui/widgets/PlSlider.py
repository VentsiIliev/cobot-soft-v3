import os
from PyQt6.QtWidgets import QWidget, QSlider, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources", "pl_ui_icons")
MINUS_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "MINUS_BUTTON.png")
PLUS_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "PLUS_BUTTON.png")


class PlSlider(QWidget):
    def __init__(self, orientation=Qt.Orientation.Horizontal, label_text="", parent=None):
        super().__init__(parent)

        self.setMaximumWidth(600)  # Example: Max width set to 400px
        self.setMaximumHeight(200)  # Example: Max height set to 100px

        # Initialize widgets
        self._initialize_widgets(orientation, label_text)

        # Set layout
        self._set_layout()

        # Connect signals
        self._connect_signals()

        # Set size policy to expand properly within layouts
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Create timers for continuous button press
        self.minus_timer = QTimer(self)
        self.plus_timer = QTimer(self)

        # Set the interval for the timers (e.g., 100ms)
        self.minus_timer.setInterval(100)
        self.plus_timer.setInterval(100)

        # Connect the timers to the actions
        self.minus_timer.timeout.connect(self.decrease_value)
        self.plus_timer.timeout.connect(self.increase_value)
        self.updateValueCallback = None

    def _initialize_widgets(self, orientation, label_text):
        """Initialize the widgets (slider, buttons, labels)"""
        # Create a label to describe the setting
        self.label = QLabel(label_text, self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.setStyleSheet("background-color: transparent;")

        # Create the slider
        self.slider = QSlider(orientation)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(50)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(10)
        self._set_slider_styles()

        # Create buttons to increase and decrease the value with icons
        self.minus_button = self._create_button(MINUS_BUTTON_ICON_PATH)  # Icon for minus
        self.plus_button = self._create_button(PLUS_BUTTON_ICON_PATH)  # Icon for plus

        # Value label to display current value of slider
        self.value_label = QLabel(str(self.slider.value()), self)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setFixedWidth(50)  # Adjust fixed width for better fit
        self.value_label.setStyleSheet("background-color: transparent;")  # Make background transparent

    def _set_slider_styles(self):
        """Set the style for the slider"""
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
              
                border: 1px solid #000000;
                height: 6px;
                background: #000000;
                margin: 0px;
            }

            QSlider::handle:horizontal {
                background: #905BA9;
                border: 1px solid #905BA9;
                width: 50px;
                height: 50px;
                margin: -22px 0px;
                border-radius: 25px;
            }
        """)

    def _create_button(self, icon_path):
        """Helper function to create buttons with icons"""
        button = QPushButton()
        button.setIcon(QIcon(icon_path))  # Set the icon from the given path
        button.setIconSize(QSize(30, 30))  # Resize icon as needed
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Make button responsive
        button.setStyleSheet("""
            background-color: transparent;  /* Remove background */
            border: none; /* Remove the button border */
            border-radius: 25px; /* Round the button corners */
        """)
        return button

    def _set_layout(self):
        """Set the layout of the widgets"""
        # Vertical layout for the label
        self.label_layout = QVBoxLayout()
        self.label_layout.addWidget(self.label)

        # Horizontal layout for buttons, slider, and value label
        self.controls_layout = QHBoxLayout()
        self.controls_layout.addWidget(self.minus_button)
        self.controls_layout.addWidget(self.slider)
        self.controls_layout.addWidget(self.plus_button)
        self.controls_layout.addWidget(self.value_label)

        # Stretch the slider to take available space
        self.controls_layout.setStretch(1, 1)

        # Main horizontal layout to combine both layouts with a controlled spacer
        self.main_layout = QHBoxLayout(self)
        self.main_layout.addLayout(self.label_layout)
        self.main_layout.addStretch(1)  # Add spacer with stretch factor 1
        self.main_layout.addLayout(self.controls_layout)

    def _connect_signals(self):
        """Connect the signals (slider value change and button clicks)"""
        self.slider.valueChanged.connect(self.update_value_label)
        self.minus_button.pressed.connect(self.start_decreasing_value)
        self.plus_button.pressed.connect(self.start_increasing_value)
        self.minus_button.released.connect(self.stop_decreasing_value)
        self.plus_button.released.connect(self.stop_increasing_value)


    def setDefaultValue(self, value):
        self.slider.setValue(value)

    def start_decreasing_value(self):
        """Start decreasing the slider value when the button is pressed"""
        self.minus_timer.start()

    def stop_decreasing_value(self):
        """Stop decreasing the slider value when the button is released"""
        self.minus_timer.stop()

    def start_increasing_value(self):
        """Start increasing the slider value when the button is pressed"""
        self.plus_timer.start()

    def stop_increasing_value(self):
        """Stop increasing the slider value when the button is released"""
        self.plus_timer.stop()

    def decrease_value(self):
        """Decrease the slider value"""
        value = self.slider.value()
        self.slider.setValue(value - 1)

    def increase_value(self):
        """Increase the slider value"""
        value = self.slider.value()
        self.slider.setValue(value + 1)

    def update_value_label(self):
        """Update the value label when slider value changes"""
        self.value_label.setText(str(self.slider.value()))
        if self.updateValueCallback is not None:
            self.updateValueCallback(self.label.text(),self.slider.value())



    def resizeEvent(self, event):
        """Adjust button sizes and slider width on resize event"""
        new_width = self.width()
        icon_size = int(new_width * 0.125)  # 12.5% of new window width
        slider_width = int(new_width * 0.4)  # 75% of new window width

        self.minus_button.setIconSize(QSize(icon_size, icon_size))
        self.plus_button.setIconSize(QSize(icon_size, icon_size))
        self.slider.setFixedWidth(slider_width)

        super().resizeEvent(event)


# Application to display the slider
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout

    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("PlSlider Example")
    window_layout = QVBoxLayout(window)

    # Create and add slider widget
    slider = PlSlider(label_text="Volume")
    window_layout.addWidget(slider)

    window.show()
    sys.exit(app.exec())

"""
Dialog for setting the length and angle of a line segment
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from src.frontend.pl_ui.ui.widgets.virtualKeyboard.VirtualKeyboard import FocusLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QDoubleValidator
import math


class SetLengthAndAngleDialog(QDialog):
    """Dialog for inputting desired line length and angle"""

    def __init__(self, current_length_mm, current_angle_deg=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Line Properties")
        self.setModal(False)

        # Window flags for touchscreen-friendly dialog
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        # Store the results
        self.new_length = None
        self.new_angle = None

        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Current values label
        if current_angle_deg is not None:
            current_label = QLabel(f"Current: {current_length_mm:.2f} mm @ {current_angle_deg:.1f}°", self)
        else:
            current_label = QLabel(f"Current Length: {current_length_mm:.2f} mm", self)
        current_label.setFont(QFont("Arial", 12))
        layout.addWidget(current_label)

        # Length input section
        length_label = QLabel("New Length (mm):", self)
        length_label.setFont(QFont("Arial", 12))
        layout.addWidget(length_label)

        self.length_input = FocusLineEdit(self)
        self.length_input.setFont(QFont("Arial", 14))
        self.length_input.setPlaceholderText("Enter length in mm")
        self.length_input.setText(f"{current_length_mm:.2f}")
        self.length_input.setMinimumHeight(40)

        # Only allow positive numbers
        length_validator = QDoubleValidator(0.01, 10000.0, 2, self)
        length_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.length_input.setValidator(length_validator)

        layout.addWidget(self.length_input)

        # Angle input section
        angle_label = QLabel("New Angle (degrees):", self)
        angle_label.setFont(QFont("Arial", 12))
        layout.addWidget(angle_label)

        self.angle_input = FocusLineEdit(self)
        self.angle_input.setFont(QFont("Arial", 14))
        self.angle_input.setPlaceholderText("Enter angle in degrees")
        if current_angle_deg is not None:
            self.angle_input.setText(f"{current_angle_deg:.1f}")
        self.angle_input.setMinimumHeight(40)

        # Allow any angle (-360 to 360)
        angle_validator = QDoubleValidator(-360.0, 360.0, 2, self)
        angle_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.angle_input.setValidator(angle_validator)

        layout.addWidget(self.angle_input)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.setFont(QFont("Arial", 12))
        self.ok_button.setMinimumHeight(40)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
        """)
        self.ok_button.clicked.connect(self._on_ok_clicked)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setFont(QFont("Arial", 12))
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #9E9E9E;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Set minimum size
        self.setMinimumWidth(300)

        # Select all text in input for easy editing
        self.length_input.selectAll()
        self.length_input.setFocus()

    def _on_ok_clicked(self):
        """Validate and accept the input"""
        length_text = self.length_input.text().strip()
        angle_text = self.angle_input.text().strip()

        if not length_text:
            return

        try:
            length_value = float(length_text)
            if length_value <= 0:
                # Invalid length value, don't accept
                return

            self.new_length = length_value

            # Angle is optional
            if angle_text:
                try:
                    angle_value = float(angle_text)
                    self.new_angle = angle_value
                except ValueError:
                    # Invalid angle input, ignore it
                    self.new_angle = None
            else:
                self.new_angle = None

            self.accept()
        except ValueError:
            # Invalid length input, don't accept
            return

    def get_length(self):
        """Get the entered length value"""
        return self.new_length

    def get_angle(self):
        """Get the entered angle value (None if not entered)"""
        return self.new_angle
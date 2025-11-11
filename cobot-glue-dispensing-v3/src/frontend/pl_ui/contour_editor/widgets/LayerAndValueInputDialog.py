from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

from src.frontend.pl_ui.ui.widgets.virtualKeyboard.VirtualKeyboard import FocusDoubleSpinBox


class LayerAndValueInputDialog(QDialog):
    def __init__(self, dialog_title, layer_label, input_labels, input_defaults, input_ranges, parent=None):
        """
        A generic dialog to handle layer selection and value inputs (spacing or shrink offset).

        :param dialog_title: Title of the dialog (e.g., "Spray Pattern Settings")
        :param layer_label: Label for the layer selection (e.g., "Select layer type for zigzag pattern")
        :param input_labels: List of input field labels (e.g., ["Line grid spacing", "Shrink offset"])
        :param input_defaults: List of default values for the inputs (e.g., [20, 0.0])
        :param input_ranges: List of tuples for each input field's range (e.g., [(1, 1000), (0.0, 50.0)])
        :param parent: The parent widget (optional)
        """
        super().__init__(parent)

        self.setWindowTitle(dialog_title)
        self.setFixedSize(360, 220)

        layout = QVBoxLayout(self)

        # Layer selection
        self.layer_label = QLabel(layer_label)
        self.layer_label.setStyleSheet("color: black; font-size: 12px;")
        layout.addWidget(self.layer_label)

        self.layer_combo = QComboBox()
        self.layer_combo.addItems(["Contour", "Fill"])
        self.layer_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: black;
                border: 1px solid gray;
                padding: 4px;
            }
        """)
        layout.addWidget(self.layer_combo)

        # Add input fields dynamically based on the input_labels and defaults
        self.input_widgets = []
        for idx, label in enumerate(input_labels):
            input_label = QLabel(label)
            input_label.setStyleSheet("color: black; font-size: 12px;")
            layout.addWidget(input_label)

            if isinstance(input_defaults[idx], int):
                input_widget = FocusDoubleSpinBox()
                input_widget.setRange(*input_ranges[idx])
                input_widget.setValue(input_defaults[idx])
                input_widget.setSuffix(" mm")
            else:
                input_widget = FocusDoubleSpinBox()
                input_widget.setRange(*input_ranges[idx])
                input_widget.setValue(input_defaults[idx])
                input_widget.setSingleStep(0.1)
                input_widget.setSuffix(" mm")

            self.input_widgets.append(input_widget)
            layout.addWidget(input_widget)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setStyleSheet("QDialog { background-color: #f8f8ff; }")

    def get_values(self):
        """
        Returns the selected layer and the values from all input fields.
        The return is a tuple (layer, value1, value2, ...).
        """
        values = [self.layer_combo.currentText()]
        for widget in self.input_widgets:
            values.append(widget.value())
        return tuple(values)
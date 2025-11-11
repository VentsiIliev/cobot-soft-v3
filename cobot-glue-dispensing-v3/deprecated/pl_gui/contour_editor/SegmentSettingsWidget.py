from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSizePolicy, QPushButton
)
from API.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from API.shared.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey
from deprecated.pl_gui.virtualKeyboard.VirtualKeyboard import FocusDoubleSpinBox
default_settings = {
    GlueSettingKey.SPRAY_WIDTH.value: "10",
    GlueSettingKey.SPRAYING_HEIGHT.value: "120",
    GlueSettingKey.FAN_SPEED.value: "50",
    GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value: "1",
    GlueSettingKey.MOTOR_SPEED.value: "5000",
    GlueSettingKey.REVERSE_DURATION.value: "0.5",
    GlueSettingKey.SPEED_REVERSE.value: "10000",
    GlueSettingKey.RZ_ANGLE.value: "90",
    GlueSettingKey.GLUE_TYPE.value: "Type B",
    GlueSettingKey.GENERATOR_TIMEOUT.value: "5",
    GlueSettingKey.TIME_BEFORE_MOTION.value: "0.1",
    GlueSettingKey.TIME_BEFORE_STOP.value: "1.0",
    GlueSettingKey.REACH_START_THRESHOLD.value: "1.0",
    GlueSettingKey.REACH_END_THRESHOLD.value: "3.0",
    GlueSettingKey.GLUE_SPEED_COEFFICIENT.value: "40",

    RobotSettingKey.VELOCITY.value: "10",
    RobotSettingKey.ACCELERATION.value: "80",
}

class SegmentSettingsWidget(QWidget):
    def __init__(self, keys: list[str], combo_enums: list[list], parent=None,segment=None):
        super().__init__(parent)
        self.segment = segment
        if self.segment is not None:
            self.segmentSettings = self.segment.settings
        else:
            self.segmentSettings = None

        # self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.keys = keys
        self.combo_enums = {label: enum for label, enum in combo_enums}  # Convert to dict
        self.inputs = {}  # Dict[str, QWidget]
        self.init_ui()
        self.populate_values()


    def init_ui(self):
        layout = QVBoxLayout(self)

        for key in self.keys:
            row_layout = QHBoxLayout()

            label = QLabel(key)
            label.setMinimumWidth(150)
            row_layout.addWidget(label)

            if key in self.combo_enums:
                combo_box = QComboBox()
                combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

                enum_class = self.combo_enums[key]
                for enum_member in enum_class:
                    combo_box.addItem(enum_member.value)

                # Connect value change signal
                combo_box.currentTextChanged.connect(lambda val, k=key: self.on_value_changed(k, val))

                row_layout.addWidget(combo_box)
                self.inputs[key] = combo_box
            else:
                input_field = FocusDoubleSpinBox()
                input_field.setDecimals(3)
                input_field.setRange(-1e6, 1e6)
                input_field.setSingleStep(0.1)
                input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                input_field.valueChanged.connect(lambda val, k=key: self.on_value_changed(k, str(val)))
                row_layout.addWidget(input_field)
                self.inputs[key] = input_field

            layout.addLayout(row_layout)

        # Add "Get Values" button
        get_button = QPushButton("Save")
        get_button.clicked.connect(self.print_values)
        layout.addWidget(get_button)

        layout.addStretch()

        self.setLayout(layout)

    def populate_values(self):
        settings_source = self.segmentSettings if self.segmentSettings and self.segmentSettings != {} else default_settings

        for key, widget in self.inputs.items():
            value = settings_source.get(key, default_settings.get(key, ""))
            if isinstance(widget, FocusDoubleSpinBox):
                widget.setValue(float(str(value).replace(",", "")))
            elif isinstance(widget, QComboBox):
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)
    def on_value_changed(self, key: str, value: str):
        print(f"[Value Changed] {key}: {value}")

    def print_values(self):
        values = self.get_values()
        print("[All Values]", values)

    def get_values(self) -> dict:
        """Return a dictionary with key: input text or selected combo."""
        result = {}
        for key, widget in self.inputs.items():
            if isinstance(widget, FocusDoubleSpinBox):
                result[key] = widget.value()
            elif isinstance(widget, QComboBox):
                result[key] = widget.currentText()

        self.segment.set_settings(result)
        print("segment settings", self.segment.settings)

        return result



    def set_values(self, values: dict):
        """Set values from a dict of key: value."""
        for key, val in values.items():
            widget = self.inputs.get(key)
            if isinstance(widget, FocusDoubleSpinBox):
                widget.setValue(float(str(val).replace(",", "")))
            elif isinstance(widget, QComboBox):
                index = widget.findText(val)
                if index >= 0:
                    widget.setCurrentIndex(index)

    def clear(self):
        """Clear all input fields."""
        for widget in self.inputs.values():
            if isinstance(widget, FocusDoubleSpinBox):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)

if __name__ == "__main__":
    from API.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
    from API.shared.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey
    from deprecated.pl_gui.specific.enums.GlueType import GlueType

    from PyQt6.QtWidgets import QApplication
    import sys

    inputKeys = [key.value for key in GlueSettingKey]
    inputKeys.remove(GlueSettingKey.GLUE_TYPE.value)

    inputKeys.append(RobotSettingKey.VELOCITY.value)
    inputKeys.append(RobotSettingKey.ACCELERATION.value)

    comboEnums = [[GlueSettingKey.GLUE_TYPE.value, GlueType]]

    app = QApplication(sys.argv)
    widget = SegmentSettingsWidget(inputKeys + [GlueSettingKey.GLUE_TYPE.value], comboEnums)
    widget.show()
    sys.exit(app.exec())

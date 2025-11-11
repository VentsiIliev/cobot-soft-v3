
from src.frontend.pl_ui.ui.widgets.virtualKeyboard.VirtualKeyboard import VirtualKeyboardSingleton
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox,
    QSizePolicy, QPushButton, QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtCore import Qt
from modules.shared.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from modules.shared.shared.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey
# import qt DoubleSpinBox
from PyQt6.QtWidgets import QDoubleSpinBox
from src.frontend.pl_ui.ui.widgets.virtualKeyboard.VirtualKeyboard import FocusDoubleSpinBox
import json
import os
default_settings = {
    GlueSettingKey.SPRAY_WIDTH.value: "10",
    GlueSettingKey.SPRAYING_HEIGHT.value: "0",
    GlueSettingKey.FAN_SPEED.value: "100",
    GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value: "1",
    GlueSettingKey.MOTOR_SPEED.value: "500",
    GlueSettingKey.REVERSE_DURATION.value: "0.5",
    GlueSettingKey.SPEED_REVERSE.value: "3000",
    GlueSettingKey.RZ_ANGLE.value: "0",
    GlueSettingKey.GLUE_TYPE.value: "Type a",
    GlueSettingKey.GENERATOR_TIMEOUT.value: "5",
    GlueSettingKey.TIME_BEFORE_MOTION.value: "0.1",
    GlueSettingKey.TIME_BEFORE_STOP.value: "1.0",
    GlueSettingKey.REACH_START_THRESHOLD.value: "1.0",
    GlueSettingKey.REACH_END_THRESHOLD.value: "30.0",
    GlueSettingKey.GLUE_SPEED_COEFFICIENT.value: "5",
    GlueSettingKey.GLUE_ACCELERATION_COEFFICIENT.value: "0",
    GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value: "1.0",
    GlueSettingKey.INITIAL_RAMP_SPEED.value: "5000",
    GlueSettingKey.REVERSE_RAMP_STEPS.value: "1",
    GlueSettingKey.FORWARD_RAMP_STEPS.value: "3",

    RobotSettingKey.VELOCITY.value: "60",
    RobotSettingKey.ACCELERATION.value: "30",

}

class SegmentSettingsWidget(QWidget):
    save_requested = pyqtSignal()

    def __init__(self, keys: list[str], combo_enums: list[list], parent=None,segment=None,global_settings=False,pointManagerWidget=None):
        super().__init__(parent)
        self.parent=parent
        self.segment = segment
        if self.segment is not None:
            self.segmentSettings = self.segment.settings
        else:
            self.segmentSettings = None
        self.global_settings = global_settings
        self.pointManagerWidget = pointManagerWidget
        # self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.keys = keys
        self.combo_enums = {label: enum for label, enum in combo_enums}  # Convert to dict
        self.inputs = {}  # Dict[str, QWidget]
        self.init_ui()
        self.populate_values()
        self.vk = VirtualKeyboardSingleton.getInstance()
        self.vk.shown.connect(self.on_virtual_keyboard_shown)
        self.vk.hidden.connect(self.on_virtual_keyboard_hidden)

    def init_ui(self):
        from PyQt6.QtWidgets import QGroupBox
        main_layout = QVBoxLayout(self)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.adjustSize()

        content_widget = QWidget()
        content_widget.setMinimumWidth(400)
        scroll.setWidget(content_widget)
        layout = QVBoxLayout(content_widget)


        # === GROUP DEFINITIONS ===
        general_keys = [
            GlueSettingKey.SPRAY_WIDTH.value,
            GlueSettingKey.SPRAYING_HEIGHT.value,
            GlueSettingKey.GLUE_TYPE.value,
        ]

        pump_speed_adjustment_keys = [
            GlueSettingKey.GLUE_SPEED_COEFFICIENT.value,
            GlueSettingKey.GLUE_ACCELERATION_COEFFICIENT.value,
            ]

        forward_keys = [
            GlueSettingKey.FORWARD_RAMP_STEPS.value,
            GlueSettingKey.INITIAL_RAMP_SPEED.value,
            GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value,
            GlueSettingKey.MOTOR_SPEED.value,
        ]

        reverse_keys = [
            GlueSettingKey.REVERSE_DURATION.value,
            GlueSettingKey.SPEED_REVERSE.value,
            GlueSettingKey.REVERSE_RAMP_STEPS.value,
        ]

        robot_keys = [
            RobotSettingKey.VELOCITY.value,
            RobotSettingKey.ACCELERATION.value,
            GlueSettingKey.RZ_ANGLE.value,
        ]

        generator_keys = [
            # GlueSettingKey.FAN_SPEED.value,
            GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value,
            GlueSettingKey.GENERATOR_TIMEOUT.value,
            # GlueSettingKey.TIME_BEFORE_MOTION.value,
            # GlueSettingKey.TIME_BEFORE_STOP.value,
        ]

        reach_threshold_keys = [
            GlueSettingKey.REACH_START_THRESHOLD.value,
            GlueSettingKey.REACH_END_THRESHOLD.value,
        ]

        # --- Helper to build each section ---
        def build_group_box(title, keys):
            box = QGroupBox(title)
            grid = QGridLayout(box)
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(1, 1)
            grid.setHorizontalSpacing(12)
            grid.setVerticalSpacing(8)

            for idx, key in enumerate(keys):
                field_widget = QWidget()
                row_layout = QHBoxLayout(field_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)

                label = QLabel(key)
                label.setMinimumWidth(150)
                row_layout.addWidget(label)

                # ComboBox if enum exists
                if key in self.combo_enums:
                    combo_box = QComboBox()
                    combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                    enum_class = self.combo_enums[key]
                    for enum_member in enum_class:
                        combo_box.addItem(enum_member.value)
                    combo_box.currentTextChanged.connect(lambda val, k=key: self.on_value_changed(k, val))
                    row_layout.addWidget(combo_box)
                    self.inputs[key] = combo_box
                else:
                    # Numeric input field
                    spin = FocusDoubleSpinBox(parent=self.parent)
                    spin.setDecimals(3)
                    spin.setRange(-1e6, 1e6)
                    spin.setSingleStep(0.1)
                    spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                    spin.valueChanged.connect(lambda val, k=key: self.on_value_changed(k, str(val)))
                    row_layout.addWidget(spin)
                    self.inputs[key] = spin

                # place in grid (2 columns)
                row, col = divmod(idx, 2)
                grid.addWidget(field_widget, row, col)

            return box

        # --- Add grouped sections ---
        layout.addWidget(build_group_box("General Settings", general_keys))
        layout.addWidget(build_group_box("Forward Motion Settings", forward_keys))
        layout.addWidget(build_group_box("Reverse Motion Settings", reverse_keys))
        layout.addWidget(build_group_box("Robot Settings", robot_keys))
        layout.addWidget(build_group_box("Generator Settings", generator_keys))
        layout.addWidget(build_group_box("Reach Threshold Settings (mm)", reach_threshold_keys))
        layout.addWidget(build_group_box("Pump speed adjustment", pump_speed_adjustment_keys))

        layout.addStretch(1)

        # --- Save button ---
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.print_values)
        layout.addWidget(save_btn)

        main_layout.addWidget(scroll)

    def populate_values(self):
        # For global settings, always use the current default_settings
        if self.global_settings:
            settings_source = default_settings
        else:
            settings_source = self.segmentSettings if self.segmentSettings and self.segmentSettings != {} else default_settings

        for key, widget in self.inputs.items():
            value = settings_source.get(key, default_settings.get(key, ""))
            if isinstance(widget, FocusDoubleSpinBox):
                try:
                    widget.setValue(float(str(value).replace(",", "")) if str(value).strip() != "" else 0.0)
                except ValueError:
                    widget.setValue(0.0)
            elif isinstance(widget, QComboBox):
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)

    def refresh_global_values(self):
        """Refresh the widget with current default settings (useful for global settings dialog)"""
        if self.global_settings:
            self.populate_values()

    def on_value_changed(self, key: str, value: str):
        print(f"[Value Changed] {key}: {value}")
        # if self.global_settings:
        #     self.pointManagerWidget.update_all_segments_settings()


    def print_values(self):
        values = self.get_values()
        print("[All Values]", values)
        self.save_requested.emit()

    def get_values(self) -> dict:
        """Return a dictionary with key: input text or selected combo."""
        result = {}
        for key, widget in self.inputs.items():
            if isinstance(widget, FocusDoubleSpinBox):
                result[key] = widget.value()
            elif isinstance(widget, QComboBox):
                result[key] = widget.currentText()

        if self.segment:
            self.segment.set_settings(result)
            print("segment settings", self.segment.settings)

        return result

    def get_global_values(self) -> dict:
        """Return a dictionary with key: input text or selected combo for global settings."""
        result = {}
        for key, widget in self.inputs.items():
            if isinstance(widget, FocusDoubleSpinBox):
                result[key] = widget.value()
            elif isinstance(widget, QComboBox):
                result[key] = widget.currentText()
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

    def on_virtual_keyboard_shown(self):
        print("vk shown")
        scroll_area: QScrollArea = self.findChild(QScrollArea)
        if not scroll_area:
            return

        # Get currently focused widget
        focused_widget = self.focusWidget()
        if focused_widget and focused_widget in self.inputs.values():
            scroll_area.ensureWidgetVisible(focused_widget, xMargin=0, yMargin=20)
        else:
            # fallback: scroll to bottom (last widget)
            if self.inputs:
                last_widget = list(self.inputs.values())[-1]
                scroll_area.ensureWidgetVisible(last_widget, xMargin=0, yMargin=20)

    def on_virtual_keyboard_hidden(self):
        print("vk hidden")
        scroll_area: QScrollArea = self.findChild(QScrollArea)
        if scroll_area:
            scroll_area.ensureVisible(0, 0)  # scroll back to top


# Settings file path
SETTINGS_FILE_PATH = os.path.join(os.path.dirname(__file__), "global_segment_settings.json")

def save_settings_to_file(settings: dict):
    """Save settings to a JSON file"""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(SETTINGS_FILE_PATH), exist_ok=True)

        with open(SETTINGS_FILE_PATH, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"Settings saved to {SETTINGS_FILE_PATH}")
    except Exception as e:
        print(f"Error saving settings to file: {e}")

def load_settings_from_file() -> dict:
    """Load settings from JSON file, return empty dict if file doesn't exist"""
    try:
        if os.path.exists(SETTINGS_FILE_PATH):
            with open(SETTINGS_FILE_PATH, 'r') as f:
                loaded_settings = json.load(f)
            print(f"Settings loaded from {SETTINGS_FILE_PATH}")
            return loaded_settings
        else:
            print(f"Settings file not found at {SETTINGS_FILE_PATH}, using defaults")
            return {}
    except Exception as e:
        print(f"Error loading settings from file: {e}")
        return {}

def initialize_default_settings():
    """Initialize default settings by loading from file if available"""
    global default_settings

    # Load settings from file
    file_settings = load_settings_from_file()

    # Update default_settings with loaded values, keeping original defaults as fallback
    if file_settings:
        for key, value in file_settings.items():
            if key in default_settings:  # Only update existing keys
                default_settings[key] = str(value)
        print("Default settings initialized with saved values")

def update_default_settings(new_settings: dict):
    """Update the global default settings dictionary and save to file"""
    global default_settings
    for key, value in new_settings.items():
        default_settings[key] = str(value)

    # Save to file
    save_settings_to_file(default_settings)
    print(f"Updated and saved default settings: {default_settings}")

def get_default_settings() -> dict:
    """Get the current default settings"""
    return default_settings.copy()

# Initialize default settings on module import
initialize_default_settings()

if __name__ == "__main__":
    from modules.shared.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
    from modules.shared.shared.settings.conreateSettings.enums.RobotSettingKey import RobotSettingKey
    from src.frontend.pl_ui.utils.enums.GlueType import GlueType

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

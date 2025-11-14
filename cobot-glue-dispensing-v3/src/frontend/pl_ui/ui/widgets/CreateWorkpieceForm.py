"""pump param height andle rz """

import json
import os
from enum import Enum

from PyQt6.QtCore import QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon, QPalette, QColor
from PyQt6.QtWidgets import QFrame, QSizePolicy, QSpacerItem, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, \
    QCheckBox, QWidget, QMessageBox, QDialog, QScrollArea, QStyleFactory, QListView
from frontend.pl_ui.utils.styles.CreateWorkpieceStyles import getStyles
from frontend.pl_ui.utils.styles.CreateWorkpieceStyles import get_input_field_styles
from frontend.pl_ui.utils.styles.CreateWorkpieceStyles import get_popup_view_styles

from frontend.pl_ui.ui.widgets.Drawer import Drawer
from frontend.pl_ui.utils.enums.GlueType import GlueType
from frontend.pl_ui.utils.enums.Gripper import Gripper
from frontend.pl_ui.utils.enums.Program import Program
from frontend.pl_ui.utils.enums.ToolID import ToolID
from frontend.pl_ui.utils.enums.WorkpieceField import WorkpieceField
from frontend.pl_ui.ui.widgets.virtualKeyboard.VirtualKeyboard import FocusLineEdit
from frontend.pl_ui.utils.IconLoader import WORKPIECE_ID_ICON_PATH, WORKPIECE_NAME_ICON_PATH, DESCRIPTION_ICON_PATH, OFFSET_ICON_PATH, \
    HEIGHT_ICON_PATH, TOOL_ID_ICON_PATH, GRIPPER_ID_ICON_PATH, GLUE_TYPE_ICON_PATH, PROGRAM_ICON_PATH, MATERIAL_ICON_PATH, ACCEPT_BUTTON_ICON_PATH, \
    CANCEL_BUTTON_ICON_PATH, GLUE_QTY_ICON_PATH, SPRAY_WIDTH_ICON_PATH
# Assuming the path to stylesheets
SETTINGS_STYLESHEET = os.path.join("settings.qss")

TITLE = "Create Workpiece"
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")

# Configuration file path
CONFIG_FILE = "settings/workpiece_form_config.json"
DEFAULT_FIELD_CONFIG = {
    WorkpieceField.WORKPIECE_ID.value: {"visible": True, "mandatory": False},
    WorkpieceField.NAME.value: {"visible": True, "mandatory": False},
    WorkpieceField.DESCRIPTION.value: {"visible": True, "mandatory": False},
    WorkpieceField.OFFSET.value: {"visible": True, "mandatory": False},
    WorkpieceField.HEIGHT.value: {"visible": True, "mandatory": False},
    WorkpieceField.GLUE_QTY.value: {"visible": True, "mandatory": False},
    WorkpieceField.SPRAY_WIDTH.value: {"visible": True, "mandatory": False},
    WorkpieceField.TOOL_ID.value: {"visible": True, "mandatory": False},
    WorkpieceField.GRIPPER_ID.value: {"visible": True, "mandatory": False},
    WorkpieceField.GLUE_TYPE.value: {"visible": True, "mandatory": False},
    WorkpieceField.PROGRAM.value: {"visible": True, "mandatory": False},
    WorkpieceField.MATERIAL.value: {"visible": True, "mandatory": False}
}

class FormConfigManager:
    """Manager class for handling form configuration save/load operations"""

    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file or return default if file doesn't exist"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                return DEFAULT_FIELD_CONFIG.copy()
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_FIELD_CONFIG.copy()

    def save_config(self, config):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.config = config
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_config(self):
        """Get current configuration"""
        return self.config

    def is_field_visible(self, field):
        """Check if a field should be visible"""
        field_key = field.value if isinstance(field, WorkpieceField) else field
        return self.config.get(field_key, {}).get("visible", True)

    def is_field_mandatory(self, field):
        """Check if a field is mandatory"""
        field_key = field.value if isinstance(field, WorkpieceField) else field
        return self.config.get(field_key, {}).get("mandatory", False)

class FieldConfigWidget(QWidget):
    """Widget for configuring a single field"""

    def __init__(self, field_name, field_config, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.init_ui(field_config)

    def init_ui(self, field_config):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Field name label
        name_label = QLabel(self.field_name.replace("_", " ").title())
        name_label.setMinimumWidth(150)
        layout.addWidget(name_label)

        # Visible checkbox
        self.visible_checkbox = QCheckBox("Visible")
        self.visible_checkbox.setChecked(field_config.get("visible", True))
        layout.addWidget(self.visible_checkbox)

        # Mandatory checkbox
        self.mandatory_checkbox = QCheckBox("Mandatory")
        self.mandatory_checkbox.setChecked(field_config.get("mandatory", False))
        layout.addWidget(self.mandatory_checkbox)

        # Connect signals to enable/disable mandatory when visibility changes
        self.visible_checkbox.toggled.connect(self._on_visibility_changed)
        self._on_visibility_changed(self.visible_checkbox.isChecked())

        layout.addStretch()
        self.setLayout(layout)

    def _on_visibility_changed(self, visible):
        """Enable/disable mandatory checkbox based on visibility"""
        self.mandatory_checkbox.setEnabled(visible)
        if not visible:
            self.mandatory_checkbox.setChecked(False)

    def get_config(self):
        """Get the current configuration for this field"""
        return {
            "visible": self.visible_checkbox.isChecked(),
            "mandatory": self.mandatory_checkbox.isChecked()
        }

class FormConfigDialog(QDialog):
    """Dialog for configuring form fields"""

    config_changed = pyqtSignal(dict)

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.field_widgets = {}
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Form Configuration")
        self.setModal(True)
        self.resize(500, 600)

        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Configure Form Fields")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Scroll area for field configurations
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Create configuration widgets for each field
        config = self.config_manager.get_config()
        for field_name, field_config in config.items():
            field_widget = FieldConfigWidget(field_name, field_config)
            self.field_widgets[field_name] = field_widget
            scroll_layout.addWidget(field_widget)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Buttons
        button_layout = QHBoxLayout()

        # Reset to defaults button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_button)

        button_layout.addStretch()

        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_config)
        save_button.setDefault(True)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def reset_to_defaults(self):
        """Reset all fields to default configuration"""
        reply = QMessageBox.question(
            self,
            "Reset Configuration",
            "Are you sure you want to reset all fields to their default configuration?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for field_name, field_widget in self.field_widgets.items():
                default_config = DEFAULT_FIELD_CONFIG.get(field_name, {"visible": True, "mandatory": False})
                field_widget.visible_checkbox.setChecked(default_config["visible"])
                field_widget.mandatory_checkbox.setChecked(default_config["mandatory"])

    def save_config(self):
        """Save the current configuration"""
        # Collect configuration from all field widgets
        new_config = {}
        for field_name, field_widget in self.field_widgets.items():
            new_config[field_name] = field_widget.get_config()

        # Validate that at least one field is visible
        visible_fields = [name for name, config in new_config.items() if config["visible"]]
        if not visible_fields:
            QMessageBox.warning(
                self,
                "Configuration Error",
                "At least one field must be visible!"
            )
            return

        # Save configuration
        if self.config_manager.save_config(new_config):
            self.config_changed.emit(new_config)
            QMessageBox.information(
                self,
                "Configuration Saved",
                "Form configuration has been saved successfully!"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Save Error",
                "Failed to save configuration. Please try again."
            )


class CreateWorkpieceForm(Drawer,QFrame):
    data_submitted = pyqtSignal(dict)
    def __init__(self, parent=None, showButtons=False, callBack=None, config_manager=None):
        super().__init__(parent)

        self._parent = parent

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("CreateWorkpieceForm")
        self.apply_stylesheet()

        self.onSubmitCallBack = callBack
        self.config_manager = config_manager or FormConfigManager()

        # Store field widgets for easy access
        self.field_widgets = {}
        self.field_layouts = {}

        self.setWindowTitle("Create Workpiece")
        self.setContentsMargins(0, 0, 0, 0)

        self.settingsLayout = QVBoxLayout()
        self.settingsLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.settingsLayout)

        self.buttons = []
        self.icon_widgets = []

        self.setStyleSheet("background: white;")

        # Add configuration button
        self.add_config_button()

        self.addWidgets()

        if showButtons:
            button_layout = QHBoxLayout()
            self.add_button("Accept", ACCEPT_BUTTON_ICON_PATH, button_layout)
            self.add_button("Cancel", CANCEL_BUTTON_ICON_PATH, button_layout)
            self.settingsLayout.addLayout(button_layout)

    def prefill_form(self, workpiece):
        """Prefill the form with existing workpiece data"""
        is_dict = isinstance(workpiece, dict)
        for field_name, widget in self.field_widgets.items():
            # Support both dict-like workpiece and object with attributes
            if is_dict:
                if field_name not in workpiece:
                    continue
                value = workpiece.get(field_name)
            else:
                if not hasattr(workpiece, field_name):
                    continue
                value = getattr(workpiece, field_name, None)

            if value is None:
                continue

            if hasattr(widget, 'setText'):  # QLineEdit
                widget.setText(str(value))
            elif hasattr(widget, 'setCurrentText'):  # QComboBox
                # For enum fields, convert value to name if necessary
                enum_mapping = {
                    WorkpieceField.TOOL_ID.value: ToolID,
                    WorkpieceField.GRIPPER_ID.value: Gripper,
                    WorkpieceField.GLUE_TYPE.value: GlueType,
                    WorkpieceField.PROGRAM.value: Program,
                }
                if field_name in enum_mapping:
                    enum_class = enum_mapping[field_name]
                    enum_name = None
                    try:
                        if isinstance(value, enum_class):
                            enum_name = value.name
                        else:
                            try:
                                enum_name = enum_class(value).name
                            except Exception:
                                # try matching by name or by comparing item.value
                                if isinstance(value, str) and hasattr(enum_class, value):
                                    enum_name = value
                                else:
                                    for item in enum_class:
                                        if str(item.value) == str(value) or item.name == str(value):
                                            enum_name = item.name
                                            break
                    except Exception:
                        enum_name = None
                    widget.setCurrentText(enum_name if enum_name is not None else str(value))
                else:
                    widget.setCurrentText(str(value))

    def apply_stylesheet(self):
        styles = getStyles()
        self.setStyleSheet(styles)


    def add_config_button(self):
        """Add configuration button to the form"""
        config_layout = QHBoxLayout()
        config_layout.addStretch()

        config_button = QPushButton("Configure Fields")
        config_button.setMaximumWidth(150)
        config_button.clicked.connect(self.show_config_dialog)
        config_button.setObjectName("config_button")
        # config_layout.addWidget(config_button)
        # Put the config button row inside a small container so it aligns with the rest of the form
        container = QFrame()
        container.setObjectName("field_container")
        container.setFrameShape(QFrame.Shape.NoFrame)
        container.setLayout(config_layout)
        self.settingsLayout.addWidget(container)

    def show_config_dialog(self):
        """Show the configuration dialog"""
        dialog = FormConfigDialog(self.config_manager, self)
        dialog.config_changed.connect(self.refresh_form)
        dialog.exec()

    def refresh_form(self, new_config):
        """Refresh the form based on new configuration"""
        # Hide all field layouts first
        for field_name, layout in self.field_layouts.items():
            self.hide_layout(layout)

        # Show only visible fields
        for field_name, config in new_config.items():
            if config["visible"] and field_name in self.field_layouts:
                self.show_layout(self.field_layouts[field_name])

    def hide_layout(self, layout):
        """Hide a layout and all its widgets"""
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget():
                item.widget().hide()

    def show_layout(self, layout):
        """Show a layout and all its widgets"""
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget():
                item.widget().show()

    def addWidgets(self):
        """Add all form widgets based on configuration"""
        # Input fields
        input_fields = [
            (WorkpieceField.WORKPIECE_ID, "", WORKPIECE_ID_ICON_PATH),
            (WorkpieceField.NAME, "", WORKPIECE_NAME_ICON_PATH),
            (WorkpieceField.DESCRIPTION, "", DESCRIPTION_ICON_PATH),
            # (WorkpieceField.OFFSET, "", OFFSET_ICON_PATH),
            (WorkpieceField.HEIGHT, "", HEIGHT_ICON_PATH),
            (WorkpieceField.GLUE_QTY, "g /m²", GLUE_QTY_ICON_PATH),
            # (WorkpieceField.SPRAY_WIDTH, "", SPRAY_WIDTH_ICON_PATH),
        ]

        for field, placeholder, icon_path in input_fields:
            if self.config_manager.is_field_visible(field):
                self.add_input_field(field, placeholder, icon_path)

        # Dropdown fields
        dropdown_fields = [
            # (WorkpieceField.TOOL_ID, ToolID, TOOL_ID_ICON_PATH),
            (WorkpieceField.GRIPPER_ID, Gripper, GRIPPER_ID_ICON_PATH),
            (WorkpieceField.GLUE_TYPE, GlueType, GLUE_TYPE_ICON_PATH),
            # (WorkpieceField.PROGRAM, Program, PROGRAM_ICON_PATH),
            # (WorkpieceField.MATERIAL, ["Material1", "Material2", "Material3"], MATERIAL_ICON_PATH),
        ]

        for field, enum_class, icon_path in dropdown_fields:
            if self.config_manager.is_field_visible(field):
                self.add_dropdown_field(field, enum_class, icon_path)

        # Add spacer
        spacer = QSpacerItem(0, 150, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.settingsLayout.addItem(spacer)

    def add_input_field(self, label, placeholder, icon_path):
        """Helper method to add a label, icon, and input field"""
        # Create a container frame for consistent sizing/alignment when embedded
        container = QFrame()
        container.setObjectName("field_container")
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(8, 6, 8, 6)
        row_layout.setSpacing(12)

        icon_label = self.create_icon_label(icon_path)
        row_layout.addWidget(icon_label)

        input_field = FocusLineEdit(parent=self._parent)
        input_field.setStyleSheet(get_input_field_styles())
        input_field.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)  # disables native focus rect

        input_field.setPlaceholderText(placeholder)
        input_field.setMinimumHeight(40)
        input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row_layout.addWidget(input_field)

        self.settingsLayout.addWidget(container)

        # Store references
        field_name = label.value
        setattr(self, f"{field_name}_edit", input_field)
        self.field_widgets[field_name] = input_field
        self.field_layouts[field_name] = container

    def add_dropdown_field(self, label, enum_class, icon_path):
        """Helper method to add a dropdown (QComboBox) with enum items"""
        # Put the dropdown into a framed row so it aligns/stretches properly
        container = QFrame()
        container.setObjectName("field_container")
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(8, 6, 8, 6)
        row_layout.setSpacing(12)

        icon_label = self.create_icon_label(icon_path)
        row_layout.addWidget(icon_label)

        dropdown = QComboBox()
        dropdown.setMinimumHeight(40)
        dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Force the popup to use a QListView (prevents native popup on some platforms) and style it
        try:
            dropdown.setView(QListView())
            popup_view = dropdown.view()  # QListView/QAbstractItemView
            pal = popup_view.palette()
            pal.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
            pal.setColor(QPalette.ColorRole.Text, QColor("#000000"))
            popup_view.setPalette(pal)
            popup_view.setStyleSheet(get_popup_view_styles())
            popup_view.setAutoFillBackground(True)
            popup_view.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            popup_view.setUniformItemSizes(True)
            if popup_view.viewport() is not None:
                popup_view.viewport().setAutoFillBackground(True)
        except Exception:
            pass

        dropdown.setEditable(False)
        dropdown.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        if isinstance(enum_class, type) and issubclass(enum_class, Enum):
            dropdown.addItems([item.name for item in enum_class])
        else:
            dropdown.addItems(enum_class)

        row_layout.addWidget(dropdown)
        self.settingsLayout.addWidget(container)

        # Store references
        field_name = label.value
        setattr(self, f"{field_name}_combo", dropdown)
        self.field_widgets[field_name] = dropdown
        self.field_layouts[field_name] = container



    def add_button(self, button_type, icon_path, layout):
        """Helper method to add a button with an icon and click functionality"""
        button = QPushButton("")
        button.setIcon(QIcon(icon_path))
        button.setMinimumHeight(50)

        if button_type == "Accept":
            self.submit_button = button
            button.clicked.connect(self.onSubmit)
        else:
            self.cancel_button = button
            button.clicked.connect(self.onCancel)

        self.buttons.append(button)
        layout.addWidget(button)

    def validate_mandatory_fields(self):
        """Validate that all mandatory fields are filled"""
        errors = []
        config = self.config_manager.get_config()

        for field_name, field_config in config.items():
            if field_config.get("visible", True) and field_config.get("mandatory", False):
                # Check if field exists and has a value
                widget = self.field_widgets.get(field_name)
                if widget:
                    if hasattr(widget, 'text'):  # QLineEdit
                        if not widget.text().strip():
                            errors.append(field_name.replace("_", " ").title())
                    elif hasattr(widget, 'currentText'):  # QComboBox
                        if not widget.currentText().strip():
                            errors.append(field_name.replace("_", " ").title())

        return errors

    def onSubmit(self):
        """Collect form data and submit it with validation"""
        # Validate mandatory fields
        validation_errors = self.validate_mandatory_fields()
        if validation_errors:
            QMessageBox.warning(
                self,
                "Validation Error",
                f"The following mandatory fields are empty:\n\n" + "\n".join(
                    f"• {field}" for field in validation_errors)
            )
            return

        # Collect data from visible fields only
        data = {}
        config = self.config_manager.get_config()

        for field_name, field_config in config.items():
            if field_config.get("visible", True):
                widget = self.field_widgets.get(field_name)
                if widget:
                    if hasattr(widget, 'text'):  # QLineEdit
                        data[field_name] = widget.text()
                    elif hasattr(widget, 'currentText'):  # QComboBox
                        current_text = widget.currentText()
                        # Special handling for enum dropdowns - convert name back to value
                        if field_name in [WorkpieceField.TOOL_ID.value, WorkpieceField.GRIPPER_ID.value, WorkpieceField.GLUE_TYPE.value, WorkpieceField.PROGRAM.value]:
                            # Find the enum class for this field  
                            enum_mapping = {
                                WorkpieceField.TOOL_ID.value: ToolID,
                                WorkpieceField.GRIPPER_ID.value: Gripper, 
                                WorkpieceField.GLUE_TYPE.value: GlueType,
                                WorkpieceField.PROGRAM.value: Program,


                            }
                            enum_class = enum_mapping.get(field_name)
                            if enum_class and hasattr(enum_class, current_text):
                                data[field_name] = getattr(enum_class, current_text).value
                            else:
                                data[field_name] = current_text
                        else:
                            data[field_name] = current_text

        # Add default values for hidden fields that backend expects (using correct camelCase field names)
        data[WorkpieceField.TOOL_ID.value] = "0"  # Default tool ID -> 'toolId'
        data[WorkpieceField.PROGRAM.value] = "Trace"  # Default program -> 'program' 
        data[WorkpieceField.MATERIAL.value] = "Material1"  # Default material -> 'material'
        data[WorkpieceField.OFFSET.value] = "0"  # Default offset -> 'offset'
        data[WorkpieceField.SPRAY_WIDTH.value] = "10"  # Default spray width -> 'spray_width'
        data[WorkpieceField.HEIGHT.value] = getattr(self, f"{WorkpieceField.HEIGHT.value}_edit").text().strip() if hasattr(self, f"{WorkpieceField.HEIGHT.value}_edit") else ""
        data[WorkpieceField.CONTOUR_AREA.value] = "0"  # Default contour area -> 'contour_area'
        # Add pickup point if it exists
        if hasattr(self, 'pickup_point') and self.pickup_point:
            data[WorkpieceField.PICKUP_POINT.value] = self.pickup_point
            print(f"DEBUG: Including pickup_point in data: {self.pickup_point}")
        else:
            data[WorkpieceField.PICKUP_POINT.value] = None
            print(f"DEBUG: No pickup_point found. hasattr: {hasattr(self, 'pickup_point')}, value: {getattr(self, 'pickup_point', 'N/A')}")

        print("ON SUBMIT DATA:", data)


        self.data_submitted.emit(data)

        self.close()


    def onCancel(self):
        """Cancel the operation and close the form"""
        self.close()

    def create_icon_label(self, path, size=50):
        """Create a label with an icon, scaled to a specific size"""
        pixmap = QPixmap(path)
        label = QLabel()
        label.setPixmap(pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
        self.icon_widgets.append((label, pixmap))  # Store original pixmap for resizing
        return label


    def resizeEvent(self, event):
        """ Handle resizing of the window and icon sizes """
        # super().resizeEvent(event)
        if self._parent is None:
            return
        newWidth = self._parent.width()

        # Resize the icons in the labels
        for label, original_pixmap in self.icon_widgets:
            label.setPixmap(original_pixmap.scaled(int(newWidth * 0.02), int(newWidth * 0.02),
                                                   Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation))

        # Resize the icons in the buttons if they exist
        if hasattr(self, 'submit_button') and self.submit_button:
            button_icon_size = QSize(int(newWidth * 0.05), int(newWidth * 0.05))
            self.submit_button.setIconSize(button_icon_size)

        if hasattr(self, 'cancel_button') and self.cancel_button:
            button_icon_size = QSize(int(newWidth * 0.05), int(newWidth * 0.05))
            self.cancel_button.setIconSize(button_icon_size)

    def setHeigh(self, value):
        """Set height field value"""
        if hasattr(self, f"{WorkpieceField.HEIGHT.value}_edit"):
            getattr(self, f"{WorkpieceField.HEIGHT.value}_edit").setText(str(value))

    def clear_form(self):
        """Clear all form fields"""
        for field_name, widget in self.field_widgets.items():
            if hasattr(widget, 'setText'):  # QLineEdit
                widget.setText("")
            elif hasattr(widget, 'setCurrentIndex'):  # QComboBox
                widget.setCurrentIndex(0)

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    # Disable focus rectangles across all widgets
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setStyleSheet("""
        *:focus { outline: 0; }
        QLineEdit:focus, QComboBox:focus { outline: none; }
    """)
    form = CreateWorkpieceForm()
    form.show()
    sys.exit(app.exec())

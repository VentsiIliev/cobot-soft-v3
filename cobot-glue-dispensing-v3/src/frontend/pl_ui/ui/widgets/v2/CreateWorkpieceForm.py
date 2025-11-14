"""pump param height andle rz """

import json
import os
from enum import Enum

from PyQt6.QtCore import pyqtSignal, Qt, QSize, QObject, QEvent
from PyQt6.QtGui import QPixmap, QColor, QPalette
from PyQt6.QtWidgets import QFrame, QSizePolicy, QSpacerItem, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, \
    QCheckBox, QWidget, QMessageBox, QDialog, QScrollArea, QStyleFactory, QListView

from frontend.pl_ui.ui.widgets.Drawer import Drawer
from frontend.pl_ui.utils.enums.GlueType import GlueType
from frontend.pl_ui.utils.enums.Gripper import Gripper
from frontend.pl_ui.utils.enums.Program import Program
from frontend.pl_ui.utils.enums.ToolID import ToolID
from frontend.pl_ui.utils.enums.WorkpieceField import WorkpieceField
from frontend.pl_ui.ui.widgets.virtualKeyboard.VirtualKeyboard import FocusLineEdit
from frontend.pl_ui.utils.IconLoader import WORKPIECE_ID_ICON_PATH, WORKPIECE_NAME_ICON_PATH, DESCRIPTION_ICON_PATH, OFFSET_ICON_PATH, \
    HEIGHT_ICON_PATH, TOOL_ID_ICON_PATH, GRIPPER_ID_ICON_PATH, GLUE_TYPE_ICON_PATH, PROGRAM_ICON_PATH, MATERIAL_ICON_PATH, GLUE_QTY_ICON_PATH, SPRAY_WIDTH_ICON_PATH
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


class TouchScrollFilter(QObject):
    """Event filter that translates touch/mouse drag movements into scrolling on a QScrollArea."""
    def __init__(self, scroll_area):
        super().__init__()
        self.scroll_area = scroll_area
        self._last_pos = None

    def eventFilter(self, obj, event):
        t = event.type()
        # Touch events
        if t in (QEvent.Type.TouchBegin, QEvent.Type.TouchUpdate):
            try:
                points = event.touchPoints()
                if points:
                    y = points[0].pos().y()
                    if self._last_pos is None:
                        self._last_pos = y
                    else:
                        dy = y - self._last_pos
                        self._last_pos = y
                        vsb = self.scroll_area.verticalScrollBar()
                        vsb.setValue(vsb.value() - int(dy))
                    event.accept()
                    return True
            except Exception:
                return False
        elif t == QEvent.Type.TouchEnd:
            self._last_pos = None
            return True

        # Mouse drag fallback (for devices that synthesize mouse events)
        if t == QEvent.Type.MouseButtonPress:
            try:
                # Qt6: event.position() -> QPointF
                y = event.position().y()
            except Exception:
                y = event.y()
            self._last_pos = y
            return False
        elif t == QEvent.Type.MouseMove:
            if self._last_pos is not None:
                try:
                    y = event.position().y()
                except Exception:
                    y = event.y()
                dy = y - self._last_pos
                self._last_pos = y
                vsb = self.scroll_area.verticalScrollBar()
                vsb.setValue(vsb.value() - int(dy))
                return True
        elif t == QEvent.Type.MouseButtonRelease:
            self._last_pos = None
            return False

        return False

class StyledComboBox(QComboBox):
    """QComboBox subclass that forces styling on its popup view/window right before showing.

    Some platforms create a native popup or reset palette when the popup is shown. Styling right
    before showPopup ensures the correct palette and stylesheet are applied.
    """
    def showPopup(self):
        try:
            view = self.view()
            if view is not None:
                try:
                    view.setAutoFillBackground(True)
                    view.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                    pal = view.palette()
                    pal.setColor(QPalette.ColorRole.Base, QColor('#ffffff'))
                    pal.setColor(QPalette.ColorRole.Text, QColor('#3A2C4A'))
                    view.setPalette(pal)
                    if view.viewport() is not None:
                        vp_pal = view.viewport().palette()
                        vp_pal.setColor(QPalette.ColorRole.Base, QColor('#ffffff'))
                        vp_pal.setColor(QPalette.ColorRole.Text, QColor('#3A2C4A'))
                        view.viewport().setPalette(vp_pal)
                except Exception:
                    pass

                try:
                    view.setStyleSheet('''
                        QListView { background: #ffffff; color: #3A2C4A; }
                        QListView::item { padding: 10px 15px; }
                        QListView::item:selected, QListView::item:hover { background: #e7f3ff; color: #3A2C4A; }
                    ''')
                except Exception:
                    pass

                # Style the view's top-level window if present
                try:
                    popup_win = view.window()
                    popup_win.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                    popup_win.setAutoFillBackground(True)
                    popup_win.setStyleSheet('background: #ffffff; color: #3A2C4A;')
                    win_pal = popup_win.palette()
                    win_pal.setColor(QPalette.ColorRole.Window, QColor('#ffffff'))
                    win_pal.setColor(QPalette.ColorRole.WindowText, QColor('#3A2C4A'))
                    popup_win.setPalette(win_pal)
                except Exception:
                    pass
        except Exception:
            pass

        super().showPopup()

class CreateWorkpieceForm(Drawer, QFrame):
    def __init__(self, parent=None, showButtons=False, callBack=None, config_manager=None):
        super().__init__(parent)

        self._parent = parent
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("CreateWorkpieceForm")

        self.onSubmitCallBack = callBack
        self.config_manager = config_manager or FormConfigManager()

        # Store field widgets for easy access
        self.field_widgets = {}
        self.field_layouts = {}

        self.setWindowTitle("Create Workpiece")
        self.setContentsMargins(0, 0, 0, 0)

        # Main scroll area
        self.main_scroll = QScrollArea()
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Content widget inside scroll area
        self.content_widget = QWidget()
        self.settingsLayout = QVBoxLayout(self.content_widget)
        self.settingsLayout.setSpacing(5)
        self.settingsLayout.setContentsMargins(30, 30, 30, 30)

        self.main_scroll.setWidget(self.content_widget)

        # Enable touch scrolling: accept touch events on the viewport and install an event filter
        try:
            viewport = self.main_scroll.viewport()
            viewport.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
            self._touch_filter = TouchScrollFilter(self.main_scroll)
            viewport.installEventFilter(self._touch_filter)
            # Also accept touch events on the scroll area itself
            self.main_scroll.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        except Exception:
            # If touch support isn't available, ignore and continue
            self._touch_filter = None

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_scroll)

        self.buttons = []
        self.icon_widgets = []

        self.apply_stylesheet()
        # self.add_title()
        self.addWidgets()

        if showButtons:
            self.add_action_buttons()

    def apply_stylesheet(self):
        self.setStyleSheet("""
            /* === Main Form Container === */
            CreateWorkpieceForm {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-radius: 16px;
                border: 1px solid #dee2e6;
            }

            /* === Scroll Area === */
            QScrollArea {
                border: none;
                background: transparent;
            }

            QScrollArea QWidget {
                background: transparent;
            }

            /* === Scroll Bar Styling === */
            QScrollBar:vertical {
                background: #f8f9fa;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background: #adb5bd;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }

            QScrollBar::handle:vertical:hover {
                background: #6c757d;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }

            /* === Title Styling === */
            QLabel#form_title {
                font-size: 28px;
                font-weight: bold;
                color: #3A2C4A;
                padding: 20px 0;
                border-bottom: 3px solid #0d6efd;
                margin-bottom: 10px;
            }

            /* === Section Headers === */
            QLabel#section_header {
                font-size: 18px;
                font-weight: 600;
                color: #495057;
                padding: 15px 0 8px 0;
                border-bottom: 1px solid #dee2e6;
                margin-top: 20px;
            }

            /* === Field Container === */
            QFrame#field_container {
                background: white;
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 15px;
                margin: 5px 0;
            }

            QFrame#field_container:hover {
                border-color: #0d6efd;
                box-shadow: 0 2px 8px rgba(13, 110, 253, 0.15);
            }

    

            /* === Field Labels === */
            QLabel#field_label {
                font-size: 14px;
                font-weight: 600;
                color: #495057;
                margin-bottom: 5px;
            }

            /* === Input Field Styling === */
            FocusLineEdit, QLineEdit {
                background: white;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 15px;
                color: #3A2C4A;
                min-height: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }

            FocusLineEdit:focus, QLineEdit:focus {
                border-color: #0d6efd;
                background: #f8f9ff;
                outline: none;
                box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.1);
            }

            FocusLineEdit:hover, QLineEdit:hover {
                border-color: #adb5bd;
            }

            /* === ComboBox Styling === */
            QComboBox {
                background: white;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 15px;
                color: #3A2C4A;
                min-height: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }

            QComboBox:focus, QComboBox:pressed {
                border-color: #0d6efd;
                background: #f8f9ff;
                outline: none;
                box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.1);
            }

            QComboBox:hover {
                border-color: #adb5bd;
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border: none;
                background: transparent;
            }

            QComboBox::down-arrow {
                image: none;
                border-left: 2px solid #6c757d;
                border-bottom: 2px solid #6c757d;
                width: 8px;
                height: 8px;
                transform: rotate(-45deg);
                margin: 2px;
            }

            /* === ComboBox Dropdown === */
            QComboBox QAbstractItemView {
                background: white;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                selection-background-color: #e7f3ff;
                selection-color: #3A2C4A;
                padding: 5px;
                font-size: 15px;
            }

            QComboBox QAbstractItemView::item {
                padding: 10px 15px;
                border-radius: 6px;
                margin: 2px;
            }

            QComboBox QAbstractItemView::item:selected {
                background: #e7f3ff;
                color: #3A2C4A;
            }

            QComboBox QAbstractItemView::item:hover {
                background: #f0f8ff;
                color: #3A2C4A;
            }

            /* === Button Styling === */
            QPushButton#action_button {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0d6efd, stop:1 #0056b3);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: 600;
                min-width: 140px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }

            QPushButton#action_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056b3, stop:1 #004085);
                transform: translateY(-1px);
            }

            QPushButton#action_button:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #004085, stop:1 #002752);
                transform: translateY(1px);
            }

            QPushButton#cancel_button {
                background: white;
                color: #6c757d;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: 600;
                min-width: 140px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }

            QPushButton#cancel_button:hover {
                background: #f8f9fa;
                border-color: #adb5bd;
                color: #495057;
            }

            QPushButton#cancel_button:pressed {
                background: #e9ecef;
                border-color: #6c757d;
            }

            /* === Configuration Button === */
            QPushButton#config_button {
                background: white;
                color: #6c757d;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }

            QPushButton#config_button:hover {
                background: #f8f9fa;
                border-color: #0d6efd;
                color: #0d6efd;
            }
        """)

    def add_title(self):
        """Add a professional title to the form"""
        title_label = QLabel("Create New Workpiece")
        title_label.setObjectName("form_title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.settingsLayout.addWidget(title_label)

    def add_config_button(self):
        """Add configuration button to the form"""
        config_layout = QHBoxLayout()
        config_layout.addStretch()

        config_button = QPushButton("⚙ Configure Fields")
        config_button.setObjectName("config_button")
        config_button.setMaximumWidth(150)
        config_button.clicked.connect(self.show_config_dialog)

        config_layout.addWidget(config_button)
        self.settingsLayout.addLayout(config_layout)

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
        """Add all form widgets based on configuration with sections"""

        # Basic Information Section
        # self.add_section_header("📋 Basic Information")
        basic_fields = [
            (WorkpieceField.WORKPIECE_ID, "Workpiece ID", WORKPIECE_ID_ICON_PATH),
            (WorkpieceField.NAME, "Workpiece name", WORKPIECE_NAME_ICON_PATH),
            (WorkpieceField.DESCRIPTION, "Description", DESCRIPTION_ICON_PATH),
        ]

        for field, placeholder, icon_path in basic_fields:
            if self.config_manager.is_field_visible(field):
                self.add_input_field(field, placeholder, icon_path)

        # Dimensions Section
        # self.add_section_header("📐 Dimensions & Properties")
        dimension_fields = [
            (WorkpieceField.OFFSET, "Offset value", OFFSET_ICON_PATH),
            (WorkpieceField.HEIGHT, "Height", HEIGHT_ICON_PATH),
            (WorkpieceField.GLUE_QTY, "g/m²", GLUE_QTY_ICON_PATH),
            (WorkpieceField.SPRAY_WIDTH, "Spray width", SPRAY_WIDTH_ICON_PATH),
        ]

        for field, placeholder, icon_path in dimension_fields:
            if self.config_manager.is_field_visible(field):
                self.add_input_field(field, placeholder, icon_path)

        # Configuration Section
        # self.add_section_header("⚙️ Configuration")
        config_fields = [
            (WorkpieceField.TOOL_ID, ToolID, TOOL_ID_ICON_PATH),
            (WorkpieceField.GRIPPER_ID, Gripper, GRIPPER_ID_ICON_PATH),
            (WorkpieceField.GLUE_TYPE, GlueType, GLUE_TYPE_ICON_PATH),
            (WorkpieceField.PROGRAM, Program, PROGRAM_ICON_PATH),
            (WorkpieceField.MATERIAL, ["Material1", "Material2", "Material3"], MATERIAL_ICON_PATH),
        ]

        for field, enum_class, icon_path in config_fields:
            if self.config_manager.is_field_visible(field):
                self.add_dropdown_field(field, enum_class, icon_path)

    def add_section_header(self, title):
        """Add a section header"""
        header = QLabel(title)
        header.setObjectName("section_header")
        self.settingsLayout.addWidget(header)

    def add_input_field(self, field_enum, placeholder, icon_path):
        """Enhanced input field with container and better layout"""
        # Create container frame
        container = QFrame()
        container.setObjectName("field_container")

        # Main layout for the container
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Field label
        field_name = field_enum.value.replace("_", " ").title()
        is_mandatory = self.config_manager.is_field_mandatory(field_enum)
        label_text = f"{field_name}" + (" *" if is_mandatory else "")

        label = QLabel(label_text)
        label.setObjectName("field_label")
        # main_layout.addWidget(label)

        # Input layout with icon and field
        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)

        # Icon
        icon_label = self.create_icon_label(icon_path, size=40)
        icon_label.setObjectName("field_icon")
        icon_label.setFixedSize(56, 56)
        input_layout.addWidget(icon_label)

        # Input field
        input_field = FocusLineEdit(parent=self._parent)
        input_field.setPlaceholderText(placeholder)
        input_field.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        input_layout.addWidget(input_field)

        main_layout.addLayout(input_layout)

        # Add container to main layout
        self.settingsLayout.addWidget(container)

        # Store references
        field_name = field_enum.value
        setattr(self, f"{field_name}_edit", input_field)
        self.field_widgets[field_name] = input_field
        self.field_layouts[field_name] = container

    def add_dropdown_field(self, field_enum, enum_class, icon_path):
        """Enhanced dropdown field with container and better layout"""
        # Create container frame
        container = QFrame()
        container.setObjectName("field_container")

        # Main layout for the container
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Field label
        field_name = field_enum.value.replace("_", " ").title()
        is_mandatory = self.config_manager.is_field_mandatory(field_enum)
        label_text = f"{field_name}" + (" *" if is_mandatory else "")

        label = QLabel(label_text)
        label.setObjectName("field_label")
        # main_layout.addWidget(label)

        # Input layout with icon and field
        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)

        # Icon
        icon_label = self.create_icon_label(icon_path, size=40)
        icon_label.setObjectName("field_icon")
        icon_label.setFixedSize(56, 56)
        input_layout.addWidget(icon_label)

        # Dropdown
        dropdown = StyledComboBox()
        dropdown.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)

        # Configure dropdown view and force a styled QListView popup to avoid native popups with bad colors
        try:
            dropdown.setView(QListView())
            popup_view = dropdown.view()
            # Make sure the popup paints its background and uses styled background attribute
            popup_view.setAutoFillBackground(True)
            popup_view.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            # Force palette colors for the popup (white background, dark text)
            try:
                pal = popup_view.palette()
                pal.setColor(QPalette.ColorRole.Base, QColor('#ffffff'))
                pal.setColor(QPalette.ColorRole.Text, QColor('#3A2C4A'))
                popup_view.setPalette(pal)
                if popup_view.viewport() is not None:
                    vp_pal = popup_view.viewport().palette()
                    vp_pal.setColor(QPalette.ColorRole.Base, QColor('#ffffff'))
                    vp_pal.setColor(QPalette.ColorRole.Text, QColor('#3A2C4A'))
                    popup_view.viewport().setPalette(vp_pal)
            except Exception:
                pass
            # Apply explicit stylesheet to popup items (hover/selected)
            try:
                popup_view.setStyleSheet('''
                    QListView { background: #ffffff; color: #3A2C4A; }
                    QListView::item { padding: 10px 15px; }
                    QListView::item:selected, QListView::item:hover { background: #e7f3ff; color: #3A2C4A; }
                ''')
                # Some platforms wrap the view in a transient window — style that window too
                try:
                    popup_win = popup_view.window()
                    popup_win.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                    popup_win.setAutoFillBackground(True)
                    popup_win.setStyleSheet('background: #ffffff; color: #3A2C4A;')
                    win_pal = popup_win.palette()
                    win_pal.setColor(QPalette.ColorRole.Window, QColor('#ffffff'))
                    win_pal.setColor(QPalette.ColorRole.WindowText, QColor('#3A2C4A'))
                    popup_win.setPalette(win_pal)
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass

        # Conservative per-combobox stylesheet to ensure the popup uses our colors
        dropdown.setStyleSheet('''
            QComboBox QAbstractItemView { background: #ffffff; color: #3A2C4A; selection-background-color: #e7f3ff; }
        ''')

        dropdown.setEditable(False)
        dropdown.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Populate dropdown
        if isinstance(enum_class, type) and issubclass(enum_class, Enum):
            dropdown.addItems([item.value for item in enum_class])
        else:
            dropdown.addItems(enum_class)

        input_layout.addWidget(dropdown)
        main_layout.addLayout(input_layout)

        # Add container to main layout
        self.settingsLayout.addWidget(container)

        # Store references
        field_name = field_enum.value
        setattr(self, f"{field_name}_combo", dropdown)
        self.field_widgets[field_name] = dropdown
        self.field_layouts[field_name] = container

    def add_action_buttons(self):
        """Add professional action buttons"""
        # Add some spacing before buttons
        spacer = QSpacerItem(0, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.settingsLayout.addItem(spacer)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancel_button")
        self.cancel_button.clicked.connect(self.onCancel)
        button_layout.addWidget(self.cancel_button)

        # Submit button
        self.submit_button = QPushButton("Create Workpiece")
        self.submit_button.setObjectName("action_button")
        self.submit_button.clicked.connect(self.onSubmit)
        self.submit_button.setDefault(True)
        button_layout.addWidget(self.submit_button)

        self.settingsLayout.addLayout(button_layout)

        # Add bottom spacing
        bottom_spacer = QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.settingsLayout.addItem(bottom_spacer)

        self.buttons = [self.cancel_button, self.submit_button]

    def validate_mandatory_fields(self):
        """Validate that all mandatory fields are filled"""
        errors = []
        config = self.config_manager.get_config()

        for field_name, field_config in config.items():
            if field_config.get("visible", True) and field_config.get("mandatory", False):
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
        """Collect form data and submit it with enhanced validation"""
        # Validate mandatory fields
        validation_errors = self.validate_mandatory_fields()
        if validation_errors:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Icon.Warning)
            error_msg.setWindowTitle("Validation Error")
            error_msg.setText("Please fill in all required fields:")
            error_msg.setDetailedText("\n".join(f"• {field}" for field in validation_errors))
            error_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            error_msg.exec()
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
                        data[field_name] = widget.currentText()

        print("Form submitted with data:", data)

        if self.onSubmitCallBack:
            self.onSubmitCallBack(data)
        else:
            success_msg = QMessageBox()
            success_msg.setIcon(QMessageBox.Icon.Information)
            success_msg.setWindowTitle("Success")
            success_msg.setText("Workpiece created successfully!")
            success_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            success_msg.exec()

        self.close()

    def onCancel(self):
        """Cancel the operation with confirmation"""
        # Check if any fields have been modified
        has_data = False
        for field_name, widget in self.field_widgets.items():
            if hasattr(widget, 'text') and widget.text().strip():
                has_data = True
                break
            elif hasattr(widget, 'currentText') and widget.currentText().strip():
                has_data = True
                break

        if has_data:
            reply = QMessageBox.question(
                self,
                "Confirm Cancel",
                "You have unsaved changes. Are you sure you want to cancel?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.close()

    def create_icon_label(self, path, size=50):
        """Create a label with an icon, scaled to a specific size"""
        try:
            pixmap = QPixmap(path)
            if pixmap.isNull():
                # Create a default icon if the image fails to load
                pixmap = QPixmap(size, size)
                pixmap.fill(QColor('#0d6efd'))

            label = QLabel()
            label.setPixmap(pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.icon_widgets.append((label, pixmap))
            return label
        except Exception as e:
            print(f"Error loading icon from {path}: {e}")
            # Return a simple colored label as fallback
            label = QLabel()
            label.setFixedSize(size, size)
            label.setStyleSheet(f"background-color: #0d6efd; border-radius: {size // 2}px;")
            return label

    def resizeEvent(self, event):
        """Handle resizing of the window and icon sizes"""
        if self._parent is None:
            return

        try:
            newWidth = self._parent.width()
            icon_size = max(20, int(newWidth * 0.02))

            # Resize the icons in the labels
            for label, original_pixmap in self.icon_widgets:
                if not original_pixmap.isNull():
                    label.setPixmap(original_pixmap.scaled(icon_size, icon_size,
                                                           Qt.AspectRatioMode.KeepAspectRatio,
                                                           Qt.TransformationMode.SmoothTransformation))

            # Resize button icons if they exist
            button_icon_size = QSize(max(16, int(newWidth * 0.02)), max(16, int(newWidth * 0.02)))

            if hasattr(self, 'submit_button') and self.submit_button:
                self.submit_button.setIconSize(button_icon_size)

            if hasattr(self, 'cancel_button') and self.cancel_button:
                self.cancel_button.setIconSize(button_icon_size)
        except Exception as e:
            print(f"Error in resizeEvent: {e}")

    def setHeigh(self, value):
        """Set height field value"""
        if hasattr(self, f"{WorkpieceField.HEIGHT.value}_edit"):
            getattr(self, f"{WorkpieceField.HEIGHT.value}_edit").setText(str(value))

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    # Disable focus rectangles across all widgets
    app.setStyle(QStyleFactory.create("Fusion"))
    # Set an application palette so popups created by the style inherit the intended colors
    try:
        pal = app.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor('#ffffff'))
        pal.setColor(QPalette.ColorRole.WindowText, QColor('#3A2C4A'))
        pal.setColor(QPalette.ColorRole.Base, QColor('#ffffff'))
        pal.setColor(QPalette.ColorRole.Text, QColor('#3A2C4A'))
        pal.setColor(QPalette.ColorRole.Button, QColor('#ffffff'))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor('#3A2C4A'))
        app.setPalette(pal)
    except Exception:
        pass
    app.setStyleSheet("""
        *:focus { outline: 0; }
        QLineEdit:focus, QComboBox:focus { outline: none; }
    """)
    form = CreateWorkpieceForm()
    form.show()
    sys.exit(app.exec())

"""
Settings dialog for customizing all constants from constants.py
Opens with Ctrl+S shortcut
Saves to JSON file instead of modifying constants.py
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                              QLabel, QSpinBox, QDoubleSpinBox, QCheckBox,
                              QPushButton, QWidget, QGridLayout, QGroupBox,
                              QColorDialog, QScrollArea, QComboBox)
from src.frontend.pl_ui.ui.widgets.virtualKeyboard.VirtualKeyboard import FocusSpinBox,FocusDoubleSpinBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QKeySequence, QShortcut
from src.frontend.pl_ui.contour_editor.ConstantsManager import ConstantsManager


class ColorButton(QPushButton):
    """Button that shows a color and opens a color picker when clicked"""

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(60, 30)
        self.update_color(color)
        self.clicked.connect(self.choose_color)

    def update_color(self, color):
        """Update the button's background color"""
        self.color = color
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()});
                border: 2px solid #333;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid #666;
            }}
        """)

    def choose_color(self):
        """Open color picker dialog"""
        options = QColorDialog.ColorDialogOption.ShowAlphaChannel
        color = QColorDialog.getColor(self.color, self, "Choose Color", options)
        if color.isValid():
            self.update_color(color)

    def get_color(self):
        """Get the current color"""
        return self.color


class ConstantsSettingsDialog(QDialog):
    """Dialog for editing all constants from constants.py"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contour Editor Settings (Ctrl+S)")
        self.setModal(False)
        self.setMinimumSize(700, 600)

        # Window flags
        # self.setWindowFlags(
        #     Qt.WindowType.Dialog |
        #     Qt.WindowType.WindowTitleHint |
        #     Qt.WindowType.WindowCloseButtonHint
        # )
        self.setWindowFlags(Qt.WindowType.Window)

        # Dictionary to store all input widgets
        self.inputs = {}

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Create tab widget
        self.tabs = QTabWidget(self)
        # Ensure tabs, comboboxes and lists use a light background/text so they aren't black
        self.tabs.setStyleSheet("""
                QTabBar::tab {
                    background: #f5f5f5;
                    color: #000000;
                    padding: 8px;
                    border: 1px solid #cccccc;
                    border-bottom: none;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabWidget::pane {
                    border: 1px solid #cccccc;
                    background: #ffffff;
                }
                QComboBox {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #aaaaaa;
                    padding: 4px;
                }
                QComboBox QAbstractItemView {
                    background: #ffffff;
                    color: #000000;
                    selection-background-color: #e0e0e0;
                }
                QScrollArea, QWidget {
                    background: transparent;
                }
                """)
        main_layout.addWidget(self.tabs)

        # Create tabs
        self._create_visualization_toggles_tab()
        self._create_axes_and_angles_tab()
        self._create_segment_length_tab()
        self._create_highlighted_line_tab()
        self._create_crosshair_tab()
        self._create_point_rendering_tab()
        self._create_overlays_tab()
        self._create_measurement_timing_tab()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Reset to defaults button (left side)
        self.reset_button = QPushButton("Reset to Defaults", self)
        self.reset_button.setFont(QFont("Arial", 11))
        self.reset_button.setMinimumHeight(35)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 4px;
                padding: 5px 20px;
            }
            QPushButton:hover {
                background-color: #FFB74D;
            }
        """)
        self.reset_button.clicked.connect(self._on_reset_clicked)

        self.apply_button = QPushButton("Apply", self)
        self.apply_button.setFont(QFont("Arial", 11))
        self.apply_button.setMinimumHeight(35)
        self.apply_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                padding: 5px 20px;
            }
            QPushButton:hover {
                background-color: #5CBF60;
            }
        """)
        self.apply_button.clicked.connect(self._on_apply_clicked)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.setFont(QFont("Arial", 11))
        self.ok_button.setMinimumHeight(35)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 4px;
                padding: 5px 20px;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
        """)
        self.ok_button.clicked.connect(self._on_ok_clicked)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setFont(QFont("Arial", 11))
        self.cancel_button.setMinimumHeight(35)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border-radius: 4px;
                padding: 5px 20px;
            }
            QPushButton:hover {
                background-color: #9E9E9E;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

        # Load current values
        self.load_current_values()

    def _create_scrollable_tab(self, title):
        """Create a scrollable tab widget"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        scroll.setWidget(widget)
        self.tabs.addTab(scroll, title)

        return layout

    def _create_visualization_toggles_tab(self):
        """Create tab for visualization enable/disable flags"""
        layout = self._create_scrollable_tab("Visibility")

        group = QGroupBox("Visualization Toggles")
        group_layout = QGridLayout()
        group_layout.setSpacing(10)

        row = 0

        # Point rendering toggles
        self._add_checkbox(group_layout, row, "SHOW_CONTROL_POINTS", "Show Control Points")
        row += 1
        self._add_checkbox(group_layout, row, "SHOW_ANCHOR_POINTS", "Show Anchor Points")
        row += 1

        # Drag visualization toggles
        group_layout.addWidget(QLabel("<b>During Drag:</b>"), row, 0, 1, 2)
        row += 1
        self._add_checkbox(group_layout, row, "SHOW_AXES_ON_DRAG", "Show Axes on Drag")
        row += 1
        self._add_checkbox(group_layout, row, "SHOW_LENGTH_ON_DRAG", "Show Length on Drag")
        row += 1
        self._add_checkbox(group_layout, row, "SHOW_ANGLE_ON_DRAG", "Show Angle on Drag")
        row += 1

        # Overlay visualization toggles
        group_layout.addWidget(QLabel("<b>In Point Info Overlay:</b>"), row, 0, 1, 2)
        row += 1
        self._add_checkbox(group_layout, row, "SHOW_AXES_ON_OVERLAY", "Show Axes on Overlay")
        row += 1
        self._add_checkbox(group_layout, row, "SHOW_LENGTH_ON_OVERLAY", "Show Length on Overlay")
        row += 1
        self._add_checkbox(group_layout, row, "SHOW_ANGLE_ON_OVERLAY", "Show Angle on Overlay")

        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()

    def _create_axes_and_angles_tab(self):
        """Create tab for coordinate axes and angle visualization"""
        layout = self._create_scrollable_tab("Axes & Angles")

        # Colors group
        colors_group = QGroupBox("Colors")
        colors_layout = QGridLayout()
        colors_layout.setSpacing(10)

        row = 0
        self._add_color(colors_layout, row, "AXIS_X_COLOR", "X Axis Color")
        row += 1
        self._add_color(colors_layout, row, "AXIS_Y_COLOR", "Y Axis Color")
        row += 1
        self._add_color(colors_layout, row, "AXIS_ANGLE_ARC_COLOR", "Angle Arc Color")
        row += 1
        self._add_color(colors_layout, row, "AXIS_VECTOR_LINE_COLOR", "Vector Line Color")
        row += 1
        self._add_color(colors_layout, row, "AXIS_LABEL_BG_COLOR", "Label Background Color")

        colors_group.setLayout(colors_layout)
        layout.addWidget(colors_group)

        # Line properties group
        lines_group = QGroupBox("Line Properties")
        lines_layout = QGridLayout()
        lines_layout.setSpacing(10)

        row = 0
        self._add_spinbox(lines_layout, row, "AXIS_LINE_THICKNESS", "Axis Line Thickness", 1, 20, False)
        row += 1
        self._add_spinbox(lines_layout, row, "AXIS_VECTOR_LINE_THICKNESS", "Vector Line Thickness", 1, 20, False)
        row += 1
        self._add_spinbox(lines_layout, row, "AXIS_ARC_RADIUS", "Arc Radius", 10, 200, False)

        lines_group.setLayout(lines_layout)
        layout.addWidget(lines_group)

        # Label properties group
        labels_group = QGroupBox("Label Properties")
        labels_layout = QGridLayout()
        labels_layout.setSpacing(10)

        row = 0
        self._add_spinbox(labels_layout, row, "AXIS_LABEL_FONT_SIZE", "Font Size", 6, 24, False)
        row += 1
        self._add_spinbox(labels_layout, row, "AXIS_LABEL_PADDING_X", "Padding X", 0, 20, False)
        row += 1
        self._add_spinbox(labels_layout, row, "AXIS_LABEL_PADDING_Y", "Padding Y", 0, 20, False)
        row += 1
        self._add_spinbox(labels_layout, row, "AXIS_LABEL_BORDER_RADIUS", "Border Radius", 0, 20, False)

        labels_group.setLayout(labels_layout)
        layout.addWidget(labels_group)

        layout.addStretch()

    def _create_segment_length_tab(self):
        """Create tab for segment length measurement"""
        layout = self._create_scrollable_tab("Length Measurement")

        group = QGroupBox("Segment Length Measurement")
        group_layout = QGridLayout()
        group_layout.setSpacing(10)

        row = 0
        self._add_color(group_layout, row, "SEGMENT_LENGTH_COLOR", "Line Color")
        row += 1
        self._add_color(group_layout, row, "SEGMENT_LENGTH_BG_COLOR", "Background Color")
        row += 1
        self._add_spinbox(group_layout, row, "SEGMENT_LENGTH_LINE_THICKNESS", "Line Thickness", 1, 10, False)
        row += 1
        self._add_spinbox(group_layout, row, "SEGMENT_LENGTH_OFFSET_DISTANCE", "Offset Distance", 5, 100, False)
        row += 1
        self._add_spinbox(group_layout, row, "SEGMENT_LENGTH_TICK_SIZE", "Tick Size", 1, 20, False)
        row += 1
        self._add_spinbox(group_layout, row, "SEGMENT_LENGTH_FONT_SIZE", "Font Size", 6, 24, False)

        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()

    def _create_highlighted_line_tab(self):
        """Create tab for highlighted line segment"""
        layout = self._create_scrollable_tab("Highlighted Line")

        group = QGroupBox("Highlighted Line Segment")
        group_layout = QGridLayout()
        group_layout.setSpacing(10)

        row = 0
        self._add_color(group_layout, row, "HIGHLIGHTED_LINE_COLOR", "Line Color")
        row += 1
        self._add_spinbox(group_layout, row, "HIGHLIGHTED_LINE_THICKNESS", "Line Thickness", 1, 20, False)

        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()

    def _create_crosshair_tab(self):
        """Create tab for drag crosshair"""
        layout = self._create_scrollable_tab("Crosshair")

        # Style options group
        style_group = QGroupBox("Crosshair Style")
        style_layout = QGridLayout()
        style_layout.setSpacing(10)

        row = 0
        self._add_combobox(style_layout, row, "CROSSHAIR_STYLE", "Crosshair Type", ["circle", "simple"])
        row += 1
        self._add_combobox(style_layout, row, "CROSSHAIR_LINE_STYLE", "Line Style", ["solid", "dashed"])

        style_group.setLayout(style_layout)
        layout.addWidget(style_group)

        # Colors group
        colors_group = QGroupBox("Colors")
        colors_layout = QGridLayout()
        colors_layout.setSpacing(10)

        row = 0
        self._add_color(colors_layout, row, "CROSSHAIR_COLOR", "Crosshair Color")
        row += 1
        self._add_color(colors_layout, row, "CROSSHAIR_CONNECTOR_COLOR", "Connector Color")

        colors_group.setLayout(colors_layout)
        layout.addWidget(colors_group)

        # Properties group
        props_group = QGroupBox("Properties")
        props_layout = QGridLayout()
        props_layout.setSpacing(10)

        row = 0
        self._add_spinbox(props_layout, row, "CROSSHAIR_LINE_THICKNESS", "Line Thickness", 1, 10, False)
        row += 1
        self._add_spinbox(props_layout, row, "CROSSHAIR_SIZE", "Crosshair Size", 10, 50, False)
        row += 1
        self._add_spinbox(props_layout, row, "CROSSHAIR_OFFSET_Y", "Offset Y", -200, 200, False)
        row += 1
        self._add_spinbox(props_layout, row, "CROSSHAIR_CIRCLE_RADIUS", "Circle Radius", 2, 30, False)
        row += 1
        self._add_spinbox(props_layout, row, "CROSSHAIR_CONNECTOR_THICKNESS", "Connector Thickness", 1, 10, False)

        props_group.setLayout(props_layout)
        layout.addWidget(props_group)

        layout.addStretch()

    def _create_point_rendering_tab(self):
        """Create tab for point rendering"""
        layout = self._create_scrollable_tab("Points")

        group = QGroupBox("Point Rendering")
        group_layout = QGridLayout()
        group_layout.setSpacing(10)

        row = 0
        self._add_color(group_layout, row, "POINT_HANDLE_COLOR", "Handle Color")
        row += 1
        self._add_color(group_layout, row, "POINT_HANDLE_SELECTED_COLOR", "Selected Handle Color")
        row += 1
        self._add_spinbox(group_layout, row, "POINT_HANDLE_RADIUS", "Handle Radius", 2, 20, False)
        row += 1
        self._add_spinbox(group_layout, row, "POINT_MIN_DISPLAY_SCALE", "Min Display Scale", 0.1, 10.0, True)

        group.setLayout(group_layout)
        layout.addWidget(group)
        layout.addStretch()

    def _create_overlays_tab(self):
        """Create tab for overlay settings"""
        layout = self._create_scrollable_tab("Overlays")

        # Button sizes group
        sizes_group = QGroupBox("Button Sizes")
        sizes_layout = QGridLayout()
        sizes_layout.setSpacing(10)

        row = 0
        self._add_spinbox(sizes_layout, row, "OVERLAY_BUTTON_SIZE", "Button Size", 20, 100, False)
        row += 1
        self._add_spinbox(sizes_layout, row, "OVERLAY_RADIUS", "Overlay Radius", 30, 150, False)
        row += 1
        self._add_spinbox(sizes_layout, row, "OVERLAY_BUTTON_BORDER_WIDTH", "Border Width", 1, 10, False)
        row += 1
        self._add_spinbox(sizes_layout, row, "OVERLAY_BUTTON_SELECTED_BORDER_WIDTH", "Selected Border Width", 1, 10, False)

        sizes_group.setLayout(sizes_layout)
        layout.addWidget(sizes_group)

        # Button colors group
        colors_group = QGroupBox("Button Colors")
        colors_layout = QGridLayout()
        colors_layout.setSpacing(10)

        row = 0
        self._add_color(colors_layout, row, "OVERLAY_BUTTON_PRIMARY_COLOR", "Primary Color")
        row += 1
        self._add_color(colors_layout, row, "OVERLAY_BUTTON_PRIMARY_HOVER", "Primary Hover")
        row += 1
        self._add_color(colors_layout, row, "OVERLAY_BUTTON_SELECTED_COLOR", "Selected Color")
        row += 1
        self._add_color(colors_layout, row, "OVERLAY_BUTTON_SELECTED_BORDER", "Selected Border")
        row += 1
        self._add_color(colors_layout, row, "OVERLAY_BUTTON_DELETE_COLOR", "Delete Color")
        row += 1
        self._add_color(colors_layout, row, "OVERLAY_BUTTON_DELETE_HOVER", "Delete Hover")
        row += 1
        self._add_color(colors_layout, row, "OVERLAY_BUTTON_SET_LENGTH_COLOR", "Set Length Color")
        row += 1
        self._add_color(colors_layout, row, "OVERLAY_BUTTON_SET_LENGTH_HOVER", "Set Length Hover")
        row += 1
        self._add_color(colors_layout, row, "OVERLAY_BUTTON_CANCEL_COLOR", "Cancel Color")
        row += 1
        self._add_color(colors_layout, row, "OVERLAY_BUTTON_CANCEL_HOVER", "Cancel Hover")

        colors_group.setLayout(colors_layout)
        layout.addWidget(colors_group)

        layout.addStretch()

    def _create_measurement_timing_tab(self):
        """Create tab for measurement and timing settings"""
        layout = self._create_scrollable_tab("Measurement & Timing")

        # Measurement group
        measurement_group = QGroupBox("Measurement & Conversion")
        measurement_layout = QGridLayout()
        measurement_layout.setSpacing(10)

        row = 0
        self._add_spinbox(measurement_layout, row, "PIXELS_PER_MM", "Pixels per MM", 0.1, 10.0, True)

        measurement_group.setLayout(measurement_layout)
        layout.addWidget(measurement_group)

        # Drag & Selection group
        drag_group = QGroupBox("Drag & Selection")
        drag_layout = QGridLayout()
        drag_layout.setSpacing(10)

        row = 0
        self._add_spinbox(drag_layout, row, "DRAG_THRESHOLD_PX", "Drag Threshold (px)", 1, 50, False)
        row += 1
        self._add_spinbox(drag_layout, row, "POINT_HIT_RADIUS_PX", "Point Hit Radius (px)", 1, 50, False)
        row += 1
        self._add_spinbox(drag_layout, row, "CLUSTER_DISTANCE_PX", "Cluster Distance (px)", 1, 50, False)

        drag_group.setLayout(drag_layout)
        layout.addWidget(drag_group)

        # Timing group
        timing_group = QGroupBox("Timing")
        timing_layout = QGridLayout()
        timing_layout.setSpacing(10)

        row = 0
        self._add_spinbox(timing_layout, row, "DRAG_UPDATE_INTERVAL_MS", "Drag Update Interval (ms)", 8, 100, False)
        row += 1
        self._add_spinbox(timing_layout, row, "POINT_INFO_HOLD_DURATION_MS", "Point Info Hold Duration (ms)", 100, 2000, False)
        row += 1
        self._add_spinbox(timing_layout, row, "PRESS_HOLD_MOVEMENT_THRESHOLD_PX", "Press Hold Movement Threshold (px)", 1, 50, False)

        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)

        layout.addStretch()

    def _add_checkbox(self, layout, row, const_name, label):
        """Add a checkbox for a boolean constant"""
        checkbox = QCheckBox(label, self)
        checkbox.setFont(QFont("Arial", 10))
        layout.addWidget(checkbox, row, 0, 1, 2)
        self.inputs[const_name] = checkbox

    def _add_color(self, layout, row, const_name, label):
        """Add a color picker button"""
        label_widget = QLabel(label + ":", self)
        label_widget.setFont(QFont("Arial", 10))

        color_button = ColorButton(QColor(255, 255, 255), self)

        layout.addWidget(label_widget, row, 0)
        layout.addWidget(color_button, row, 1)

        self.inputs[const_name] = color_button

    def _add_spinbox(self, layout, row, const_name, label, min_val, max_val, is_float):
        """Add a spinbox for numeric constants"""
        label_widget = QLabel(label + ":", self)
        label_widget.setFont(QFont("Arial", 10))

        if is_float:
            spinbox = FocusDoubleSpinBox(self)
            spinbox.setDecimals(3)
            spinbox.setSingleStep(0.1)
        else:
            spinbox = FocusSpinBox(self)

        spinbox.setMinimum(min_val)
        spinbox.setMaximum(max_val)
        spinbox.setFont(QFont("Arial", 10))
        spinbox.setMinimumWidth(100)

        layout.addWidget(label_widget, row, 0)
        layout.addWidget(spinbox, row, 1)

        self.inputs[const_name] = spinbox

    def _add_combobox(self, layout, row, const_name, label, options):
        """Add a combobox for string constants with predefined options"""
        label_widget = QLabel(label + ":", self)
        label_widget.setFont(QFont("Arial", 10))

        combobox = QComboBox(self)
        combobox.addItems(options)
        combobox.setFont(QFont("Arial", 10))
        combobox.setMinimumWidth(100)

        layout.addWidget(label_widget, row, 0)
        layout.addWidget(combobox, row, 1)

        self.inputs[const_name] = combobox

    def load_current_values(self):
        """Load current values from constants module (with JSON overrides if they exist)"""
        try:
            # Get all current constant values (already has JSON overrides applied)
            current_values = ConstantsManager.get_all_constants()

            for const_name, widget in self.inputs.items():
                if const_name in current_values:
                    value = current_values[const_name]

                    if isinstance(widget, QCheckBox):
                        widget.setChecked(value)
                    elif isinstance(widget, ColorButton):
                        widget.update_color(value)
                    elif isinstance(widget, (FocusSpinBox, FocusDoubleSpinBox)):
                        widget.setValue(value)
                    elif isinstance(widget, QComboBox):
                        # Set combobox to the current value
                        index = widget.findText(value)
                        if index >= 0:
                            widget.setCurrentIndex(index)

        except Exception as e:
            print(f"Error loading constants: {e}")
            import traceback
            traceback.print_exc()

    def get_values(self):
        """Get all values from input widgets as a dictionary"""
        values = {}
        for const_name, widget in self.inputs.items():
            if isinstance(widget, QCheckBox):
                values[const_name] = widget.isChecked()
            elif isinstance(widget, ColorButton):
                values[const_name] = widget.get_color()
            elif isinstance(widget, (FocusSpinBox, FocusDoubleSpinBox)):
                values[const_name] = widget.value()
            elif isinstance(widget, QComboBox):
                values[const_name] = widget.currentText()
        return values

    def apply_changes(self):
        """Apply changes by saving to JSON and updating the constants module"""
        try:
            # Get all values from widgets
            values = self.get_values()

            # Save to JSON file
            if not ConstantsManager.save_settings(values):
                print("Failed to save settings to JSON")
                return False

            # Apply the settings to the constants module
            ConstantsManager.apply_settings(values)

            # Update parent editor if available
            if self.parent():
                # Reload cached constants in the parent editor
                if hasattr(self.parent(), '_reload_constants'):
                    self.parent()._reload_constants()
                else:
                    # Fallback to just updating the display
                    self.parent().update()

            print("Settings applied successfully!")
            return True

        except Exception as e:
            print(f"Error applying settings: {e}")
            import traceback
            traceback.print_exc()
            return False

    def reset_to_defaults(self):
        """Reset all settings to default values"""
        if ConstantsManager.reset_to_defaults():
            # Reload the dialog with default values
            self.load_current_values()

            # Update parent editor if available
            if self.parent():
                # Reload cached constants in the parent editor
                if hasattr(self.parent(), '_reload_constants'):
                    self.parent()._reload_constants()
                else:
                    # Fallback to just updating the display
                    self.parent().update()

            print("Settings reset to defaults")
            return True
        return False

    def _on_apply_clicked(self):
        """Handle Apply button click"""
        self.apply_changes()

    def _on_ok_clicked(self):
        """Handle OK button click"""
        if self.apply_changes():
            self.accept()

    def _on_reset_clicked(self):
        """Handle Reset to Defaults button click"""
        # Ask for confirmation
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.reset_to_defaults()

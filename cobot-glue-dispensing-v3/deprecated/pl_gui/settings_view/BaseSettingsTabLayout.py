from PyQt6.QtWidgets import QSizePolicy

from API.localization.LanguageResourceLoader import LanguageResourceLoader
from deprecated.pl_gui.virtualKeyboard.VirtualKeyboard import FocusDoubleSpinBox, FocusSpinBox


class BaseSettingsTabLayout:
    def __init__(self,parent_widget):
        self.className = self.__class__.__name__
        self.langLoader = LanguageResourceLoader()
        self.input_fields = []
        self.parent_widget = parent_widget
        self.sliders = [] # temp so the robot settings tab can work
        self.setup_styling()

    def setup_styling(self):
        """Set up responsive styling for the layout"""
        if self.parent_widget:
            # Base responsive font sizes
            base_font_size = "12px"
            label_font_size = "11px"
            title_font_size = "14px"

            self.parent_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: #f8f9fa;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }}

                QGroupBox {{
                    font-weight: bold;
                    font-size: {title_font_size};
                    color: #2c3e50;
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 12px;
                    background-color: white;
                }}

                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                }}

                QLabel {{
                    color: #34495e;
                    font-size: {label_font_size};
                    font-weight: 500;
                    min-width: 120px;
                    padding-right: 10px;

                }}

                QDoubleSpinBox, QComboBox {{word-wrap: true
                    border: 2px solid #905BA9;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: {base_font_size};
                    background-color: white;
                    min-height: 20px;
                    min-width: 100px;
                }}

                QDoubleSpinBox:focus, QComboBox:focus {{
                    border-color: #3498db;
                    outline: none;
                }}

                QDoubleSpinBox:hover, QComboBox:hover {{
                    border-color: #74b9ff;
                }}

                QComboBox::drop-down {{
                    border: none;
                    width: 20px;
                }}

                QComboBox::down-arrow {{
                    image: none;
                    border: none;
                    width: 0px;
                    height: 0px;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid #74b9ff;
                }}

                QComboBox QAbstractItemView {{
                    background-color: white;
                    color: #2c3e50;
                    selection-background-color: #d6eaff;
                    selection-color: #2c3e50;
                }}

                QComboBox QAbstractItemView::item:hover {{
                    background-color: #d6eaff;
                    color: #905BA9;
                }}

                QComboBox QAbstractItemView::item:selected {{
                    background-color: #74b9ff;
                    color: #905BA9;
                }}

                QScrollArea {{
                    border: none;
                    background-color: #f8f9fa;
                }}

                QScrollBar:vertical {{
                    background-color: #ecf0f1;
                    width: 12px;
                    border-radius: 6px;
                }}

                QScrollBar::handle:vertical {{
                    background-color: #bdc3c7;
                    border-radius: 6px;
                    min-height: 20px;
                }}

                QScrollBar::handle:vertical:hover {{
                    background-color: #95a5a6;
                }}

                /* Responsive toggle buttons */
                QToggle {{
                    font-size: {base_font_size};
                    min-height: 35px;
                    padding: 5px 10px;
                }}
            """)

    def create_double_spinbox(self, min_val, max_val, default_val, suffix=""):
        """Create a styled double spinbox with responsive settings"""
        spinbox = FocusDoubleSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default_val)
        spinbox.setDecimals(2)
        if suffix:
            spinbox.setSuffix(suffix)

        spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        spinbox.setMinimumWidth(100)

        self.input_fields.append(spinbox)
        return spinbox

    def create_spinbox(self, min_val, max_val, default_val, suffix=""):
        """Create a styled spinbox with responsive settings - EXACT match to GlueSettings"""
        spinbox = FocusSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default_val)
        if suffix:
            spinbox.setSuffix(suffix)

        # EXACT responsive sizing match to GlueSettings - NO setMinimumWidth for spinboxes
        spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.input_fields.append(spinbox)
        return spinbox




from dataclasses import dataclass

from PyQt6.QtGui import QColor


@dataclass
class ComboBoxStyle:
    base_color: str = "#6750A4"
    background: str = "white"
    text_color: str = "black"
    border_radius: str = "14px"
    font_size: str = "11px"
    padding: str = "4px 12px"

    def generate_stylesheet(self, object_name: str) -> str:
        """Generate complete stylesheet for combo box"""
        lighter = QColor(self.base_color).lighter(110).name()
        darker = QColor(self.base_color).darker(110).name()

        return f"""
            QComboBox#{object_name} {{
                background: {self.background};
                color: {self.text_color};
                border: 2px solid {self.base_color};
                border-radius: {self.border_radius};
                padding: {self.padding};
                font-size: {self.font_size};
            }}
            QComboBox#{object_name}:hover {{
                background: {lighter};
                color: #FFFFFF;
            }}
            QComboBox#{object_name}:pressed {{
                background: {darker};
                color: #FFFFFF;
            }}
            QComboBox#{object_name}:disabled {{
                background: #E8DEF8;
                color: #79747E;
            }}
            QComboBox#{object_name}::drop-down {{
                border: none;
                background: transparent;
            }}
            QComboBox#{object_name}::drop-down:hover {{
                background: {lighter};
            }}
            QComboBox#{object_name}::down-arrow {{
                image: none;
                border: none;
                width: 0px;
                height: 0px;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #FFFFFF;
                margin-right: 6px;
            }}
            QComboBox#{object_name} QAbstractItemView {{
                border: 1px solid {self.base_color};
                background-color: white;
                selection-background-color: {self.base_color};
                border-radius: 8px;
                outline: none;
                font-size: 16px;
            }}
            QComboBox#{object_name} QAbstractItemView::item {{
                padding: 6px 12px;
                border: none;
                color: #000000;
                font-size: 32px;
            }}
            QComboBox#{object_name} QAbstractItemView::item:hover {{
                background-color: {lighter};
                color: #FFFFFF;
            }}
            QComboBox#{object_name} QAbstractItemView::item:selected {{

                background-color: {lighter};
                color: #FFFFFF;
            }}
        """
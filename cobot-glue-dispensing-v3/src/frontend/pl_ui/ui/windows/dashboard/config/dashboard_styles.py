from dataclasses import dataclass
from PyQt6.QtGui import QColor
from src.frontend.pl_ui.utils.styles.ComboBoxStyle import ComboBoxStyle




@dataclass
class DashboardConfig:
    glue_meters_count: int = 3
    trajectory_width: int = 800  # Reduced from 960 to give glue cards more space
    trajectory_height: int = 450  # Reduced from 540 to give glue cards more space
    card_min_height: int = 75
    glue_cards_min_width: int = 350  # Increased to ensure cards get enough space
    glue_cards_max_width: int = 450  # Increased to ensure cards get enough space
    combo_style: ComboBoxStyle = None

    def __post_init__(self):
        if self.combo_style is None:
            self.combo_style = ComboBoxStyle()
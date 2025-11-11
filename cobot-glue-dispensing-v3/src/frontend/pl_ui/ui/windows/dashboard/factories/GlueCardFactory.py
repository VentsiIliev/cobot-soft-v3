from PyQt6.QtWidgets import QComboBox

from src.frontend.pl_ui.ui.windows.dashboard.widgets.DashboardCard import DashboardCard
from src.frontend.pl_ui.ui.windows.dashboard.widgets.GlueMeterWidget import GlueMeterWidget
from src.frontend.pl_ui.utils.enums.GlueType import GlueType
from src.frontend.pl_ui.ui.windows.dashboard.config.dashboard_styles import DashboardConfig
from src.backend.robot_application.glue_dispensing_application.tools.GlueCell import GlueCellsManagerSingleton


class GlueCardFactory:
    def __init__(self, config: DashboardConfig, message_manager):
        self.config = config
        self.message_manager = message_manager
        self.glue_cells_manager = GlueCellsManagerSingleton.get_instance()

    def create_glue_card(self, index: int, label_text: str, container=None) -> DashboardCard:
        """Create a fully configured glue card"""
        # Create components
        meter = self._create_meter(index)
        combo_box = self._create_combo_box(index)

        # Create card with index
        card = DashboardCard(label_text, [combo_box, meter], container=container, card_index=index)
        # Store combo reference for external access
        card.glue_type_combo = combo_box

        return card

    def _create_meter(self, index: int) -> GlueMeterWidget:
        """Create and configure meter widget"""
        meter = GlueMeterWidget(index)
        self.message_manager.subscribe_glue_meter(meter, index)
        return meter

    def _create_combo_box(self, index: int) -> QComboBox:
        """Create and configure combo box"""
        combo = QComboBox()
        combo.addItems([glue_type.value for glue_type in GlueType])

        # Get the current glue type from the configuration
        cell = self.glue_cells_manager.getCellById(index)
        if cell:
            combo.setCurrentText(cell.glueType.value)
        else:
            combo.setCurrentText("Type A")  # Fallback to Type A if cell not found

        combo.setObjectName(f"glue_combo_{index}")

        # Apply styling
        stylesheet = self.config.combo_style.generate_stylesheet(f"glue_combo_{index}")
        combo.setStyleSheet(stylesheet)

        return combo
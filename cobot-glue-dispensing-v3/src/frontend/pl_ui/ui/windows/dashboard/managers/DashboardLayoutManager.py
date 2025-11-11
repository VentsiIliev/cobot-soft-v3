from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt
from typing import List

from src.frontend.pl_ui.ui.widgets.MaterialButton import MaterialButton


class DashboardLayoutManager:
    def __init__(self, parent_widget: QWidget, config):
        self.parent = parent_widget
        self.config = config
        self.main_layout = QVBoxLayout(parent_widget)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

    def setup_complete_layout(self, trajectory_widget, glue_cards: List[QWidget],
                              control_buttons: QWidget,clean_button:MaterialButton,
                              reset_errors_button:MaterialButton,
                              run_demo_button:MaterialButton,
                              mode_toggle_button:MaterialButton) -> None:
        """Setup the complete dashboard layout"""
        # Create main sections
        top_section = self._create_top_section(trajectory_widget, glue_cards)
        bottom_section = self._create_bottom_section(control_buttons,clean_button,reset_errors_button,run_demo_button,mode_toggle_button)


        # Add to main layout
        self.main_layout.addLayout(top_section, stretch=2)
        self.main_layout.addLayout(bottom_section, stretch=1)

    def _create_top_section(self, trajectory_widget, glue_cards: List[QWidget]) -> QHBoxLayout:
        """Create top section with preview and glue cards"""
        top_section = QHBoxLayout()
        top_section.setSpacing(10)

        # Left: Preview container
        preview_container = self._create_preview_container(trajectory_widget)
        top_section.addWidget(preview_container, stretch=2)

        # Right: Glue cards container
        glue_container = self._create_glue_cards_container(glue_cards)
        top_section.addWidget(glue_container, stretch=1)

        return top_section

    def _create_preview_container(self, trajectory_widget) -> QWidget:
        """Create container for trajectory widget"""
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)

        trajectory_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        trajectory_widget.setMinimumHeight(300)
        trajectory_widget.setMaximumWidth(1200)  # Limit trajectory widget max width

        preview_layout.addWidget(trajectory_widget)
        return preview_widget

    def _create_glue_cards_container(self, glue_cards: List[QWidget]) -> QWidget:
        """Create container for glue cards"""
        glue_cards_widget = QWidget()
        glue_cards_layout = QVBoxLayout(glue_cards_widget)
        glue_cards_layout.setContentsMargins(0, 0, 0, 0)
        glue_cards_layout.setSpacing(8)

        for card in glue_cards:
            card.setMinimumHeight(self.config.card_min_height)
            card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            glue_cards_layout.addWidget(card)

        glue_cards_layout.addStretch()
        glue_cards_widget.setMinimumWidth(self.config.glue_cards_min_width)
        glue_cards_widget.setMaximumWidth(self.config.glue_cards_max_width)

        return glue_cards_widget

    def _create_bottom_section(self, control_buttons: QWidget,
                               clean_btn:MaterialButton,
                               reset_errors_button:MaterialButton,
                               run_demo_button:MaterialButton,
                               mode_toggle_button:MaterialButton) -> QVBoxLayout:
        """Create bottom section with placeholders and control buttons"""
        bottom_section = QVBoxLayout()
        bottom_section.setSpacing(10)

        placeholders_container = QWidget()
        placeholders_layout = QGridLayout(placeholders_container)
        placeholders_layout.setSpacing(15)
        placeholders_layout.setContentsMargins(0, 0, 0, 0)

        # Create placeholder grid
        for row in range(2):
            for col in range(3):
                if row == 0 and col == 0:
                    # placeholder = self._create_placeholder(row * 3 + col + 1)
                    # placeholders_layout.addWidget(placeholder, row, col)
                    # # placeholders_layout.addWidget(mode_toggle_button, row, col)
                    # placeholders_layout.addWidget(mode_toggle_button, row, col)
                    continue
                if row == 0 and col == 2:
                    # Control buttons span 2 rows
                    placeholders_layout.addWidget(control_buttons, row, col, 2, 1)
                    continue
                elif row == 1 and col == 2:
                    # Skip - occupied by control buttons
                    continue
                elif row == 1 and col == 0:
                    # placeholder = self._create_placeholder(row * 3 + col + 1)
                    # placeholders_layout.addWidget(placeholder, row, col)
                    # # placeholders_layout.addWidget(reset_errors_button, row, col)
                    # placeholders_layout.addWidget(run_demo_button, row, col)
                    placeholder = self._create_placeholder(row * 3 + col + 1)
                    placeholders_layout.addWidget(placeholder, row, col)
                    # placeholders_layout.addWidget(mode_toggle_button, row, col)
                    placeholders_layout.addWidget(mode_toggle_button, row, col)
                elif row == 1 and col == 1:


                    placeholders_layout.addWidget(clean_btn, row, col)
                else:
                    placeholder = self._create_placeholder(row * 3 + col + 1)
                    placeholders_layout.addWidget(placeholder, row, col)

        bottom_section.addWidget(placeholders_container)
        return bottom_section

    def _create_placeholder(self, number: int) -> QFrame:
        """Create a placeholder widget"""
        placeholder_frame = QFrame()
        # placeholder_frame.setStyleSheet(
        #     "QFrame {border: 2px dashed #CAC4D0; background-color: #FAF9FC; border-radius: 12px;}"
        # )
        placeholder_frame.setMinimumHeight(120)
        placeholder_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        placeholder_label = QLabel(f"Component {number}")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet(
            "font-size: 14px; color: #79747E; font-style: italic; background: transparent; border: none;"
        )

        layout = QVBoxLayout(placeholder_frame)
        layout.setContentsMargins(10, 10, 10, 10)
        # layout.addWidget(placeholder_label)

        return placeholder_frame
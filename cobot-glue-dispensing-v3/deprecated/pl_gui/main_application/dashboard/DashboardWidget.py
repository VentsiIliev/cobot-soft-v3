import os
import sys

from PyQt6.QtCore import (
    Qt, QPoint, pyqtSignal
)
from PyQt6.QtGui import (
    QColor
)
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QComboBox, QHBoxLayout, QLabel,
    QVBoxLayout, QApplication, QSizePolicy, QFrame
)

from API.MessageBroker import MessageBroker
from pl_ui.ui.windows.dashboard.widgets.DashboardCard import DashboardCard
from deprecated.pl_gui.dashboard.EmptyPlaceholder import EmptyPlaceholder
from deprecated.pl_gui.dashboard.GlueMeterWidget import GlueMeterWidget
from deprecated.pl_gui.main_application.dashboard.ControlButtonsWidget import ControlButtonsWidget
from deprecated.pl_gui.main_application.dashboard.RobotTrajectoryWidget import SmoothTrajectoryWidget
from deprecated.pl_gui.specific.enums.GlueType import GlueType

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources")
HIDE_CAMERA_FEED_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "HIDE_CAMERA_FEED.png")
SHOW_CAMERA_FEED_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "SHOW_CAMERA_FEED.png")
CAMERA_PREVIEW_PLACEHOLDER = os.path.join(RESOURCE_DIR, "pl_ui_icons", "Background_&_Logo_white.png")

class CardContainer(QWidget):
    select_card_signal = pyqtSignal(object)
    def __init__(self, columns=3, rows=2):
        super().__init__()
        self.columns = columns
        self.rows = rows
        self.total_cells = columns * rows

        self.layout = QGridLayout()
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.setAcceptDrops(True)

        # Set equal stretch for all rows and columns for uniform sizing
        # This ensures all cells have the same size
        for row in range(self.rows):
            self.layout.setRowStretch(row, 1)
            # FIX: Use dynamic minimum height based on available space
            self.layout.setRowMinimumHeight(row, 180)  # Reduced from 200

        for col in range(self.columns):
            self.layout.setColumnStretch(col, 1)
            # FIX: Use dynamic minimum width based on available space
            self.layout.setColumnMinimumWidth(col, 200)  # Reduced from 250

        # Set size policy for the container to ensure it expands properly
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Initialize grid with empty placeholders
        self.grid_items = []
        for i in range(self.total_cells):
            placeholder = EmptyPlaceholder()
            # Set size policy for placeholders to ensure they expand properly
            placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            # FIX: Reduced minimum size to prevent overlapping
            placeholder.setMinimumSize(200, 150)  # Reduced from 250, 200

            row = i // self.columns
            col = i % self.columns
            self.layout.addWidget(placeholder, row, col)
            self.grid_items.append(placeholder)

        # Connect signal to main-thread-safe method
        self.select_card_signal.connect(self.select_card)
        broker = MessageBroker()
        broker.subscribe("glueType", self.selectCardByGlueType)


    def _replace_item_at_index(self, index, new_widget):
        """Replace widget at specific grid index"""
        if 0 <= index < len(self.grid_items):
            # Remove old widget
            old_widget = self.grid_items[index]
            self.layout.removeWidget(old_widget)
            old_widget.setParent(None)

            # Set size policy for new widget to ensure proper expansion
            if isinstance(new_widget, DashboardCard):
                new_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                new_widget.setMinimumSize(250, 200)
            elif isinstance(new_widget, EmptyPlaceholder):
                new_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                new_widget.setMinimumSize(250, 200)
            elif isinstance(new_widget, QFrame):  # For trajectory frame
                new_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

            # Add new widget
            row = index // self.columns
            col = index % self.columns
            self.layout.addWidget(new_widget, row, col)
            self.grid_items[index] = new_widget

            # If it's a card, set up container reference
            if isinstance(new_widget, DashboardCard):
                new_widget.container = self

    # ... rest of the methods remain the same ...

    def selectCardByGlueType(self, glueType):
        print("Executing callback with glueType: ", glueType)
        glue_value = glueType.value if hasattr(glueType, 'value') else str(glueType)

        for item in self.grid_items:
            if isinstance(item, DashboardCard) and hasattr(item, 'glue_type_combo'):
                current_text = item.glue_type_combo.currentText()
                print(f"Card glue type: {current_text}, Target glue type: {glue_value}")
                if current_text == glue_value:
                    print("Emitting signal to select card on main thread.")
                    self.select_card_signal.emit(item)
                    break

    def get_card_index(self, card):
        """Get the index of a card in the grid"""
        try:
            return self.grid_items.index(card)
        except ValueError:
            return -1

    def add_card(self, card: DashboardCard):
        """Add a card to the first available empty slot"""
        for i, item in enumerate(self.grid_items):
            if isinstance(item, EmptyPlaceholder):
                # Replace placeholder with card
                self._replace_item_at_index(i, card)
                break
        else:
            print("No empty slots available!")

    def select_card(self, selected_card):
        """Select a card and deselect others"""
        for item in self.grid_items:
            if isinstance(item, DashboardCard):
                item.is_selected = (item == selected_card)
                item.set_selected(item.is_selected)

    def remove_card(self, card: DashboardCard):
        """Remove a card and rearrange all cards to avoid gaps"""
        index_to_remove = self.get_card_index(card)
        if index_to_remove == -1:
            return

        # Remove the card from layout and memory
        self.layout.removeWidget(card)
        card.setParent(None)
        card.deleteLater()

        # Shift all widgets after the removed index one slot forward
        for i in range(index_to_remove + 1, len(self.grid_items)):
            prev_widget = self.grid_items[i - 1]
            curr_widget = self.grid_items[i]

            # Move the current widget to the previous slot
            self.grid_items[i - 1] = curr_widget
            row = (i - 1) // self.columns
            col = (i - 1) % self.columns
            self.layout.addWidget(curr_widget, row, col)

        # Add an empty placeholder at the last slot
        last_index = len(self.grid_items) - 1
        last_placeholder = EmptyPlaceholder()
        last_placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        last_placeholder.setMinimumSize(250, 200)

        self.grid_items[last_index] = last_placeholder
        row = last_index // self.columns
        col = last_index % self.columns
        self.layout.addWidget(last_placeholder, row, col)

    def swap_cards(self, card1, card2):
        """Swap two cards in the grid"""
        index1 = self.get_card_index(card1)
        index2 = self.get_card_index(card2)

        if index1 == -1 or index2 == -1:
            return

        # Swap in the grid_items list
        self.grid_items[index1], self.grid_items[index2] = self.grid_items[index2], self.grid_items[index1]

        # Update layout positions
        row1, col1 = index1 // self.columns, index1 % self.columns
        row2, col2 = index2 // self.columns, index2 % self.columns

        self.layout.removeWidget(card1)
        self.layout.removeWidget(card2)

        self.layout.addWidget(card2, row1, col1)
        self.layout.addWidget(card1, row2, col2)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasText():
            event.ignore()
            return

        source_name = event.mimeData().text()
        source_card = self.find_card_by_name(source_name)
        if not source_card:
            event.ignore()
            return

        # Get the position and find the target widget
        pos = event.position().toPoint()
        target_widget = self.get_widget_at(pos)

        if not target_widget or target_widget == source_card:
            event.ignore()
            return

        # Handle drop on placeholder
        if isinstance(target_widget, EmptyPlaceholder):
            source_index = self.get_card_index(source_card)
            target_index = self.grid_items.index(target_widget)

            if source_index == -1 or target_index == -1:
                event.ignore()
                return

            # Create new placeholder for source position
            new_placeholder = EmptyPlaceholder()

            # Remove widgets from layout
            self.layout.removeWidget(source_card)
            self.layout.removeWidget(target_widget)

            # Calculate grid positions
            row_target, col_target = target_index // self.columns, target_index % self.columns
            row_source, col_source = source_index // self.columns, source_index % self.columns

            # Update grid_items list
            self.grid_items[target_index] = source_card
            self.grid_items[source_index] = new_placeholder

            # Add widgets to new positions
            self.layout.addWidget(source_card, row_target, col_target)
            self.layout.addWidget(new_placeholder, row_source, col_source)

            # Set container reference
            source_card.container = self

            # Clean up old target placeholder
            target_widget.setParent(None)
            target_widget.deleteLater()

            print(f"Moved card '{source_name}' from position {source_index} to {target_index}")

        # Handle drop on another card (swap)
        elif isinstance(target_widget, DashboardCard):
            self.swap_cards(source_card, target_widget)
            print(f"Swapped cards '{source_name}' and '{target_widget.objectName()}'")

        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()

    def reset_placeholder_styling(self):
        """Reset all placeholder widgets to normal styling"""
        for item in self.grid_items:
            if isinstance(item, EmptyPlaceholder):
                item.setStyleSheet("""
                    QWidget {
                        border: 1px dashed #ccc;
                        border-radius: 10px;
                        background-color: transparent;
                    }
                """)

    def find_card_by_name(self, name):
        """Find card by object name"""
        for item in self.grid_items:
            if isinstance(item, DashboardCard) and item.objectName() == name:
                return item
        return None

    def get_widget_at(self, pos: QPoint):
        """Get widget at specific position"""
        for i, item in enumerate(self.grid_items):
            if item and item.isVisible():
                # Get the widget's position in the container
                row = i // self.columns
                col = i % self.columns

                # Calculate the widget's geometry
                widget_rect = self.layout.cellRect(row, col)

                if widget_rect.contains(pos):
                    return item
        return None

    def get_cards(self):
        """Get all cards (non-placeholder items)"""
        return [item for item in self.grid_items if isinstance(item, DashboardCard)]


class DashboardWidget(QWidget):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    glue_type_changed_signal = pyqtSignal(int,str)

    def __init__(self, updateCameraFeedCallback, parent=None):
        super().__init__(parent)
        # This tracks cards that can still be added
        self.card_map = {
            "Glue 1": lambda: self.create_glue_card(1, "Glue 1"),
            "Glue 2": lambda: self.create_glue_card(2, "Glue 2"),
            "Glue 3": lambda: self.create_glue_card(3, "Glue 3"),
        }

        self._broker_callbacks = []  # store (topic, callback) pairs
        self.glueMetersCount = 3
        self.glueMeters = []
        self.predefined_cards = []
        self.updateCameraFeedCallback = updateCameraFeedCallback
        self.shared_card_container = CardContainer(columns=1, rows=3)
        self.init_ui()
        # self.createSettingsTogglePanel()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- TOP SECTION: Preview (left) + Glue Cards (right) ---
        top_section = QHBoxLayout()
        top_section.setSpacing(10)

        # LEFT: Preview Widget
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)

        self.trajectory_widget = SmoothTrajectoryWidget(image_width=640, image_height=360)
        # self.trajectory_widget.setFixedSize(640,360)
        self.trajectory_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.trajectory_widget.setMinimumHeight(240)
        broker = MessageBroker()
        broker.subscribe("robot/trajectory/updateImage", self.trajectory_widget.set_image)
        broker.subscribe("robot/trajectory/point", self.trajectory_widget.update)

        preview_layout.addWidget(self.trajectory_widget)
        top_section.addWidget(preview_widget, stretch=3)  # takes 3/4 width

        # RIGHT: Glue Cards
        glue_cards_widget = QWidget()
        glue_cards_layout = QVBoxLayout(glue_cards_widget)
        glue_cards_layout.setContentsMargins(0, 0, 0, 0)
        glue_cards_layout.setSpacing(8)

        for i in range(1, self.glueMetersCount + 1):
            glue_card = self.create_glue_card(i, f"Glue {i}")
            glue_card.setMinimumHeight(75)
            glue_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            glue_cards_layout.addWidget(glue_card)

        glue_cards_layout.addStretch()
        glue_cards_widget.setMinimumWidth(320)
        glue_cards_widget.setMaximumWidth(400)

        top_section.addWidget(glue_cards_widget, stretch=1)  # takes 1/4 width

        # --- BOTTOM SECTION: Placeholders ---
        bottom_section = QVBoxLayout()
        bottom_section.setSpacing(10)

        placeholders_container = QWidget()
        placeholders_layout = QGridLayout(placeholders_container)
        placeholders_layout.setSpacing(15)
        placeholders_layout.setContentsMargins(0, 0, 0, 0)

        # Create control buttons widget
        self.control_buttons = ControlButtonsWidget()
        self.control_buttons.start_clicked.connect(self.start_requested.emit)
        self.control_buttons.stop_clicked.connect(self.stop_requested.emit)
        self.control_buttons.pause_clicked.connect(self.pause_requested.emit)

        for row in range(2):
            for col in range(3):

                if row == 0 and col == 2:
                    # Place the control buttons widget spanning both rows in column 2
                    placeholders_layout.addWidget(self.control_buttons, row, col, 2, 1)  # span 2 rows
                    continue
                elif row == 1 and col == 2:
                    # Skip this cell as it's already occupied by the control buttons widget
                    continue

                else:
                    placeholder_frame = QFrame()
                    placeholder_frame.setStyleSheet(
                        "QFrame {border: 2px dashed #CAC4D0; background-color: #FAF9FC; border-radius: 12px;}"
                    )
                    placeholder_frame.setMinimumHeight(120)
                    placeholder_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

                    placeholder_label = QLabel(f"Component {row * 3 + col + 1}")
                    placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    placeholder_label.setStyleSheet(
                        "font-size: 14px; color: #79747E; font-style: italic; background: transparent; border: none;"
                    )

                    layout = QVBoxLayout(placeholder_frame)
                    layout.setContentsMargins(10, 10, 10, 10)
                    layout.addWidget(placeholder_label)

                    placeholders_layout.addWidget(placeholder_frame, row, col)

        bottom_section.addWidget(placeholders_container)

        # Add top and bottom sections to main layout
        main_layout.addLayout(top_section, stretch=2)
        main_layout.addLayout(bottom_section, stretch=1)

        self.setLayout(main_layout)

    def create_glue_card(self, index: int, label_text: str) -> DashboardCard:
        # Create the meter widget - DON'T override its internal styling
        meter = GlueMeterWidget(index)

        # Subscribe to message broker
        broker = MessageBroker()
        cb1 = meter.updateWidgets
        cb2 = meter.updateState
        broker.subscribe(f"GlueMeter_{index}/VALUE", cb1)
        broker.subscribe(f"GlueMeter_{index}/STATE", cb2)

        self._broker_callbacks.extend([
            (f"GlueMeter_{index}/VALUE", cb1),
            (f"GlueMeter_{index}/STATE", cb2)
        ])

        # Create the combo box
        glue_type_combo = QComboBox()
        glue_type_combo.addItems([glue_type.value for glue_type in GlueType])
        glue_type_combo.setCurrentText("Type A")
        glue_type_combo.setObjectName(f"glue_combo_{index}")
        glue_type_combo.currentTextChanged.connect(
            lambda value, idx=index: self.glue_type_changed_signal.emit(idx, value))

        # Create the card - let GlueMeterWidget handle its own alignment
        card = DashboardCard(label_text, [glue_type_combo, meter],
                             remove_callback=None,
                             container=self.shared_card_container)

        card.glue_type_combo = glue_type_combo

        # Apply styling ONLY to the combo box
        base_color = "#6750A4"
        lighter = QColor(base_color).lighter(110).name()
        darker = QColor(base_color).darker(110).name()

        glue_type_combo.setStyleSheet(f"""
            QComboBox#glue_combo_{index} {{
                background: white;
                color: black;
                border: 2px solid {base_color};
                border-radius: 14px;
                padding: 4px 12px;
                font-size: 11px;
            }}
            QComboBox#glue_combo_{index}:hover {{
                background: {lighter};
            }}
            QComboBox#glue_combo_{index}:pressed {{
                background: {darker};
            }}
            QComboBox#glue_combo_{index}:disabled {{
                background: #E8DEF8;
                color: #79747E;
            }}
            QComboBox#glue_combo_{index}::drop-down {{
                border: none;
                background: transparent;
            }}
            QComboBox#glue_combo_{index}::drop-down:hover {{
                background: {lighter};
            }}
            QComboBox#glue_combo_{index}::down-arrow {{
                image: none;
                border: none;
                width: 0px;
                height: 0px;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #FFFFFF;
                margin-right: 6px;
            }}
            QComboBox#glue_combo_{index} QAbstractItemView {{
                border: 1px solid {base_color};
                background-color: white;
                selection-background-color: {base_color};
                border-radius: 8px;
                outline: none;
                font-size: 16px;
            }}
            QComboBox#glue_combo_{index} QAbstractItemView::item {{
                padding: 6px 12px;
                border: none;
                color: #000000;
                font-size: 32px;
            }}
            QComboBox#glue_combo_{index} QAbstractItemView::item:hover {{
                background-color: {lighter};
                color: #FFFFFF;
            }}
            QComboBox#glue_combo_{index} QAbstractItemView::item:selected {{
                background-color: {base_color};
                color: #FFFFFF;
            }}
        """)

        return card

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Resize event handling can be added here if needed

    def clean_up(self):
        """Clean up resources when the widget is closed"""
        print("Cleaning up DashboardWidget")
        broker = MessageBroker()
        for topic, cb in self._broker_callbacks:
            broker.unsubscribe(topic, cb)

        broker.unsubscribe("robot/trajectory/updateImage", self.trajectory_widget.set_image)
        broker.unsubscribe("robot/trajectory/point", self.trajectory_widget.update)

        self._broker_callbacks.clear()
        # Clear the shared card container
        self.shared_card_container = None

        broker.unsubscribe("robot/trajectory/updateImage", self.trajectory_widget.set_image)
        broker.unsubscribe("robot/trajectory/point", self.trajectory_widget.update)
        self.control_buttons.clean_up()


if __name__ == "__main__":
    def updateCameraFeedCallback():
        print("updating camera feed")


    app = QApplication(sys.argv)
    dashboard = DashboardWidget(updateCameraFeedCallback)
    dashboard.resize(1200, 800)  # Increased default size for better layout
    dashboard.show()
    sys.exit(app.exec())
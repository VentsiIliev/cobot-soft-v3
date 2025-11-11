import sys
import os
import random

from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QComboBox, QHBoxLayout, QLabel,
    QVBoxLayout, QApplication, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QPoint, pyqtSignal
)
from PyQt6.QtGui import (
    QFont
)
from API.MessageBroker import MessageBroker
from deprecated.pl_gui.CameraFeed import CameraFeed
from deprecated.pl_gui.dashboard.ProximitySensorCard import SensorCard
from deprecated.pl_gui.dashboard.WorkpiecesGraphCard import WorkpiecesGraphCard
from deprecated.pl_gui.specific.enums.GlueType import GlueType
from deprecated.pl_gui.dashboard.GlueMeterWidget import GlueMeterWidget
from deprecated.pl_gui.dashboard.GlueNozzleCard import GlueNozzleCard
from deprecated.pl_gui.dashboard.TrollyCard import TrollyCard
from deprecated.pl_gui.dashboard.TogglePanel import TogglePanel
from deprecated.pl_gui.dashboard.DraggableCard import DraggableCard
from deprecated.pl_gui.dashboard.EmptyPlaceholder import EmptyPlaceholder
from deprecated.pl_gui.dashboard.GlueMeterCard import GlueSetpointFields
from deprecated.pl_gui.SessionInfoWidget import SessionInfoWidget
from deprecated.pl_gui.customWidgets.FloatingToggleButton import FloatingToggleButton
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","resources")
HIDE_CAMERA_FEED_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "HIDE_CAMERA_FEED.png")
SHOW_CAMERA_FEED_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "SHOW_CAMERA_FEED.png")


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
            # Set minimum row height to ensure cards don't get squashed
            self.layout.setRowMinimumHeight(row, 200)

        for col in range(self.columns):
            self.layout.setColumnStretch(col, 1)
            # Set minimum column width to ensure cards maintain proper width
            self.layout.setColumnMinimumWidth(col, 250)

        # Set size policy for the container to ensure it expands properly
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Initialize grid with empty placeholders
        self.grid_items = []
        for i in range(self.total_cells):
            placeholder = EmptyPlaceholder()
            # Set size policy for placeholders to ensure they expand properly
            placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            placeholder.setMinimumSize(250, 200)  # Set minimum size for placeholders

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
            if isinstance(new_widget, DraggableCard):
                new_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                new_widget.setMinimumSize(250, 200)
            elif isinstance(new_widget, EmptyPlaceholder):
                new_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                new_widget.setMinimumSize(250, 200)

            # Add new widget
            row = index // self.columns
            col = index % self.columns
            self.layout.addWidget(new_widget, row, col)
            self.grid_items[index] = new_widget

            # If it's a card, set up container reference
            if isinstance(new_widget, DraggableCard):
                new_widget.container = self

    # ... rest of the methods remain the same ...

    def selectCardByGlueType(self, glueType):
        print("Executing callback with glueType: ", glueType)
        glue_value = glueType.value if hasattr(glueType, 'value') else str(glueType)

        for item in self.grid_items:
            if isinstance(item, DraggableCard) and hasattr(item, 'glue_type_combo'):
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

    def add_card(self, card: DraggableCard):
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
            if isinstance(item, DraggableCard):
                item.is_selected = (item == selected_card)
                item.set_selected(item.is_selected)

    def remove_card(self, card: DraggableCard):
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
            # event.acceptProposedAction(Qt.DropAction.MoveAction)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
            # event.acceptProposedAction(Qt.DropAction.MoveAction)
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
        elif isinstance(target_widget, DraggableCard):
            self.swap_cards(source_card, target_widget)
            print(f"Swapped cards '{source_name}' and '{target_widget.objectName()}'")

        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        # event.acceptProposedAction(Qt.DropAction.MoveAction)
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
            if isinstance(item, DraggableCard) and item.objectName() == name:
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
        return [item for item in self.grid_items if isinstance(item, DraggableCard)]



class GlueDashboardWidget(QWidget):
    def __init__(self, updateCameraFeedCallback, parent=None):
        super().__init__(parent)
        # This tracks cards that can still be added
        self.card_map = {
            "Glue 1": lambda: self.create_glue_card(1, "Glue 1"),
            "Glue 2": lambda: self.create_glue_card(2, "Glue 2"),
            "Glue 3": lambda: self.create_glue_card(3, "Glue 3"),
            # "Proximity Sensors": lambda: DraggableCard("Proximity Sensors",
            #                                            [SensorCard()],
            #                                            remove_callback=self.remove_card_and_restore,
            #                                            container=self.shared_card_container),
            "Workpieces Graph": lambda: self.create_workpieces_graph_card(),
            "User Info": lambda: self.createUserInfoCard(),
            # "Glue Nozzle": lambda: DraggableCard("Glue Nozzle",
            #                                      [GlueNozzleCard()],
            #                                      remove_callback=self.remove_card_and_restore,
            #                                      container=self.shared_card_container),
            # "Trolley":lambda: DraggableCard("Trolley",[TrollyCard()],remove_callback=self.remove_card_and_restore,
            #                                container=self.shared_card_container),
            # "AccountInfo": lambda: DraggableCard("Account",[SessionInfoWidget()],remove_callback=self.remove_card_and_restore,
            #                                      container=self.shared_card_container)
        }

        self.glueMetersCount = 3
        self.glueMeters = []
        self.predefined_cards = []
        self.updateCameraFeedCallback = updateCameraFeedCallback
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Top horizontal layout: Toolbar + Camera ---
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        top_layout.setContentsMargins(0, 0, 0, 0)

        toolbar_widget = QWidget()
        self.toolbar_layout = QHBoxLayout(toolbar_widget)
        self.toolbar_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.card_selector = QComboBox()
        self.card_selector.addItem("Add Card")  # Placeholder item
        self.card_selector.addItems([])  # Add your predefined card names
        self.card_selector.currentIndexChanged.connect(self.add_selected_card)
        # Create floating toggle arrow button
        self.createFlowingToggleButton()
        top_layout.addWidget(toolbar_widget, 3)

        # --- Right: CameraFeed ---
        self.camera_feed = CameraFeed(updateCallback=self.updateCameraFeedCallback, toggleCallback=self.dummy_toggle)
        self.camera_feed.pause_feed()
        self.camera_feed.setVisible(False)
        if self.camera_feed.current_resolution == self.camera_feed.resolution_small:
            self.camera_feed.toggle_resolution()

        # top_layout.addWidget(self.camera_feed, 1, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.camera_feed)

        # --- Card container with fixed grid ---
        self.shared_card_container = CardContainer(columns=4, rows=3)
        main_layout.addWidget(self.shared_card_container)
        # main_layout.addStretch()
        main_layout.addWidget(self.shared_card_container, 1)  # Give it stretch factor of 1
        self.setLayout(main_layout)

        # Initialize with default cards
        self.createGlueMeterCards()
        # self.createProximitySensorCard()
        self.createWorkDoneGraphCard()
        self.createUserInfoCard()
        # self.createGlueNozzleCard()
        # self.createTrolleyCard()
        # self.createAccountInfoCard()
        self.createSettingsTogglePanel()


    def createFlowingToggleButton(self):
        self.floating_toggle_button = FloatingToggleButton(self, on_toggle_callback=self.toggle_settings_panel)

    def createSettingsTogglePanel(self):
        """Create the settings toggle panel"""
        available_labels = list(self.card_map.keys())
        self.settings_panel = TogglePanel(available_labels, self, onToggleCallback=self.onSettingsToggle,cameraToggleCallback=self.showCameraFeed)
        # self.settings_panel = TogglePanel(available_labels, self, onToggleCallback=self.onSettingsToggle)
        self.settings_panel.setFixedWidth(300)
        self.settings_panel.setGeometry(self.width(), 0, 300, self.height())
        self.settings_panel.setStyleSheet("background-color: #ffffff; border-left: 1px solid #ccc;")
        self.settings_panel.raise_()
        self.settings_panel.hide()

        # Set initial toggle states based on existing cards
        existing_card_names = [card.objectName() for card in self.shared_card_container.get_cards()]

        for label in available_labels:
            is_active = label in existing_card_names
            self.settings_panel.setToggleState(label, is_active)

            # Add inactive cards to dropdown
            if not is_active:
                self.card_selector.addItem(label)

    def toggle_settings_panel(self):
        # Toggle the settings panel using its Drawer logic
        self.settings_panel.toggle()

        # Reposition the floating toggle button with animation
        self.floating_toggle_button.reposition(
            is_panel_visible=self.settings_panel.is_open,
            panel_width=self.settings_panel.width()
        )

        # Update arrow direction after animation
        direction = "▶" if self.settings_panel.is_open else "◀"
        self.floating_toggle_button.set_arrow_direction(direction)
    def onSettingsToggle(self, label_text, state):
        """Handle toggle state changes from the settings panel"""
        print(f"Settings toggle for '{label_text}' changed to: {'ON' if state else 'OFF'}")

        if state == False:  # Turning OFF - remove card
            card = self.shared_card_container.find_card_by_name(label_text)
            if card:
                print(f"Removing card: {label_text}")
                card.on_close()  # This will call remove_card_and_restore
                # Don't manually add to card_selector here - remove_card_and_restore handles it
            else:
                print(f"Card '{label_text}' not found for removal")

        else:  # Turning ON - add card
            # Check if card already exists
            existing_card = self.shared_card_container.find_card_by_name(label_text)
            if existing_card:
                print(f"Card '{label_text}' already exists")
                return

            # Create and add the card
            if label_text in self.card_map:
                print(f"Adding card: {label_text}")
                card = self.card_map[label_text]()
                self.shared_card_container.add_card(card)

                # Remove from dropdown if it exists there
                for i in range(self.card_selector.count()):
                    if self.card_selector.itemText(i) == label_text:
                        self.card_selector.removeItem(i)
                        break
            else:
                print(f"Card '{label_text}' not found in card_map")
    def createAccountInfoCard(self):
        accountInfoCard =  DraggableCard("Account",[SessionInfoWidget()],remove_callback=self.remove_card_and_restore,
                                                 container=self.shared_card_container)
        self.shared_card_container.add_card(accountInfoCard)
        # print("Card: ",card)
    def createTrolleyCard(self):
        trolleyCard = DraggableCard("Trolley",[TrollyCard()],remove_callback=self.remove_card_and_restore,
                                           container=self.shared_card_container)
        self.shared_card_container.add_card(trolleyCard)
    def createGlueNozzleCard(self):
        glueNozzleCard = DraggableCard("Glue Nozzle", [GlueNozzleCard()], self.remove_card_and_restore,
                                       container=self.shared_card_container)
        self.shared_card_container.add_card(glueNozzleCard)
    def create_camera_feed_card(self):
        card = DraggableCard("Camera Feed",
                             [CameraFeed(self.updateCameraFeedCallback, toggleCallback=self.dummy_toggle)],
                             self.remove_card_and_restore, container=self.shared_card_container)
        self.shared_card_container.add_card(card)
        return card
    def createUserInfoCard(self):
        user_info_card = DraggableCard("User Info", [SessionInfoWidget()],
                                       remove_callback=self.remove_card_and_restore,
                                       container=self.shared_card_container)
        self.shared_card_container.add_card(user_info_card)
        return user_info_card
    def create_workpieces_graph_card(self):
        start_time = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=5)
        data = [random.randint(5, 20) for _ in range(6)]

        card = DraggableCard(
            "Workpieces Graph",
            [WorkpiecesGraphCard(start_time, data)],
            remove_callback=self.remove_card_and_restore,
            container=self.shared_card_container
        )
        card.dragEnabled = False
        return card
    def createWorkDoneGraphCard(self):
        start_time = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=5)
        data = [random.randint(5, 20) for _ in range(6)]

        card = DraggableCard("Workpieces Graph",
                             [WorkpiecesGraphCard(start_time, data)],
                             remove_callback=self.remove_card_and_restore,
                             container=self.shared_card_container)
        card.dragEnabled = False
        self.shared_card_container.add_card(card)
    def createProximitySensorCard(self):
        sensorCard = SensorCard()
        card = DraggableCard("Proximity Sensors", [sensorCard],
                             remove_callback=self.remove_card_and_restore,
                             container=self.shared_card_container)
        self.shared_card_container.add_card(card)
    def create_glue_card(self, index: int, label_text: str) -> DraggableCard:
        label = QLabel(label_text)
        label.setFont(QFont("", 12, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        meter = GlueMeterWidget(index)
        broker = MessageBroker()
        broker.subscribe(f"GlueMeter_{index}/VALUE", meter.updateWidgets)
        broker.subscribe(f"GlueMeter_{index}/STATE", meter.updateState)

        glue_type_combo = QComboBox()
        glue_type_combo.addItems([glue_type.value for glue_type in GlueType])
        glue_type_combo.setCurrentText("Type A")

        card = DraggableCard(label_text, [glue_type_combo, meter],
                             remove_callback=self.remove_card_and_restore,
                             container=self.shared_card_container)
        card.glue_type_combo = glue_type_combo
        return card
    def createGlueMeterCards(self):
        for i in range(self.glueMetersCount):

            card = self.create_glue_card(i + 1, f"Glue {i + 1}")
            self.shared_card_container.add_card(card)
    def showCameraFeed(self):
        # pass
        print("Camera Toggle")
        visible = self.camera_feed.isVisible()
        if visible:
            self.camera_feed.pause_feed()
            self.shared_card_container.setVisible(True)
        else:
            self.camera_feed.resume_feed()
            self.shared_card_container.setVisible(False)

        self.camera_feed.setVisible(not visible)
    def dummy_toggle(self):
        is_expanded = self.camera_feed.current_resolution != self.camera_feed.resolution_small
        print("Camera resolution toggled.")
    def add_selected_card(self, index):
        """Add card selected from dropdown"""
        if index == 0:  # Skip placeholder item
            return

        self.card_selector.blockSignals(True)
        card_name = self.card_selector.itemText(index)

        # Check if card already exists
        existing_cards = self.shared_card_container.get_cards()
        if any(card.objectName() == card_name for card in existing_cards):
            print("Card already exists:", card_name)
            self.card_selector.setCurrentIndex(0)
            self.card_selector.blockSignals(False)
            return

        if card_name in self.card_map:
            print("Adding card:", card_name)
            card = self.card_map[card_name]()
            self.shared_card_container.add_card(card)
            self.card_selector.removeItem(index)

            # Update settings panel toggle state
            if hasattr(self, 'settings_panel'):
                self.settings_panel.setToggleState(card_name, True)
        else:
            print("Card not in card map:", card_name)

        self.card_selector.setCurrentIndex(0)
        self.card_selector.blockSignals(False)
    def remove_card_and_restore(self, card):
        """Remove card and restore it to the dropdown"""
        print("Removing card:", card.objectName())
        card_name = card.objectName()
        # Remove from container
        self.shared_card_container.remove_card(card)
        # Add back to dropdown (avoid duplicates)
        existing_items = [self.card_selector.itemText(i) for i in range(self.card_selector.count())]
        if card_name not in existing_items:
            self.card_selector.addItem(card_name)

        # Update settings panel toggle state
        if hasattr(self, 'settings_panel'):
            self.settings_panel.setToggleState(card_name, False)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_width = self.width()

        panel_width = self.settings_panel.width()
        panel_visible = self.settings_panel.isVisible()

        # Adjust panel position
        if panel_visible:
            self.settings_panel.setGeometry(new_width - panel_width, 0, panel_width, self.height())
            arrow_x = new_width - panel_width - self.floating_toggle_button.width()
        else:
            self.settings_panel.setGeometry(new_width, 0, panel_width, self.height())
            arrow_x = new_width - self.floating_toggle_button.width()

        arrow_y = self.height() // 2 - self.floating_toggle_button.height() // 2
        self.floating_toggle_button.move(arrow_x, arrow_y)
        self.floating_toggle_button.raise_()


if __name__ == "__main__":
    def updateCameraFeedCallback():
        print("updating camera feed")


    app = QApplication(sys.argv)
    dashboard = GlueDashboardWidget(updateCameraFeedCallback)
    dashboard.resize(600, 500)
    dashboard.show()
    sys.exit(app.exec())
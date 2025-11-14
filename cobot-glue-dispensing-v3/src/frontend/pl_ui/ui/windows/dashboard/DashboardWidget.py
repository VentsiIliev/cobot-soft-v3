from PyQt6.QtCore import (
    pyqtSignal
)
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QSizePolicy
)

from frontend.pl_ui.localization import TranslatableWidget, TranslationKeys
from frontend.pl_ui.ui.windows.dashboard.widgets.ControlButtonsWidget import ControlButtonsWidget
from frontend.pl_ui.ui.windows.dashboard.widgets.RobotTrajectoryWidget import RobotTrajectoryWidget
from frontend.pl_ui.ui.windows.dashboard.config.dashboard_styles import DashboardConfig
from frontend.pl_ui.ui.windows.dashboard.factories.GlueCardFactory import GlueCardFactory
from frontend.pl_ui.ui.windows.dashboard.managers.DashboardLayoutManager import DashboardLayoutManager
from frontend.pl_ui.ui.windows.dashboard.managers.DashboardMessageManager import DashboardMessageManager
from frontend.pl_ui.ui.windows.dashboard.widgets.DashboardCard import DashboardCard


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

class DashboardWidget(TranslatableWidget):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    clean_requested= pyqtSignal()
    reset_errors_requested = pyqtSignal()
    glue_type_changed_signal = pyqtSignal(int, str)
    start_demo_requested = pyqtSignal()
    stop_demo_requested = pyqtSignal()


    def __init__(self, updateCameraFeedCallback, config=None, parent=None):
        super().__init__(parent, auto_retranslate=False)

        # Configuration
        self.config = config or DashboardConfig()
        self.updateCameraFeedCallback = updateCameraFeedCallback

        # Managers - composition over inheritance
        self.message_manager = DashboardMessageManager()
        self.card_factory = GlueCardFactory(self.config, self.message_manager)

        # Shared components
        self.shared_card_container = CardContainer(columns=1, rows=3)
        self.run_demo = False
        # Initialize UI
        self.init_ui()
        self.init_translations()

    def on_mode_toggle(self):
        current_text = self.mode_toggle_button.text()
        if current_text == "Pick And Spray":
            new_mode = "Spray Only"
        else:
            new_mode = "Pick And Spray"

        self.message_manager.publish_mode_change(new_mode)
        self.mode_toggle_button.setText(new_mode)
        print(f"Mode changed to {new_mode}")

        # self.message_manager.publish_mode_change(new_mode)

    def on_run_demo(self):
        if self.run_demo == False:
            self.run_demo = True
            self.run_demo_button.setText("Stop Demo")
            print("Run Demo started")
            self.start_demo_requested.emit()
        else:
            self.run_demo = False
            self.run_demo_button.setText("Run Demo")
            print("Run Demo stopped")
            self.stop_demo_requested.emit()

    def init_ui(self):
        # Create layout manager
        self.layout_manager = DashboardLayoutManager(self, self.config)

        # Create trajectory widget
        self.trajectory_widget = RobotTrajectoryWidget(
            image_width=self.config.trajectory_width,
            image_height=self.config.trajectory_height
        )

        # Subscribe trajectory widget
        self.message_manager.subscribe_trajectory_widget(self.trajectory_widget)

        # Create control buttons
        self.control_buttons = ControlButtonsWidget()
        self.control_buttons.start_clicked.connect(self.start_requested.emit)
        self.control_buttons.stop_clicked.connect(self.stop_requested.emit)
        self.control_buttons.pause_clicked.connect(self.pause_requested.emit)

        from frontend.pl_ui.ui.widgets.MaterialButton import MaterialButton
        self.clean_button = MaterialButton("Clean", font_size=20)
        self.clean_button.clicked.connect(self.clean_requested.emit)

        self.reset_errors_button = MaterialButton("Reset Errors", font_size=20)
        self.reset_errors_button.clicked.connect(self.reset_errors_requested.emit)

        self.run_demo_button = MaterialButton("Run Demo", font_size=20)
        self.run_demo_button.clicked.connect(self.on_run_demo)

        self.mode_toggle_button = MaterialButton("Pick And Spray", font_size=20)
        self.mode_toggle_button.clicked.connect(self.on_mode_toggle)

        # Create glue cards
        glue_cards = []
        self.glue_cards_dict = {}  # Store cards for easy access by index
        for i in range(1, self.config.glue_meters_count + 1):
            card = self.create_glue_card(i, f"Glue {i}")
            glue_cards.append(card)
            self.glue_cards_dict[i] = card  # Store reference by index

        # Subscribe card container
        self.message_manager.subscribe_card_container(self.shared_card_container)

        # Setup layout
        self.layout_manager.setup_complete_layout(
            self.trajectory_widget,
            glue_cards,
            self.control_buttons,
            self.clean_button,
            self.reset_errors_button,
            self.run_demo_button,
            self.mode_toggle_button
        )

    def retranslate(self) -> None:

        self.clean_button.setText(self.tr(TranslationKeys.Dashboard.CLEAN))
        for card in self.glue_cards_dict.values():
            # update the title of each glue card: "Glue {id}"
            card.title_label.setText(f"{self.tr(TranslationKeys.Dashboard.GLUE)} {card.card_index}")

    def create_glue_card(self, index: int, label_text: str) -> DashboardCard:
        """Create glue card using factory"""
        card = self.card_factory.create_glue_card(index, label_text, self.shared_card_container)
        # Connect signals
        card.glue_type_combo.currentTextChanged.connect(
            lambda value, idx=index: self.glue_type_changed_signal.emit(idx, value)
        )
        card.long_press_detected.connect(self.on_glue_card_long_press)

        return card

    def on_glue_card_long_press(self, card_index: int):
        """Handle long press on glue card - show glue change wizard"""
        from new_development.setupWizard import SetupWizard

        wizard = SetupWizard()
        wizard.setWindowTitle(f"Change Glue for Cell {card_index}")

        # Store the card index in the wizard for later use
        wizard.card_index = card_index

        # Connect wizard finished signal
        wizard.finished.connect(lambda result: self.on_wizard_finished(result, wizard))

        wizard.exec()

    def on_wizard_finished(self, result, wizard):
        """Handle wizard completion"""
        print(f"Wizard finished with result: {result}")

        if result == 1:  # QDialog.Accepted
            # Get selected glue type from wizard
            selected_glue_type = wizard.get_selected_glue_type()
            card_index = wizard.card_index

            print(f"Selected glue type: {selected_glue_type}, Card index: {card_index}")

            if selected_glue_type and card_index:
                # Use the stored dictionary to find the card
                if card_index in self.glue_cards_dict:
                    card = self.glue_cards_dict[card_index]
                    print(f"Found card with index {card_index}, updating combo to {selected_glue_type}")
                    card.glue_type_combo.setCurrentText(selected_glue_type)
                else:
                    print(f"Warning: Card with index {card_index} not found in dictionary")
                    print(f"Available card indices: {list(self.glue_cards_dict.keys())}")

                # Emit signal to update configuration
                print(f"Emitting glue_type_changed_signal: {card_index}, {selected_glue_type}")
                self.glue_type_changed_signal.emit(card_index, selected_glue_type)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Resize event handling can be added here if needed

    def clean_up(self):
        """Clean up resources when the widget is closed"""
        print("Cleaning up DashboardWidget")
        self.message_manager.cleanup()
        self.shared_card_container = None
        self.control_buttons.clean_up()




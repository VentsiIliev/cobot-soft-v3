from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QVBoxLayout
from PyQt6.QtWidgets import QFrame

from modules.shared.MessageBroker import MessageBroker
from src.frontend.pl_ui.ui.windows.dashboard.widgets.GlueMeterWidget import GlueMeterWidget
from src.frontend.pl_ui.utils.enums.GlueType import GlueType


class GlueMeterCard(QFrame):
    glue_type_changed = pyqtSignal(str)

    def __init__(self, label_text: str, index: int):
        super().__init__()
        self.label_text = label_text
        self.index = index
        self.build_ui()
        self.subscribe()

    def build_ui(self) -> None:
        self.dragEnabled = True
        # Create the main layout for the card
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        # Create the glue type combo box
        self.glue_type_combo = QComboBox()
        self.glue_type_combo.addItems([GlueType.TypeA.value, GlueType.TypeB.value, GlueType.TypeC.value])
        self.glue_type_combo.setCurrentText("Type A")
        self.glue_type_combo.currentTextChanged.connect(lambda value: self.glue_type_changed.emit(value))

        # Add hover styling to the combo box and dropdown items

        self.meter_widget = GlueMeterWidget(self.index)

        main_layout.addWidget(self.glue_type_combo)
        main_layout.addWidget(self.meter_widget)

        # Set a border for the card
        self.apply_stylesheet()

    def apply_stylesheet(self) -> None:
        self.setStyleSheet("GlueMeterCard { border: 2px solid #ccc; border-radius: 5px; }")
        self.meter_widget.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; padding: 20px;")
        self.glue_type_combo.setStyleSheet("""
                    QComboBox {
                        border: 1px solid #ccc;
                        border-radius: 3px;
                        padding: 5px;
                        background-color: white;
                    }
                    QComboBox:hover {
                        background-color: #905BA9;
                        color: white;
                        border-color: #905BA9;
                    }
                    QComboBox::drop-down {
                        border: none;
                    }
                    QComboBox::drop-down:hover {
                        background-color: #905BA9;
                    }
                    QComboBox QAbstractItemView {
                        border: 1px solid #ccc;
                        background-color: white;
                        selection-background-color: #905BA9;
                    }
                    QComboBox QAbstractItemView::item {
                        padding: 5px;
                        border: none;
                    }
                    QComboBox QAbstractItemView::item:hover {
                        background-color: #905BA9;
                        color: white;
                    }
                    QComboBox QAbstractItemView::item:selected {
                        background-color: #905BA9;
                        color: white;
                    }
                """)
    def subscribe(self) -> None:

        broker = MessageBroker()
        broker.subscribe(f"GlueMeter_{self.index}/VALUE", self.meter_widget.updateWidgets)
        broker.subscribe(f"GlueMeter_{self.index}/STATE", self.meter_widget.updateState)

    def unsubscribe(self) -> None:
        broker = MessageBroker()
        broker.unsubscribe(f"GlueMeter_{self.index}/VALUE", self.meter_widget.updateWidgets)
        broker.unsubscribe(f"GlueMeter_{self.index}/STATE", self.meter_widget.updateState)

    def __del__(self):
        """Cleanup when the widget is destroyed"""
        print(f">>> GlueMeterCard {self.index} __del__ called")
        self.unsubscribe()

    def closeEvent(self, event) -> None:
        self.unsubscribe()
        super().closeEvent(event)


from PyQt6.QtWidgets import QApplication, QMainWindow

if __name__ == "__main__":
    app = QApplication([])

    # Create a main window to host the GlueMeterCard
    main_window = QMainWindow()
    main_window.setWindowTitle("GlueMeterCard Test")
    main_window.setGeometry(100, 100, 400, 300)

    # Initialize the GlueMeterCard
    card = GlueMeterCard("Test Glue Meter", 1)

    # Set the card as the central widget of the main window
    main_window.setCentralWidget(card)

    # Show the main window
    main_window.show()

    # Execute the application
    app.exec()

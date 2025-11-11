from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtWidgets import QFrame

from API.MessageBroker import MessageBroker
from deprecated.pl_gui.dashboard.GlueMeterWidget import GlueMeterWidget
from deprecated.pl_gui.specific.enums.GlueType import GlueType


class GlueMeterCard(QFrame):
    glueTypeChanged = pyqtSignal(str)

    def __init__(self, label_text, index):
        super().__init__()
        self.label_text = label_text
        self.index = index
        self.build_ui()
        self.subscribe()

    def build_ui(self):
        # Create the main layout for the card
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create horizontal layout for label and combo box
        header_layout = QHBoxLayout()

        # Create the label
        self.label = QLabel(f"{self.label_text} {self.index}")

        # Create the glue type combo box
        self.glue_type_combo = QComboBox()
        self.glue_type_combo.addItems([GlueType.TypeA.value, GlueType.TypeB.value, GlueType.TypeC.value])
        self.glue_type_combo.setCurrentText("Type A")
        self.glue_type_combo.currentTextChanged.connect(self.on_glue_type_changed)

        # Add label and combo to horizontal layout
        header_layout.addWidget(self.label)
        header_layout.addWidget(self.glue_type_combo)
        header_layout.addStretch()  # This pushes everything to the left

        # Create the meter widget (placeholder for now)
        self.meter_widget = GlueMeterWidget(self.index)
        self.meter_widget.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; padding: 20px;")

        # Add the horizontal layout and meter widget to the main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.meter_widget)

        # Set a border for the card
        self.setStyleSheet("GlueMeterCard { border: 2px solid #ccc; border-radius: 5px; }")

    def on_glue_type_changed(self, glue_type):
        print(f"Glue type changed to: {glue_type}")
        self.glueTypeChanged.emit(glue_type)

    def subscribe(self):
        meter = GlueMeterWidget(self.index)
        broker = MessageBroker()
        broker.subscribe(f"GlueMeter_{self.index}/VALUE", meter.updateWidgets)
        broker.subscribe(f"GlueMeter_{self.index}/STATE", meter.updateState)

    def unsubscribe(self):
        meter = GlueMeterWidget(self.index)
        broker = MessageBroker()
        broker.unsubscribe(f"GlueMeter_{self.index}/VALUE", meter.updateWidgets)
        broker.unsubscribe(f"GlueMeter_{self.index}/STATE", meter.updateState)

    def closeEvent(self, event):
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
    card = GlueMeterCard("Glue", 1)

    # Set the card as the central widget of the main window
    main_window.setCentralWidget(card)

    # Show the main window
    main_window.show()

    # Execute the application
    app.exec()
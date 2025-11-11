from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget

from API.MessageBroker import MessageBroker
from API.localization.LanguageResourceLoader import LanguageResourceLoader
from deprecated.pl_gui.dashboard.DraggableCard import DraggableCard
from deprecated.pl_gui.dashboard.GlueMeterWidget import GlueMeterWidget
from deprecated.pl_gui.specific.enums.GlueType import GlueType


class GlueSetpointFields(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.langLoader = LanguageResourceLoader()
        self.layout = QFormLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.g_per_m_input = QLineEdit()
        self.g_per_sqm_input = QLineEdit()


        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)


from PyQt6.QtWidgets import QFormLayout, QLineEdit, QComboBox, QSizePolicy, QVBoxLayout
# from pl_gui.dashboard.DraggableCard import DraggableCard
# from pl_gui.dashboard.GlueMeterWidget import GlueMeterWidget
# from API.MessageBroker import MessageBroker
# from pl_gui.specific.enums.GlueType import GlueType
from PyQt6.QtWidgets import QFrame





class GlueMeterCard(QFrame):
    glue_type_changed = pyqtSignal(str)
    def __init__(self, label_text, index):
        super().__init__()
        self.label_text = label_text
        self.index = index
        self.build_ui()
        self.subscribe()

    def build_ui(self):
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

        self.meter_widget = GlueMeterWidget(self.index)
        self.meter_widget.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; padding: 20px;")

        main_layout.addWidget(self.glue_type_combo)
        main_layout.addWidget(self.meter_widget)

        # Set a border for the card
        self.setStyleSheet("GlueMeterCard { border: 2px solid #ccc; border-radius: 5px; }")

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
    card = GlueMeterCard("Test Glue Meter", 1)
    card = DraggableCard(
        title="Glue Meter Card",
        content_widgets=[card],
        remove_callback=lambda x: print("Card removed:", x.label_text)
    )

    # Set the card as the central widget of the main window
    main_window.setCentralWidget(card)

    # Show the main window
    main_window.show()

    # Execute the application
    app.exec()


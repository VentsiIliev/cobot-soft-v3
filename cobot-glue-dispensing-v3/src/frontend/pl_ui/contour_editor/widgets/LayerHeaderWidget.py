from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel

class LayerHeaderWidget(QWidget):
    def __init__(self, layer_name, button_widget, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(layer_name))
        layout.addWidget(button_widget)
        layout.addStretch()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication([])
    widget = LayerHeaderWidget("Layer 1", QWidget())
    widget.show()
    app.exec()
# floating_toggle_button.py

from PyQt6.QtCore import QPropertyAnimation, QPoint, Qt
from PyQt6.QtWidgets import QPushButton


class FloatingToggleButton(QPushButton):
    def __init__(self, parent, on_toggle_callback=None):
        super().__init__("◀", parent)
        self.parent_widget = parent
        self.on_toggle_callback = on_toggle_callback

        self.setFixedSize(32, 64)
        self.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                color: white;
                background-color: #905BA9;
                border: 1px solid #aaa;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: white;
                color: #905BA9;
            }
        """)

        self.clicked.connect(self.toggle)
        self.raise_()
        self.show()

        self.button_animation = QPropertyAnimation(self, b"pos")
        self.button_animation.setDuration(250)  # ms

    def toggle(self):
        if callable(self.on_toggle_callback):
            self.on_toggle_callback()

    def reposition(self, is_panel_visible=False, panel_width=0):
        """Reposition the button with optional animation based on panel visibility"""
        parent = self.parent_widget
        if not parent:
            return

        parent_height = parent.height()
        button_height = self.height()
        y = (parent_height - button_height) // 2
        x = parent.width() - self.width() - 10 - (panel_width if is_panel_visible else 0)

        self.button_animation.stop()
        self.button_animation.setEndValue(QPoint(x, y))
        self.button_animation.start()

    def set_arrow_direction(self, direction: str):
        if direction in ["◀", "▶"]:
            self.setText(direction)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout

    app = QApplication([])

    window = QWidget()
    layout = QVBoxLayout(window)

    def toggle_callback():
        print("Button toggled!")

    button = FloatingToggleButton(window, on_toggle_callback=toggle_callback)
    layout.addWidget(button)

    window.setLayout(layout)
    window.resize(400, 300)
    window.show()

    app.exec()
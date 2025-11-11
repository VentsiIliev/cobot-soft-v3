import sys
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QSpinBox,
    QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer


class SpacingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spacing")
        self.spacing = 20

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter spacing in pixels:"))

        self.spin_box = QSpinBox()
        self.spin_box.setMinimum(1)
        self.spin_box.setMaximum(1000)
        self.spin_box.setValue(20)
        layout.addWidget(self.spin_box)

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_spacing(self):
        return self.spin_box.value()

    def showEvent(self, event):
        super().showEvent(event)
        # Delay the centering until the event loop processes pending events
        QTimer.singleShot(0, self.center_on_screen)

    def center_on_screen(self):
        screen = self.screen()
        if screen:
            screen_geometry = screen.geometry()
            # Use actual size, not sizeHint
            size = self.size()
            x = screen_geometry.x() + (screen_geometry.width() - size.width()) // 2
            y = screen_geometry.y() + (screen_geometry.height() - size.height()) // 2
            self.move(x, y)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = SpacingDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        spacing = dialog.get_spacing()
        print("Spacing:", spacing)
    else:
        print("Cancelled")

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QPushButton

import os

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
HIDE_ICON = os.path.join(RESOURCE_DIR, "hide.png")
SHOW_ICON = os.path.join(RESOURCE_DIR, "show.png")
PLUS_ICON = os.path.join(RESOURCE_DIR, "PLUS_BUTTON.png")
LOCK_ICON = os.path.join(RESOURCE_DIR, "locked.png")
UNLOCK_ICON = os.path.join(RESOURCE_DIR, "unlocked.png")


class LayerButtonsWidget(QWidget):
    def __init__(self, layer_name, layer_item, on_visibility_toggle, on_add_segment, on_lock_toggle, is_locked=False):
        super().__init__()

        self.layer_name = layer_name
        self.layer_item = layer_item
        self.on_visibility_toggle = on_visibility_toggle
        self.on_add_segment = on_add_segment
        self.on_lock_toggle = on_lock_toggle
        self.is_locked = is_locked

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.layer_name_label = QPushButton(layer_name)
        self.layer_name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.layer_name_label.setToolTip(f"{layer_name}")
        self.layer_name_label.setFixedHeight(50)
        self.layer_name_label.setStyleSheet("background-color: transparent; text-align: left; padding-left: 10px;")
        layout.addWidget(self.layer_name_label)

        # Visibility Button
        self.visibility_btn = QPushButton("")
        self.visibility_btn.setIcon(QIcon(HIDE_ICON))
        self.visibility_btn.setCheckable(True)
        self.visibility_btn.setChecked(True)
        self.visibility_btn.setIconSize(QSize(50, 50))
        self.visibility_btn.setFixedSize(50, 50)
        self.visibility_btn.setToolTip(f"Toggle {layer_name} visibility")
        self.visibility_btn.clicked.connect(self._handle_visibility_toggle)
        self.visibility_btn.setStyleSheet("background-color: transparent; border: none;")
        layout.addWidget(self.visibility_btn)

        # Add Segment Button
        self.add_segment_btn = QPushButton("")
        self.add_segment_btn.setIcon(QIcon(PLUS_ICON))
        self.add_segment_btn.setIconSize(QSize(50, 50))
        self.add_segment_btn.setFixedSize(50, 50)
        self.add_segment_btn.setToolTip(f"Add new segment to {layer_name}")
        self.add_segment_btn.clicked.connect(self._handle_add_segment)
        self.add_segment_btn.setStyleSheet("background-color: transparent; border: none;")
        layout.addWidget(self.add_segment_btn)

        # Lock Button
        self.lock_btn = QPushButton("")
        self.lock_btn.setCheckable(True)
        self.lock_btn.setChecked(is_locked)
        self.lock_btn.setIcon(QIcon(LOCK_ICON if is_locked else UNLOCK_ICON))
        self.lock_btn.setIconSize(QSize(50, 50))
        self.lock_btn.setFixedSize(50, 50)
        self.lock_btn.setToolTip(f"Lock/unlock {layer_name}")
        self.lock_btn.clicked.connect(self._handle_lock_toggle)
        self.lock_btn.setStyleSheet("background-color: transparent; border: none;")
        layout.addWidget(self.lock_btn)

    def _handle_visibility_toggle(self):
        visible = self.visibility_btn.isChecked()
        self.visibility_btn.setIcon(QIcon(HIDE_ICON if visible else SHOW_ICON))
        if self.on_visibility_toggle:
            self.on_visibility_toggle(visible)

    def _handle_add_segment(self):
        if self.on_add_segment:
            self.on_add_segment()

    def _handle_lock_toggle(self):
        locked = self.lock_btn.isChecked()
        self.lock_btn.setIcon(QIcon(LOCK_ICON if locked else UNLOCK_ICON))
        if self.on_lock_toggle:
            self.on_lock_toggle(locked)



if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication([])

    def on_visibility_toggle(visible):
        print(f"Visibility toggled: {visible}")

    def on_add_segment():
        print("Add segment clicked")

    def on_lock_toggle(locked):
        print(f"Lock toggled: {locked}")

    widget = LayerButtonsWidget("Layer 1", None, on_visibility_toggle, on_add_segment, on_lock_toggle)
    widget.show()
    app.exec()
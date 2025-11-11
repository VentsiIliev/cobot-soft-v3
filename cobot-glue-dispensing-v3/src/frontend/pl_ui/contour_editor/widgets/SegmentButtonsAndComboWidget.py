import os
import sys
from types import SimpleNamespace

from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout,
    QPushButton, QComboBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QTimer, QPoint  # Add QPoint
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout,
    QPushButton, QComboBox, QSizePolicy, QMenu, QWidgetAction  # Add QMenu, QWidgetAction
)

# --- Resource Paths ---
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","icons")
HIDE_ICON = os.path.join(RESOURCE_DIR, "hide.png")
SHOW_ICON = os.path.join(RESOURCE_DIR, "show.png")
BIN_ICON = os.path.join(RESOURCE_DIR, "BIN_BUTTON_SQUARE.png")
PLUS_ICON = os.path.join(RESOURCE_DIR, "PLUS_BUTTON.png")
LOCK_ICON = os.path.join(RESOURCE_DIR, "locked.png")
UNLOCK_ICON = os.path.join(RESOURCE_DIR, "unlocked.png")
ACTIVE_ICON = os.path.join(RESOURCE_DIR, "active.png")
INACTIVE_ICON = os.path.join(RESOURCE_DIR, "inactive.png")
DROPDOWN_OPEN_ICON = os.path.join(RESOURCE_DIR, "dropdown_open.png")
GEAR_ICON = os.path.join(RESOURCE_DIR, "SETTINGS_BUTTON.png")


class LayerSelectionPopup(QMenu):
    """Custom popup menu for layer selection"""

    def __init__(self, current_layer, on_layer_change, parent=None):
        super().__init__(parent)
        self.on_layer_change = on_layer_change
        self.current_layer = current_layer

        self.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 2px solid #007acc;
                border-radius: 8px;
                padding: 5px;
                font-size: 14px;
            }
            QMenu::item {
                padding: 8px 20px;
                margin: 2px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #e6f3ff;
                color: #007acc;
            }
            QMenu::item:pressed {
                background-color: #cce7ff;
            }
        """)

        # Add layer options
        layers = ["Workpiece", "Contour", "Fill"]
        for layer in layers:
            action = self.addAction(layer)
            action.triggered.connect(lambda checked, l=layer: self._on_layer_selected(l))

            # Mark current layer
            if layer == current_layer:
                action.setText(f"✓ {layer}")

    def _on_layer_selected(self, layer):
        if self.on_layer_change:
            self.on_layer_change(layer)

class PressAndHoldButton(QPushButton):
    """Custom button that supports press and hold functionality"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)

        self.press_timer = QTimer()
        self.press_timer.timeout.connect(self._on_long_press)
        self.press_timer.setSingleShot(True)
        self.long_press_duration = 500  # milliseconds
        self.is_long_press = False

        # Callbacks
        self.on_click_callback = None
        self.on_long_press_callback = None

    def set_click_callback(self, callback):
        """Set callback for normal click"""
        self.on_click_callback = callback

    def set_long_press_callback(self, callback):
        """Set callback for long press"""
        self.on_long_press_callback = callback

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_long_press = False
            self.press_timer.start(self.long_press_duration)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.press_timer.stop()

            if not self.is_long_press:
                # Normal click
                if self.on_click_callback:
                    self.on_click_callback()

        super().mouseReleaseEvent(event)

    def _on_long_press(self):
        """Handle long press event"""
        self.is_long_press = True
        if self.on_long_press_callback:
            self.on_long_press_callback()

class SegmentButtonsAndComboWidget(QWidget):
    def __init__(self, seg_index, segment, layer_name,
                 on_visibility, on_activate, on_delete, on_settings, on_layer_change,on_long_press):
        super().__init__()

        self.segment = segment
        self.on_visibility = on_visibility
        self.on_layer_change = on_layer_change
        self.seg_index = seg_index
        self.current_layer = layer_name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Use custom press and hold button for index label
        self.index_label = PressAndHoldButton(f"S{seg_index}")
        self.index_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.index_label.setFixedHeight(50)
        self.index_label.setFixedWidth(50)
        self.index_label.setToolTip(
            f"Segment {seg_index} - Click to activate, Hold for layer options")  # Updated tooltip
        self.index_label.setStyleSheet("text-align: center;")

        # Set callbacks for press and hold
        self.index_label.set_click_callback(on_activate)
        self.index_label.set_long_press_callback(self._show_layer_popup)  # Changed this line

        layout.addWidget(self.index_label)

        # Buttons
        self.visibility_btn = self._create_visibility_button()
        layout.addWidget(self.visibility_btn)

        # self.on_activate = on_activate
        self.active_btn = self._create_icon_button(
            ACTIVE_ICON if getattr(segment, "is_active", False) else INACTIVE_ICON,
            "Set as active segment",
            on_activate
        )
        # layout.addWidget(self.active_btn)

        self.delete_btn = self._create_icon_button(
            BIN_ICON, "Delete this segment", on_delete
        )
        layout.addWidget(self.delete_btn)

        # Updated settings button with gear icon
        self.settings_btn = self._create_icon_button(
            GEAR_ICON, "Segment settings", on_settings
        )
        layout.addWidget(self.settings_btn)

        # # Combo Box for Layer Selection
        # self.combo_box = QComboBox()
        # self.combo_box.addItems(["External", "Contour", "Fill"])
        # self.combo_box.setCurrentText(layer_name)
        # self.combo_box.setFixedHeight(50)
        # self.combo_box.setMinimumWidth(100)
        # self.combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # self.combo_box.currentTextChanged.connect(on_layer_change)
        # layout.addWidget(self.combo_box)

        layout.addStretch()

    def _show_layer_popup(self):
        """Show layer selection popup on long press"""
        popup = LayerSelectionPopup(
            current_layer=self.current_layer,
            on_layer_change=self._handle_layer_change,
            parent=self
        )

        # Position popup near the button
        button_pos = self.index_label.mapToGlobal(QPoint(0, 0))
        popup_pos = QPoint(button_pos.x(), button_pos.y() + self.index_label.height() + 5)
        popup.exec(popup_pos)

    def _handle_layer_change(self, new_layer):
        """Handle layer change from popup"""
        self.current_layer = new_layer
        if self.on_layer_change:
            self.on_layer_change(new_layer)
        print(f"Layer changed to: {new_layer}")

    def update_layer(self, new_layer):
        """Update the current layer (call this from parent when layer changes)"""
        self.current_layer = new_layer

    def _create_icon_button(self, icon_path, tooltip, callback):
        button = QPushButton()
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(50, 50))
        button.setToolTip(tooltip)
        button.setFixedSize(80, 80)
        button.clicked.connect(callback)
        button.setStyleSheet("background-color: transparent; border: none;")
        return button

    def _create_visibility_button(self):
        button = QPushButton()
        button.setCheckable(True)
        is_visible = getattr(self.segment, "visible", True)
        button.setChecked(is_visible)
        button.setIcon(QIcon(HIDE_ICON if is_visible else SHOW_ICON))
        button.setIconSize(QSize(50, 50))
        button.setToolTip("Toggle segment visibility")
        button.setFixedSize(80, 80)
        button.clicked.connect(lambda: self._toggle_visibility(button))
        button.setStyleSheet("background-color: transparent; border: none;")
        return button

    def _toggle_visibility(self, button):
        is_visible = button.isChecked()
        button.setIcon(QIcon(HIDE_ICON if is_visible else SHOW_ICON))
        self.on_visibility(button)


# --- Testing ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    segment = SimpleNamespace(visible=True, is_active=False)
    layer_name = "Contour"


    def on_visibility(btn):
        print("Visibility toggled:", btn.isChecked())


    def on_activate():
        print("Activated")


    def on_delete():
        print("Deleted")


    def on_settings():
        print("Settings opened")


    def on_layer_change(value):
        print("Layer changed to:", value)


    def on_long_press(seg_index):
        print(f"Long press detected on segment {seg_index}!")



    widget = SegmentButtonsAndComboWidget(
        seg_index=0,
        segment=segment,
        layer_name=layer_name,
        on_visibility=on_visibility,
        on_activate=on_activate,
        on_delete=on_delete,
        on_settings=on_settings,
        on_layer_change=on_layer_change,
        on_long_press=on_long_press
    )
    widget.show()
    sys.exit(app.exec())

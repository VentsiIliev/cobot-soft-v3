
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from deprecated.pl_gui.customWidgets.SwitchButton import QToggle
from deprecated.pl_gui.customWidgets.Drawer import Drawer

class TogglePanel(Drawer):
    def __init__(self, labels, parent=None, onToggleCallback=None, cameraToggleCallback=None):
        super().__init__(parent)

        self.setObjectName("TogglePanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Use a QFrame for visible border/background
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setStyleSheet("""
            QFrame#mainFrame {
                background-color: white;
                border-radius: 12px;
                border: 2px solid #905BA9;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(self.main_frame)

        main_layout = QVBoxLayout(self.main_frame)
        self.toggle_map = {}
        self.label_to_toggle = {}

        for label_text in labels:
            row = QHBoxLayout()
            label = QLabel(label_text)
            toggle = QToggle()
            toggle.setFixedHeight(20)
            toggle.active_color = QColor("#905BA9")
            toggle.disabled_color = QColor("#666")
            toggle.bg_color = QColor("#666")
            toggle.clicked.connect(lambda checked, t=toggle: self.onToggle(t))
            self.toggle_map[toggle] = label_text
            self.label_to_toggle[label_text] = toggle
            row.addWidget(label)
            row.addStretch(1)
            row.addWidget(toggle)
            main_layout.addLayout(row)

        camera_toggle_row = QHBoxLayout()
        camera_label = QLabel("Camera View")
        camera_toggle = QToggle()
        camera_toggle.setFixedHeight(20)
        camera_toggle.active_color = QColor("#905BA9")
        camera_toggle.disabled_color = QColor("#666")
        camera_toggle.bg_color = QColor("#666")
        camera_toggle.clicked.connect(
            lambda checked: self.cameraToggleCallback() if self.cameraToggleCallback else print("No camera toggle callback"))
        camera_toggle_row.addWidget(camera_label)
        camera_toggle_row.addStretch(1)
        camera_toggle_row.addWidget(camera_toggle)
        main_layout.addLayout(camera_toggle_row)
        main_layout.addStretch(1)

        self.cameraToggleCallback = cameraToggleCallback
        self.onToggleCallback = onToggleCallback
        self.labels = labels

    def setToggleState(self, label_text, state):
        toggle = self.label_to_toggle.get(label_text)
        if toggle:
            toggle.blockSignals(True)
            toggle.setChecked(state)
            toggle.blockSignals(False)

    def onToggle(self, toggle):
        label_text = self.toggle_map.get(toggle, "Unknown")
        state = toggle.isChecked()
        if self.onToggleCallback:
            try:
                self.onToggleCallback(label_text, state)
            except Exception as e:
                print(f"Error in onToggleCallback: {e}")

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    panel = TogglePanel(["Option 1", "Option 2"])
    panel.setWindowTitle("Toggle Panel Example")
    panel.resize(200, 300)
    panel.show()
    sys.exit(app.exec())
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QPushButton, QLabel,
    QMainWindow
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QFont, QLinearGradient
from enum import Enum
from deprecated.pl_gui.customWidgets.LanguageSelectorWidget import LanguageSelectorWidget
from API.MessageBroker import MessageBroker

class MachineState(Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING..."
    RUNNING = "RUNNING"
    PAUSING = "PAUSING..."
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    INITIALIZING = "INITIALIZING..."


class StatusLight(QWidget):
    def __init__(self, color=QColor(200, 200, 200)):
        super().__init__()
        self.color = color
        self._brightness = 0.2
        self.setFixedSize(24, 24)
        self.animation = QPropertyAnimation(self, b"brightness")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def get_brightness(self):
        return self._brightness

    def set_brightness(self, value):
        self._brightness = value
        self.update()

    brightness = property(get_brightness, set_brightness)

    def set_active(self, active):
        target = 1.0 if active else 0.2
        self.animation.setStartValue(self.brightness)
        self.animation.setEndValue(target)
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = 24

        if self.brightness > 0.5:
            glow_color = QColor(self.color)
            glow_color.setAlphaF(0.3)
            painter.setBrush(glow_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(0, 0, size, size)

        gradient = QLinearGradient(0, 0, 0, 18)
        main_color = QColor(self.color)
        main_color.setAlphaF(self.brightness)
        darker_color = QColor(self.color).darker(120)
        darker_color.setAlphaF(self.brightness * 0.8)
        gradient.setColorAt(0, main_color)
        gradient.setColorAt(1, darker_color)
        painter.setBrush(gradient)
        painter.drawEllipse(3, 3, 18, 18)

        if self.brightness > 0.3:
            highlight = QColor(255, 255, 255, int(self.brightness * 150))
            painter.setBrush(highlight)
            painter.drawEllipse(7, 6, 6, 6)


class MaterialButton(QPushButton):
    def __init__(self, text, color="#6750A4",font_size = 12):
        super().__init__(text)
        self.color = color
        self.font_size = font_size
        self.setMinimumHeight(50)
        self.setMaximumHeight(100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Roboto", 9, QFont.Weight.Medium))
        self.apply_style()

    def apply_style(self):
        lighter = QColor(self.color).lighter(110).name()
        darker = QColor(self.color).darker(110).name()
        self.setStyleSheet(f"""
            QPushButton {{
                background: {self.color};
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                padding: 4px 12px;
                font-size: {self.font_size}px;
            }}
            QPushButton:hover {{ background: {lighter}; }}
            QPushButton:pressed {{ background: {darker}; }}
            QPushButton:disabled {{
                background: #E8DEF8;
                color: #79747E;
            }}
        """)


class MachineToolbar(QWidget):
    state_changed = pyqtSignal(MachineState)
    start_request = pyqtSignal()

    # Add signal for thread-safe GUI updates
    gui_update_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.broker = MessageBroker()
        self.current_state = MachineState.STOPPED
        self.setup_ui()
        self.setup_timer()
        self.update_display()

        # Connect the thread-safe signal to the actual update method
        self.gui_update_signal.connect(self._update_info_label_safe)

        # Subscribe to broker - weak references will handle cleanup automatically
        broker = MessageBroker()
        broker.subscribe("vision/state", self.update_info_label_threadsafe)

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget { background: #FFFBFE; font-family: 'Roboto'; }
        """)
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 8, 10, 8)

        # Lights
        self.lights = {}
        light_configs = [
            ("POWER", QColor(76, 175, 80)),
            ("ACTIVE", QColor(103, 80, 164)),
            ("ERROR", QColor(179, 38, 30))
        ]
        for key, color in light_configs:
            light = StatusLight(color)
            self.lights[key] = light
            layout.addWidget(light)

        # State label
        self.state_label = QLabel("STOPPED")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setFont(QFont("Roboto", 10, QFont.Weight.Bold))
        self.state_label.setStyleSheet("""
            background: #F3EDF7;
            color: #6750A4;
            border-radius: 8px;
            padding: 4px 10px;
        """)
        layout.addWidget(self.state_label)

        # Spacer
        layout.addStretch()
        # Language Selector (centered)
        self.language_selector = LanguageSelectorWidget()
        self.language_selector.languageChanged.connect(self.handle_language_change)
        self.language_selector.setFixedWidth(200)
        layout.addWidget(self.language_selector)
        # New text label between indicators and buttons
        # self.info_label = QLabel("Machine Info")
        # self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.info_label.setFont(QFont("Roboto", 9, QFont.Weight.Normal))
        # self.info_label.setStyleSheet("""
        #     background: #E8DEF8;
        #     color: #6750A4;
        #     border-radius: 8px;
        #     padding: 2px 8px;
        # """)
        # layout.addWidget(self.info_label)
        # self.info_label.hide()

        # Spacer
        layout.addStretch()

        # Buttons
        self.start_btn = MaterialButton("START", "#6750A4")
        self.stop_btn = MaterialButton("STOP", "#B3261E")
        self.pause_btn = MaterialButton("PAUSE", "#F57C00")
        self.clean_btn = MaterialButton("CLEAN", "#F57C00")
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.pause_btn)
        layout.addWidget(self.clean_btn)

        self.start_btn.clicked.connect(self.start_machine)
        self.pause_btn.clicked.connect(self.pause_machine)
        self.stop_btn.clicked.connect(self.stop_machine)
        self.clean_btn.clicked.connect(self.clean_nozzle)

    def handle_language_change(self,message):
        self.broker.publish("Language","Change")
        # print("Language changed")

    def update_info_label_threadsafe(self, message):
        """Thread-safe version that emits signal instead of directly updating GUI"""
        try:
            info = message.get("state", "No info available")
            # print(f"Received info: {info}")

            # Emit signal to update GUI on main thread
            self.gui_update_signal.emit(info)
        except RuntimeError as e:
            print(f"Widget deleted during callback: {e}")
            # The weak reference system will handle cleanup automatically

    def _update_info_label_safe(self, info):
        """Main thread GUI update method"""
        # Check if widgets still exist before updating
        if not self.start_btn or not self.pause_btn or not self.stop_btn:
            print("Warning: Buttons have been deleted, skipping update")
            return

        try:
            if info == "waiting_image":
                # disable buttons
                self.start_btn.setEnabled(False)
                self.pause_btn.setEnabled(False)
                self.stop_btn.setEnabled(False)
                self.set_state(MachineState.INITIALIZING)
            else:
                # enable buttons
                self.start_btn.setEnabled(True)
                self.pause_btn.setEnabled(True)
                self.stop_btn.setEnabled(True)
                self.set_state(MachineState.STOPPED)
        except RuntimeError as e:
            print(f"Error updating GUI elements: {e}")
            # Weak references will handle cleanup automatically

    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.complete_transition)
        self.timer.setSingleShot(True)

    def start_machine(self):
        if self.current_state in [MachineState.STOPPED, MachineState.PAUSED]:
            self.set_state(MachineState.STARTING)
            self.timer.start(1500)
        self.start_request.emit()

    def pause_machine(self):
        if self.current_state == MachineState.RUNNING:
            self.set_state(MachineState.PAUSING)
            self.timer.start(800)

    def stop_machine(self):
        if self.current_state != MachineState.STOPPED:
            self.set_state(MachineState.STOPPED)

    def  clean_nozzle(self):
        """Placeholder for cleaning nozzle functionality"""
        print("Cleaning nozzle... (not implemented)")

    def complete_transition(self):
        import random
        if self.current_state == MachineState.STARTING:
            self.set_state(MachineState.ERROR if random.random() < 0.1 else MachineState.RUNNING)
        elif self.current_state == MachineState.PAUSING:
            self.set_state(MachineState.PAUSED)

    def set_state(self, new_state):
        self.current_state = new_state
        self.update_display()
        self.state_changed.emit(new_state)

    def update_display(self):
        for light in self.lights.values():
            light.set_active(False)

        state_configs = {
            MachineState.STOPPED: ([], "#79747E", "#F3EDF7"),
            MachineState.STARTING: (["POWER"], "#F57C00", "#FFF8E1"),
            MachineState.RUNNING: (["POWER", "ACTIVE"], "#6750A4", "#F3EDF7"),
            MachineState.PAUSING: (["POWER", "ACTIVE"], "#F57C00", "#FFF8E1"),
            MachineState.PAUSED: (["POWER"], "#F57C00", "#FFF8E1"),
            MachineState.ERROR: (["ERROR"], "#B3261E", "#FCEEEE")
        }

        if self.current_state in state_configs:
            active_lights, text_color, bg_color = state_configs[self.current_state]
            for light_name in active_lights:
                if light_name in self.lights:
                    self.lights[light_name].set_active(True)
            self.state_label.setText(self.current_state.value)
            self.state_label.setStyleSheet(f"""
                background: {bg_color};
                color: {text_color};
                border-radius: 8px;
                padding: 4px 10px;
            """)

        if self.current_state == MachineState.INITIALIZING:
            self.state_label.setText("INITIALIZING...")
            # disable buttons - check if they exist first
            if hasattr(self, 'start_btn') and self.start_btn:
                self.start_btn.setEnabled(False)
            if hasattr(self, 'pause_btn') and self.pause_btn:
                self.pause_btn.setEnabled(False)
            if hasattr(self, 'stop_btn') and self.stop_btn:
                self.stop_btn.setEnabled(False)
        else:
            if hasattr(self, 'start_btn') and self.start_btn:
                self.start_btn.setEnabled(self.current_state in [MachineState.STOPPED, MachineState.PAUSED])
            if hasattr(self, 'pause_btn') and self.pause_btn:
                self.pause_btn.setEnabled(self.current_state == MachineState.RUNNING)
            if hasattr(self, 'stop_btn') and self.stop_btn:
                self.stop_btn.setEnabled(self.current_state != MachineState.STOPPED)

    def closeEvent(self, event):
        """Clean up when widget is closed - weak references handle most cleanup automatically"""
        super().closeEvent(event)

    def deleteLater(self):
        """Override deleteLater - weak references handle cleanup automatically"""
        super().deleteLater()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Machine Toolbar Header")
        self.setMinimumSize(600, 200)

        # Toolbar-style header
        toolbar_widget = MachineToolbar()
        toolbar_widget.state_changed.connect(lambda s: print(f"State: {s.value}"))
        self.addToolBarBreak()  # Optional: for multiple toolbars
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.create_toolbar(toolbar_widget))

    def create_toolbar(self, widget):
        from PyQt6.QtWidgets import QToolBar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.addWidget(widget)
        return toolbar


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
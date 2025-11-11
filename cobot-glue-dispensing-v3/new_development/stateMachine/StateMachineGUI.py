import sys
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
)
from PyQt6.QtCore import QTimer, pyqtSignal, QObject

# Import your state machine modules
from new_development.stateMachine.DummyGlueSprayingApplication import DummyGlueSprayingApplication
from new_development.stateMachine.StateMachineEnhancedGlueSprayingApplication import StateMachineEnhancedGlueSprayingApplication


class EmittingStream(QObject):
    text_written = pyqtSignal(str)

    def write(self, text):
        if text.strip():  # avoid empty newlines
            self.text_written.emit(text)

    def flush(self):
        pass  # not needed for this simple logger


class StateMachineGUI(QWidget):
    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance

        self.setWindowTitle("State Machine Tester")
        self.resize(500, 400)

        layout = QVBoxLayout()

        # State label
        self.state_label = QLabel(f"Current State: {self.app_instance.get_current_state().name}")
        self.state_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.state_label)

        # Buttons
        buttons = [
            ("Start", lambda: self.app_instance.start(contourMatching=True)),
            ("Calibrate Robot", self.app_instance.calibrateRobot),
            ("Create Workpiece", self.app_instance.createWorkpiece),
            ("Emergency Stop", self.app_instance.emergency_stop),
            ("Reset", self.app_instance.reset),
        ]

        # Add these after your main control buttons
        simulate_buttons = [
            ("Simulate Success", lambda: app_instance.state_machine.process_event("OPERATION_COMPLETED")),
            ("Simulate Failure", lambda: app_instance.state_machine.process_event("OPERATION_FAILED")),
            ("Simulate Error", lambda: app_instance.state_machine.process_event("ERROR_OCCURRED")),
        ]

        for text, cmd in simulate_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _, c=cmd: self.run_command(c))
            layout.addWidget(btn)

        for text, cmd in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _, c=cmd: self.run_command(c))
            layout.addWidget(btn)

        # Log output panel
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #111; color: #0f0; font-family: Consolas;")
        layout.addWidget(self.log_output)

        self.setLayout(layout)

        # Timer to update state label
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_state_label)
        self.timer.start(200)

        # Redirect stdout to the GUI log
        sys.stdout = EmittingStream(text_written=self.append_log)
        sys.stderr = EmittingStream(text_written=self.append_log)

    def run_command(self, command):
        def worker():
            result = command()
            print("[GUI Command Result]", result)
        threading.Thread(target=worker, daemon=True).start()

    def update_state_label(self):
        self.state_label.setText(f"Current State: {self.app_instance.get_current_state().name}")

    def append_log(self, text):
        self.log_output.append(text.strip())


if __name__ == "__main__":
    original_app = DummyGlueSprayingApplication()
    app_instance = StateMachineEnhancedGlueSprayingApplication(original_app)

    qt_app = QApplication(sys.argv)
    gui = StateMachineGUI(app_instance)
    gui.show()
    sys.exit(qt_app.exec())

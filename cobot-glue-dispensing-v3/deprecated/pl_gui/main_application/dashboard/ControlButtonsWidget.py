from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy
from PyQt6.QtCore import pyqtSignal
from deprecated.pl_gui.main_application.dashboard.MachineIndicatorsWidget import MaterialButton
from API.MessageBroker import MessageBroker
from GlueDispensingApplication.GlueSprayApplicationState import GlueSprayApplicationState

class ControlButtonsWidget(QWidget):
    # Define custom signals
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.connect_signals()
        self.broker = MessageBroker()
        # self.broker.subscribe("system/state", self.on_system_status_update)

    def init_ui(self):
        # Main layout for the widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top frame for Start/Stop buttons (row 0, col 2)
        top_frame = QFrame()
        top_frame.setStyleSheet("QFrame {border: none; background-color: transparent;}")
        top_frame.setMinimumHeight(120)
        top_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(5, 5, 5, 5)

        # Start and Stop buttons
        self.start_btn = MaterialButton("Start", font_size=20)
        self.start_btn.setEnabled(False)  # Initially disabled
        self.stop_btn = MaterialButton("Stop", font_size=20)
        self.stop_btn.setEnabled(False)  # Initially disabled

        top_layout.addWidget(self.start_btn)
        top_layout.addWidget(self.stop_btn)

        # Bottom frame for Pause button (row 1, col 2)
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet("QFrame {border: none; background-color: transparent;}")
        bottom_frame.setMinimumHeight(120)
        bottom_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(5, 5, 5, 5)

        # Pause button
        self.pause_btn = MaterialButton("Pause", font_size=20)
        self.pause_btn.setEnabled(False)  # Initially disabled
        bottom_layout.addWidget(self.pause_btn)

        # Add frames to main layout
        main_layout.addWidget(top_frame)
        main_layout.addWidget(bottom_frame)

    def connect_signals(self):
        """Connect button clicks to custom signals"""
        self.start_btn.clicked.connect(self.start_clicked.emit)
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        self.pause_btn.clicked.connect(self.pause_clicked.emit)

    def get_start_button(self):
        """Return reference to start button for connecting signals"""
        return self.start_btn

    def get_stop_button(self):
        """Return reference to stop button for connecting signals"""
        return self.stop_btn

    def get_pause_button(self):
        """Return reference to pause button for connecting signals"""
        return self.pause_btn

    def enable_start_button(self, enabled=True):
        """Enable or disable the start button"""
        self.start_btn.setEnabled(enabled)

    def enable_stop_button(self, enabled=True):
        """Enable or disable the stop button"""
        self.stop_btn.setEnabled(enabled)

    def enable_pause_button(self, enabled=True):
        """Enable or disable the pause button"""
        self.pause_btn.setEnabled(enabled)

    def on_system_status_update(self, state):
        if state == GlueSprayApplicationState.IDLE:
            self.start_btn.setEnabled(True)
        elif state == GlueSprayApplicationState.STARTED:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.pause_btn.setEnabled(True)
        elif state == GlueSprayApplicationState.INITIALIZING:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)

    def clean_up(self):
        """Cleanup subscriptions and resources"""
        print("Cleaning up ControlButtonsWidget")
        self.broker.unsubscribe("system/state", self.on_system_status_update)
        self.broker = None
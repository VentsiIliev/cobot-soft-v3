from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QMetaObject, pyqtSlot

from modules.shared.MessageBroker import MessageBroker
from src.frontend.pl_ui.ui.widgets.MaterialButton import MaterialButton
from src.frontend.pl_ui.localization import TranslationKeys, TranslatableWidget
from src.backend.GlueDispensingApplication.GlueSprayApplicationState import GlueSprayApplicationState
from src.backend.GlueDispensingApplication.robot.robotService.RobotService import RobotServiceState


class ControlButtonsWidget(TranslatableWidget):
    # Define custom signals
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, auto_retranslate=False)
        
        # Track current states
        self.is_paused = False
        self.robot_state = None
        self.app_state = None
        
        self.init_ui()
        self.connect_signals()
        
        # Initialize translations after UI is created
        self.init_translations()
        self.broker = MessageBroker()
        self.broker.subscribe("system/state", self.on_system_status_update)
        self.broker.subscribe("robot-service/state", self.on_robot_service_state_update)

    def init_ui(self) -> None:
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



        # Start and Stop buttons (text set in retranslate())
        self.start_btn = MaterialButton("", font_size=20)
        self.start_btn.setEnabled(False)  # Initially disabled
        self.stop_btn = MaterialButton("", font_size=20)
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

        # Pause button (text set in retranslate())
        self.pause_btn = MaterialButton("", font_size=20)
        self.pause_btn.setEnabled(False)  # Initially disabled
        bottom_layout.addWidget(self.pause_btn)

        # Add frames to main layout
        main_layout.addWidget(top_frame)
        main_layout.addWidget(bottom_frame)

    def connect_signals(self) -> None:
        """Connect button clicks to custom signals"""
        self.start_btn.clicked.connect(self.start_clicked.emit)
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        self.pause_btn.clicked.connect(self.pause_clicked.emit)

    def enable_start_button(self, enabled=True) -> None:
        """Enable or disable the start button"""
        self.start_btn.setEnabled(enabled)

    def enable_stop_button(self, enabled=True) -> None:
        """Enable or disable the stop button"""
        self.stop_btn.setEnabled(enabled)

    def enable_pause_button(self, enabled=True) -> None:
        """Enable or disable the pause button"""
        self.pause_btn.setEnabled(enabled)

    def on_robot_service_state_update(self, robot_state) -> None:
        """Handle robot service state updates for pause/resume button management"""
        try:
            if not self.pause_btn:
                return

            if self.robot_state == robot_state:
                return
            # Store the state and schedule GUI update on main thread
            self.robot_state = robot_state
            QMetaObject.invokeMethod(self, "_update_button_states_safe", Qt.ConnectionType.QueuedConnection)
        except RuntimeError:
            # Widget has been deleted, silently ignore
            pass

    def on_system_status_update(self, state) -> None:
        """Handle GlueSprayApplication state updates"""
        try:
            if not self.start_btn or not self.stop_btn or not self.pause_btn:
                return

            # Store the state and schedule GUI update on main thread
            # FIST CHECK IF THE RECEIVED STATE IS DIFFERENT FROM THE CURRENT ONE
            if self.app_state == state:
                return
            self.app_state = state
            QMetaObject.invokeMethod(self, "_update_button_states_safe", Qt.ConnectionType.QueuedConnection)
        except RuntimeError:
            # Widget has been deleted, silently ignore
            pass

    @pyqtSlot()
    def _update_button_states_safe(self) -> None:
        """Thread-safe method to update button states - called on main thread via QMetaObject.invokeMethod"""
        try:
            # Double-check that widgets still exist (widget could be deleted between queuing and execution)
            if not self.start_btn or not self.stop_btn or not self.pause_btn:
                return
            
            self.update_button_states()
        except RuntimeError:
            # Widget has been deleted, silently ignore
            pass

    def update_button_states(self) -> None:
        """Update button states and text based on current application and robot states"""
        if not self.app_state:
            return

        # Special handling for robot PAUSED state - override app state logic
        if self.robot_state == RobotServiceState.PAUSED:
            # When robot is paused, keep stop/pause enabled regardless of app state
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)  # Allow stopping from paused state
            self.pause_btn.setEnabled(True)  # Allow resuming from paused state
            self.is_paused = True
            self.pause_btn.setText("Resume")  # Show Resume when paused
            return

        # Handle GlueSprayApplication states (when robot is not paused)
        if self.app_state == GlueSprayApplicationState.IDLE:
            # Only start button enabled when system is idle
            self.start_btn.setEnabled(True)
            print(f"START BUTTON ENABLED: {self.start_btn.isEnabled()}")
            self.stop_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            # Reset pause button text to "Pause"
            self.is_paused = False
            self.pause_btn.setText(self.tr(TranslationKeys.Dashboard.PAUSE))
            
        elif self.app_state == GlueSprayApplicationState.STARTED:
            # When started, disable start and enable stop/pause
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.pause_btn.setEnabled(True)
            
            # Handle pause button text (robot should not be paused here due to early return above)
            self.is_paused = False
            self.pause_btn.setText(self.tr(TranslationKeys.Dashboard.PAUSE))
                
        elif self.app_state == GlueSprayApplicationState.INITIALIZING:
            # All buttons disabled during initialization
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)

    def retranslate(self) -> None:
        """Update all text labels for language changes - called automatically"""
        self.start_btn.setText(self.tr(TranslationKeys.Dashboard.START))
        self.stop_btn.setText(self.tr(TranslationKeys.Dashboard.STOP))
        self.pause_btn.setText(self.tr(TranslationKeys.Dashboard.PAUSE))

    def clean_up(self) -> None:
        """Clean up resources when the widget is closed"""
        self.broker.unsubscribe("system/state", self.on_system_status_update)
        self.broker.unsubscribe("robot-service/state", self.on_robot_service_state_update)

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = ControlButtonsWidget()
    window.show()
    sys.exit(app.exec())
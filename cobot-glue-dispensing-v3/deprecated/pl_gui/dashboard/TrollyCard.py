from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
import os
from API.MessageBroker import MessageBroker
from GlueDispensingApplication.SensorPublisher import Sensor, SENSOR_STATE_NO_COMMUNICATION, SENSOR_STATE_CONNECTED, \
    SENSOR_STATE_DISCONNECTED, SENSOR_STATE_RECONNECTING, SENSOR_STATE_READY, SENSOR_STATE_ERROR, \
    SENSOR_STATE_INITIALIZING,SENSOR_STATE_USB_NOT_CONNECTED
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
# Fixed missing quotes and unused constants removed; using ICON_PATH below instead

class TrollyCard(QFrame):
    updateConnectionSignal = pyqtSignal(bool)
    ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "resources","pl_ui_icons")
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logTag = "TrolleyCard"
        self.setObjectName("TrolleyCard")

        broker = MessageBroker()
        broker.subscribe("Trolly_22/STATE", self.on_left_trolley_state)
        broker.subscribe("Trolly_20/STATE", self.on_right_trolley_state)

        # Track connection status for each trolley
        self._trolley_states = {
            "left": None,
            "right": None
        }

        self._build_ui()
        self._apply_styles()


    def _build_ui(self):
        self.setMinimumHeight(180)
        self.setMinimumWidth(120)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)

        # --- Trolley Icon Layout ---
        self.status_layout = QHBoxLayout()
        self.status_layout.setSpacing(20)
        self.status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.trolley_1 = self._create_trolley_icon("Trolley 1")
        self.trolley_2 = self._create_trolley_icon("Trolley 2")

        self.status_layout.addLayout(self.trolley_1["layout"])
        self.status_layout.addLayout(self.trolley_2["layout"])
        self.layout.addLayout(self.status_layout)

        # Initialize icons to gray
        self._set_trolley_pixmap(self.trolley_1["icon"], "gray")
        self._set_trolley_pixmap(self.trolley_2["icon"], "gray")


    def on_left_trolley_state(self, message):
        self._handle_state_message("left", message)

    def on_right_trolley_state(self, message):
        self._handle_state_message("right", message)

    def _handle_state_message(self, trolley_id, message):
        message = message.strip()
        # print("_handle_state_message Received Message ",message)
        if message == SENSOR_STATE_READY:
            connected = True
        elif message == SENSOR_STATE_DISCONNECTED:
            connected = False
        elif message == SENSOR_STATE_ERROR:
            connected = False
        elif message == SENSOR_STATE_NO_COMMUNICATION:
            connected = False
        elif message == SENSOR_STATE_RECONNECTING:
            connected = False
        else:
            print(f"[WARN] Unknown state payload: {message}")
            return

        self.update_trolley_status(trolley_id, connected,message)
        self.updateConnectionSignal.emit(connected)

    def _create_trolley_icon(self, label_text):
        layout = QVBoxLayout()
        label = QLabel(label_text)
        label.setObjectName("statusLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel()
        icon.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        icon.setMinimumSize(40, 40)
        icon.setScaledContents(True)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setObjectName("trolleyIcon")

        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        return {"layout": layout, "icon": icon, "label": label}

    def _apply_styles(self):
        self.setStyleSheet("""
            QFrame#TrolleyCard {
                border: 1px solid #ccc;
                border-radius: 12px;
                background-color: #ffffff;
                padding: 15px;
            }
            QLabel#titleLabel {
                font-size: 20px;
                font-weight: bold;
                color: #333;
            }
            QLabel#statusLabel {
                font-size: 14px;
                color: #666;
            }
        """)

    def _set_trolley_pixmap(self, label: QLabel, color: str):
        icon_path = os.path.join(self.ICON_PATH, f"trolley_{color}.png")
        pixmap = QPixmap(icon_path)
        if pixmap.isNull():
            print(f"[WARN] Icon not found: {icon_path}")
            label.clear()
            return
        label.original_pixmap = pixmap
        self._rescale_pixmap(label)

    def _rescale_pixmap(self, label: QLabel):
        if hasattr(label, "original_pixmap"):
            size = label.size()
            scaled = label.original_pixmap.scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rescale_pixmap(self.trolley_1["icon"])
        self._rescale_pixmap(self.trolley_2["icon"])



    def update_trolley_status(self, trolley_id: str, connected: bool,message:str):
        # Skip update if state hasn't changed
        if self._trolley_states.get(trolley_id) == connected:
            return

        self._trolley_states[trolley_id] = connected  # Cache new state
        color = "purple" if connected else "gray"
        # status_text = "Connected" if connected else "Not Connected"
        status_text = message
        if trolley_id == "left":
            self._set_trolley_pixmap(self.trolley_1["icon"], color)
            self.trolley_1["label"].setText(status_text)
        elif trolley_id == "right":
            self._set_trolley_pixmap(self.trolley_2["icon"], color)
            self.trolley_2["label"].setText(status_text)

    def unsubscribe(self):
        broker = MessageBroker()
        broker.unsubscribe("Trolly_22/STATE", self.on_left_trolley_state)
        broker.unsubscribe("Trolly_20/STATE", self.on_right_trolley_state)

    def closeEvent(self, event):
        self.unsubscribe()
        print(f"[DEBUG] {self.logTag} CLEANING UP")
        # Call base implementation
        super().closeEvent(event)


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    from GlueDispensingApplication.SensorPublisher import SensorPublisher, SENSOR_STATE_READY
    from API.MessageBroker import MessageBroker
    from GlueDispensingApplication.tools.Trolly import Trolly

    app = QApplication([])

    publisher = SensorPublisher()
    broker = MessageBroker()
    card = TrollyCard()
    sensor= Trolly(22)
    sensor2= Trolly(20)

    publisher.registerSensor(sensor)
    publisher.registerSensor(sensor2)
    publisher.start()

    card.show()
    app.exec()

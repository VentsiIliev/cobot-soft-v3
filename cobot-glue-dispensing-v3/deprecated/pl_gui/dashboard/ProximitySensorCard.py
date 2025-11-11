from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout,QHBoxLayout,QFrame
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QFrame, QSizePolicy
)
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt, QTimer
import sys
from API.MessageBroker import MessageBroker
from GlueDispensingApplication.tools.ProximitySensor import ProximitySensor,DetectionStatus
from GlueDispensingApplication.SensorPublisher import Sensor, SENSOR_STATE_NO_COMMUNICATION, SENSOR_STATE_CONNECTED, \
    SENSOR_STATE_DISCONNECTED, SENSOR_STATE_RECONNECTING, SENSOR_STATE_READY, SENSOR_STATE_ERROR, \
    SENSOR_STATE_INITIALIZING,SENSOR_STATE_USB_NOT_CONNECTED
from GlueDispensingApplication.tools.ProximitySensor import DetectionStatus
class SensorCard(QFrame,):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logTag = "SensorCard"

        broker = MessageBroker()
        broker.subscribe("ProximitySensor_13/STATE",self.updateStatus)

        self.setStyleSheet("""
            QFrame {
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
        self.setMinimumHeight(180)
        self.setMinimumWidth(120)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)

        # --- Status indicators ---
        self.status_layout = QHBoxLayout()
        self.left_indicator = self._create_indicator("Left")
        self.right_indicator = self._create_indicator("Right")
        self.status_layout.addLayout(self.left_indicator['layout'])
        self.status_layout.addLayout(self.right_indicator['layout'])
        self.layout.addLayout(self.status_layout)

    def updateDotIndicator(self, message):
        if message == DetectionStatus.NOTHING_DETECTED.value:
            # Both indicators gray
            self.left_indicator['dot'].setStyleSheet("background-color: #AAAAAA; border-radius: 20px;")
            self.right_indicator['dot'].setStyleSheet("background-color: #AAAAAA; border-radius: 20px;")
        elif message == DetectionStatus.DETECTED_LEFT.value:
            # Left indicator purple, right indicator gray
            self.left_indicator['dot'].setStyleSheet("background-color: #800080; border-radius: 20px;")
            self.right_indicator['dot'].setStyleSheet("background-color: #AAAAAA; border-radius: 20px;")
        elif message == DetectionStatus.DETECTED_RIGHT.value:
            # Left indicator gray, right indicator purple
            self.left_indicator['dot'].setStyleSheet("background-color: #AAAAAA; border-radius: 20px;")
            self.right_indicator['dot'].setStyleSheet("background-color: #800080; border-radius: 20px;")
        elif message == DetectionStatus.DETECTED_BOTH.value:
            # Both indicators purple
            self.left_indicator['dot'].setStyleSheet("background-color: #800080; border-radius: 20px;")
            self.right_indicator['dot'].setStyleSheet("background-color: #800080; border-radius: 20px;")
        else:
            # Unknown detection status
            print("UNKNOWN DETECTION STATUS IN PROXIMITY CARD:", message)

    def updateStatus(self,status):
        self.left_indicator["label"].setText(status)
        self.right_indicator["label"].setText(status)
        # if status == SENSOR_STATE_READY:
        #     self.left_indicator["label"].setText("Connected")
        #     self.right_indicator["label"].setText("Connected")
        # elif status == "Disconnected":
        #     self.left_indicator["label"].setText("Disconnected")
        #     self.right_indicator["label"].setText("Disconnected")
        # else:
        #     self.left_indicator["label"].setText("Unknown")
        #     self.right_indicator["label"].setText("Unknown")

    def _create_indicator(self, label_text):
        layout = QVBoxLayout()
        label = QLabel(label_text)
        label.setObjectName("statusLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dot = QLabel()
        dot.setFixedSize(40, 40)
        dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot.setStyleSheet("background-color: #ccc; border-radius: 20px; border: 2px solid #444;")

        layout.addWidget(dot, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        return {"layout": layout, "dot": dot, "label": label}

    def closeEvent(self, event):
        print(f"{self.logTag}: Cleaning up before destruction...")

        # If using a real MessageBroker that allows unsubscribe:
        broker = MessageBroker()
        broker.unsubscribe("ProximitySensor_13/STATE",self.updateStatus)  # if supported

        # Call base implementation
        super().closeEvent(event)

    def set_indicator_color(self, widget, color):
        widget.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 20px;
                border: 2px solid #555;
            }}
        """)

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    from GlueDispensingApplication.SensorPublisher import SensorPublisher
    from API.MessageBroker import MessageBroker
    from GlueDispensingApplication.tools.ProximitySensor import ProximitySensor

    app = QApplication([])

    publisher = SensorPublisher()
    broker = MessageBroker()
    card = SensorCard()
    sensor = ProximitySensor(13)

    publisher.registerSensor(sensor)
    publisher.start()
    broker.subscribe("ProximitySensor_13/STATE", card.updateStatus)
    broker.subscribe("ProximitySensor_13/VALUE", card.updateDotIndicator)

    card.show()
    app.exec()


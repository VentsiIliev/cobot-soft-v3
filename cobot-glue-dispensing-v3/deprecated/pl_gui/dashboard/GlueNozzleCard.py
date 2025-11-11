from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from API.MessageBroker import MessageBroker
from GlueDispensingApplication.SensorPublisher import Sensor, SENSOR_STATE_NO_COMMUNICATION, SENSOR_STATE_CONNECTED, \
    SENSOR_STATE_DISCONNECTED, SENSOR_STATE_RECONNECTING, SENSOR_STATE_READY, SENSOR_STATE_ERROR, \
    SENSOR_STATE_INITIALIZING,SENSOR_STATE_USB_NOT_CONNECTED,SENSOR_STATE_BUSY

class GlueNozzleCard(QFrame):
    updateStatusSignal = pyqtSignal(object)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logTag = "GlueNozzleCard"
        self._status_callback = lambda status: self.updateStatusSignal.emit(status)
        broker = MessageBroker()
        broker.subscribe("GlueNozzleService/STATE", self._status_callback)

        # self.setStyleSheet("""
        #     QFrame {
        #         border: 1px solid #ccc;
        #         border-radius: 12px;
        #         background-color: #ffffff;
        #         padding: 15px;
        #     }
        #     QLabel#titleLabel {
        #         font-size: 20px;
        #         font-weight: bold;
        #         color: #333;
        #     }
        #     QLabel#statusLabel {
        #         font-size: 14px;
        #         color: #666;
        #     }
        # """)
        self.setMinimumHeight(180)
        self.setMinimumWidth(120)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)

        self.status_dot = QLabel()
        self.status_dot.setFixedSize(40, 40)
        self.status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_dot.setStyleSheet("background-color: #ccc; border-radius: 20px; border: 2px solid #444;")

        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.status_dot, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.updateStatusSignal.connect(lambda status : self.update_status(status))

    def update_status(self, status):

        status_mapping = {
            SENSOR_STATE_READY: {"color": "#00FF00", "text": "Ready"},
            SENSOR_STATE_BUSY: {"color": "#FFA500", "text": "Dispensing"},
            SENSOR_STATE_ERROR: {"color": "#FF0000", "text": "Error"},
            SENSOR_STATE_DISCONNECTED: {"color": "#808080", "text": "Disconnected"},
            "STOPPING": {"color": "#0000FF", "text": "Stopping"},
            SENSOR_STATE_INITIALIZING: {"color": "#FFFF00", "text": "Initializing"},
            SENSOR_STATE_RECONNECTING: {"color": "#FFFF00", "text": "Reconnecting"}

        }

        # Get status info or default to "Unknown"
        info = status_mapping.get(status, {"color": "#AAAAAA", "text": "Unknown"})

        self.set_indicator_color(info["color"])
        self.status_label.setText(info["text"])

    def set_indicator_color(self, color):
        self.status_dot.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 20px;
                border: 2px solid #555;
            }}
        """)

    def closeEvent(self, event):
        print(f"{self.logTag}: Cleaning up before destruction...")
        # Unsubscribe or disconnect signals here
        self.updateStatusSignal.disconnect()
        # If using a real MessageBroker that allows unsubscribe:
        broker = MessageBroker()
        broker.unsubscribe("GlueNozzleService/STATE",self._status_callback)  # if supported

        # Call base implementation
        super().closeEvent(event)



if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    from GlueDispensingApplication.SensorPublisher import SensorPublisher
    from API.MessageBroker import MessageBroker
    from GlueDispensingApplication.tools.GlueNozzleService import GlueNozzleService

    app = QApplication([])

    card = GlueNozzleCard()


    card.show()
    app.exec()
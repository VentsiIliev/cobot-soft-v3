from PyQt6.QtWidgets import QWidget, QVBoxLayout,QSizePolicy, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer,QRect
from PyQt6.QtGui import QFont, QPainter, QPen, QColor
import threading
import requests
import logging


# GLUE_METER_URL_1 = "http://192.168.222.76/weight"
# GLUE_METER_URL_2 = "http://192.168.222.76/weight1"
# GLUE_METER_URL_3 = "http://192.168.222.76/weight2"

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPainter, QColor, QFont, QPen
from API.MessageBroker import MessageBroker  # Ensure this is your real path

class GlueMeterWidget(QWidget):
    def __init__(self, id, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.id = id
        self.glue_percent = 0
        self.glue_grams = 0
        self.max_volume_grams = 5000
        self.setMinimumWidth(250)
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel("0 g")
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.label.setMinimumWidth(100)
        self.label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        font = QFont()
        font.setPointSize(15)
        self.label.setFont(font)
        self.main_layout.addWidget(self.label)

        # State indicator circle
        self.state_indicator = QLabel()
        self.state_indicator.setFixedSize(16, 16)
        self.state_indicator.setStyleSheet("background-color: gray; border-radius: 8px;")
        self.main_layout.addWidget(self.state_indicator)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)


        self.canvas = QWidget()
        self.canvas.setMinimumHeight(50)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_layout.addWidget(self.canvas)

    def updateState(self, message):
        """
        Updates the circular status indicator.
        Green = Connected, Red = Disconnected/Error, Gray = Unknown
        """
        try:
            self.logger.debug(f"[{self.__class__.__name__}] received message: {message}")
            if isinstance(message, str):
                state = message.strip().lower()

                if state == "ready":
                    self.logger.debug(f"[{self.__class__.__name__}] Update state to ready")
                    self.state_indicator.setStyleSheet("background-color: green; border-radius: 8px;")
                elif state in ("disconnected", "error"):
                    self.logger.debug(f"[{self.__class__.__name__}] Update state to error")
                    self.state_indicator.setStyleSheet("background-color: red; border-radius: 8px;")
                else:
                    self.state_indicator.setStyleSheet("background-color: gray; border-radius: 8px;")
            else:
                raise ValueError("Invalid state message format")
        except Exception as e:
            self.logger.debug(f"[{self.__class__.__name__}] [GlueMeterWidget:{self.id}] Failed to update state: ")
            self.state_indicator.setStyleSheet("background-color: gray; border-radius: 8px;")

    def updateWidgets(self, message):
        """
        Callback function to receive messages from the broker and update the widget.
        Expected message format: {"grams": <float>}
        Computes the percent based on max_volume_grams.
        """
        try:
            grams = message
            if grams is not None:
                percent = (grams / self.max_volume_grams) * 100
                self.setGluePercent(percent, grams)
            else:
                raise ValueError("Missing 'grams' in message")

        except Exception as e:
            # print(f"[GlueMeterWidget:{self.id}] Failed to update from broker: {e}")
            self.setGluePercent(0)
            self.label.setText("N/A")
            self.canvas.update()

    def setGluePercent(self, percent, grams=None):
        self.glue_percent = max(0, min(100, percent))
        if grams is not None:
            self.glue_grams = grams
            self.label.setText(f"{int(grams)} g")
            self.label.setMaximumHeight(40)
        self.canvas.update()

    def get_shade(self):
        base = QColor("#905BA9")
        if self.glue_percent <= 20:
            return base.lighter(150)
        elif self.glue_percent <= 50:
            return base.lighter(120)
        elif self.glue_percent <= 80:
            return base
        else:
            return base.darker(120)

    def paintEvent(self, event):
        pass

    def resizeEvent(self, event):
        self.canvas.repaint()

    def showEvent(self, event):
        self.canvas.paintEvent = self.custom_paint_event

    def custom_paint_event(self, event):
        painter = QPainter(self.canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        full_width = self.canvas.width() - 20
        border_rect = QRect(10, 20, full_width, 20)

        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)

        num_steps = 5
        for i in range(num_steps + 1):
            percent = i * (100 // num_steps)
            x = 10 + int((i * full_width) / num_steps)
            painter.drawLine(x, 18, x, 15)
            painter.drawText(x - 10, 10, f"{percent}%")

        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawRect(border_rect)

        fill_width = int((self.glue_percent / 100) * border_rect.width())
        fill_rect = QRect(border_rect.left() + 1, border_rect.top() + 1,
                          fill_width, border_rect.height() - 2)

        painter.fillRect(fill_rect, self.get_shade())

    def closeEvent(self, event):
        broker = MessageBroker()
        broker.unsubscribe(f"GlueMeter_{self.id}/VALUE", self.updateWidgets)
        broker.unsubscribe(f"GlueMeter_{self.id}/STATE", self.updateState)
        super().closeEvent(event)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = GlueMeterWidget(id=1)
    widget.show()
    sys.exit(app.exec())





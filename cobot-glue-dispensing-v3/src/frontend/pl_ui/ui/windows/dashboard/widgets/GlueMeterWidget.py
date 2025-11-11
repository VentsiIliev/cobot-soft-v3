import logging

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QFont, QPainter, QPen, QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QLabel, QHBoxLayout

from modules.shared.MessageBroker import MessageBroker  # Ensure this is your real path


class GlueMeterWidget(QWidget):
    def __init__(self, id: int, parent: QWidget = None):
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
        # REMOVED: self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create a container widget for the label to prevent frame wrapping
        self.label_container = QWidget()
        self.label_container.setStyleSheet("QWidget { border: none; background: transparent; }")
        label_layout = QVBoxLayout(self.label_container)
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(0)

        self.label = QLabel("0 g")
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        self.label.setMinimumWidth(100)
        self.label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.label.setStyleSheet("QLabel { border: none; background: transparent; }")

        font = QFont()
        font.setPointSize(15)
        self.label.setFont(font)

        # Add label to its container, then container to main layout
        label_layout.addWidget(self.label)
        self.main_layout.addWidget(self.label_container)

        # Create container for state indicator
        self.state_container = QWidget()
        self.state_container.setStyleSheet("QWidget { border: none; background: transparent; }")
        state_layout = QVBoxLayout(self.state_container)
        state_layout.setContentsMargins(0, 0, 0, 0)
        state_layout.setSpacing(0)

        # State indicator circle
        self.state_indicator = QLabel()
        self.state_indicator.setFixedSize(16, 16)
        self.state_indicator.setStyleSheet("background-color: gray; border-radius: 8px;")

        # Center the state indicator within its container
        state_layout.addWidget(self.state_indicator, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.state_container)

        self.canvas = QWidget()
        self.canvas.setMinimumHeight(50)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_layout.addWidget(self.canvas)

    def updateState(self, message) -> None:
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

    def updateWidgets(self, message) -> None:
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

    def setGluePercent(self, percent, grams=None) -> None:
        self.glue_percent = max(0, min(100, percent))
        if grams is not None:
            self.glue_grams = grams
            try:
                self.label.setText(f"{float(grams):.2f} g")
            except (ValueError, TypeError):
                self.label.setText(f"{grams} g")
            self.label.setMaximumHeight(40)
        self.canvas.update()

    def get_shade(self) -> QColor:
        base = QColor("#905BA9")
        if self.glue_percent <= 20:
            return base.lighter(150)
        elif self.glue_percent <= 50:
            return base.lighter(120)
        elif self.glue_percent <= 80:
            return base
        else:
            return base.darker(120)

    def paintEvent(self, event) -> None:
        pass

    def resizeEvent(self, event) -> None:
        self.canvas.repaint()

    def showEvent(self, event) -> None:
        self.canvas.paintEvent = self.custom_paint_event

    def custom_paint_event(self, event) -> None:
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

    def __del__(self):
        """Cleanup when the widget is destroyed"""
        try:
            print(f">>> GlueMeterWidget {self.id} __del__ called - unsubscribing from MessageBroker")
            broker = MessageBroker()
            broker.unsubscribe(f"GlueMeter_{self.id}/VALUE", self.updateWidgets)
            broker.unsubscribe(f"GlueMeter_{self.id}/STATE", self.updateState)
            print(f">>> GlueMeterWidget {self.id} successfully unsubscribed")
        except Exception as e:
            print(f"Error during GlueMeterWidget {self.id} cleanup: {e}")

    def closeEvent(self, event) -> None:
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
import math
import sys
import threading
import time

import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication

from modules.shared.MessageBroker import MessageBroker
from src.frontend.pl_ui.ui.windows.dashboard.widgets.RobotTrajectoryWidget import RobotTrajectoryWidget


class TestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Space-Optimized Trajectory Tracker")
        self.setGeometry(50, 50, 800, 600)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.camera_widget = RobotTrajectoryWidget(image_width=640, image_height=360)
        self.camera_widget.set_image(np.zeros((1280, 720, 3), dtype=np.uint8))
        self.camera_widget.estimated_time_value = 5.0
        self.camera_widget.time_left_value = 3.0

        broker = MessageBroker()
        broker.subscribe("robot/trajectory/point", self.camera_widget.update)
        broker.subscribe("robot/trajectory/updateImage", self.camera_widget.set_image)

        layout.addWidget(self.camera_widget)
        self.setLayout(layout)
        self.start_smooth_trajectory_thread()

    def start_smooth_trajectory_thread(self):
        def generate_smooth_trajectory():
            broker = MessageBroker()
            t = 0.0
            dt = 0.02
            while True:
                x = 80 * math.cos(t * 2)
                y = 80 * math.sin(t * 2)
                broker.publish("robot/trajectory/point", {"x": x, "y": y})

                t += dt
                time.sleep(dt)

        threading.Thread(target=generate_smooth_trajectory, daemon=True).start()


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
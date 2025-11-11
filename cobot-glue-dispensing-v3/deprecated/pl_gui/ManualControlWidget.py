import os
from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QPushButton, QGridLayout, QSizePolicy,
    QSpacerItem, QHBoxLayout, QVBoxLayout, QFrame
)
from deprecated.pl_gui.customWidgets.PlSlider import PlSlider
from .Endpoints import *

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "manualMoveIcons")
Z_PLUS_ICON_PATH = os.path.join(RESOURCE_DIR, "Z+_BUTTON.png")
Z_MINUS_ICON_PATH = os.path.join(RESOURCE_DIR, "Z-_BUTTON.png")
X_PLUS_ICON_PATH = os.path.join(RESOURCE_DIR, "X+_BUTTON.png")
X_MINUS_ICON_PATH = os.path.join(RESOURCE_DIR, "X-_BUTTON.png")
Y_PLUS_ICON_PATH = os.path.join(RESOURCE_DIR, "Y+_BUTTON.png")
Y_MINUS_ICON_PATH = os.path.join(RESOURCE_DIR, "Y-_BUTTON.png")
CANCEL_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "CANCEL_BUTTON.png")


class ManualControlWidget(QFrame):
    def __init__(self, parent=None, callback=None, jogCallback=None):
        super().__init__(parent)
        self.callback = callback
        self.jogCallback = jogCallback
        self.onSaveCallback = None
        self.initUI()
        self.setStyleSheet("background-color: white; ")
        self.setMinimumWidth(300)

    def initUI(self):
        main_layout = QGridLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        control_container_layout = QVBoxLayout()
        control_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        control_container_layout.setContentsMargins(0, 0, 0, 0)
        control_container_layout.setSpacing(0)

        slider_layout = QHBoxLayout()
        slider_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        slider_layout.setSpacing(0)

        self.slider = PlSlider(label_text="Step", parent=self)
        self.slider.setDefaultValue(1)
        slider_layout.addWidget(self.slider)
        main_layout.addLayout(slider_layout, 0, 0)

        z_layout = QHBoxLayout()
        z_layout.setSpacing(0)
        z_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        z_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_z_plus = QPushButton()
        self.btn_z_minus = QPushButton()
        self.btn_z_plus.setIcon(QIcon(Z_PLUS_ICON_PATH))
        self.btn_z_minus.setIcon(QIcon(Z_MINUS_ICON_PATH))

        for btn in [self.btn_z_plus, self.btn_z_minus]:
            btn.setFixedSize(60, 60)
            btn.setIconSize(QSize(40, 40))

        self.z_plus_timer = QTimer(self)
        self.z_minus_timer = QTimer(self)
        self.z_plus_timer.setInterval(100)
        self.z_minus_timer.setInterval(100)

        self.btn_z_plus.pressed.connect(self.start_z_plus)
        self.btn_z_minus.pressed.connect(self.start_z_minus)
        self.btn_z_plus.released.connect(self.stop_z_plus)
        self.btn_z_minus.released.connect(self.stop_z_minus)

        self.z_plus_timer.timeout.connect(self.z_plus_action)
        self.z_minus_timer.timeout.connect(self.z_minus_action)

        z_layout.addWidget(self.btn_z_plus)
        z_layout.addWidget(self.btn_z_minus)

        cross_layout = QGridLayout()
        cross_layout.setSpacing(0)
        cross_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cross_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_x_minus = QPushButton()
        self.btn_x_plus = QPushButton()
        self.btn_y_plus = QPushButton()
        self.btn_y_minus = QPushButton()

        self.btn_x_minus.setIcon(QIcon(X_MINUS_ICON_PATH))
        self.btn_y_minus.setIcon(QIcon(Y_MINUS_ICON_PATH))
        self.btn_x_plus.setIcon(QIcon(X_PLUS_ICON_PATH))
        self.btn_y_plus.setIcon(QIcon(Y_PLUS_ICON_PATH))

        for btn in [self.btn_x_minus, self.btn_x_plus, self.btn_y_plus, self.btn_y_minus]:
            btn.setFixedSize(60, 60)
            btn.setIconSize(QSize(40, 40))

        self.x_plus_timer = QTimer(self)
        self.x_minus_timer = QTimer(self)
        self.y_plus_timer = QTimer(self)
        self.y_minus_timer = QTimer(self)
        self.x_plus_timer.setInterval(100)
        self.x_minus_timer.setInterval(100)
        self.y_plus_timer.setInterval(100)
        self.y_minus_timer.setInterval(100)

        self.btn_x_plus.pressed.connect(self.start_x_plus)
        self.btn_x_minus.pressed.connect(self.start_x_minus)
        self.btn_y_plus.pressed.connect(self.start_y_plus)
        self.btn_y_minus.pressed.connect(self.start_y_minus)

        self.btn_x_plus.released.connect(self.stop_x_plus)
        self.btn_x_minus.released.connect(self.stop_x_minus)
        self.btn_y_plus.released.connect(self.stop_y_plus)
        self.btn_y_minus.released.connect(self.stop_y_minus)

        self.x_plus_timer.timeout.connect(self.x_plus_action)
        self.x_minus_timer.timeout.connect(self.x_minus_action)
        self.y_plus_timer.timeout.connect(self.y_plus_action)
        self.y_minus_timer.timeout.connect(self.y_minus_action)

        cross_layout.addWidget(self.btn_x_minus, 0, 1)
        cross_layout.addWidget(self.btn_y_minus, 1, 0)
        cross_layout.addWidget(self.btn_x_plus, 2, 1)
        cross_layout.addWidget(self.btn_y_plus, 1, 2)

        spacer = QSpacerItem(0, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        cross_layout.addItem(spacer, 1, 1)

        control_container_layout.addLayout(z_layout)
        control_container_layout.addLayout(cross_layout)
        control_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        main_layout.addLayout(control_container_layout, 1, 0)

        spacer = QSpacerItem(0, 50, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        main_layout.addItem(spacer)

        self.savePointButton = QPushButton("Save Point")
        self.savePointButton.clicked.connect(self.onSavePoint)
        self.savePointButton.hide()
        main_layout.addWidget(self.savePointButton)

        spacer = QSpacerItem(0, 150, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        main_layout.addItem(spacer)

        self.close_button = QPushButton("")
        self.close_button.setIcon(QIcon(CANCEL_BUTTON_ICON_PATH))
        main_layout.addWidget(self.close_button)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(main_layout)

    def onSave(self):
        print("Saving points")

    # Methods for starting/stopping timers for Z, X, Y buttons
    def start_z_plus(self):
        self.z_plus_timer.start()

    def stop_z_plus(self):
        self.z_plus_timer.stop()

    def start_z_minus(self):
        self.z_minus_timer.start()

    def stop_z_minus(self):
        self.z_minus_timer.stop()

    def start_x_plus(self):
        self.x_plus_timer.start()

    def stop_x_plus(self):
        self.x_plus_timer.stop()

    def start_x_minus(self):
        self.x_minus_timer.start()

    def stop_x_minus(self):
        self.x_minus_timer.stop()

    def start_y_plus(self):
        self.y_plus_timer.start()

    def stop_y_plus(self):
        self.y_plus_timer.stop()

    def start_y_minus(self):
        self.y_minus_timer.start()

    def stop_y_minus(self):
        self.y_minus_timer.stop()

    # Action methods for button presses
    def z_plus_action(self):
        self.jogCallback(JOG_ROBOT,"Z","Plus",self.slider.slider.value())

    def z_minus_action(self):
        self.jogCallback(JOG_ROBOT, "Z", "Minus", self.slider.slider.value())

    def x_plus_action(self):
        self.jogCallback(JOG_ROBOT, "X", "Plus", self.slider.slider.value())

    def x_minus_action(self):
        self.jogCallback(JOG_ROBOT, "X", "Minus", self.slider.slider.value())

    def y_plus_action(self):
        self.jogCallback(JOG_ROBOT, "Y", "Plus", self.slider.slider.value())

    def y_minus_action(self):
        self.jogCallback(JOG_ROBOT, "Y", "Minus", self.slider.slider.value())


    def resizeEvent(self, event):
        width = self.width()
        height = self.height()
        icon_size = min(width, height) // 6
        if width > 500:
            icon_size = min(width, height) // 6

        for btn in [self.btn_z_plus, self.btn_z_minus, self.btn_x_minus, self.btn_x_plus, self.btn_y_plus,
                    self.btn_y_minus]:
            btn.setIconSize(QSize(icon_size, icon_size))
            btn.setFixedSize(QSize(icon_size, icon_size))

        newWidth = self.parent().width()
        button_icon_size = QSize(int(newWidth * 0.05), int(newWidth * 0.05))
        self.close_button.setIconSize(button_icon_size)
        self.close_button.clicked.connect(self.onClose)

        super().resizeEvent(event)

    def onSavePoint(self):

        if self.onSaveCallback is None:
            print("onSaveCallback did not return a valid result.")
            return

        res, done = self.onSaveCallback(SAVE_ROBOT_CALIBRATION_POINT)

        if done:
            self.close

    def onClose(self):
        if self.callback is not None:
            self.callback()
        self.close()


# if __name__ == "__main__":
#     import sys
#
#     app = QApplication(sys.argv)
#     window = ManualControlWidget()
#     window.setWindowTitle("Manual Robot Control")
#     window.resize(300, 300)
#     window.show()
#     sys.exit(app.exec())

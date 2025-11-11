from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel,
    QMessageBox, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from pl_ui.ui.widgets.robotManualControl.JogSlider import JogSlider


class RobotJogWidget(QFrame):
    """Robot jogging control widget"""

    # Define signals
    jogRequested = pyqtSignal(str, str, str, float)  # command, axis, direction, value
    jogStarted = pyqtSignal(str)  # emitted when a jog button is pressed
    jogStopped = pyqtSignal(str)  # emitted when a jog button is released
    save_point_requested = pyqtSignal()  # emitted when saving a point

    def __init__(self, parent=None):
        super().__init__(parent)
        self.saved_points = []
        self.initUI()
        self.setupTimers()
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 4px;
                padding: 15px;
            }
        """)

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Step size slider
        self.step_slider = JogSlider("Jog Step Size", self)
        self.step_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #E5E5E5;
                height: 6px;
                background: #F5F5F5;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #905BA9;
                border: 1px solid #905BA9;
                width: 18px;
                height: 18px;
                border-radius: 9px;
                margin: -7px 0;
            }
            QSlider::handle:horizontal:hover {
                background: #7D4D96;
                border-color: #7D4D96;
            }
            QSlider::handle:horizontal:pressed {
                background: #6B4182;
                border-color: #6B4182;
            }
            QSlider::sub-page:horizontal {
                background: #905BA9;
                border: 1px solid #905BA9;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background: #F5F5F5;
                border: 1px solid #E5E5E5;
                height: 6px;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.step_slider)

        main_layout.addSpacing(15)

        # Jog controls layout
        jog_controls_layout = QHBoxLayout()
        jog_controls_layout.setSpacing(40)
        jog_controls_layout.addStretch(1)

        # Z-axis
        z_layout = QVBoxLayout()
        z_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        z_layout.addStretch(1)
        z_label = QLabel("Z-Axis")
        z_label.setStyleSheet("font-size: 12px; font-weight: 500; color: #666666; margin-bottom: 8px;")
        z_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        z_layout.addWidget(z_label)

        self.btn_z_plus = self.createJogButton("Z+", "#905BA9")
        self.btn_z_minus = self.createJogButton("Z−", "#905BA9")
        z_layout.addWidget(self.btn_z_plus)
        z_layout.addSpacing(12)
        z_layout.addWidget(self.btn_z_minus)
        z_layout.addStretch(1)
        jog_controls_layout.addLayout(z_layout)

        jog_controls_layout.addSpacing(40)

        # XY axes
        xy_container = QVBoxLayout()
        xy_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        xy_label = QLabel("X-Y Axes")
        xy_label.setStyleSheet("font-size: 12px; font-weight: 500; color: #666666; margin-bottom: 8px;")
        xy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        xy_container.addWidget(xy_label)

        xy_layout = QGridLayout()
        xy_layout.setSpacing(12)
        xy_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_x_minus = self.createJogButton("X−", "#F5F5F5", "#666666")
        self.btn_x_plus = self.createJogButton("X+", "#F5F5F5", "#666666")
        self.btn_y_plus = self.createJogButton("Y+", "#F5F5F5", "#666666")
        self.btn_y_minus = self.createJogButton("Y−", "#F5F5F5", "#666666")

        xy_layout.addWidget(self.btn_y_plus, 0, 1)
        xy_layout.addWidget(self.btn_x_minus, 1, 0)
        xy_layout.addWidget(self.btn_x_plus, 1, 2)
        xy_layout.addWidget(self.btn_y_minus, 2, 1)
        xy_layout.addItem(QSpacerItem(50, 50, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed), 1, 1)

        xy_container.addLayout(xy_layout)
        jog_controls_layout.addLayout(xy_container)
        jog_controls_layout.addStretch(1)

        main_layout.addLayout(jog_controls_layout)
        main_layout.addSpacing(20)

        # Save/Clear buttons
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(15)

        self.save_point_btn = QPushButton("Save Point")
        self.save_point_btn.setStyleSheet("""
            QPushButton {
                background-color: #905BA9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 500;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #7D4D96;
            }
            QPushButton:pressed {
                background-color: #6B4182;
            }
        """)
        self.save_point_btn.clicked.connect(self.saveCurrentPoint)

        self.clear_points_btn = QPushButton("Clear Points")
        self.clear_points_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #666666;
                border: 1px solid #D0D0D0;
                border-radius: 4px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 500;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
                border-color: #BBBBBB;
            }
            QPushButton:pressed {
                background-color: #E8E8E8;
            }
        """)
        self.clear_points_btn.clicked.connect(self.clearSavedPoints)

        button_layout.addWidget(self.save_point_btn)
        button_layout.addWidget(self.clear_points_btn)
        main_layout.addLayout(button_layout)

        self.points_label = QLabel("Saved Points: 0")
        self.points_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 500; 
            color: #666666; 
            margin-top: 10px;
        """)
        self.points_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.points_label)

        self.setLayout(main_layout)

    def createJogButton(self, text, bg_color="#905BA9", text_color="#FFFFFF"):
        btn = QPushButton(text)
        btn.setMinimumSize(50, 50)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setMinimumHeight(50)
        btn.setMaximumHeight(50)

        if bg_color == "#905BA9":
            hover_color = "#7D4D96"
            pressed_color = "#6B4182"
        else:
            hover_color = "#EEEEEE"
            pressed_color = "#E0E0E0"

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: {'none' if bg_color == '#905BA9' else '1px solid #D0D0D0'};
                border-radius: 4px;
                font-size: 14px;
                font-weight: 500;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                {'border-color: #BBBBBB;' if bg_color != '#905BA9' else ''}
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
        """)
        return btn

    def setupTimers(self):
        """Setup timers for continuous jogging"""
        self.timers = {}
        for axis in ['x_plus', 'x_minus', 'y_plus', 'y_minus', 'z_plus', 'z_minus']:
            timer = QTimer(self)
            timer.setInterval(100)
            timer.timeout.connect(lambda axis=axis: self.performJog(axis))
            self.timers[axis] = timer

        # Connect buttons to handlers
        self.btn_x_plus.pressed.connect(lambda: self._handleJogStart('x_plus'))
        self.btn_x_plus.released.connect(lambda: self._handleJogStop('x_plus'))
        self.btn_x_minus.pressed.connect(lambda: self._handleJogStart('x_minus'))
        self.btn_x_minus.released.connect(lambda: self._handleJogStop('x_minus'))

        self.btn_y_plus.pressed.connect(lambda: self._handleJogStart('y_plus'))
        self.btn_y_plus.released.connect(lambda: self._handleJogStop('y_plus'))
        self.btn_y_minus.pressed.connect(lambda: self._handleJogStart('y_minus'))
        self.btn_y_minus.released.connect(lambda: self._handleJogStop('y_minus'))

        self.btn_z_plus.pressed.connect(lambda: self._handleJogStart('z_plus'))
        self.btn_z_plus.released.connect(lambda: self._handleJogStop('z_plus'))
        self.btn_z_minus.pressed.connect(lambda: self._handleJogStart('z_minus'))
        self.btn_z_minus.released.connect(lambda: self._handleJogStop('z_minus'))

    def _handleJogStart(self, direction):
        self.jogStarted.emit(direction)
        self.startJog(direction)

    def _handleJogStop(self, direction):
        self.jogStopped.emit(direction)
        self.stopJog(direction)

    def startJog(self, direction):
        if direction in self.timers:
            self.timers[direction].start()

    def stopJog(self, direction):
        if direction in self.timers:
            self.timers[direction].stop()

    def performJog(self, direction):
        """Emit jog signals with the specified parameters format"""
        step_size = self.step_slider.value()

        # Map direction to axis and direction
        axis_mapping = {
            'x_plus': ('X', 'Plus'),
            'x_minus': ('X', 'Minus'),
            'y_plus': ('Y', 'Plus'),
            'y_minus': ('Y', 'Minus'),
            'z_plus': ('Z', 'Plus'),
            'z_minus': ('Z', 'Minus')
        }

        if direction in axis_mapping:
            axis, dir_str = axis_mapping[direction]
            # Emit signal with your specified parameters: JOG_ROBOT, axis, direction, slider_value
            self.jogRequested.emit("JOG_ROBOT", axis, dir_str, step_size)

    def saveCurrentPoint(self):
        self.save_point_requested.emit()

    def clearSavedPoints(self):
        if self.saved_points:
            reply = QMessageBox.question(
                self, "Clear Points",
                f"Are you sure you want to clear all {len(self.saved_points)} saved points?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.saved_points.clear()
                self.updatePointsDisplay()
        else:
            QMessageBox.information(self, "No Points", "No points to clear")

    def updatePointsDisplay(self):
        self.points_label.setText(f"Saved Points: {len(self.saved_points)}")

    def getSavedPoints(self):
        return self.saved_points.copy()

    def exportPoints(self, filename):
        try:
            with open(filename, 'w') as f:
                for point in self.saved_points:
                    f.write(" ".join(f"{p:.3f}" for p in point) + "\n")
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = RobotJogWidget()
    widget.show()

    # Example: connect to signals with new signature
    widget.jogRequested.connect(lambda cmd, axis, direction, value:
                                print(f"Jog: {cmd}, {axis}, {direction}, {value}"))
    widget.jogStarted.connect(lambda d: print(f"Jog started: {d}"))
    widget.jogStopped.connect(lambda d: print(f"Jog stopped: {d}"))

    sys.exit(app.exec())
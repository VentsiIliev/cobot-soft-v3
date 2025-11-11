from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QSpinBox, QPushButton,
    QGridLayout, QGroupBox, QVBoxLayout, QHBoxLayout, QScrollArea,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QFrame,
    QSizePolicy, QSpacerItem, QSlider, QComboBox, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer
import sys
import json
import os
import copy
from dataclasses import dataclass, field
from typing import Dict, List, Optional

class RequestSender(QObject):
    """Mock RequestSender to simulate sending requests"""
    def send_request(self, command, *args):
        if command == "UPDATE_CONFIG":
            config_file = args[0] if args else "unknown_file"
            print(f"🔄 UPDATE_CONFIG request sent for file: {config_file}")
            print(f"   └── Configuration has been updated and saved")
        else:
            print(f"📤 Request sent: {command}, args: {args}")

# ========================= DATA CLASSES =========================

@dataclass
class MovementGroup:
    """Data class representing a movement group configuration"""
    velocity: int = 0
    acceleration: int = 0
    position: Optional[str] = None
    points: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MovementGroup':
        """Create MovementGroup from dictionary data"""
        return cls(
            velocity=data.get("velocity", 0),
            acceleration=data.get("acceleration", 0),
            position=data.get("position"),
            points=data.get("points", [])
        )
    
    def to_dict(self) -> Dict:
        """Convert MovementGroup to dictionary"""
        result = {
            "velocity": self.velocity,
            "acceleration": self.acceleration
        }
        if self.position:
            result["position"] = self.position
        if self.points:
            result["points"] = self.points
        return result


@dataclass
class RobotConfig:
    """Data class representing the complete robot configuration"""
    robot_ip: str = "192.168.58.2"
    robot_tool: int = 0
    robot_user: int = 0
    movement_groups: Dict[str, MovementGroup] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RobotConfig':
        """Create RobotConfig from dictionary data"""
        movement_groups = {}
        for group_name, group_data in data.get("MOVEMENT_GROUPS", {}).items():
            movement_groups[group_name] = MovementGroup.from_dict(group_data)
        
        return cls(
            robot_ip=data.get("ROBOT_IP", "192.168.58.2"),
            robot_tool=data.get("ROBOT_TOOL", 0),
            robot_user=data.get("ROBOT_USER", 0),
            movement_groups=movement_groups
        )
    
    def to_dict(self) -> Dict:
        """Convert RobotConfig to dictionary for JSON serialization"""
        return {
            "ROBOT_IP": self.robot_ip,
            "ROBOT_TOOL": self.robot_tool,
            "ROBOT_USER": self.robot_user,
            "MOVEMENT_GROUPS": {name: group.to_dict() for name, group in self.movement_groups.items()}
        }


# Simple JogSlider implementation
class JogSlider(QWidget):
    """Simple jog slider implementation"""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 12px; font-weight: 500; color: #666666;")
        layout.addWidget(title_label)

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(1, 100)
        self.slider.setValue(10)
        layout.addWidget(self.slider)

        # Value label
        self.value_label = QLabel("10")
        self.value_label.setStyleSheet("font-size: 11px; color: #666666;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)

        self.slider.valueChanged.connect(self.update_value_label)
        self.setLayout(layout)

    def update_value_label(self, value):
        self.value_label.setText(str(value))

    def value(self):
        return self.slider.value()

    def setValue(self, value):
        self.slider.setValue(value)

    def setStyleSheet(self, style):
        self.slider.setStyleSheet(style)


# Robot Jog Widget
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

# Command Pattern for Undo/Redo
class Command:
    """Base class for command pattern - enables undo/redo functionality"""

    def execute(self):
        pass

    def undo(self):
        pass

    def get_description(self):
        return "Unknown command"


class ConfigChangeCommand(Command):
    """Command for configuration changes that can be undone"""

    def __init__(self, controller, old_config, new_config, description):
        self.controller = controller
        self.old_config = old_config
        self.new_config = new_config
        self.description = description

    def execute(self):
        self.controller.apply_config_to_ui(self.new_config)
        self.controller.save_config_to_file(self.new_config.to_dict())

    def undo(self):
        self.controller.apply_config_to_ui(self.old_config)
        self.controller.save_config_to_file(self.old_config.to_dict())

    def get_description(self):
        return self.description


class CommandHistory:
    """Manages command history for undo/redo functionality"""

    def __init__(self):
        self.history = []
        self.current_index = -1
        self.max_history = 50  # Limit history size

    def execute_command(self, command):
        """Execute a command and add it to history"""
        # Remove any commands after current index (when undoing then doing new action)
        self.history = self.history[:self.current_index + 1]

        # Add new command
        self.history.append(command)
        self.current_index += 1

        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1

        # Execute the command
        command.execute()

    def can_undo(self):
        return self.current_index >= 0

    def can_redo(self):
        return self.current_index < len(self.history) - 1

    def undo(self):
        if self.can_undo():
            command = self.history[self.current_index]
            command.undo()
            self.current_index -= 1
            return command.get_description()
        return None

    def redo(self):
        if self.can_redo():
            self.current_index += 1
            command = self.history[self.current_index]
            command.execute()
            return command.get_description()
        return None

    def clear(self):
        self.history.clear()
        self.current_index = -1


# Signals
class RobotConfigSignals(QObject):
    """Signal definitions for robot configuration UI"""
    # Robot info signals
    robot_ip_changed = pyqtSignal(str)
    robot_tool_changed = pyqtSignal(int)
    robot_user_changed = pyqtSignal(int)

    # Movement signals
    velocity_changed = pyqtSignal(str, int)  # group_name, value
    acceleration_changed = pyqtSignal(str, int)  # group_name, value

    # Position management signals
    add_point_requested = pyqtSignal(str)  # group_name
    remove_point_requested = pyqtSignal(str)  # group_name
    edit_point_requested = pyqtSignal(str)  # group_name
    move_to_point_requested = pyqtSignal(str)  # group_name

    # Single position signals
    edit_single_position_requested = pyqtSignal(str)  # group_name
    set_current_position_requested = pyqtSignal(str)  # group_name
    move_to_single_position_requested = pyqtSignal(str)  # group_name

    # File operations
    save_requested = pyqtSignal()
    reset_requested = pyqtSignal()

    # Undo/Redo operations
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()

    # Jog operations
    jog_requested = pyqtSignal(str, str, str, float)  # command, axis, direction, value
    jog_started = pyqtSignal(str)  # direction
    jog_stopped = pyqtSignal(str)  # direction
    save_current_position_as_point = pyqtSignal(str)  # group_name

    # Trajectory execution
    execute_trajectory_requested = pyqtSignal(str)  # group_name


# Controller
class RobotConfigController:
    """Controller class to handle all robot configuration logic"""

    def __init__(self, request_sender=None):
        self.ui = None  # Will be set by the UI after initialization
        self.config_file = "robot_config.json"
        self.command_history = CommandHistory()
        self.is_loading = False  # Flag to prevent undo tracking during load
        self.request_sender = request_sender or RequestSender()  # Default to mock sender
    
    def set_ui(self, ui):
        """Set the UI reference and initialize"""
        self.ui = ui
        self.connect_signals()
        self.load_config()

    def connect_signals(self):
        """Connect all UI signals to controller methods"""
        signals = self.ui.signals

        # Robot info signals
        signals.robot_ip_changed.connect(self.on_robot_ip_changed)
        signals.robot_tool_changed.connect(self.on_robot_tool_changed)
        signals.robot_user_changed.connect(self.on_robot_user_changed)

        # Movement signals
        signals.velocity_changed.connect(self.on_velocity_changed)
        signals.acceleration_changed.connect(self.on_acceleration_changed)

        # Position management signals
        signals.add_point_requested.connect(self.on_add_point)
        signals.remove_point_requested.connect(self.on_remove_point)
        signals.edit_point_requested.connect(self.on_edit_point)
        signals.move_to_point_requested.connect(self.on_move_to_point)

        # Single position signals
        signals.edit_single_position_requested.connect(self.on_edit_single_position)
        signals.set_current_position_requested.connect(self.on_set_current_position)
        signals.move_to_single_position_requested.connect(self.on_move_to_single_position)

        # File operations
        signals.save_requested.connect(self.on_save)
        signals.reset_requested.connect(self.on_reset)

        # Undo/Redo operations
        signals.undo_requested.connect(self.on_undo)
        signals.redo_requested.connect(self.on_redo)

        # Jog operations
        signals.jog_requested.connect(self.on_jog_requested)
        signals.jog_started.connect(self.on_jog_started)
        signals.jog_stopped.connect(self.on_jog_stopped)
        signals.save_current_position_as_point.connect(self.on_save_current_position_as_point)

        # Trajectory execution
        signals.execute_trajectory_requested.connect(self.on_execute_trajectory)

    def get_default_config(self):
        """Get default configuration data"""
        movement_groups = {
            "LOGIN_POS": MovementGroup(
                position="[59.118, -334, 721.66, 180, 0, -90]",
                velocity=0,
                acceleration=0
            ),
            "HOME_POS": MovementGroup(
                position="[-232.343, -93.902, 819.846, 180, 0, 90]",
                velocity=0,
                acceleration=0
            ),
            "CALIBRATION_POS": MovementGroup(
                position="[-25.4, 370.001, 819.846, 180, 0, 0]",
                velocity=0,
                acceleration=0
            ),
            "JOG": MovementGroup(
                velocity=20,
                acceleration=100
            ),
            "NOZZLE CLEAN": MovementGroup(
                velocity=30,
                acceleration=30,
                points=[
                    "[-165.037, -300.705, 298.201, 180, 0, 90]",
                    "[-165.037, -431.735, 298.201, 180, 0, 90]",
                    "[-165.037, -400, 298.201, 180, 0, 90]"
                ]
            ),
            "TOOL CHANGER": MovementGroup(
                velocity=100,
                acceleration=30,
                points=[]
            ),
            "SLOT 0 PICKUP": MovementGroup(
                points=[
                    "[-98.555, -224.46, 300, 180, 0, 90]",
                    "[-98.555, -224.46, 181.11, 180, 0, 90]",
                    "[-98.555, -190.696, 181.11, 180, 0, 90]",
                    "[-98.555, -190.696, 300, 180, 0, 90]"
                ]
            ),
            "SLOT 0 DROPOFF": MovementGroup(
                points=[
                    "[-98.555, -190.696, 300, 180, 0, 90]",
                    "[-98.555, -190.696, 181.11, 180, 0, 90]",
                    "[-98.555, -224.46, 181.11, 180, 0, 90]",
                    "[-98.555, -224.46, 300, 180, 0, 90]"
                ]
            ),
            "SLOT 1 PICKUP": MovementGroup(
                points=[
                    "[-247.871, -221.213, 300, 180, 0, 90]",
                    "[-247.871, -221.213, 180.278, 180, 0, 90]",
                    "[-247.871, -150, 180.278, 180, 0, 90]"
                ]
            ),
            "SLOT 1 DROPOFF": MovementGroup(
                points=[
                    "[-247.871, -150, 180.278, 180, 0, 90]",
                    "[-247.871, -221.213, 180.278, 180, 0, 90]",
                    "[-247.871, -221.213, 300, 180, 0, 90]"
                ]
            ),
            "SLOT 4 PICKUP": MovementGroup(
                points=[
                    "[-441.328, -280.786, 300, -180, 0, 90]",
                    "[-441.328, -280.786, 184.912, -180, 0, 90]",
                    "[-441.328, -201.309, 184.912, -180, 0, 90]"
                ]
            ),
            "SLOT 4 DROPOFF": MovementGroup(
                points=[
                    "[-441.328, -201.309, 184.912, -180, 0, 90]",
                    "[-441.328, -280.786, 184.912, -180, 0, 90]",
                    "[-441.328, -280.786, 300, -180, 0, 90]"
                ]
            )
        }
        
        return RobotConfig(
            robot_ip="192.168.58.2",
            robot_tool=0,
            robot_user=0,
            movement_groups=movement_groups
        )

    # Signal handlers
    def on_robot_ip_changed(self, value):
        """Handle robot IP change"""
        if not self.is_loading:
            old_config = self.get_current_config()
            new_config = copy.deepcopy(old_config)
            new_config.robot_ip = value
            command = ConfigChangeCommand(self, old_config, new_config, f"Change Robot IP to {value}")
            self.execute_command_with_history(command)

    def on_robot_tool_changed(self, value):
        """Handle robot tool change"""
        if not self.is_loading:
            old_config = self.get_current_config()
            new_config = copy.deepcopy(old_config)
            new_config.robot_tool = value
            command = ConfigChangeCommand(self, old_config, new_config, f"Change Robot Tool to {value}")
            self.execute_command_with_history(command)

    def on_robot_user_changed(self, value):
        """Handle robot user change"""
        if not self.is_loading:
            old_config = self.get_current_config()
            new_config = copy.deepcopy(old_config)
            new_config.robot_user = value
            command = ConfigChangeCommand(self, old_config, new_config, f"Change Robot User to {value}")
            self.execute_command_with_history(command)

    def on_velocity_changed(self, group_name, value):
        """Handle velocity change"""
        if not self.is_loading:
            old_config = self.get_current_config()
            new_config = copy.deepcopy(old_config)
            if group_name not in new_config.movement_groups:
                new_config.movement_groups[group_name] = MovementGroup()
            new_config.movement_groups[group_name].velocity = value
            command = ConfigChangeCommand(self, old_config, new_config, f"Change {group_name} velocity to {value}")
            self.execute_command_with_history(command)

    def on_acceleration_changed(self, group_name, value):
        """Handle acceleration change"""
        if not self.is_loading:
            old_config = self.get_current_config()
            new_config = copy.deepcopy(old_config)
            if group_name not in new_config.movement_groups:
                new_config.movement_groups[group_name] = MovementGroup()
            new_config.movement_groups[group_name].acceleration = value
            command = ConfigChangeCommand(self, old_config, new_config, f"Change {group_name} acceleration to {value}")
            self.execute_command_with_history(command)

    def on_add_point(self, group_name):
        """Handle add point request"""
        old_config = self.get_current_config()
        mock_position = [0, 0, 0, 0, 0, 0]

        list_widget = self.ui.position_lists[group_name]
        item = QListWidgetItem(str(mock_position))
        list_widget.addItem(item)

        new_config = self.get_current_config()
        command = ConfigChangeCommand(self, old_config, new_config, f"Add point to {group_name}")
        self.execute_command_with_history(command)

    def on_remove_point(self, group_name):
        """Handle remove point request"""
        list_widget = self.ui.position_lists[group_name]
        current_item = list_widget.currentItem()

        if current_item:
            old_config = self.get_current_config()
            row = list_widget.row(current_item)
            removed_point = current_item.text()
            list_widget.takeItem(row)

            new_config = self.get_current_config()
            command = ConfigChangeCommand(self, old_config, new_config, f"Remove point from {group_name}")
            self.execute_command_with_history(command)
        else:
            QMessageBox.information(self.ui, "No Selection", "Please select a point to remove.")

    def on_edit_point(self, group_name):
        """Handle edit point request"""
        list_widget = self.ui.position_lists[group_name]
        current_item = list_widget.currentItem()

        if current_item:
            old_config = self.get_current_config()
            old_text = current_item.text()

            success = self._edit_position_dialog(current_item.text(), group_name, current_item)
            if success:
                new_config = self.get_current_config()
                command = ConfigChangeCommand(self, old_config, new_config, f"Edit point in {group_name}")
                self.execute_command_with_history(command)
        else:
            QMessageBox.information(self.ui, "No Selection", "Please select a point to edit.")

    def on_move_to_point(self, group_name):
        """Handle move to point request"""
        list_widget = self.ui.position_lists[group_name]
        current_item = list_widget.currentItem()

        if current_item:
            point_name = current_item.text()
            vel_acc_info = self._get_velocity_acceleration_info(group_name)
            print(f"Moving to point: {point_name} in group: {group_name}{vel_acc_info}")
        else:
            QMessageBox.information(self.ui, "No Selection", "Please select a point to move to.")

    def on_edit_single_position(self, group_name):
        """Handle edit single position request"""
        position_widget = self.ui.position_lists[group_name]
        old_config = self.get_current_config()
        old_text = position_widget.text()

        dummy_item = type('Item', (), {'setText': lambda self, text: position_widget.setText(text)})()
        success = self._edit_position_dialog(old_text, group_name, dummy_item)
        if success:
            new_config = self.get_current_config()
            command = ConfigChangeCommand(self, old_config, new_config, f"Edit {group_name}")
            self.execute_command_with_history(command)

    def on_set_current_position(self, group_name):
        """Handle set current position request"""
        old_config = self.get_current_config()
        mock_position = [0, 0, 0, 0, 0, 0]

        position_widget = self.ui.position_lists[group_name]
        position_widget.setText(str(mock_position))

        new_config = self.get_current_config()
        command = ConfigChangeCommand(self, old_config, new_config, f"Set current position for {group_name}")
        self.execute_command_with_history(command)

    def on_move_to_single_position(self, group_name):
        """Handle move to single position request"""
        position_widget = self.ui.position_lists[group_name]
        position_text = position_widget.text()

        if position_text.strip():
            vel_acc_info = self._get_velocity_acceleration_info(group_name)
            print(f"Moving to {group_name}: {position_text}{vel_acc_info}")
        else:
            QMessageBox.information(self.ui, "No Position", f"No position set for {group_name}.")

    def on_save(self):
        """Handle save request"""
        config = self.get_current_config()
        self.save_config_to_file(config.to_dict())
        QMessageBox.information(self.ui, "Current Configuration",
                                f"Configuration saved to {self.config_file}\n\n" +
                                json.dumps(config.to_dict(), indent=2))

    def on_reset(self):
        """Handle reset request"""
        old_config = self.get_current_config()
        default_config = self.get_default_config()

        command = ConfigChangeCommand(self, old_config, default_config, "Reset configuration to defaults")
        self.execute_command_with_history(command)

        QMessageBox.information(self.ui, "Reset Complete", "Configuration has been reset to defaults and saved.")

    def on_jog_requested(self, command, axis, direction, value):
        """Handle jog request from jog widget"""
        print(f"Jog request: {command} {axis} {direction} {value}")

    def on_jog_started(self, direction):
        """Handle jog start"""
        print(f"Jog started: {direction}")

    def on_jog_stopped(self, direction):
        """Handle jog stop"""
        print(f"Jog stopped: {direction}")

    def on_save_current_position_as_point(self, group_name):
        """Handle saving current robot position to a specific group"""
        print(f"Saving current position to {group_name}")
        current_position = [100, 200, 300, 180, 0, 90]  # Mock current position

        if group_name in self.ui.position_lists:
            widget = self.ui.position_lists[group_name]

            if isinstance(widget, QLineEdit):
                old_config = self.get_current_config()
                widget.setText(str(current_position))
                new_config = self.get_current_config()
                command = ConfigChangeCommand(self, old_config, new_config, f"Save current position to {group_name}")
                self.execute_command_with_history(command)

            elif isinstance(widget, QListWidget):
                old_config = self.get_current_config()
                item = QListWidgetItem(str(current_position))
                widget.addItem(item)
                new_config = self.get_current_config()
                command = ConfigChangeCommand(self, old_config, new_config, f"Add current position to {group_name}")
                self.execute_command_with_history(command)

        QMessageBox.information(self.ui, "Position Saved", f"Current position saved to {group_name}")

    def on_execute_trajectory(self, group_name):
        """Handle trajectory execution request"""
        print(f"\n🚀 EXECUTING TRAJECTORY: {group_name}")
        print("=" * 50)

        # Get the trajectory points
        if group_name in self.ui.position_lists:
            widget = self.ui.position_lists[group_name]

            if isinstance(widget, QListWidget):
                points = []
                for i in range(widget.count()):
                    item = widget.item(i)
                    points.append(item.text())

                if not points:
                    print("❌ No points defined for trajectory!")
                    QMessageBox.warning(self.ui, "Empty Trajectory", f"No points defined for {group_name} trajectory.")
                    return

                # Get velocity and acceleration settings
                vel_acc_info = self._get_velocity_acceleration_info(group_name)
                if vel_acc_info:
                    print(f"⚙️  Settings: {vel_acc_info.strip(' ()')}")

                print(f"📍 Trajectory Points ({len(points)} total):")

                # Print each point in the sequence
                for i, point in enumerate(points, 1):
                    print(f"   {i}. {point}")

                print(f"\n🔄 Executing {group_name} trajectory...")
                print("   → Moving through points in sequence...")

                # Simulate trajectory execution steps
                trajectory_steps = {
                    "NOZZLE CLEAN": [
                        "Moving to nozzle clean start position",
                        "Lowering to cleaning depth",
                        "Performing cleaning motion",
                        "Raising to safe height"
                    ],
                    "SLOT 0 PICKUP": [
                        "Moving to slot 0 approach position",
                        "Descending to pickup height",
                        "Closing gripper/engaging tool",
                        "Lifting with part/tool"
                    ],
                    "SLOT 0 DROPOFF": [
                        "Moving to slot 0 with part/tool",
                        "Descending to dropoff height",
                        "Opening gripper/releasing tool",
                        "Retracting to safe position"
                    ],
                    "SLOT 1 PICKUP": [
                        "Moving to slot 1 approach position",
                        "Descending to pickup height",
                        "Closing gripper/engaging tool",
                        "Lifting with part/tool"
                    ],
                    "SLOT 1 DROPOFF": [
                        "Moving to slot 1 with part/tool",
                        "Descending to dropoff height",
                        "Opening gripper/releasing tool",
                        "Retracting to safe position"
                    ],
                    "SLOT 4 PICKUP": [
                        "Moving to slot 4 approach position",
                        "Descending to pickup height",
                        "Closing gripper/engaging tool",
                        "Lifting with part/tool"
                    ],
                    "SLOT 4 DROPOFF": [
                        "Moving to slot 4 with part/tool",
                        "Descending to dropoff height",
                        "Opening gripper/releasing tool",
                        "Retracting to safe position"
                    ],
                    "TOOL CHANGER": [
                        "Moving to tool changer position",
                        "Aligning with tool interface",
                        "Engaging/disengaging tool",
                        "Confirming tool change"
                    ]
                }

                # Print operation-specific steps
                if group_name in trajectory_steps:
                    print(f"\n🎯 {group_name} Operations:")
                    for step in trajectory_steps[group_name]:
                        print(f"   • {step}")

                print(f"\n✅ {group_name} trajectory execution completed!")
                print("=" * 50)

                # Show success message to user
                QMessageBox.information(
                    self.ui,
                    "Trajectory Executed",
                    f"{group_name} trajectory executed successfully!\n\n"
                    f"Points executed: {len(points)}\n"
                    f"Check console for detailed execution log."
                )

            else:
                print("❌ Cannot execute trajectory - not a multi-point group!")
                QMessageBox.warning(self.ui, "Invalid Trajectory",
                                    f"{group_name} is not a multi-point trajectory group.")
        else:
            print(f"❌ Group {group_name} not found!")

    def on_undo(self):
        """Handle undo request"""
        description = self.command_history.undo()
        if description:
            print(f"Undid: {description}")
            self.update_undo_redo_buttons()
        else:
            QMessageBox.information(self.ui, "Nothing to Undo", "No actions available to undo.")

    def on_redo(self):
        """Handle redo request"""
        description = self.command_history.redo()
        if description:
            print(f"Redid: {description}")
            self.update_undo_redo_buttons()
        else:
            QMessageBox.information(self.ui, "Nothing to Redo", "No actions available to redo.")

    def execute_command_with_history(self, command):
        """Execute command and add to history"""
        self.command_history.execute_command(command)
        self.update_undo_redo_buttons()
        print(f"Executed: {command.get_description()}")

    def update_undo_redo_buttons(self):
        """Update undo/redo button states"""
        if hasattr(self.ui, 'undo_btn'):
            self.ui.undo_btn.setEnabled(self.command_history.can_undo())
        if hasattr(self.ui, 'redo_btn'):
            self.ui.redo_btn.setEnabled(self.command_history.can_redo())

    # Helper methods
    def _edit_position_dialog(self, current_text, group_name, item):
        """Show position edit dialog"""
        try:
            position_str = current_text.strip("[]")
            position_values = [float(x.strip()) for x in position_str.split(",")]
            formatted_position = "\n".join([f"{i}: {val}" for i, val in enumerate(position_values)])
        except:
            formatted_position = current_text

        new_text, ok = QInputDialog.getMultiLineText(
            self.ui,
            f"Edit Position in {group_name}",
            "Edit position values (format: 0: x, 1: y, 2: z, 3: rx, 4: ry, 5: rz):",
            formatted_position
        )

        if ok and new_text.strip():
            try:
                lines = new_text.strip().split('\n')
                new_values = []

                for line in lines:
                    if ':' in line:
                        value = float(line.split(':', 1)[1].strip())
                        new_values.append(value)
                    else:
                        new_values.append(float(line.strip()))

                item.setText(str(new_values))
                print(f"Updated position in {group_name}: {new_values}")
                return True

            except ValueError as e:
                QMessageBox.warning(
                    self.ui,
                    "Invalid Input",
                    f"Could not parse the position values. Please ensure all values are valid numbers.\nError: {str(e)}"
                )
        return False

    def _get_velocity_acceleration_info(self, group_name):
        """Get velocity/acceleration info string for a group"""
        if group_name in self.ui.velocity_acceleration_widgets:
            vel = self.ui.velocity_acceleration_widgets[group_name]["velocity"].value()
            acc = self.ui.velocity_acceleration_widgets[group_name]["acceleration"].value()
            return f" (Velocity: {vel}, Acceleration: {acc})"
        return ""

    # Configuration management
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    config = RobotConfig.from_dict(data)
            else:
                config = self.get_default_config()
                self.save_config_to_file(config.to_dict())

            self.apply_config_to_ui(config)

        except Exception as e:
            QMessageBox.warning(self.ui, "Config Load Error", f"Failed to load config: {str(e)}\nUsing defaults.")
            config = self.get_default_config()
            self.apply_config_to_ui(config)

    def apply_config_to_ui(self, config):
        """Apply configuration to UI elements"""
        self.is_loading = True

        self.ui.ip_edit.setText(config.robot_ip)
        self.ui.tool_edit.setValue(config.robot_tool)
        self.ui.user_edit.setValue(config.robot_user)

        for group_name, group_data in config.movement_groups.items():
            if group_name in self.ui.position_lists:
                widget = self.ui.position_lists[group_name]

                if isinstance(widget, QLineEdit):
                    widget.setText(group_data.position or "")
                elif isinstance(widget, QListWidget):
                    widget.clear()
                    for point in group_data.points:
                        item = QListWidgetItem(point)
                        widget.addItem(item)

            if group_name in self.ui.velocity_acceleration_widgets:
                widgets = self.ui.velocity_acceleration_widgets[group_name]
                widgets["velocity"].setValue(group_data.velocity)
                widgets["acceleration"].setValue(group_data.acceleration)

        self.is_loading = False
        self.update_undo_redo_buttons()

    def get_current_config(self):
        """Get current configuration from UI"""
        movement_groups = {}

        for group_name, widget in self.ui.position_lists.items():
            group_data = MovementGroup()

            if isinstance(widget, QLineEdit):
                position_text = widget.text().strip()
                if position_text:
                    group_data.position = position_text
            elif isinstance(widget, QListWidget):
                points = []
                for i in range(widget.count()):
                    item = widget.item(i)
                    points.append(item.text())
                group_data.points = points

            movement_groups[group_name] = group_data

        for group_name, widgets in self.ui.velocity_acceleration_widgets.items():
            if group_name not in movement_groups:
                movement_groups[group_name] = MovementGroup()

            movement_groups[group_name].velocity = widgets["velocity"].value()
            movement_groups[group_name].acceleration = widgets["acceleration"].value()

        return RobotConfig(
            robot_ip=self.ui.ip_edit.text(),
            robot_tool=self.ui.tool_edit.value(),
            robot_user=self.ui.user_edit.value(),
            movement_groups=movement_groups
        )

    def save_config_to_file(self, config_data):
        """Save configuration to JSON file and send UPDATE_CONFIG request"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
            
            # Send UPDATE_CONFIG request after successful save
            if self.request_sender:
                self.request_sender.send_request("UPDATE_CONFIG", self.config_file)
            
        except Exception as e:
            QMessageBox.warning(self.ui, "Save Error", f"Failed to save config: {str(e)}")


# Main UI Class
class RobotConfigUI(QWidget):
    def __init__(self, robotConfigController=None):
        super().__init__()
        self.setWindowTitle("Robot Config UI")
        self.resize(1200, 800)
        self.position_lists = {}
        self.velocity_acceleration_widgets = {}
        self.signals = RobotConfigSignals()
        self.init_ui()
        self.connect_ui_signals()

        # Initialize controller
        if robotConfigController is None:
            # Create default request sender for the controller
            request_sender = RequestSender()
            self.controller = RobotConfigController(request_sender)
        else:
            self.controller = robotConfigController
        
        # Set UI reference in controller and initialize
        self.controller.set_ui(self)

    def init_ui(self):
        # Main horizontal layout
        main_layout = QHBoxLayout()

        # Left side - Configuration panel (2/3 width)
        config_panel = QWidget()
        config_layout = QVBoxLayout()

        # Robot Info
        robot_group = QGroupBox("Robot Info")
        robot_layout = QGridLayout()
        self.ip_edit = QLineEdit("192.168.58.2")
        self.tool_edit = QSpinBox()
        self.tool_edit.setRange(0, 10)
        self.tool_edit.setValue(0)
        self.user_edit = QSpinBox()
        self.user_edit.setRange(0, 10)
        self.user_edit.setValue(0)
        robot_layout.addWidget(QLabel("ROBOT_IP:"), 0, 0)
        robot_layout.addWidget(self.ip_edit, 0, 1)
        robot_layout.addWidget(QLabel("ROBOT_TOOL:"), 1, 0)
        robot_layout.addWidget(self.tool_edit, 1, 1)
        robot_layout.addWidget(QLabel("ROBOT_USER:"), 2, 0)
        robot_layout.addWidget(self.user_edit, 2, 1)
        robot_group.setLayout(robot_layout)
        config_layout.addWidget(robot_group)

        # Scrollable area for movement groups
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout()

        # Movement groups
        movement_groups = {
            "LOGIN_POS": {"has_vel_acc": True, "single_position": True},
            "HOME_POS": {"has_vel_acc": True, "single_position": True},
            "CALIBRATION_POS": {"has_vel_acc": True, "single_position": True},
            "JOG": {"velocity": 20, "acceleration": 100, "has_positions": False},
            "NOZZLE CLEAN": {"velocity": 30, "acceleration": 30, "has_positions": True},
            "TOOL CHANGER": {"velocity": 100, "acceleration": 30, "has_positions": True},
            "SLOT 0 PICKUP": {"has_vel_acc": False, "has_positions": True},
            "SLOT 0 DROPOFF": {"has_vel_acc": False, "has_positions": True},
            "SLOT 1 PICKUP": {"has_vel_acc": False, "has_positions": True},
            "SLOT 1 DROPOFF": {"has_vel_acc": False, "has_positions": True},
            "SLOT 4 PICKUP": {"has_vel_acc": False, "has_positions": True},
            "SLOT 4 DROPOFF": {"has_vel_acc": False, "has_positions": True},
        }

        for group_name, config in movement_groups.items():
            group_box = QGroupBox(group_name)
            group_layout = QVBoxLayout()

            # Velocity/acceleration controls
            if "velocity" in config and "acceleration" in config:
                vel_acc_layout = QHBoxLayout()
                vel_label = QLabel("Velocity:")
                vel_spin = QSpinBox()
                vel_spin.setRange(0, 1000)
                vel_spin.setValue(config["velocity"])
                acc_label = QLabel("Acceleration:")
                acc_spin = QSpinBox()
                acc_spin.setRange(0, 1000)
                acc_spin.setValue(config["acceleration"])

                vel_acc_layout.addWidget(vel_label)
                vel_acc_layout.addWidget(vel_spin)
                vel_acc_layout.addWidget(acc_label)
                vel_acc_layout.addWidget(acc_spin)
                vel_acc_layout.addStretch()
                group_layout.addLayout(vel_acc_layout)

                self.velocity_acceleration_widgets[group_name] = {
                    "velocity": vel_spin,
                    "acceleration": acc_spin
                }
            elif config.get("has_vel_acc", False):
                vel_acc_layout = QHBoxLayout()
                vel_label = QLabel("Velocity:")
                vel_spin = QSpinBox()
                vel_spin.setRange(0, 1000)
                vel_spin.setValue(0)
                acc_label = QLabel("Acceleration:")
                acc_spin = QSpinBox()
                acc_spin.setRange(0, 1000)
                acc_spin.setValue(0)

                vel_acc_layout.addWidget(vel_label)
                vel_acc_layout.addWidget(vel_spin)
                vel_acc_layout.addWidget(acc_label)
                vel_acc_layout.addWidget(acc_spin)
                vel_acc_layout.addStretch()
                group_layout.addLayout(vel_acc_layout)

                self.velocity_acceleration_widgets[group_name] = {
                    "velocity": vel_spin,
                    "acceleration": acc_spin
                }

            # Position controls
            if config.get("single_position", False):
                # Single position display
                position_layout = QHBoxLayout()
                position_label = QLabel(f"{group_name} Position:")
                position_display = QLineEdit()
                position_display.setReadOnly(True)
                edit_position_btn = QPushButton("Edit")
                set_current_btn = QPushButton("Set Current")
                move_to_btn = QPushButton("Move To")

                edit_position_btn.clicked.connect(
                    lambda checked, gn=group_name: self.signals.edit_single_position_requested.emit(gn))
                set_current_btn.clicked.connect(
                    lambda checked, gn=group_name: self.signals.set_current_position_requested.emit(gn))
                move_to_btn.clicked.connect(
                    lambda checked, gn=group_name: self.signals.move_to_single_position_requested.emit(gn))

                position_layout.addWidget(position_display)
                position_layout.addWidget(edit_position_btn)
                position_layout.addWidget(set_current_btn)
                position_layout.addWidget(move_to_btn)

                group_layout.addWidget(position_label)
                group_layout.addLayout(position_layout)
                self.position_lists[group_name] = position_display

            elif config.get("has_positions", True):
                # Multiple positions
                position_list = QListWidget()
                position_list.setMaximumHeight(120)
                group_layout.addWidget(QLabel(f"{group_name} Points:"))
                group_layout.addWidget(position_list)

                button_layout = QHBoxLayout()
                add_btn = QPushButton("Add")
                remove_btn = QPushButton("Remove")
                edit_btn = QPushButton("Edit")
                move_btn = QPushButton("Move To")
                save_current_btn = QPushButton("Save Current")

                add_btn.clicked.connect(lambda checked, gn=group_name: self.signals.add_point_requested.emit(gn))
                remove_btn.clicked.connect(lambda checked, gn=group_name: self.signals.remove_point_requested.emit(gn))
                edit_btn.clicked.connect(lambda checked, gn=group_name: self.signals.edit_point_requested.emit(gn))
                move_btn.clicked.connect(lambda checked, gn=group_name: self.signals.move_to_point_requested.emit(gn))
                save_current_btn.clicked.connect(
                    lambda checked, gn=group_name: self.signals.save_current_position_as_point.emit(gn))

                button_layout.addWidget(add_btn)
                button_layout.addWidget(remove_btn)
                button_layout.addWidget(edit_btn)
                button_layout.addWidget(move_btn)
                button_layout.addWidget(save_current_btn)

                # Add Execute Trajectory button for trajectory groups
                trajectory_groups = ["NOZZLE CLEAN", "TOOL CHANGER", "SLOT 0 PICKUP", "SLOT 0 DROPOFF",
                                     "SLOT 1 PICKUP", "SLOT 1 DROPOFF", "SLOT 4 PICKUP", "SLOT 4 DROPOFF"]

                if group_name in trajectory_groups:
                    execute_btn = QPushButton("Execute Trajectory")
                    execute_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #28a745;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 6px 12px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #218838;
                        }
                        QPushButton:pressed {
                            background-color: #1e7e34;
                        }
                    """)
                    execute_btn.clicked.connect(
                        lambda checked, gn=group_name: self.signals.execute_trajectory_requested.emit(gn))
                    button_layout.addWidget(execute_btn)

                group_layout.addLayout(button_layout)

                self.position_lists[group_name] = position_list

            group_box.setLayout(group_layout)
            content_layout.addWidget(group_box)

        content.setLayout(content_layout)
        scroll.setWidget(content)
        config_layout.addWidget(scroll)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        self.undo_btn = QPushButton("↶ Undo")
        self.redo_btn = QPushButton("↷ Redo")
        self.undo_btn.clicked.connect(lambda: self.signals.undo_requested.emit())
        self.redo_btn.clicked.connect(lambda: self.signals.redo_requested.emit())
        self.undo_btn.setEnabled(False)
        self.redo_btn.setEnabled(False)

        btn_layout.addWidget(self.undo_btn)
        btn_layout.addWidget(self.redo_btn)
        btn_layout.addStretch()

        save_btn = QPushButton("Save")
        reset_btn = QPushButton("Reset")
        save_btn.clicked.connect(lambda: self.signals.save_requested.emit())
        reset_btn.clicked.connect(lambda: self.signals.reset_requested.emit())
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(reset_btn)
        config_layout.addLayout(btn_layout)

        config_panel.setLayout(config_layout)
        main_layout.addWidget(config_panel, 2)  # 2/3 width

        # Right side - Jog control panel (1/3 width)
        jog_panel = QWidget()
        jog_layout = QVBoxLayout()

        jog_title = QLabel("Robot Jog Control")
        jog_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333333;
            margin-bottom: 10px;
            padding: 10px;
            background-color: #F0F0F0;
            border-radius: 4px;
        """)
        jog_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        jog_layout.addWidget(jog_title)

        self.jog_widget = RobotJogWidget()
        jog_layout.addWidget(self.jog_widget)
        jog_layout.addStretch()

        jog_panel.setLayout(jog_layout)
        main_layout.addWidget(jog_panel, 1)  # 1/3 width

        self.setLayout(main_layout)

    def connect_ui_signals(self):
        """Connect UI element signals to custom signals"""
        # Robot info signals
        self.ip_edit.textChanged.connect(self.signals.robot_ip_changed.emit)
        self.tool_edit.valueChanged.connect(self.signals.robot_tool_changed.emit)
        self.user_edit.valueChanged.connect(self.signals.robot_user_changed.emit)

        # Velocity/acceleration signals
        for group_name, widgets in self.velocity_acceleration_widgets.items():
            widgets["velocity"].valueChanged.connect(
                lambda value, gn=group_name: self.signals.velocity_changed.emit(gn, value)
            )
            widgets["acceleration"].valueChanged.connect(
                lambda value, gn=group_name: self.signals.acceleration_changed.emit(gn, value)
            )

        # Connect jog widget signals
        self.jog_widget.jogRequested.connect(self.signals.jog_requested.emit)
        self.jog_widget.jogStarted.connect(self.signals.jog_started.emit)
        self.jog_widget.jogStopped.connect(self.signals.jog_stopped.emit)
        self.jog_widget.save_point_requested.connect(self.on_jog_save_point)

    def on_jog_save_point(self):
        """Handle save point request from jog widget"""
        # Create dialog to select target group
        dialog = QDialog(self)
        dialog.setWindowTitle("Save Current Position")
        dialog.setModal(True)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select target group to save current position:"))

        combo = QComboBox()
        # Add groups that can accept new points
        for group_name in self.position_lists.keys():
            widget = self.position_lists[group_name]
            if isinstance(widget, QListWidget):  # Multi-position groups
                combo.addItem(group_name)

        layout.addWidget(combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted and combo.currentText():
            selected_group = combo.currentText()
            self.signals.save_current_position_as_point.emit(selected_group)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    request_sender = RequestSender()
    robot_config_controller = RobotConfigController(request_sender)
    window = RobotConfigUI(robotConfigController=robot_config_controller)
    window.show()
    sys.exit(app.exec())
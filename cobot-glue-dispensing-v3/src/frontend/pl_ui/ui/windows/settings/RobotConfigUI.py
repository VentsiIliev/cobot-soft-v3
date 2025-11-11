from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QGridLayout, QGroupBox, QVBoxLayout, QHBoxLayout, QScrollArea,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog, QFrame,
    QSizePolicy, QSpacerItem, QSlider, QComboBox, QDialog, QDialogButtonBox
)
from src.frontend.pl_ui.ui.widgets.virtualKeyboard.VirtualKeyboard import FocusLineEdit,FocusSpinBox,FocusDoubleSpinBox
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer
import sys
import json
import os
import copy
from modules.shared.shared.settings.robotConfig.robotConfigModel import RobotConfig, MovementGroup,get_default_config

from modules.shared.v1.Response import Response
from modules.shared.v1.DomesticRequestSender import DomesticRequestSender
from modules.shared.v1.Constants import ROBOT_MOVE_TO_HOME_POS, ROBOT_MOVE_TO_LOGIN_POS, ROBOT_MOVE_TO_CALIB_POS, \
    ROBOT_SLOT_0_PICKUP, ROBOT_SLOT_0_DROP, ROBOT_EXECUTE_NOZZLE_CLEAN, ROBOT_GET_CURRENT_POSITION, \
    RESPONSE_STATUS_ERROR
from modules.shared.v1.Constants import ROBOT_MOVE_TO_POSITION
from modules.shared.v1.Constants import ROBOT_SLOT_1_DROP,ROBOT_SLOT_1_PICKUP, ROBOT_SLOT_4_DROP,ROBOT_SLOT_4_PICKUP
from modules.shared.v1.Constants import ROBOT_UPDATE_CONFIG
from src.frontend.pl_ui.ui.windows.settings.BaseSettingsTabLayout import BaseSettingsTabLayout
from src.frontend.pl_ui.localization import TranslationKeys, get_app_translator
class RequestHandler:

    def handleRequest(self,request,data):
        if request == ROBOT_MOVE_TO_HOME_POS:
            print(f"🏠 Executing {request}: {data}")
        elif request == ROBOT_MOVE_TO_LOGIN_POS:
            print(f"🔐 Executing {request}: {data}")
        elif request == ROBOT_MOVE_TO_CALIB_POS:
            print(f"⚙️  Executing {request}: {data}")
        elif request == ROBOT_MOVE_TO_POSITION:
            print(f"📍 Executing {request}: {data}")
        elif request == ROBOT_UPDATE_CONFIG:
            print(f"💾 Executing UPDATE_CONFIG: {data}")
        else:
            print(f"Handling request: {request} with data {data}")



# ========================= DATA CLASSES =========================




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
        self.step_slider = JogSlider("Step", self) # TODO TRANSLATE
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

        self.btn_z_plus = self.createJogButton("Z-", "#905BA9")
        self.btn_z_minus = self.createJogButton("Z+", "#905BA9")
        z_layout.addWidget(self.btn_z_plus)
        z_layout.addSpacing(12)
        z_layout.addWidget(self.btn_z_minus)
        z_layout.addStretch(1)
        jog_controls_layout.addLayout(z_layout)

        jog_controls_layout.addSpacing(40)

        # XY axes
        xy_container = QVBoxLayout()
        xy_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        xy_label = QLabel("X-Y Axes") # TODO TRANSLATE just Axes
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

        self.save_point_btn = QPushButton("Save Point") # TODO TRANSLATE
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

        self.clear_points_btn = QPushButton("Clear Points") # TODO TRANSLATE
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
        self.points_label.setVisible(False)
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
                self, "Clear Points", # TODO TRANSLATE
                f"Are you sure you want to clear all {len(self.saved_points)} saved points?", # TODO TRANSLATE
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.saved_points.clear()
                self.updatePointsDisplay()
        else:
            QMessageBox.information(self, "No Points", "No points to clear") # TODO TRANSLATE

    def updatePointsDisplay(self):
        self.points_label.setText(f"Saved Points: {len(self.saved_points)}") # TODO TRANSLATE

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
    tcp_x_offset_changed = pyqtSignal(float)
    tcp_y_offset_changed = pyqtSignal(float)

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

    # Safety limit signals
    safety_limit_changed = pyqtSignal(str, int)  # limit_name, value

    # Global motion settings signals
    global_velocity_changed = pyqtSignal(int)  # value
    global_acceleration_changed = pyqtSignal(int)  # value

    # Jog operations
    jog_requested = pyqtSignal(str, str, str, float)  # command, axis, direction, value
    jog_started = pyqtSignal(str)  # direction
    jog_stopped = pyqtSignal(str)  # direction
    save_current_position_as_point = pyqtSignal(str)  # group_name

    # Trajectory execution
    execute_trajectory_requested = pyqtSignal(str)  # group_name
    
    # Nozzle clean iterations
    nozzle_clean_iterations_changed = pyqtSignal(int)  # iterations_value

# Controller
class RobotConfigController:
    """Controller class to handle all robot configuration logic"""

    def __init__(self,requestSender):
        self.ui = None  # Will be set by the UI after initialization
        self.requestSender=requestSender
        # Use absolute path to the config file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up from current directory to project root (5 levels up from settings directory)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..', '..'))
        self.config_file = os.path.join(project_root,  "backend", 'system', 'storage', 'settings', 'robot_config.json')
        self.command_history = CommandHistory()
        self.is_loading = False  # Flag to prevent undo tracking during load

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
        signals.tcp_x_offset_changed.connect(self.on_tcp_x_offset_changed)
        signals.tcp_y_offset_changed.connect(self.on_tcp_y_offset_changed)

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

        # Safety limit signals
        signals.safety_limit_changed.connect(self.on_safety_limit_changed)
        
        # Nozzle clean iterations signal
        signals.nozzle_clean_iterations_changed.connect(self.on_nozzle_clean_iterations_changed)

        # Global motion settings signals
        signals.global_velocity_changed.connect(self.on_global_velocity_changed)
        signals.global_acceleration_changed.connect(self.on_global_acceleration_changed)

    def on_safety_limit_changed(self, limit_name, value):
        """Handle safety limit change"""
        if not self.is_loading:
            old_config = self.get_current_config()
            new_config = copy.deepcopy(old_config)

            # Update the specific safety limit
            safety_limits = new_config.safety_limits
            if limit_name == "X_MIN":
                safety_limits.x_min = value
            elif limit_name == "X_MAX":
                safety_limits.x_max = value
            elif limit_name == "Y_MIN":
                safety_limits.y_min = value
            elif limit_name == "Y_MAX":
                safety_limits.y_max = value
            elif limit_name == "Z_MIN":
                safety_limits.z_min = value
            elif limit_name == "Z_MAX":
                safety_limits.z_max = value
            elif limit_name == "RX_MIN":
                safety_limits.rx_min = value
            elif limit_name == "RX_MAX":
                safety_limits.rx_max = value
            elif limit_name == "RY_MIN":
                safety_limits.ry_min = value
            elif limit_name == "RY_MAX":
                safety_limits.ry_max = value
            elif limit_name == "RZ_MIN":
                safety_limits.rz_min = value
            elif limit_name == "RZ_MAX":
                safety_limits.rz_max = value

            command = ConfigChangeCommand(self, old_config, new_config, f"Change {limit_name} to {value}")
            self.execute_command_with_history(command)
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

    def on_tcp_x_offset_changed(self, value):
        """Handle TCP X offset change"""
        if not self.is_loading:
            old_config = self.get_current_config()
            new_config = copy.deepcopy(old_config)
            new_config.tcp_x_offset = value
            command = ConfigChangeCommand(self, old_config, new_config, f"Change TCP X Offset to {value}")
            self.execute_command_with_history(command)

    def on_tcp_y_offset_changed(self, value):
        """Handle TCP Y offset change"""
        if not self.is_loading:
            old_config = self.get_current_config()
            new_config = copy.deepcopy(old_config)
            new_config.tcp_y_offset = value
            command = ConfigChangeCommand(self, old_config, new_config, f"Change TCP Y Offset to {value}")
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
            QMessageBox.information(self.ui, "No Selection", "Please select a point to edit.") # TODO TRANSLATE

    def on_move_to_point(self, group_name):
        """Handle move to point request"""
        list_widget = self.ui.position_lists[group_name]
        current_item = list_widget.currentItem()

        if current_item:
            point_name = current_item.text()
            x, y, z, rx, ry, rz = [s.strip() for s in point_name.strip('[]').split(',')]
            print(f"Parsed coordinates: x={x}, y={y}, z={z}, rx={rx}, ry={ry}, rz={rz}")
            req = ROBOT_MOVE_TO_POSITION.format(position = f"{x}/{y}/{z}/{rx}/{ry}/{rz}")
            vel_acc_info = self._get_velocity_acceleration_info(group_name)
            print(f"Moving to point: {point_name} in group: {group_name}{vel_acc_info}")
            self.requestSender.sendRequest(req, "")
        else:
            QMessageBox.information(self.ui, "No Selection", "Please select a point to move to.") # TODO TRANSLATE

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

            # Send appropriate movement request based on group name
            if self.requestSender:
                if group_name == "HOME_POS":
                    self.requestSender.sendRequest(ROBOT_MOVE_TO_HOME_POS, position_text)
                    print(f"🤖 ROBOT_MOVE_TO_HOME_POS request sent: {position_text}")
                elif group_name == "LOGIN_POS":
                    self.requestSender.sendRequest(ROBOT_MOVE_TO_LOGIN_POS, position_text)
                    print(f"🤖 ROBOT_MOVE_TO_LOGIN_POS request sent: {position_text}")
                elif group_name == "CALIBRATION_POS":
                    self.requestSender.sendRequest(ROBOT_MOVE_TO_CALIB_POS, position_text)
                    print(f"🤖 ROBOT_MOVE_TO_CALIB_POS request sent: {position_text}")
                else:
                    # For other positions, just print the movement info
                    print(f"Moving to {group_name} (no specific request constant defined)")
        else:
            QMessageBox.information(self.ui, "No Position", f"No position set for {group_name}.") # TODO TRANSLATE

    def on_save(self):
        """Handle save request"""
        config = self.get_current_config()
        self.save_config_to_file(config.to_dict())
        QMessageBox.information(self.ui, "Current Configuration", # TODO TRANSLATE
                                f"Configuration saved to {self.config_file}\n\n" + # TODO TRANSLATE
                                json.dumps(config.to_dict(), indent=2))

    def on_reset(self):
        """Handle reset request"""
        old_config = self.get_current_config()
        default_config = get_default_config()

        command = ConfigChangeCommand(self, old_config, default_config, "Reset configuration to defaults")
        self.execute_command_with_history(command)

        QMessageBox.information(self.ui, "Reset Complete", "Configuration has been reset to defaults and saved.")# TODO TRANSLATE

    def on_jog_requested(self, command, axis, direction, step):
        """Handle jog request from jog widget"""
        print(f"Jog request: {command} {axis} {direction} {step}")
        request = f"robot/jog/{axis}/{direction}/{step}"
        self.requestSender.sendRequest(request)

    def on_jog_started(self, direction):
        """Handle jog start"""
        print(f"Jog started: {direction}")

    def on_jog_stopped(self, direction):
        """Handle jog stop"""
        print(f"Jog stopped: {direction}")

    def on_save_current_position_as_point(self, group_name):
        """Handle saving current robot position to a specific group"""
        print(f"Saving current position to {group_name}")
        response = self.requestSender.sendRequest(ROBOT_GET_CURRENT_POSITION)
        response = Response.from_dict(response)
        status = response.status
        if status == RESPONSE_STATUS_ERROR:
            message = response.message
            # show error message
            QMessageBox.critical(self.ui, "Error", f"Failed to get current position: {message}") # TODO TRANSLATE
            return

        current_position = response.data.get("position", None)
        # current_position = [100, 200, 300, 180, 0, 90]  # Mock current position

        if group_name in self.ui.position_lists:
            widget = self.ui.position_lists[group_name]

            if isinstance(widget, FocusLineEdit):
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

        QMessageBox.information(self.ui, "Position Saved", f"Current position saved to {group_name}") # TODO TRANSLATE

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
                    QMessageBox.warning(self.ui, "Empty Trajectory", f"No points defined for {group_name} trajectory.") # TODO TRANSLATE
                    return

                request = None
                if group_name == "SLOT 1 PICKUP":
                    request = ROBOT_SLOT_1_PICKUP
                elif group_name == "SLOT 1 DROPOFF":
                    request = ROBOT_SLOT_1_DROP
                elif group_name == "SLOT 4 PICKUP":
                    request = ROBOT_SLOT_4_PICKUP
                elif group_name == "SLOT 4 DROPOFF":
                    request = ROBOT_SLOT_4_DROP
                elif group_name == "SLOT 0 PICKUP":
                    request = ROBOT_SLOT_0_PICKUP
                elif group_name == "SLOT 0 DROPOFF":
                    request = ROBOT_SLOT_0_DROP
                elif group_name == "NOZZLE CLEAN":
                    request = ROBOT_EXECUTE_NOZZLE_CLEAN

                self.requestSender.sendRequest(request)

        else:
            print(f"❌ Group {group_name} not found!")

    def on_nozzle_clean_iterations_changed(self, value):
        """Handle nozzle clean iterations change"""
        if not self.is_loading:
            old_config = self.get_current_config()
            new_config = copy.deepcopy(old_config)
            if "NOZZLE CLEAN" not in new_config.movement_groups:
                new_config.movement_groups["NOZZLE CLEAN"] = MovementGroup()
            new_config.movement_groups["NOZZLE CLEAN"].iterations = value
            command = ConfigChangeCommand(self, old_config, new_config, f"Change NOZZLE CLEAN iterations to {value}")
            self.execute_command_with_history(command)

    def on_global_velocity_changed(self, value):
        """Handle global velocity change"""
        if not self.is_loading:
            old_config = self.get_current_config()
            new_config = copy.deepcopy(old_config)
            if "GLOBAL" not in new_config.movement_groups:
                new_config.movement_groups["GLOBAL"] = MovementGroup()
            new_config.movement_groups["GLOBAL"].velocity = value
            command = ConfigChangeCommand(self, old_config, new_config, f"Change GLOBAL velocity to {value}")
            self.execute_command_with_history(command)

    def on_global_acceleration_changed(self, value):
        """Handle global acceleration change"""
        if not self.is_loading:
            old_config = self.get_current_config()
            new_config = copy.deepcopy(old_config)
            if "GLOBAL" not in new_config.movement_groups:
                new_config.movement_groups["GLOBAL"] = MovementGroup()
            new_config.movement_groups["GLOBAL"].acceleration = value
            command = ConfigChangeCommand(self, old_config, new_config, f"Change GLOBAL acceleration to {value}")
            self.execute_command_with_history(command)

    def on_undo(self):
        """Handle undo request"""
        description = self.command_history.undo()
        if description:
            print(f"Undid: {description}")
            self.update_undo_redo_buttons()
        else:
            QMessageBox.information(self.ui, "Nothing to Undo", "No actions available to undo.") # TODO TRANSLATE

    def on_redo(self):
        """Handle redo request"""
        description = self.command_history.redo()
        if description:
            print(f"Redid: {description}")
            self.update_undo_redo_buttons()
        else:
            QMessageBox.information(self.ui, "Nothing to Redo", "No actions available to redo.") # TODO TRANSLATE

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
                    "Invalid Input", # TODO TRANSLATE
                    f"Could not parse the position values. Please ensure all values are valid numbers.\nError: {str(e)}" # TODO TRANSLATE
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
                config = get_default_config()
                self.save_config_to_file(config.to_dict())

            self.apply_config_to_ui(config)

        except Exception as e:
            QMessageBox.warning(self.ui, "Config Load Error", f"Failed to load config: {str(e)}\nUsing defaults.") # TODO TRANSLATE
            config = get_default_config()
            self.apply_config_to_ui(config)

    def apply_config_to_ui(self, config):
        """Apply configuration to UI elements"""
        self.is_loading = True

        self.ui.ip_edit.setText(config.robot_ip)
        self.ui.tool_edit.setValue(config.robot_tool)
        self.ui.user_edit.setValue(config.robot_user)
        self.ui.tcp_x_offset_edit.setValue(config.tcp_x_offset)
        self.ui.tcp_y_offset_edit.setValue(config.tcp_y_offset)

        # Apply safety limits
        if hasattr(self.ui, 'safety_limits'):
            self.ui.safety_limits['X_MIN'].setValue(config.safety_limits.x_min)
            self.ui.safety_limits['X_MAX'].setValue(config.safety_limits.x_max)
            self.ui.safety_limits['Y_MIN'].setValue(config.safety_limits.y_min)
            self.ui.safety_limits['Y_MAX'].setValue(config.safety_limits.y_max)
            self.ui.safety_limits['Z_MIN'].setValue(config.safety_limits.z_min)
            self.ui.safety_limits['Z_MAX'].setValue(config.safety_limits.z_max)
            self.ui.safety_limits['RX_MIN'].setValue(config.safety_limits.rx_min)
            self.ui.safety_limits['RX_MAX'].setValue(config.safety_limits.rx_max)
            self.ui.safety_limits['RY_MIN'].setValue(config.safety_limits.ry_min)
            self.ui.safety_limits['RY_MAX'].setValue(config.safety_limits.ry_max)
            self.ui.safety_limits['RZ_MIN'].setValue(config.safety_limits.rz_min)
            self.ui.safety_limits['RZ_MAX'].setValue(config.safety_limits.rz_max)

        # Apply global motion settings
        if hasattr(self.ui, 'global_velocity'):
            self.ui.global_velocity.setValue(config.global_motion_settings.global_velocity)
        if hasattr(self.ui, 'global_acceleration'):
            self.ui.global_acceleration.setValue(config.global_motion_settings.global_acceleration)
        if hasattr(self.ui, 'emergency_decel'):
            self.ui.emergency_decel.setValue(config.global_motion_settings.emergency_decel)
        if hasattr(self.ui, 'max_jog_step'):
            self.ui.max_jog_step.setValue(config.global_motion_settings.max_jog_step)

        for group_name, group_data in config.movement_groups.items():
            if group_name in self.ui.position_lists:
                widget = self.ui.position_lists[group_name]

                if isinstance(widget, FocusLineEdit):
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
                
            # Load iterations value for NOZZLE CLEAN group
            if group_name == "NOZZLE CLEAN" and hasattr(self.ui, 'nozzle_clean_iterations'):
                self.ui.nozzle_clean_iterations.setValue(group_data.iterations)

        self.is_loading = False
        self.update_undo_redo_buttons()

    def get_current_config(self):
        """Get current configuration from UI"""
        movement_groups = {}

        for group_name, widget in self.ui.position_lists.items():
            group_data = MovementGroup()

            if isinstance(widget, FocusLineEdit):
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

        # Get iterations value for NOZZLE CLEAN group  
        if hasattr(self.ui, 'nozzle_clean_iterations'):
            if "NOZZLE CLEAN" not in movement_groups:
                movement_groups["NOZZLE CLEAN"] = MovementGroup()
            movement_groups["NOZZLE CLEAN"].iterations = self.ui.nozzle_clean_iterations.value()

        # Get safety limits from UI
        from modules.shared.shared.settings.robotConfig.robotConfigModel import SafetyLimits, GlobalMotionSettings
        
        safety_limits = SafetyLimits()
        if hasattr(self.ui, 'safety_limits'):
            safety_limits.x_min = self.ui.safety_limits['X_MIN'].value()
            safety_limits.x_max = self.ui.safety_limits['X_MAX'].value()
            safety_limits.y_min = self.ui.safety_limits['Y_MIN'].value()
            safety_limits.y_max = self.ui.safety_limits['Y_MAX'].value()
            safety_limits.z_min = self.ui.safety_limits['Z_MIN'].value()
            safety_limits.z_max = self.ui.safety_limits['Z_MAX'].value()
            safety_limits.rx_min = self.ui.safety_limits['RX_MIN'].value()
            safety_limits.rx_max = self.ui.safety_limits['RX_MAX'].value()
            safety_limits.ry_min = self.ui.safety_limits['RY_MIN'].value()
            safety_limits.ry_max = self.ui.safety_limits['RY_MAX'].value()
            safety_limits.rz_min = self.ui.safety_limits['RZ_MIN'].value()
            safety_limits.rz_max = self.ui.safety_limits['RZ_MAX'].value()

        # Get global motion settings from UI
        global_motion_settings = GlobalMotionSettings()
        if hasattr(self.ui, 'global_velocity'):
            global_motion_settings.global_velocity = self.ui.global_velocity.value()
        if hasattr(self.ui, 'global_acceleration'):
            global_motion_settings.global_acceleration = self.ui.global_acceleration.value()
        if hasattr(self.ui, 'emergency_decel'):
            global_motion_settings.emergency_decel = self.ui.emergency_decel.value()
        if hasattr(self.ui, 'max_jog_step'):
            global_motion_settings.max_jog_step = self.ui.max_jog_step.value()

        return RobotConfig(
            robot_ip=self.ui.ip_edit.text(),
            robot_tool=self.ui.tool_edit.value(),
            robot_user=self.ui.user_edit.value(),
            tcp_x_offset=self.ui.tcp_x_offset_edit.value(),
            tcp_y_offset=self.ui.tcp_y_offset_edit.value(),
            movement_groups=movement_groups,
            safety_limits=safety_limits,
            global_motion_settings=global_motion_settings
        )

    def save_config_to_file(self, config_data):
        """Save configuration to JSON file and send ROBOT_UPDATE_CONFIG request"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)

            # Send UPDATE_CONFIG request after successful save
            if self.requestSender:
                self.requestSender.sendRequest(ROBOT_UPDATE_CONFIG)
                print(f"🔄 ROBOT_UPDATE_CONFIG request sent for file: {self.config_file}")
                print(f"   └── Configuration has been updated and saved")
            else:
                print("⚠️ RequestSender not available. Cannot send ROBOT_UPDATE_CONFIG request.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self.ui, "Save Error", f"Failed to save config: {str(e)}")


# Main UI Class
class RobotConfigUI(BaseSettingsTabLayout, QWidget):
    def __init__(self,parent_widget= None, robotConfigController=None):
        # super().__init__()
        BaseSettingsTabLayout.__init__(self,parent_widget)
        QWidget.__init__(self)
        self.setWindowTitle("Robot Config UI")
        self.resize(1200, 800)
        self.position_lists = {}
        self.velocity_acceleration_widgets = {}
        self.signals = RobotConfigSignals()
        # Initialize translation mapping for UI elements
        self._button_translation_map = {}
        self._group_box_translation_map = {}
        self._label_translation_map = {}
        self.init_ui()
        self.connect_ui_signals()

        # Initialize controller
        if robotConfigController is None:
            self.controller = RobotConfigController()
        else:
            self.controller = robotConfigController

        # Set UI reference in controller and initialize
        self.controller.set_ui(self)
        self.translator = get_app_translator()
        self.translator.language_changed.connect(self.translate)
        self.translate()
    def init_ui(self):
        # Main horizontal layout
        main_layout = QHBoxLayout()

        # Left side - Scrollable Configuration panel (2/3 width)
        config_scroll = QScrollArea()
        config_scroll.setWidgetResizable(True)
        config_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        config_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        config_panel = QWidget()
        config_layout = QVBoxLayout()

        # Robot Info
        self.robot_group = QGroupBox("Robot Info")
        robot_layout = QGridLayout()
        self.ip_edit = FocusLineEdit("192.168.58.2")
        self.tool_edit = FocusSpinBox()
        self.tool_edit.setRange(0, 10)
        self.tool_edit.setValue(0)
        self.user_edit = FocusSpinBox()
        self.user_edit.setRange(0, 10)
        self.user_edit.setValue(0)
        self.tcp_x_offset_edit = FocusDoubleSpinBox()
        self.tcp_x_offset_edit.setRange(-1000, 1000)
        self.tcp_x_offset_edit.setValue(0.0)
        self.tcp_x_offset_edit.setSuffix(" mm")
        self.tcp_x_offset_edit.setDecimals(3)
        self.tcp_y_offset_edit = FocusDoubleSpinBox()
        self.tcp_y_offset_edit.setRange(-1000, 1000)
        self.tcp_y_offset_edit.setValue(0.0)
        self.tcp_y_offset_edit.setSuffix(" mm")
        self.tcp_y_offset_edit.setDecimals(3)
        self.ip_label = QLabel("IP:")
        robot_layout.addWidget(self.ip_label, 0, 0)
        robot_layout.addWidget(self.ip_edit, 0, 1)

        self.robot_tool_label = QLabel("ROBOT_TOOL:")
        robot_layout.addWidget(self.robot_tool_label, 1, 0)
        robot_layout.addWidget(self.tool_edit, 1, 1)

        self.robot_user_label = QLabel("ROBOT_USER:")
        robot_layout.addWidget(self.robot_user_label, 2, 0)
        robot_layout.addWidget(self.user_edit, 2, 1)

        self.tcp_x_offset_label = QLabel("TCP X OFFSET:")
        robot_layout.addWidget(self.tcp_x_offset_label, 3, 0)
        robot_layout.addWidget(self.tcp_x_offset_edit, 3, 1)

        self.tcp_y_offset_label = QLabel("TCP Y OFFSET:")
        robot_layout.addWidget(self.tcp_y_offset_label, 4, 0)
        robot_layout.addWidget(self.tcp_y_offset_edit, 4, 1)
        self.robot_group.setLayout(robot_layout)
        # Create main scroll content widget and layout
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Add Robot Info to scroll content
        scroll_layout.addWidget(self.robot_group)

        # Safety Settings
        self.safety_group = QGroupBox("Safety Limits")
        safety_layout = QGridLayout()
        
        # Initialize safety limit spinboxes
        self.safety_limits = {}
        
        # Position limits (X, Y, Z in mm)
        position_limits = [
            ("X_MIN", "X Min (mm):", -1000, 1000, -500),
            ("X_MAX", "X Max (mm):", -1000, 1000, 500),
            ("Y_MIN", "Y Min (mm):", -1000, 1000, -500),
            ("Y_MAX", "Y Max (mm):", -1000, 1000, 500),
            ("Z_MIN", "Z Min (mm):", 0, 1000, 100),
            ("Z_MAX", "Z Max (mm):", 0, 1000, 800)
        ]
        
        # Orientation limits (RX, RY, RZ in degrees)
        orientation_limits = [
            ("RX_MIN", "RX Min (°):", -180, 180, 170),
            ("RX_MAX", "RX Max (°):", -180, 180, 190),
            ("RY_MIN", "RY Min (°):", -180, 180, -10),
            ("RY_MAX", "RY Max (°):", -180, 180, 10),
            ("RZ_MIN", "RZ Min (°):", -180, 180, -180),
            ("RZ_MAX", "RZ Max (°):", -180, 180, 180)
        ]
        
        # Create position limit controls (left column)
        row = 0
        for key, label, min_val, max_val, default_val in position_limits:
            safety_layout.addWidget(QLabel(label), row, 0)
            spinbox = FocusSpinBox()
            spinbox.setRange(min_val, max_val)
            spinbox.setValue(default_val)
            spinbox.setSuffix(" mm" if "mm" in label else " °")
            self.safety_limits[key] = spinbox
            safety_layout.addWidget(spinbox, row, 1)
            row += 1
        
        # Create orientation limit controls (right column)
        row = 0
        for key, label, min_val, max_val, default_val in orientation_limits:
            safety_layout.addWidget(QLabel(label), row, 2)
            spinbox = FocusSpinBox()
            spinbox.setRange(min_val, max_val)
            spinbox.setValue(default_val)
            spinbox.setSuffix(" °")
            self.safety_limits[key] = spinbox
            safety_layout.addWidget(spinbox, row, 3)
            row += 1
        
        self.safety_group.setLayout(safety_layout)
        scroll_layout.addWidget(self.safety_group)

        # Global Velocity and Acceleration Settings
        self.global_group = QGroupBox("Global Motion Settings")
        global_layout = QGridLayout()
        
        # Global velocity
        self.global_velocity_label = QLabel("Global Velocity:")
        global_layout.addWidget(self.global_velocity_label, 0, 0)
        self.global_velocity = FocusSpinBox()
        self.global_velocity.setRange(1, 1000)
        self.global_velocity.setValue(100)
        self.global_velocity.setSuffix(" mm/s")
        global_layout.addWidget(self.global_velocity, 0, 1)
        
        # Global acceleration
        self.global_acceleration_label = QLabel("Global Acceleration:")
        global_layout.addWidget(self.global_acceleration_label, 1, 0)
        self.global_acceleration = FocusSpinBox()
        self.global_acceleration.setRange(1, 1000)
        self.global_acceleration.setValue(100)
        self.global_acceleration.setSuffix(" mm/s²")
        global_layout.addWidget(self.global_acceleration, 1, 1)
        
        # # Emergency stop velocity
        # global_layout.addWidget(QLabel("Emergency Stop Decel:"), 2, 0) # TODO TRANSLATE
        # self.emergency_decel = FocusSpinBox()
        # self.emergency_decel.setRange(1, 2000)
        # self.emergency_decel.setValue(500)
        # self.emergency_decel.setSuffix(" mm/s²")
        # global_layout.addWidget(self.emergency_decel, 2, 1)
        #
        # # Maximum jog step
        # global_layout.addWidget(QLabel("Max Jog Step:"), 3, 0) # TODO TRANSLATE
        # self.max_jog_step = FocusSpinBox()
        # self.max_jog_step.setRange(1, 100)
        # self.max_jog_step.setValue(50)
        # self.max_jog_step.setSuffix(" mm")
        # global_layout.addWidget(self.max_jog_step, 3, 1)
        
        self.global_group.setLayout(global_layout)
        scroll_layout.addWidget(self.global_group)

        # Add Movement groups to scroll content
        movement_groups = {
            "LOGIN_POS": {"has_vel_acc": True, "single_position": True},
            "HOME_POS": {"has_vel_acc": True, "single_position": True},
            "CALIBRATION_POS": {"has_vel_acc": True, "single_position": True},
            "JOG": {"velocity": 20, "acceleration": 100, "has_positions": False},
            "NOZZLE CLEAN": {"velocity": 30, "acceleration": 30, "has_positions": True},
            "TOOL CHANGER": {"velocity": 100, "acceleration": 30, "has_positions": True},
            "SLOT 0 PICKUP": {"has_vel_acc": True, "has_positions": True},
            "SLOT 0 DROPOFF": {"has_vel_acc": True, "has_positions": True},
            "SLOT 1 PICKUP": {"has_vel_acc": True, "has_positions": True},
            "SLOT 1 DROPOFF": {"has_vel_acc": True, "has_positions": True},
            "SLOT 4 PICKUP": {"has_vel_acc": True, "has_positions": True},
            "SLOT 4 DROPOFF": {"has_vel_acc": True, "has_positions": True},
        }

        for group_name, config in movement_groups.items():
            group_box = QGroupBox(group_name)
            group_layout = QVBoxLayout()
            
            # Store group box reference for translation
            self._group_box_translation_map[group_box] = group_name

            # Velocity/acceleration controls
            if "velocity" in config and "acceleration" in config:
                vel_acc_layout = QHBoxLayout()
                vel_label = QLabel("Velocity:") # TODO TRANSLATE
                vel_spin = FocusSpinBox()
                vel_spin.setRange(0, 1000)
                vel_spin.setValue(config["velocity"])
                acc_label = QLabel("Acceleration:") # TODO TRANSLATE
                acc_spin = FocusSpinBox()
                acc_spin.setRange(0, 1000)
                acc_spin.setValue(config["acceleration"])

                vel_acc_layout.addWidget(vel_label)
                vel_acc_layout.addWidget(vel_spin)
                vel_acc_layout.addWidget(acc_label)
                vel_acc_layout.addWidget(acc_spin)
                vel_acc_layout.addStretch()
                group_layout.addLayout(vel_acc_layout)

                # Store label references for translation
                self._label_translation_map[vel_label] = "VELOCITY"
                self._label_translation_map[acc_label] = "ACCELERATION"

                self.velocity_acceleration_widgets[group_name] = {
                    "velocity": vel_spin,
                    "acceleration": acc_spin
                }
            elif config.get("has_vel_acc", False):
                vel_acc_layout = QHBoxLayout()
                vel_label = QLabel("Velocity:") # TODO TRANSLATE
                vel_spin = FocusSpinBox()
                vel_spin.setRange(0, 1000)
                vel_spin.setValue(0)
                acc_label = QLabel("Acceleration:") # TODO TRANSLATE
                acc_spin = FocusSpinBox()
                acc_spin.setRange(0, 1000)
                acc_spin.setValue(0)

                vel_acc_layout.addWidget(vel_label)
                vel_acc_layout.addWidget(vel_spin)
                vel_acc_layout.addWidget(acc_label)
                vel_acc_layout.addWidget(acc_spin)
                vel_acc_layout.addStretch()
                group_layout.addLayout(vel_acc_layout)

                # Store label references for translation
                self._label_translation_map[vel_label] = "VELOCITY"
                self._label_translation_map[acc_label] = "ACCELERATION"

                self.velocity_acceleration_widgets[group_name] = {
                    "velocity": vel_spin,
                    "acceleration": acc_spin
                }

            # Add iterations field specifically for NOZZLE CLEAN
            if group_name == "NOZZLE CLEAN":
                iterations_layout = QHBoxLayout()
                iterations_label = QLabel("Iterations:")
                iterations_spin = FocusSpinBox()
                iterations_spin.setRange(1, 100)
                iterations_spin.setValue(1)
                
                iterations_layout.addWidget(iterations_label)
                iterations_layout.addWidget(iterations_spin)
                iterations_layout.addStretch()
                group_layout.addLayout(iterations_layout)
                
                # Store for later access
                if not hasattr(self, 'nozzle_clean_iterations'):
                    self.nozzle_clean_iterations = iterations_spin

            # Position controls
            if config.get("single_position", False):
                # Single position display
                position_layout = QHBoxLayout()
                position_label = QLabel(f"{group_name} Position:") # TODO TRANSLATE
                position_display = FocusLineEdit()
                position_display.setReadOnly(True)
                edit_position_btn = QPushButton("Edit") # TODO TRANSLATE
                set_current_btn = QPushButton("Set Current") # TODO TRANSLATE
                move_to_btn = QPushButton("Move To") # TODO TRANSLATE
                
                # Store button references for translation
                self._button_translation_map[edit_position_btn] = "EDIT"
                self._button_translation_map[set_current_btn] = "SAVE_CURRENT_POSITION"
                self._button_translation_map[move_to_btn] = "MOVE_TO"

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
                group_layout.addWidget(QLabel(f"{group_name} Points:")) # TODO TRANSLATE
                group_layout.addWidget(position_list)

                button_layout = QHBoxLayout()
                add_btn = QPushButton("Add") # TODO TRANSLATE
                remove_btn = QPushButton("Remove") # TODO TRANSLATE
                edit_btn = QPushButton("Edit") # TODO TRANSLATE
                move_btn = QPushButton("Move To") # TODO TRANSLATE
                save_current_btn = QPushButton("Save Current") # TODO TRANSLATE

                # Store button references for translation
                self._button_translation_map[add_btn] = "ADD"
                self._button_translation_map[remove_btn] = "REMOVE"
                self._button_translation_map[edit_btn] = "EDIT"
                self._button_translation_map[move_btn] = "MOVE_TO"
                self._button_translation_map[save_current_btn] = "SAVE_CURRENT_POSITION"

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
                    
                    # Store button reference for translation
                    self._button_translation_map[execute_btn] = "EXECUTE_TRAJECTORY"
                    
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
            scroll_layout.addWidget(group_box)

        # Bottom buttons - also add them to scroll content
        btn_layout = QHBoxLayout()
        self.undo_btn = QPushButton("↶ Undo") # TODO TRANSLATE
        self.redo_btn = QPushButton("↷ Redo") # TODO TRANSLATE
        self.undo_btn.clicked.connect(lambda: self.signals.undo_requested.emit())
        self.redo_btn.clicked.connect(lambda: self.signals.redo_requested.emit())
        self.undo_btn.setEnabled(False)
        self.redo_btn.setEnabled(False)

        btn_layout.addWidget(self.undo_btn)
        btn_layout.addWidget(self.redo_btn)
        btn_layout.addStretch()

        save_btn = QPushButton("Save") # TODO TRANSLATE
        reset_btn = QPushButton("Reset") # TODO TRANSLATE
        
        # Store button references for translation
        self._button_translation_map[save_btn] = "SAVE"
        # Note: RESET key doesn't exist in Message enum, so reset_btn won't be translated
        
        save_btn.clicked.connect(lambda: self.signals.save_requested.emit())
        reset_btn.clicked.connect(lambda: self.signals.reset_requested.emit())
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(reset_btn)
        scroll_layout.addLayout(btn_layout)

        # Set the scroll content and add to main scroll area
        scroll_content.setLayout(scroll_layout)
        config_scroll.setWidget(scroll_content)
        main_layout.addWidget(config_scroll, 2)  # 2/3 width

        # Right side - Jog control panel (1/3 width)
        jog_panel = QWidget()
        jog_layout = QVBoxLayout()

        jog_title = QLabel("Robot Jog Control") # TODO TRANSLATE
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
        self.tcp_x_offset_edit.valueChanged.connect(self.signals.tcp_x_offset_changed.emit)
        self.tcp_y_offset_edit.valueChanged.connect(self.signals.tcp_y_offset_changed.emit)

        # Velocity/acceleration signals
        for group_name, widgets in self.velocity_acceleration_widgets.items():
            widgets["velocity"].valueChanged.connect(
                lambda value, gn=group_name: self.signals.velocity_changed.emit(gn, value)
            )
            widgets["acceleration"].valueChanged.connect(
                lambda value, gn=group_name: self.signals.acceleration_changed.emit(gn, value)
            )

        # Safety limit signals
        for limit_name, spinbox in self.safety_limits.items():
            spinbox.valueChanged.connect(
                lambda value, ln=limit_name: self.signals.safety_limit_changed.emit(ln, value)
            )

        # Global motion settings signals
        self.global_velocity.valueChanged.connect(self.signals.global_velocity_changed.emit)
        self.global_acceleration.valueChanged.connect(self.signals.global_acceleration_changed.emit)

        # Connect jog widget signals
        self.jog_widget.jogRequested.connect(self.signals.jog_requested.emit)
        self.jog_widget.jogStarted.connect(self.signals.jog_started.emit)
        self.jog_widget.jogStopped.connect(self.signals.jog_stopped.emit)
        self.jog_widget.save_point_requested.connect(self.on_jog_save_point)

        # Connect nozzle clean iterations signal
        if hasattr(self, 'nozzle_clean_iterations'):
            self.nozzle_clean_iterations.valueChanged.connect(self.signals.nozzle_clean_iterations_changed.emit)

    def on_jog_save_point(self):
        """Handle save point request from jog widget"""
        # Create dialog to select target group
        dialog = QDialog(self)
        dialog.setWindowTitle("Save Current Position")
        dialog.setModal(True)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select target group to save current position:")) # TODO TRANSLATE

        combo = QComboBox()
        # Add groups that can accept new points (both single and multi-position groups)
        for group_name in self.position_lists.keys():
            widget = self.position_lists[group_name]
            if isinstance(widget, QListWidget):  # Multi-position groups
                combo.addItem(group_name)
            elif isinstance(widget, FocusLineEdit):  # Single-position groups (LOGIN_POS, HOME_POS, CALIBRATION_POS)
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


    def translate(self):
        print(f"Translating RobotConfigUI")
        self.robot_group.setTitle(self.translator.get(TranslationKeys.RobotSettings.ROBOT_INFORMATION))
        self.robot_tool_label.setText(self.translator.get(TranslationKeys.RobotSettings.ROBOT_TOOL))
        self.robot_user_label.setText(self.translator.get(TranslationKeys.RobotSettings.ROBOT_USER))
        self.tcp_x_offset_label.setText(self.translator.get(TranslationKeys.RobotSettings.TCP_X_OFFSET))
        self.tcp_y_offset_label.setText(self.translator.get(TranslationKeys.RobotSettings.TCP_Y_OFFSET))
        self.safety_group.setTitle(self.translator.get(TranslationKeys.RobotSettings.SAFETY_LIMITS))
        self.global_group.setTitle(self.translator.get(TranslationKeys.RobotSettings.GLOBAL_MOTION_SETTINGS))
        self.global_velocity_label.setText(self.translator.get(TranslationKeys.RobotSettings.GLOBAL_VELOCITY))
        self.global_acceleration_label.setText(self.translator.get(TranslationKeys.RobotSettings.GLOBAL_ACCELERATION))
        
        # Update labels using stored references 
        if hasattr(self, '_label_translation_map'):
            for label, translation_key in self._label_translation_map.items():
                if translation_key == "VELOCITY":
                    label.setText(f"{self.translator.get(TranslationKeys.RobotSettings.VELOCITY)}:")
                elif translation_key == "ACCELERATION":
                    label.setText(f"{self.translator.get(TranslationKeys.RobotSettings.ACCELERATION)}:")
        
        # Update group box titles using stored references
        if hasattr(self, '_group_box_translation_map'):
            for group_box, original_name in self._group_box_translation_map.items():
                if original_name == "LOGIN_POS":
                    group_box.setTitle(self.translator.get(TranslationKeys.RobotSettings.LOGIN_POSITION))
                elif original_name == "CALIBRATION_POS":
                    group_box.setTitle(self.translator.get(TranslationKeys.RobotSettings.CALIBRATION_POSITION))
                elif original_name == "NOZZLE CLEAN":
                    group_box.setTitle(self.translator.get(TranslationKeys.RobotSettings.NOZZLE_CLEANING_POSITIONS))
                elif original_name == "TOOL CHANGER":
                    group_box.setTitle(self.translator.get(TranslationKeys.RobotSettings.TOOL_CHANGER_POSITION))
                elif "PICKUP" in original_name:
                    slot_number = original_name.split()[1]
                    group_box.setTitle(f"{self.translator.get(TranslationKeys.RobotSettings.SLOT)} {slot_number} {self.translator.get(TranslationKeys.RobotSettings.PICKUP_POSITIONS)}")
                elif "DROPOFF" in original_name:
                    slot_number = original_name.split()[1]
                    group_box.setTitle(f"{self.translator.get(TranslationKeys.RobotSettings.SLOT)} {slot_number} {self.translator.get(TranslationKeys.RobotSettings.DROP_POSITIONS)}")
        
        # Update button texts using stored button references
        # Store button references during creation and update them directly
        if hasattr(self, '_button_translation_map'):
            for button, translation_key in self._button_translation_map.items():
                if translation_key and hasattr(TranslationKeys, translation_key.split('.')[0]):
                    try:
                        # Navigate to nested attribute (e.g., "RobotSettings.EXECUTE_TRAJECTORY")
                        key_parts = translation_key.split('.')
                        key_obj = TranslationKeys
                        for part in key_parts:
                            key_obj = getattr(key_obj, part)
                        button.setText(self.translator.get(key_obj))
                    except AttributeError:
                        # Fallback: use Message enum directly
                        try:
                            from modules.shared.localization.enums.Message import Message
                            key_name = translation_key.split('.')[-1]  # Get last part
                            if hasattr(Message, key_name):
                                button.setText(self.translator.get(getattr(Message, key_name)))
                        except:
                            pass  # Keep original text as fallback


if __name__ == "__main__":
    requestHandler = RequestHandler()
    requestSender = DomesticRequestSender(requestHandler)
    robotConfigController = RobotConfigController(requestSender)
    app = QApplication(sys.argv)
    window = RobotConfigUI(
        robotConfigController=robotConfigController)
    window.show()
    sys.exit(app.exec())
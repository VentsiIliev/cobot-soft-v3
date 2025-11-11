import sys
from enum import Enum

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QScroller
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QApplication, QHBoxLayout,
                             QSizePolicy, QComboBox,
                             QScrollArea, QGroupBox, QGridLayout)
from src.frontend.pl_ui.ui.widgets.MaterialButton import MaterialButton
from src.frontend.pl_ui.localization import TranslationKeys, get_app_translator
from modules.shared.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from modules.glueSprayService.GlueSprayService import GlueSprayService
from src.frontend.pl_ui.ui.widgets.SwitchButton import QToggle
from src.frontend.pl_ui.ui.widgets.ToastWidget import ToastWidget
from src.frontend.pl_ui.utils.enums.GlueType import GlueType
from src.frontend.pl_ui.ui.windows.settings.BaseSettingsTabLayout import BaseSettingsTabLayout
# from BaseSettingsTabLayout import BaseSettingsTabLayout


class GlueSettingsTabLayout(BaseSettingsTabLayout, QVBoxLayout):
    def __init__(self, parent_widget,glueSettings):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)

        self.dropdown = None
        self.parent_widget = parent_widget

        self.glueSprayService = GlueSprayService(glueSettings)
        self.translator = get_app_translator()
        self.translator.language_changed.connect(self.translate)
        self.create_main_content()
        # Connect to parent widget resize events if possible
        if self.parent_widget:
            self.parent_widget.resizeEvent = self.on_parent_resize

    def translate(self):
            """Update UI text based on current language"""
            # Update styling to ensure responsive fonts are applied
            self.setup_styling()

            # Spray settings group
            if hasattr(self, 'spray_group'):
                self.spray_group.setTitle(self.translator.get(TranslationKeys.GlueSettings.SPRAY_SETTINGS))
                if hasattr(self, 'spray_layout'):
                    if self.spray_layout.itemAtPosition(0, 0):
                        self.spray_layout.itemAtPosition(0, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.SPRAY_WIDTH))
                    if self.spray_layout.itemAtPosition(1, 0):
                        self.spray_layout.itemAtPosition(1, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.SPRAYING_HEIGHT))
                    if self.spray_layout.itemAtPosition(2, 0):
                        self.spray_layout.itemAtPosition(2, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.FAN_SPEED))
                    if self.spray_layout.itemAtPosition(3, 0):
                        self.spray_layout.itemAtPosition(3, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.GENERATOR_TO_GLUE_DELAY))

            # Motor settings group
            if hasattr(self, 'motor_group'):
                self.motor_group.setTitle(self.translator.get(TranslationKeys.GlueSettings.MOTOR_SETTINGS))
                if hasattr(self, 'motor_layout'):
                    if self.motor_layout.itemAtPosition(0, 0):
                        self.motor_layout.itemAtPosition(0, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.MOTOR_SPEED))
                    if self.motor_layout.itemAtPosition(1, 0):
                        self.motor_layout.itemAtPosition(1, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.REVERSE_DURATION))
                    if self.motor_layout.itemAtPosition(2, 0):
                        self.motor_layout.itemAtPosition(2, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.REVERSE_SPEED))

            # General settings group
            if hasattr(self, 'general_group'):
                self.general_group.setTitle(self.translator.get(TranslationKeys.GlueSettings.GENERAL_SETTINGS))
                if hasattr(self, 'general_layout'):
                    if self.general_layout.itemAtPosition(0, 0):
                        self.general_layout.itemAtPosition(0, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.RZ_ANGLE))
                    if self.general_layout.itemAtPosition(2, 0):
                        self.general_layout.itemAtPosition(2, 0).widget().setText(
                            self.translator.get(TranslationKeys.GlueSettings.GLUE_TYPE))

            # Device control groups
            if hasattr(self, 'motor_control_group'):
                self.motor_control_group.setTitle(self.translator.get(TranslationKeys.GlueSettings.MOTOR_CONTROL))
            if hasattr(self, 'other_control_group'):
                self.other_control_group.setTitle(self.translator.get(TranslationKeys.GlueSettings.OTHER_SETTINGS))

            # Update toggle button texts
            if hasattr(self, 'generator_toggle_btn'):
                self.generator_toggle_btn.setText(self.translator.get(TranslationKeys.GlueSettings.GENERATOR))
            if hasattr(self, 'fan_toggle_btn'):
                self.fan_toggle_btn.setText(self.translator.get(TranslationKeys.GlueSettings.FAN))

            # Update motor toggles
            if hasattr(self, 'motor_toggles'):
                for i, motor_toggle in enumerate(self.motor_toggles, start=1):
                    motor_toggle.setText(f"{self.translator.get(TranslationKeys.GlueSettings.MOTOR)} {i}")

            # Glue dispensing group
            if hasattr(self, 'glue_dispensing_group'):
                self.glue_dispensing_group.setTitle(self.translator.get(TranslationKeys.GlueSettings.DISPENSE_GLUE))
    def on_parent_resize(self, event):
        """Handle parent widget resize events"""
        if hasattr(super(QWidget, self.parent_widget), 'resizeEvent'):
            super(QWidget, self.parent_widget).resizeEvent(event)
    def update_layout_for_screen_size(self):
        """Update layout based on current screen size"""
        # Clear and recreate the main content
        self.clear_layout()
        self.create_main_content()
    def clear_layout(self):
        """Clear all widgets from the layout"""
        while self.count():
            child = self.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
    def create_main_content(self):
        """Create the main scrollable content area with responsive layout"""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # After self.table is created
        QScroller.grabGesture(scroll_area.viewport(), QScroller.ScrollerGestureType.TouchGesture)

        # Create main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)

        self.add_settings_desktop(content_layout)

        self.add_device_control_group(content_layout)
        self.add_glue_dispensing_group(content_layout)
        self.connectDeviceControlCallbacks()

        self.addRobotMotionButtonsGroup(content_layout)

        # Add stretch at the end
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)

        # Add scroll area to main layout
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(scroll_area)

        self.addWidget(scroll_widget)

    def create_settings_control_groups(self):
        self.spray_group = self.create_spray_settings_group()
        self.motor_group = self.create_motor_settings_group()
        self.general_group = self.create_general_settings_group()

        return self.spray_group, self.motor_group, self.general_group
    def add_settings_desktop(self, parent_layout):
        """Add settings in desktop layout (3 columns)"""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(15)

        groups = self.create_settings_control_groups()

        for group in groups:
            row_layout.addWidget(group)

        parent_layout.addLayout(row_layout)

    def create_spray_settings_group(self):
        """Create spray-related settings group with responsive layout"""
        group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.SPRAY_SETTINGS))
        layout = QGridLayout(group)


        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.spray_layout = layout

        # Spray Width
        row = 0
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.SPRAY_WIDTH))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.spray_width_input = self.create_double_spinbox(0.0, 100.0, 5.0, " mm")
        layout.addWidget(self.spray_width_input, row, 1)

        # Spraying Height
        row += 1
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.SPRAYING_HEIGHT))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.spraying_height_input = self.create_double_spinbox(0.0, 500.0, 120.0, " mm")
        layout.addWidget(self.spraying_height_input, row, 1)

        # Fan Speed
        row += 1
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.FAN_SPEED))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.fan_speed_input = self.create_double_spinbox(0.0, 100.0, 100.0, " %")
        layout.addWidget(self.fan_speed_input, row, 1)

        # Time Between Generator and Glue
        row += 1
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.GENERATOR_TO_GLUE_DELAY))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.time_between_generator_and_glue_input = self.create_double_spinbox(0.0, 10.0, 1.0, " s")
        layout.addWidget(self.time_between_generator_and_glue_input, row, 1)


        row+=1
        label = QLabel("Timeout before motion")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.time_before_motion = self.create_double_spinbox(0.0,10,1.0,"s")
        layout.addWidget(self.time_before_motion, row, 1)
        # Set column stretch to make inputs expand
        layout.setColumnStretch(1, 1)

        row += 1
        label = QLabel("Reach Start Threshold")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.reach_pos_thresh = self.create_double_spinbox(0.0, 10, 1.0, "mm")
        layout.addWidget(self.reach_pos_thresh, row, 1)
        # Set column stretch to make inputs expand
        layout.setColumnStretch(1, 1)

        return group

    def create_motor_settings_group(self):
        """Create motor-related settings group with organized subsections"""
        group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.MOTOR_SETTINGS))
        main_layout = QVBoxLayout(group)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 25, 20, 20)

        # Forward Motion Settings Subsection
        forward_group = QGroupBox("Forward Motion")
        forward_layout = QGridLayout(forward_group)
        forward_layout.setSpacing(10)
        forward_layout.setContentsMargins(15, 15, 15, 15)

        row = 0
        # Motor Speed (Forward)
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.MOTOR_SPEED))
        label.setWordWrap(True)
        forward_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.motor_speed_input = self.create_double_spinbox(0.0, 100000.0, 3000.0, " Hz")
        forward_layout.addWidget(self.motor_speed_input, row, 1)

        row += 1
        # Forward Ramp Steps
        label = QLabel("Forward Ramp Steps")
        label.setWordWrap(True)
        forward_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.forward_ramp_steps = self.create_spinbox(1, 100, 1, " step(s)")
        forward_layout.addWidget(self.forward_ramp_steps, row, 1)

        row += 1
        # Initial Ramp Speed
        label = QLabel("Initial Ramp Speed")
        label.setWordWrap(True)
        forward_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.initial_ramp_speed = self.create_double_spinbox(0.0, 100000.0, 1000.0, " Hz")
        forward_layout.addWidget(self.initial_ramp_speed, row, 1)

        row += 1
        # Initial Ramp Speed Duration
        label = QLabel("Initial Ramp Speed Duration")
        label.setWordWrap(True)
        forward_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.initial_ramp_speed_duration = self.create_double_spinbox(0.0, 10.0, 1.0, " s")
        forward_layout.addWidget(self.initial_ramp_speed_duration, row, 1)

        forward_layout.setColumnStretch(1, 1)

        # Reverse Motion Settings Subsection
        reverse_group = QGroupBox("Reverse Motion")
        reverse_layout = QGridLayout(reverse_group)
        reverse_layout.setSpacing(10)
        reverse_layout.setContentsMargins(15, 15, 15, 15)

        row = 0
        # Reverse Speed
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.REVERSE_SPEED))
        label.setWordWrap(True)
        reverse_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.speed_reverse_input = self.create_double_spinbox(0.0, 100000.0, 10000.0, " Hz")
        reverse_layout.addWidget(self.speed_reverse_input, row, 1)

        row += 1
        # Reverse Duration
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.REVERSE_DURATION))
        label.setWordWrap(True)
        reverse_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.reverse_duration_input = self.create_double_spinbox(0.0, 100000.0, 1500.0, " s")
        reverse_layout.addWidget(self.reverse_duration_input, row, 1)

        row += 1
        # Reverse Ramp Steps
        label = QLabel("Reverse Ramp Steps")
        label.setWordWrap(True)
        reverse_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.reverse_ramp_steps = self.create_spinbox(1, 100, 1, " step(s)")
        reverse_layout.addWidget(self.reverse_ramp_steps, row, 1)

        reverse_layout.setColumnStretch(1, 1)

        # Add subsections to main layout
        main_layout.addWidget(forward_group)
        main_layout.addWidget(reverse_group)

        # Keep reference to main layout for compatibility
        self.motor_layout = forward_layout  # For any existing code that might reference it
        
        return group

    def create_general_settings_group(self):
        """Create general settings group with responsive layout"""
        group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.GENERAL_SETTINGS))
        layout = QGridLayout(group)


        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.general_layout = layout

        # RZ Angle
        row = 0
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.RZ_ANGLE))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.rz_angle_input = self.create_double_spinbox(-180.0, 180.0, 0.0, "°")
        layout.addWidget(self.rz_angle_input, row, 1)

        # generator timeout
        row += 1
        label = QLabel("GENERATOR_TIMEOUT")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.generator_timeout_input = self.create_double_spinbox(0.0, 600.0, 300, " s")
        layout.addWidget(self.generator_timeout_input, row, 1)

        # Spray On
        row += 1
        label = QLabel("Spray On")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.spray_on_toggle = QToggle("")
        self.spray_on_toggle.setMinimumHeight(40)
        layout.addWidget(self.spray_on_toggle, row, 1)

        # Glue Type
        row += 1
        label = QLabel(self.translator.get(TranslationKeys.GlueSettings.GLUE_TYPE))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.dropdown = QComboBox()
        self.dropdown.setMinimumHeight(40)
        self.dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        if isinstance(GlueType, type) and issubclass(GlueType, Enum):
            self.dropdown.addItems([item.value for item in GlueType])

        self.dropdown.setCurrentIndex(0)
        layout.addWidget(self.dropdown, row, 1)
        setattr(self, f"{GlueType.TypeA.value}_combo", self.dropdown)

        layout.setColumnStretch(1, 1)
        return group

    def add_device_control_group(self, parent_layout):
        """Add device control group with responsive layout"""
        group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.DEVICE_CONTROL))

        # Choose layout based on screen size

        main_layout = QHBoxLayout(group)
        main_layout.setSpacing(20)

        main_layout.setContentsMargins(20, 25, 20, 20)
        self.device_control_layout = main_layout

        # Motor Control Section
        motor_control_group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.MOTOR_CONTROL))
        motor_layout = QGridLayout(motor_control_group)
        motor_layout.setSpacing(10)
        motor_layout.setContentsMargins(15, 20, 15, 15)
        self.motor_control_group = motor_control_group

        self.motor_toggles = []
        
        # Initialize motors_healthy dictionary
        motors_healthy = {}
        
        # Get all motor states at once (efficient - only 3 seconds instead of 12)
        try:
            all_motors_state = self.glueSprayService.motorController.getAllMotorStates()
            
            if all_motors_state.success:
                # Extract motor states from the AllMotorsState object
                for motor_addr, motor_state in all_motors_state.motors.items():
                    motors_healthy[motor_addr] = motor_state.is_healthy
                    # Print debug info about motor errors
                    if not motor_state.is_healthy:
                        print(f"Motor {motor_addr} unhealthy - Errors: {motor_state.get_filtered_errors()}")
            else:
                # If failed to get states, assume all motors are unhealthy
                print("Failed to get motor states - assuming all unhealthy")
                for i in range(4):
                    motor_addr = self.glueSprayService.glueMapping.get(i + 1)
                    motors_healthy[motor_addr] = False
                    
        except Exception as e:
            print(f"Error getting all motor states: {e}")
            # Fallback: assume all motors are unhealthy
            for i in range(4):
                motor_addr = self.glueSprayService.glueMapping.get(i + 1)
                motors_healthy[motor_addr] = False
        
        for i in range(4):
            motor_toggle = QToggle(f"M{i + 1}")
            motor_toggle.setCheckable(True)
            motor_toggle.setMinimumHeight(35)

            motor_addr = self.glueSprayService.glueMapping.get(i + 1)
            is_healthy = motors_healthy.get(motor_addr, False)
            
            # Set toggle state based on motor health
            if is_healthy:
                motor_toggle.setEnabled(True)   # Enable toggle for healthy motors
                motor_toggle.setChecked(False)  # But don't auto-check them
                motor_toggle.setStyleSheet("")  # Reset to default style
            else:
                motor_toggle.setEnabled(False)  # Disable toggle for unhealthy motors
                motor_toggle.setChecked(False)  # Ensure it's not checked
                motor_toggle.setStyleSheet("QToggle { color: red; }")  # Red styling for unhealthy

            # Responsive grid layout
            motor_layout.addWidget(motor_toggle, i // 2, i % 2)  # Two columns

            setattr(self, f"motor_{i + 1}_toggle", motor_toggle)
            self.motor_toggles.append(motor_toggle)



        # Other Control Section
        other_control_group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.OTHER_SETTINGS))
        other_layout = QVBoxLayout(other_control_group)
        other_layout.setSpacing(10)
        other_layout.setContentsMargins(15, 20, 15, 15)
        self.other_control_group = other_control_group

        # Generator toggle
        generator_toggle = QToggle(self.translator.get(TranslationKeys.GlueSettings.GENERATOR))
        generator_toggle.setCheckable(True)
        generator_toggle.setMinimumHeight(35)

        # Initialize generator state using new GeneratorState
        try:
            generator_state = self.glueSprayService.getGeneratorState()
            
            if generator_state.is_healthy:
                generator_toggle.setEnabled(True)
                generator_toggle.setChecked(generator_state.is_on)
                generator_toggle.setStyleSheet("")  # Default style
            else:
                generator_toggle.setEnabled(False)
                generator_toggle.setChecked(False)
                generator_toggle.setStyleSheet("QToggle { color: red; }")
                print(f"Generator initialization: unhealthy - {generator_state.modbus_errors}")
                
        except Exception as e:
            print(f"Error initializing generator state: {e}")
            generator_toggle.setEnabled(False)
            generator_toggle.setChecked(False)
            generator_toggle.setStyleSheet("QToggle { color: red; }")


        other_layout.addWidget(generator_toggle)
        setattr(self, "generator_toggle", generator_toggle)
        self.generator_toggle_btn = generator_toggle

        # Fan toggle
        fan_toggle = QToggle(self.translator.get(TranslationKeys.GlueSettings.FAN))
        fan_toggle.setCheckable(True)
        fan_toggle.setMinimumHeight(35)

        # Initialize fan state using new FanState
        try:
            fan_state = self.glueSprayService.getFanState()
            
            if fan_state.is_healthy:
                fan_toggle.setEnabled(True)
                fan_toggle.setChecked(False)  # Enable but not checked as per requirement
                fan_toggle.setStyleSheet("")  # Default style
            else:
                fan_toggle.setEnabled(False)
                fan_toggle.setChecked(False)
                fan_toggle.setStyleSheet("QToggle { color: red; }")
                print(f"Fan initialization: unhealthy - {fan_state.modbus_errors}")
                
        except Exception as e:
            print(f"Error initializing fan state: {e}")
            fan_toggle.setEnabled(False)
            fan_toggle.setChecked(False)
            fan_toggle.setStyleSheet("QToggle { color: red; }")
        other_layout.addWidget(fan_toggle)
        setattr(self, "fan_toggle", fan_toggle)
        self.fan_toggle_btn = fan_toggle

        # Add refresh button for generator state
        refresh_generator_button = MaterialButton("Refresh Generator")
        refresh_generator_button.setMinimumHeight(35)
        refresh_generator_button.clicked.connect(self.refresh_generator_state)
        other_layout.addWidget(refresh_generator_button)

        # Add refresh button for fan state
        refresh_fan_button = MaterialButton("Refresh Fan")
        refresh_fan_button.setMinimumHeight(35)
        refresh_fan_button.clicked.connect(self.refresh_fan_state)
        other_layout.addWidget(refresh_fan_button)

        # Add refresh button for motor states
        refresh_button = MaterialButton("Refresh Motor States")
        refresh_button.setMinimumHeight(35)
        refresh_button.clicked.connect(self.refresh_motor_states)
        motor_layout.addWidget(refresh_button, 2, 0, 1, 2)  # Span across both columns


        # Add all sections to main layout
        main_layout.addWidget(motor_control_group)

        main_layout.addWidget(other_control_group)

        parent_layout.addWidget(group)

    def add_glue_dispensing_group(self, parent_layout):
        """Add glue dispensing-related settings group"""
        group = QGroupBox(self.translator.get(TranslationKeys.GlueSettings.DISPENSE_GLUE))
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.glue_dispensing_group = group
        self.glue_dispensing_layout = layout

        self.glueDispenseButton = QToggle("")
        self.glueDispenseButton.setMinimumHeight(35)
        layout.addWidget(self.glueDispenseButton)

        parent_layout.addWidget(group)

    def addRobotMotionButtonsGroup(self, parent_layout):
        # Robot motion buttons group
        group = QGroupBox("Robot Motion Controls")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # # spray
        # # Move to Start
        # start_spray = MaterialButton("Spray Start")
        # start_spray.setMinimumHeight(35)
        # start_spray.clicked.connect(lambda: self.start_spray())
        # layout.addWidget(start_spray)

        # Move to Start
        btn_move_start = MaterialButton("Move to Start")
        btn_move_start.setMinimumHeight(35)
        layout.addWidget(btn_move_start)

        # Move to Login
        btn_move_login = MaterialButton("Move to Login")
        btn_move_login.setMinimumHeight(35)
        layout.addWidget(btn_move_login)

        # Move to Calibration
        btn_move_calib = MaterialButton("Move to Calibration")
        btn_move_calib.setMinimumHeight(35)
        layout.addWidget(btn_move_calib)

        # Clean
        btn_clean = MaterialButton("Clean")
        btn_clean.setMinimumHeight(35)
        layout.addWidget(btn_clean)
        parent_layout.addWidget(group)




    def toggleMotor(self, motor_number, state):
        address = self.glueSprayService.glueMapping.get(motor_number)
        result = False
        if state:
            print(f"toggleMotor Motor {motor_number} turned on, forward_ramp_steps: {self.forward_ramp_steps.value()}")
            result = self.glueSprayService.motorOn(motorAddress=address,
                                                   speed=self.motor_speed_input.value(),
                                                   ramp_steps=self.forward_ramp_steps.value(),
                                                   initial_ramp_speed=self.initial_ramp_speed.value(),
                                                   initial_ramp_speed_duration=self.initial_ramp_speed_duration.value())
        else:
            print(f"toggleMotor Motor {motor_number} turned off, reverse ramp steps: {self.reverse_ramp_steps.value()}")
            result = self.glueSprayService.motorOff(motorAddress=address,
                                                    speedReverse = self.speed_reverse_input.value(),
                                                    reverse_time=self.reverse_duration_input.value(),
                                                    ramp_steps=self.reverse_ramp_steps.value())

        if result is False:
            self.showToast(f"Error toggling motor {motor_number}")
            toggle_btn = getattr(self, f"motor_{motor_number}_toggle", None)
            if toggle_btn:
                toggle_btn.blockSignals(True)
                toggle_btn.setChecked(not state)
                toggle_btn.blockSignals(False)

    def toggleGenerator(self, state):
        result = False
        if state:
            print("Generator turned On")

            if self.glueSprayService.generatorCurrentState is True:
                self.showToast("Generator is already On")
                toggle_btn = getattr(self, "generator_toggle", None)
                if toggle_btn:
                    toggle_btn.blockSignals(True)
                    toggle_btn.setChecked(True)
                    toggle_btn.blockSignals(False)
                return

            result = self.glueSprayService.generatorOn()
        else:

            if self.glueSprayService.generatorCurrentState is False:
                self.showToast("Generator is already Off")
                toggle_btn = getattr(self, "generator_toggle", None)
                if toggle_btn:
                    toggle_btn.blockSignals(True)
                    toggle_btn.setChecked(False)
                    toggle_btn.blockSignals(False)
                return

            print("Generator turned Off")
            result = self.glueSprayService.generatorOff()

        if result is False:
            self.showToast("Error toggling generator state")
            toggle_btn = getattr(self, "generator_toggle", None)
            if toggle_btn:
                toggle_btn.blockSignals(True)
                toggle_btn.setChecked(not state)
                toggle_btn.blockSignals(False)

    def toggleFan(self, state):
        result = False
        if state:
            print("Fan turned On")
            result = self.glueSprayService.fanOn(self.fan_speed_input.value())
        else:
            print("Fan turned Off")
            result = self.glueSprayService.fanOff()

        if result is False:
            self.showToast("Error toggling fan state")
            toggle_btn = getattr(self, "fan_toggle", None)
            if toggle_btn:
                toggle_btn.blockSignals(True)
                toggle_btn.setChecked(not state)
                toggle_btn.blockSignals(False)

    def toggleGlueDispense(self, state):
        glue_type = getattr(self, f"{GlueType.TypeA.value}_combo").currentText()
        glueNumber = -1
        print(f"Glue Type: {glue_type}")
        if glue_type == GlueType.TypeA.value:
            glueType_addresses = self.glueSprayService.glueMapping.get(1)
            glueNumber = 1
        elif glue_type == GlueType.TypeB.value:
            glueType_addresses = self.glueSprayService.glueMapping.get(2)
            glueNumber = 2
        elif glue_type == GlueType.TypeC.value:
            glueType_addresses = self.glueSprayService.glueMapping.get(3)
            glueNumber = 3
        elif glue_type == GlueType.TypeD.value:
            glueType_addresses = self.glueSprayService.glueMapping.get(4)
            glueNumber = 4
        else:
            raise ValueError(f"Unknown glue type: {glue_type}")

        result = False
        if state:
            print(f"Glue {glueNumber} dispensing started")
            result = self.glueSprayService.startGlueDispensing(glueType_addresses=glueType_addresses,
                                                               speed=self.motor_speed_input.value(),
                                                               reverse_time=self.reverse_duration_input.value(),
                                                               speedReverse=self.speed_reverse_input.value(),
                                                               gen_pump_delay=self.time_between_generator_and_glue_input.value(),
                                                               fanSpeed=self.fan_speed_input.value())
        else:
            self.glueDispenseButton.setText(f"Dispense Glue {glueNumber} Off")
            result = self.glueSprayService.stopGlueDispensing(glueType_addresses=glueType_addresses,
                                                              speed_reverse=self.speed_reverse_input.value(),
                                                              pump_reverse_time=self.reverse_duration_input.value(),
                                                              pump_gen_delay=self.time_between_generator_and_glue_input.value(),
                                                              ramp_steps=self.reverse_ramp_steps.value())

        if result is False:
            self.showToast(f"Error toggling glue dispense for glue {glueNumber}")
            toggle_btn = getattr(self, "glueDispenseButton", None)
            if toggle_btn:
                toggle_btn.blockSignals(True)
                toggle_btn.setChecked(not state)
                toggle_btn.blockSignals(False)
            return

    def connectDeviceControlCallbacks(self):
        # Motor toggles
        self.motor_1_toggle.toggled.connect(lambda state: self.toggleMotor(1, state))
        self.motor_2_toggle.toggled.connect(lambda state: self.toggleMotor(2, state))
        self.motor_3_toggle.toggled.connect(lambda state: self.toggleMotor(3, state))
        self.motor_4_toggle.toggled.connect(lambda state: self.toggleMotor(4, state))

        # Generator toggle
        self.generator_toggle.toggled.connect(lambda state: self.toggleGenerator(state))
        self.fan_toggle_btn.toggled.connect(lambda state: self.toggleFan(state))
        self.glueDispenseButton.toggled.connect(lambda state: self.toggleGlueDispense(state))

    def connectValueChangeCallbacks(self, callback):
        """Connect value change signals to callback methods with key, value, and className."""
        self.spray_width_input.valueChanged.connect(
            lambda value: callback(GlueSettingKey.SPRAY_WIDTH.value, value, "GlueSettingsTabLayout"))
        self.spraying_height_input.valueChanged.connect(
            lambda value: callback(GlueSettingKey.SPRAYING_HEIGHT.value, value, "GlueSettingsTabLayout"))
        self.fan_speed_input.valueChanged.connect(
            lambda value: callback(GlueSettingKey.FAN_SPEED.value, value, "GlueSettingsTabLayout"))
        self.time_between_generator_and_glue_input.valueChanged.connect(
            lambda value: callback(GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value, value,
                                   "GlueSettingsTabLayout"))
        self.motor_speed_input.valueChanged.connect(
            lambda value: callback(GlueSettingKey.MOTOR_SPEED.value, value, "GlueSettingsTabLayout"))
        self.reverse_duration_input.valueChanged.connect(
            lambda value: callback(GlueSettingKey.REVERSE_DURATION.value, value, "GlueSettingsTabLayout"))
        self.speed_reverse_input.valueChanged.connect(
            lambda value: callback(GlueSettingKey.SPEED_REVERSE.value, value, "GlueSettingsTabLayout"))
        self.rz_angle_input.valueChanged.connect(
            lambda value: callback("RZ Angle", value, "GlueSettingsTabLayout"))
        self.dropdown.currentTextChanged.connect(
            lambda value: callback(GlueSettingKey.GLUE_TYPE.value, value, "GlueSettingsTabLayout"))
        self.generator_timeout_input.valueChanged.connect(
            lambda value: self.onTimeoutChanged(value, callback))
        self.time_before_motion.valueChanged.connect(
            lambda value: callback(GlueSettingKey.TIME_BEFORE_MOTION.value, value, "GlueSettingsTabLayout"))
        self.reach_pos_thresh.valueChanged.connect(
            lambda value: callback(GlueSettingKey.REACH_START_THRESHOLD.value, value, "GlueSettingsTabLayout"))
        
        # Connect new motor ramp settings
        self.forward_ramp_steps.valueChanged.connect(
            lambda value: callback(GlueSettingKey.FORWARD_RAMP_STEPS.value, value, "GlueSettingsTabLayout"))
        self.reverse_ramp_steps.valueChanged.connect(
            lambda value: callback(GlueSettingKey.REVERSE_RAMP_STEPS.value, value, "GlueSettingsTabLayout"))
        self.initial_ramp_speed.valueChanged.connect(
            lambda value: callback(GlueSettingKey.INITIAL_RAMP_SPEED.value, value, "GlueSettingsTabLayout"))
        self.initial_ramp_speed_duration.valueChanged.connect(
            lambda value: callback(GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value, value, "GlueSettingsTabLayout"))
        
        # Connect Spray On toggle
        self.spray_on_toggle.toggled.connect(
            lambda value: callback(GlueSettingKey.SPRAY_ON.value, value, "GlueSettingsTabLayout"))


    def connectRobotMotionCallbacks(self, move_start_cb=None, move_login_cb=None, move_calib_cb=None, clean_cb=None,
                                    pickup_cb=None, dropoff_cb=None):
        """
        Connects robot motion button callbacks.
        Each argument is a callable or None.
        pickup_cb and dropoff_cb should be single functions taking gripper_id as an argument.
        """
        # Find the group and layout
        if not hasattr(self, 'robot_motion_buttons_group'):
            for i in range(self.count()):
                widget = self.itemAt(i).widget()
                if isinstance(widget, QWidget):
                    for child in widget.findChildren(QGroupBox):
                        if child.title() == "Robot Motion Controls":
                            self.robot_motion_buttons_group = child
                            break

        group = getattr(self, 'robot_motion_buttons_group', None)
        if not group:
            return

        layout = group.layout()
        if not layout:
            return

        btn_idx = 0

        # Move to Start
        if move_start_cb:
            btn = layout.itemAt(btn_idx).widget()
            btn.clicked.connect(move_start_cb)
        btn_idx += 1

        # Move to Login
        if move_login_cb:
            btn = layout.itemAt(btn_idx).widget()
            btn.clicked.connect(move_login_cb)
        btn_idx += 1

        # Move to Calibration
        if move_calib_cb:
            btn = layout.itemAt(btn_idx).widget()
            btn.clicked.connect(move_calib_cb)
        btn_idx += 1

        # Clean
        if clean_cb:
            btn = layout.itemAt(btn_idx).widget()
            btn.clicked.connect(clean_cb)
        btn_idx += 1

        # # Pickup Tool 0, 1, 2
        # if pickup_cb:
        #     for i in range(3):
        #         btn = layout.itemAt(btn_idx).widget()
        #         btn.clicked.connect(lambda _, idx=i: pickup_cb(idx))
        #         btn_idx += 1
        # else:
        #     btn_idx += 3
        #
        # # Drop Off Tool 0, 1, 2 — ✅ Fixed Here
        # if dropoff_cb:
        #     for i in range(3):
        #         btn = layout.itemAt(btn_idx).widget()
        #         btn.clicked.connect(lambda _, idx=i: dropoff_cb(idx))
        #         btn_idx += 1
        # else:
        #     btn_idx += 3

    def onTimeoutChanged(self, value,callback):
        """Handle timeout value changes."""
        value = value / 60  # Convert seconds to minutes
        self.glueSprayService.generatorTurnOffTimeout = value
        callback(GlueSettingKey.GENERATOR_TIMEOUT.value, value, "GlueSettingsTabLayout")

    def updateValues(self, glueSettings):
        """Updates input field values from glue settings object."""
        self.spray_width_input.setValue(glueSettings.get_spray_width())
        self.spraying_height_input.setValue(glueSettings.get_spraying_height())
        self.fan_speed_input.setValue(glueSettings.get_fan_speed())
        self.time_between_generator_and_glue_input.setValue(glueSettings.get_time_between_generator_and_glue())
        self.motor_speed_input.setValue(glueSettings.get_motor_speed())
        self.reverse_duration_input.setValue(glueSettings.get_steps_reverse())
        self.speed_reverse_input.setValue(glueSettings.get_speed_reverse())
        self.rz_angle_input.setValue(glueSettings.get_rz_angle())
        self.generator_timeout_input.setValue(glueSettings.get_generator_timeout()*60) # Convert minutes to seconds
        self.time_before_motion.setValue(glueSettings.get_time_before_motion())
        self.reach_pos_thresh.setValue(glueSettings.get_reach_position_threshold())
        self.forward_ramp_steps.setValue(glueSettings.get_forward_ramp_steps())
        self.reverse_ramp_steps.setValue(glueSettings.get_reverse_ramp_steps())
        self.initial_ramp_speed.setValue(glueSettings.get_initial_ramp_speed())
        self.initial_ramp_speed_duration.setValue(glueSettings.get_initial_ramp_speed_duration())
        self.spray_on_toggle.setChecked(glueSettings.get_spray_on())
        self.glueSprayService.settings=glueSettings

    def getInputFields(self):
        """Returns the list of input fields."""
        return self.input_fields

    def getSliders(self):
        """Deprecated: Returns input fields for backward compatibility."""
        return self.getInputFields()

    def getValues(self):
        """Returns a dictionary of current values from all input fields."""
        return {
            GlueSettingKey.SPRAY_WIDTH.value: self.spray_width_input.value(),
            GlueSettingKey.SPRAYING_HEIGHT.value: self.spraying_height_input.value(),
            GlueSettingKey.FAN_SPEED.value: self.fan_speed_input.value(),
            GlueSettingKey.TIME_BETWEEN_GENERATOR_AND_GLUE.value: self.time_between_generator_and_glue_input.value(),
            GlueSettingKey.MOTOR_SPEED.value: self.motor_speed_input.value(),
            GlueSettingKey.REVERSE_DURATION.value: self.reverse_duration_input.value(),
            GlueSettingKey.SPEED_REVERSE.value: self.speed_reverse_input.value(),
            GlueSettingKey.RZ_ANGLE.value: self.rz_angle_input.value(),
            GlueSettingKey.GLUE_TYPE.value: getattr(self, f"{GlueType.TypeA.value}_combo").currentText(),
            GlueSettingKey.GENERATOR_TIMEOUT.value: self.generator_timeout_input.value() / 60 ,  # Convert seconds to minutes
            GlueSettingKey.TIME_BEFORE_MOTION.value: self.time_before_motion.value(),
            GlueSettingKey.INITIAL_RAMP_SPEED.value: self.initial_ramp_speed.value(),
            GlueSettingKey.INITIAL_RAMP_SPEED_DURATION.value: self.initial_ramp_speed_duration.value(),
            GlueSettingKey.FORWARD_RAMP_STEPS.value: self.forward_ramp_steps.value(),
            GlueSettingKey.REVERSE_RAMP_STEPS.value: self.reverse_ramp_steps.value(),
            GlueSettingKey.REACH_START_THRESHOLD.value: self.reach_pos_thresh.value(),
            GlueSettingKey.SPRAY_ON.value: self.spray_on_toggle.isChecked(),

        }


    def refresh_motor_states(self):
        """Refresh motor states and update toggle buttons."""
        print("Refreshing motor states...")
        
        # Initialize motors_healthy dictionary
        motors_healthy = {}
        
        # Get all motor states at once (efficient - only 3 seconds instead of 12)
        try:
            all_motors_state = self.glueSprayService.motorController.getAllMotorStates()
            
            if all_motors_state.success:
                # Extract motor states from the AllMotorsState object
                for motor_addr, motor_state in all_motors_state.motors.items():
                    motors_healthy[motor_addr] = motor_state.is_healthy
                    # Print debug info about motor errors
                    if not motor_state.is_healthy:
                        print(f"Motor {motor_addr} unhealthy - Errors: {motor_state.get_filtered_errors()}")
                        self.showToast(f"Motor {motor_addr} has errors: {motor_state.get_filtered_errors()}")
                    else:
                        print(f"Motor {motor_addr} is healthy")
                        
                # Show summary toast
                healthy_count = sum(motors_healthy.values())
                self.showToast(f"Motor states refreshed: {healthy_count}/4 healthy")
                
            else:
                # If failed to get states, assume all motors are unhealthy
                print("Failed to get motor states - assuming all unhealthy")
                self.showToast("Failed to get motor states")
                for i in range(4):
                    motor_addr = self.glueSprayService.glueMapping.get(i + 1)
                    motors_healthy[motor_addr] = False
                    
        except Exception as e:
            print(f"Error getting all motor states: {e}")
            self.showToast(f"Error refreshing motor states: {str(e)}")
            # Fallback: assume all motors are unhealthy
            for i in range(4):
                motor_addr = self.glueSprayService.glueMapping.get(i + 1)
                motors_healthy[motor_addr] = False
        
        # Update toggle buttons
        for i in range(4):
            motor_addr = self.glueSprayService.glueMapping.get(i + 1)
            is_healthy = motors_healthy.get(motor_addr, False)
            
            motor_toggle = getattr(self, f"motor_{i + 1}_toggle", None)
            if motor_toggle:
                # Block signals to prevent triggering motor control
                motor_toggle.blockSignals(True)
                
                # Set toggle state based on motor health
                if is_healthy:
                    motor_toggle.setEnabled(True)   # Enable toggle for healthy motors
                    motor_toggle.setChecked(False)  # But don't auto-check them
                    motor_toggle.setStyleSheet("")  # Reset to default style
                else:
                    motor_toggle.setEnabled(False)  # Disable toggle for unhealthy motors
                    motor_toggle.setChecked(False)  # Ensure it's not checked
                    motor_toggle.setStyleSheet("QToggle { color: red; }")  # Red styling for unhealthy
                
                motor_toggle.blockSignals(False)

    def refresh_generator_state(self):
        """Refresh generator state and update toggle button using new GeneratorState."""
        print("Refreshing generator state...")
        
        try:
            # Get comprehensive generator state using new GeneratorState
            generator_state = self.glueSprayService.getGeneratorState()
            
            generator_toggle = getattr(self, "generator_toggle", None)
            if generator_toggle:
                # Block signals to prevent triggering generator control
                generator_toggle.blockSignals(True)
                
                if not generator_state.is_healthy:
                    # Generator has errors or is unhealthy
                    generator_toggle.setEnabled(False)
                    generator_toggle.setChecked(False)
                    generator_toggle.setStyleSheet("QToggle { color: red; }")
                    
                    # Show specific error information
                    error_info = []
                    if generator_state.modbus_errors:
                        error_info.extend(generator_state.modbus_errors)
                    if generator_state.error_code and generator_state.error_code != 0:
                        error_info.append(f"Error code: {generator_state.error_code}")
                    
                    error_text = ", ".join(error_info) if error_info else "Unknown errors"
                    self.showToast(f"Generator unhealthy - {error_text}")
                    print(f"Generator is unhealthy: {error_info}")
                    
                else:
                    # Generator is healthy
                    generator_toggle.setEnabled(True)
                    generator_toggle.setChecked(generator_state.is_on)
                    generator_toggle.setStyleSheet("")  # Reset to default style
                    
                    state_text = "ON" if generator_state.is_on else "OFF"
                    health_text = "Healthy" if generator_state.is_healthy else "Unhealthy"
                    time_text = f", Runtime: {generator_state.elapsed_time:.1f}s" if generator_state.elapsed_time else ""
                    
                    self.showToast(f"Generator: {state_text}, {health_text}{time_text}")
                    print(f"Generator state: {generator_state}")
                
                generator_toggle.blockSignals(False)
                
        except Exception as e:
            print(f"Error refreshing generator state: {e}")
            self.showToast(f"Error refreshing generator state: {str(e)}")
            
            # Mark generator as unknown/disabled on error
            generator_toggle = getattr(self, "generator_toggle", None)
            if generator_toggle:
                generator_toggle.blockSignals(True)
                generator_toggle.setEnabled(False)
                generator_toggle.setChecked(False)
                generator_toggle.setStyleSheet("QToggle { color: red; }")
                generator_toggle.blockSignals(False)

    def refresh_fan_state(self):
        """Refresh fan state and update toggle button using new FanState."""
        print("Refreshing fan state...")
        
        try:
            # Get comprehensive fan state using new FanState
            fan_state = self.glueSprayService.getFanState()
            
            fan_toggle = getattr(self, "fan_toggle", None)
            if fan_toggle:
                # Block signals to prevent triggering fan control
                fan_toggle.blockSignals(True)
                
                if not fan_state.is_healthy:
                    # Fan is unhealthy - disable toggle
                    fan_toggle.setEnabled(False)
                    fan_toggle.setChecked(False)
                    fan_toggle.setStyleSheet("QToggle { color: red; }")
                    
                    # Show specific error information
                    error_msg = "Fan unhealthy - disabled"
                    if fan_state.modbus_errors:
                        error_msg += f": {', '.join(fan_state.modbus_errors[:2])}"  # Show first 2 errors
                    
                    self.showToast(error_msg)
                    print(f"Fan unhealthy: {fan_state}")
                else:
                    # Fan is healthy - enable but don't auto-check
                    fan_toggle.setEnabled(True)
                    fan_toggle.setChecked(False)  # Enable but not checked as per requirement
                    fan_toggle.setStyleSheet("")  # Reset to default style
                    
                    # Show detailed state information
                    speed_info = ""
                    if fan_state.speed is not None and fan_state.speed_percentage is not None:
                        speed_info = f" (Speed: {fan_state.speed}, {fan_state.speed_percentage:.1f}%)"
                    
                    state_text = "ON" if fan_state.is_on else "OFF"
                    self.showToast(f"Fan healthy - {state_text}{speed_info}")
                    print(f"Fan state: {fan_state}")
                
                fan_toggle.blockSignals(False)
                
        except Exception as e:
            print(f"Error refreshing fan state: {e}")
            self.showToast(f"Error refreshing fan state: {str(e)}")
            
            # Mark fan as unknown/disabled on error
            fan_toggle = getattr(self, "fan_toggle", None)
            if fan_toggle:
                fan_toggle.blockSignals(True)
                fan_toggle.setEnabled(False)
                fan_toggle.setChecked(False)
                fan_toggle.setStyleSheet("QToggle { color: red; }")
                fan_toggle.blockSignals(False)

    def showToast(self, message):
        """Show toast notification"""
        if self.parent_widget:
            toast = ToastWidget(self.parent_widget, message, 5)
            toast.show()


# Example usage:
# Run this file to launch the settings tab layout in a PyQt6 application window.

if __name__ == "__main__":
    from src.backend.system.settings.SettingsService import SettingsService
    from src.backend.system.robot.FairinoRobot import FairinoRobot
    from src.backend.system.robot.robotService.RobotService import RobotService
    settingsService = SettingsService()
    glueSettings = settingsService.glue_settings

    robot_config = settingsService.robot_config
    robot = FairinoRobot(robot_config.robot_ip)
    robotService = RobotService(robot,settingsService)

    app = QApplication(sys.argv)
    main_widget = QWidget()

    layout = GlueSettingsTabLayout(main_widget,
                                   glueSettings=glueSettings)


    def settingsChangeCallback(key, value, className):
        print(f"Settings changed in {className}: {key} = {value}")
        settingsService.updateGlueSettings({key: value})
        setattr(layout.glueSprayService.settings, key, value)

    layout.updateValues(glueSettings)
    layout.connectValueChangeCallbacks(settingsChangeCallback)

    layout.connectRobotMotionCallbacks(
        move_start_cb=robotService.moveToStartPosition,
        move_login_cb=robotService.moveToLoginPosition,
        move_calib_cb=robotService.moveToCalibrationPosition,
        # clean_cb=robotService.cleanNozzle,# this is movet to glue spray application
        clean_cb= None,
        pickup_cb=lambda gripper_id: robotService.pickupGripper(gripper_id),
        dropoff_cb=lambda gripper_id: robotService.dropOffGripper(gripper_id),
    )

    main_widget.setLayout(layout)
    main_widget.resize(1200, 800)
    main_widget.show()

    sys.exit(app.exec())



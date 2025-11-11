import sys
from enum import Enum

from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QApplication, QHBoxLayout,
                             QSizePolicy, QComboBox,
                             QScrollArea, QGroupBox, QGridLayout, QPushButton)

from API.MessageBroker import MessageBroker
from API.localization.enums.Message import Message
from API.shared.settings.conreateSettings.enums.GlueSettingKey import GlueSettingKey
from .BaseSettingsTabLayout import BaseSettingsTabLayout
from GlueDispensingApplication.tools.GlueSprayService import GlueSprayService
from deprecated.pl_gui.ToastWidget import ToastWidget
from deprecated.pl_gui.customWidgets.SwitchButton import QToggle
from deprecated.pl_gui.specific.enums.GlueType import GlueType
from PyQt6.QtWidgets import QScroller
from PyQt6.QtCore import Qt

class GlueSettingsTabLayout(BaseSettingsTabLayout, QVBoxLayout):
    def __init__(self, parent_widget):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)

        self.dropdown = None
        self.parent_widget = parent_widget
        self.glueSprayService = GlueSprayService()
        broker = MessageBroker()
        broker.subscribe("Language", self.translate)
        self.create_main_content()
        # Connect to parent widget resize events if possible
        if self.parent_widget:
            self.parent_widget.resizeEvent = self.on_parent_resize

    def translate(self, message):
            """Update UI text based on current language"""
            # Update styling to ensure responsive fonts are applied
            self.setup_styling()

            # Spray settings group
            if hasattr(self, 'spray_group'):
                self.spray_group.setTitle(self.langLoader.get_message(Message.SPRAY_SETTINGS))
                if hasattr(self, 'spray_layout'):
                    if self.spray_layout.itemAtPosition(0, 0):
                        self.spray_layout.itemAtPosition(0, 0).widget().setText(
                            self.langLoader.get_message(Message.SPRAY_WIDTH))
                    if self.spray_layout.itemAtPosition(1, 0):
                        self.spray_layout.itemAtPosition(1, 0).widget().setText(
                            self.langLoader.get_message(Message.SPRAYING_HEIGHT))
                    if self.spray_layout.itemAtPosition(2, 0):
                        self.spray_layout.itemAtPosition(2, 0).widget().setText(
                            self.langLoader.get_message(Message.FAN_SPEED))
                    if self.spray_layout.itemAtPosition(3, 0):
                        self.spray_layout.itemAtPosition(3, 0).widget().setText(
                            self.langLoader.get_message(Message.GENERATOR_TO_GLUE_DELAY))

            # Motor settings group
            if hasattr(self, 'motor_group'):
                self.motor_group.setTitle(self.langLoader.get_message(Message.MOTOR_SETTINGS))
                if hasattr(self, 'motor_layout'):
                    if self.motor_layout.itemAtPosition(0, 0):
                        self.motor_layout.itemAtPosition(0, 0).widget().setText(
                            self.langLoader.get_message(Message.MOTOR_SPEED))
                    if self.motor_layout.itemAtPosition(1, 0):
                        self.motor_layout.itemAtPosition(1, 0).widget().setText(
                            self.langLoader.get_message(Message.REVERSE_DURATION))
                    if self.motor_layout.itemAtPosition(2, 0):
                        self.motor_layout.itemAtPosition(2, 0).widget().setText(
                            self.langLoader.get_message(Message.REVERSE_SPEED))

            # General settings group
            if hasattr(self, 'general_group'):
                self.general_group.setTitle(self.langLoader.get_message(Message.GENERAL_SETTINGS))
                if hasattr(self, 'general_layout'):
                    if self.general_layout.itemAtPosition(0, 0):
                        self.general_layout.itemAtPosition(0, 0).widget().setText(
                            self.langLoader.get_message(Message.RZ_ANGLE))
                    if self.general_layout.itemAtPosition(2, 0):
                        self.general_layout.itemAtPosition(2, 0).widget().setText(
                            self.langLoader.get_message(Message.GLUE_TYPE))

            # Device control groups
            if hasattr(self, 'motor_control_group'):
                self.motor_control_group.setTitle(self.langLoader.get_message(Message.MOTOR_CONTROL))
            if hasattr(self, 'other_control_group'):
                self.other_control_group.setTitle(self.langLoader.get_message(Message.OTHER_SETTINGS))

            # Update toggle button texts
            if hasattr(self, 'generator_toggle_btn'):
                self.generator_toggle_btn.setText(self.langLoader.get_message(Message.GENERATOR))
            if hasattr(self, 'fan_toggle_btn'):
                self.fan_toggle_btn.setText(self.langLoader.get_message(Message.FAN))

            # Update motor toggles
            if hasattr(self, 'motor_toggles'):
                for i, motor_toggle in enumerate(self.motor_toggles, start=1):
                    motor_toggle.setText(f"{self.langLoader.get_message(Message.MOTOR)} {i}")

            # Glue dispensing group
            if hasattr(self, 'glue_dispensing_group'):
                self.glue_dispensing_group.setTitle(self.langLoader.get_message(Message.DISPENSE_GLUE))
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
        group = QGroupBox(self.langLoader.get_message(Message.SPRAY_SETTINGS))
        layout = QGridLayout(group)


        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.spray_layout = layout

        # Spray Width
        row = 0
        label = QLabel(self.langLoader.get_message(Message.SPRAY_WIDTH))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.spray_width_input = self.create_double_spinbox(0.0, 100.0, 5.0, " mm")
        layout.addWidget(self.spray_width_input, row, 1)

        # Spraying Height
        row += 1
        label = QLabel(self.langLoader.get_message(Message.SPRAYING_HEIGHT))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.spraying_height_input = self.create_double_spinbox(0.0, 500.0, 120.0, " mm")
        layout.addWidget(self.spraying_height_input, row, 1)

        # Fan Speed
        row += 1
        label = QLabel(self.langLoader.get_message(Message.FAN_SPEED))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.fan_speed_input = self.create_double_spinbox(0.0, 100.0, 100.0, " %")
        layout.addWidget(self.fan_speed_input, row, 1)

        # Time Between Generator and Glue
        row += 1
        label = QLabel(self.langLoader.get_message(Message.GENERATOR_TO_GLUE_DELAY))
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
        """Create motor-related settings group with responsive layout"""
        group = QGroupBox(self.langLoader.get_message(Message.MOTOR_SETTINGS))
        layout = QGridLayout(group)


        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.motor_layout = layout

        # Motor Speed
        row = 0
        label = QLabel(self.langLoader.get_message(Message.MOTOR_SPEED))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.motor_speed_input = self.create_double_spinbox(0.0, 100000.0, 3000.0, " Hz")
        layout.addWidget(self.motor_speed_input, row, 1)

        # Steps Reverse
        row += 1
        label = QLabel(self.langLoader.get_message(Message.REVERSE_DURATION))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.reverse_duration_input = self.create_double_spinbox(0.0, 100000.0, 1500.0, " s")
        layout.addWidget(self.reverse_duration_input, row, 1)

        # Speed Reverse
        row += 1
        label = QLabel(self.langLoader.get_message(Message.REVERSE_SPEED))
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.speed_reverse_input = self.create_double_spinbox(0.0, 100000.0, 10000.0, " Hz")
        layout.addWidget(self.speed_reverse_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_general_settings_group(self):
        """Create general settings group with responsive layout"""
        group = QGroupBox(self.langLoader.get_message(Message.GENERAL_SETTINGS))
        layout = QGridLayout(group)


        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.general_layout = layout

        # RZ Angle
        row = 0
        label = QLabel(self.langLoader.get_message(Message.RZ_ANGLE))
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

        # Glue Type
        row += 1
        label = QLabel(self.langLoader.get_message(Message.GLUE_TYPE))
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
        group = QGroupBox(self.langLoader.get_message(Message.DEVICE_CONTROL))

        # Choose layout based on screen size

        main_layout = QHBoxLayout(group)
        main_layout.setSpacing(20)

        main_layout.setContentsMargins(20, 25, 20, 20)
        self.device_control_layout = main_layout

        # Motor Control Section
        motor_control_group = QGroupBox(self.langLoader.get_message(Message.MOTOR_CONTROL))
        motor_layout = QGridLayout(motor_control_group)
        motor_layout.setSpacing(10)
        motor_layout.setContentsMargins(15, 20, 15, 15)
        self.motor_control_group = motor_control_group

        self.motor_toggles = []
        for i in range(4):
            motor_toggle = QToggle(f"M{i + 1}")
            motor_toggle.setCheckable(True)
            motor_toggle.setMinimumHeight(35)

            result, currentState = self.glueSprayService.motorState(self.glueSprayService.glueMapping.get(i + 1))
            currentState = 0
            if result is False:
                motor_toggle.setChecked(False)

            if currentState == 0:
                currentState = False
            elif currentState == 1:
                currentState = True
            else:
                currentState = False
                motor_toggle.setEnabled(False)

            motor_toggle.setChecked(currentState)

            # Responsive grid layout

            motor_layout.addWidget(motor_toggle, i // 2, i % 2)  # Two columns

            setattr(self, f"motor_{i + 1}_toggle", motor_toggle)
            self.motor_toggles.append(motor_toggle)



        # Other Control Section
        other_control_group = QGroupBox(self.langLoader.get_message(Message.OTHER_SETTINGS))
        other_layout = QVBoxLayout(other_control_group)
        other_layout.setSpacing(10)
        other_layout.setContentsMargins(15, 20, 15, 15)
        self.other_control_group = other_control_group

        # Generator toggle
        generator_toggle = QToggle(self.langLoader.get_message(Message.GENERATOR))
        generator_toggle.setCheckable(True)
        generator_toggle.setMinimumHeight(35)

        result, currentState = self.glueSprayService.generatorState()

        if result is False:
            generator_toggle.setChecked(False)

        if currentState == 0:
            currentState = False
        elif currentState == 1:
            currentState = True
        else:
            currentState = False
            generator_toggle.setEnabled(False)

        generator_toggle.setChecked(currentState)
        other_layout.addWidget(generator_toggle)
        setattr(self, "generator_toggle", generator_toggle)
        self.generator_toggle_btn = generator_toggle

        # Fan toggle
        fan_toggle = QToggle(self.langLoader.get_message(Message.FAN))
        fan_toggle.setCheckable(True)
        fan_toggle.setMinimumHeight(35)

        result, currentState = self.glueSprayService.fanState()
        currentState = 0
        if result is False:
            fan_toggle.setChecked(False)
            currentState = False

        if currentState == 0:
            currentState = False
        elif currentState == 1:
            currentState = True

        fan_toggle.setChecked(currentState)
        other_layout.addWidget(fan_toggle)
        setattr(self, "fan_toggle", fan_toggle)
        self.fan_toggle_btn = fan_toggle

        # Add all sections to main layout
        main_layout.addWidget(motor_control_group)

        main_layout.addWidget(other_control_group)

        parent_layout.addWidget(group)

    def add_glue_dispensing_group(self, parent_layout):
        """Add glue dispensing-related settings group"""
        group = QGroupBox(self.langLoader.get_message(Message.DISPENSE_GLUE))
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
        # start_spray = QPushButton("Spray Start")
        # start_spray.setMinimumHeight(35)
        # start_spray.clicked.connect(lambda: self.start_spray())
        # layout.addWidget(start_spray)

        # Move to Start
        btn_move_start = QPushButton("Move to Start")
        btn_move_start.setMinimumHeight(35)
        layout.addWidget(btn_move_start)

        # Move to Login
        btn_move_login = QPushButton("Move to Login")
        btn_move_login.setMinimumHeight(35)
        layout.addWidget(btn_move_login)

        # Move to Calibration
        btn_move_calib = QPushButton("Move to Calibration")
        btn_move_calib.setMinimumHeight(35)
        layout.addWidget(btn_move_calib)

        # Clean
        btn_clean = QPushButton("Clean")
        btn_clean.setMinimumHeight(35)
        layout.addWidget(btn_clean)

        # Pickup Tool 0, 1, 2
        for i in range(3):
            btn_pickup = QPushButton(f"Pickup Tool {i}")
            btn_pickup.setMinimumHeight(35)
            layout.addWidget(btn_pickup)

        # Drop Off Tool 0, 1, 2
        for i in range(3):
            btn_dropoff = QPushButton(f"Drop Off Tool {i}")
            btn_dropoff.setMinimumHeight(35)
            layout.addWidget(btn_dropoff)

        parent_layout.addWidget(group)




    def toggleMotor(self, motor_number, state):
        address = self.glueSprayService.glueMapping.get(motor_number)
        result = False
        if state:
            print(f"Motor {motor_number} turned on")
            result = self.glueSprayService.motorOn(address, self.motor_speed_input.value())
        else:
            print(f"Motor {motor_number} turned off")
            result = self.glueSprayService.motorOff(address,
                                                    speedReverse = self.speed_reverse_input.value(),
                                                    delay=self.reverse_duration_input.value())

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

        result = False
        if state:
            print(f"Glue {glueNumber} dispensing started")
            result = self.glueSprayService.startGlueDispensing(glueType_addresses,
                                                               self.motor_speed_input.value(),
                                                               self.reverse_duration_input.value(),
                                                               self.speed_reverse_input.value(),
                                                               delay=self.time_between_generator_and_glue_input.value(),
                                                               fanSpeed=self.fan_speed_input.value())
        else:
            self.glueDispenseButton.setText(f"Dispense Glue {glueNumber} Off")
            result = self.glueSprayService.stopGlueDispensing(glueType_addresses,delay=self.time_between_generator_and_glue_input.value())

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

        # Pickup Tool 0, 1, 2
        if pickup_cb:
            for i in range(3):
                btn = layout.itemAt(btn_idx).widget()
                btn.clicked.connect(lambda _, idx=i: pickup_cb(idx))
                btn_idx += 1
        else:
            btn_idx += 3

        # Drop Off Tool 0, 1, 2 — ✅ Fixed Here
        if dropoff_cb:
            for i in range(3):
                btn = layout.itemAt(btn_idx).widget()
                btn.clicked.connect(lambda _, idx=i: dropoff_cb(idx))
                btn_idx += 1
        else:
            btn_idx += 3

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
            GlueSettingKey.GENERATOR_TIMEOUT: self.generator_timeout_input.value() / 60 ,  # Convert seconds to minutes
            GlueSettingKey.TIME_BEFORE_MOTION: self.time_before_motion.value()
        }


    def showToast(self, message):
        """Show toast notification"""
        if self.parent_widget:
            toast = ToastWidget(self.parent_widget, message, 5)
            toast.show()


# Example usage:
# Run this file to launch the settings tab layout in a PyQt6 application window.

if __name__ == "__main__":
    from GlueDispensingApplication.settings.SettingsService import SettingsService
    from GlueDispensingApplication.robot.RobotConfig import *
    from GlueDispensingApplication.robot.RobotWrapper import RobotWrapper
    from GlueDispensingApplication.robot.RobotService import RobotService
    settingsService = SettingsService()
    glueSettings = settingsService.glue_settings

    robot = RobotWrapper(ROBOT_IP)
    robotService = RobotService(robot,settingsService)

    app = QApplication(sys.argv)
    main_widget = QWidget()

    layout = GlueSettingsTabLayout(main_widget)


    def settingsChangeCallback(key, value, className):
        print(f"Settings changed in {className}: {key} = {value}")
        settingsService.updateGlueSettings({key: value})

    layout.updateValues(glueSettings)
    layout.connectValueChangeCallbacks(settingsChangeCallback)

    layout.connectRobotMotionCallbacks(
        move_start_cb=robotService.moveToStartPosition,
        move_login_cb=robotService.moveToLoginPosition,
        move_calib_cb=robotService.moveToCalibrationPosition,
        clean_cb=robotService.cleanNozzle,
        pickup_cb=lambda gripper_id: robotService.pickupGripper(gripper_id),
        dropoff_cb=lambda gripper_id: robotService.dropOffGripper(gripper_id),
    )

    main_widget.setLayout(layout)
    main_widget.resize(1200, 800)
    main_widget.show()

    sys.exit(app.exec())



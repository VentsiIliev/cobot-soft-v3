#!/usr/bin/env python3
"""
Robot Configuration GUI - Modern interface for managing robot settings
"""

import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QScrollArea, QGroupBox, QGridLayout, QTabWidget, QFrame,
    QGraphicsDropShadowEffect, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon


class ModernCard(QFrame):
    """Modern card widget with shadow and rounded corners"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            ModernCard {
                background-color: white;
                border-radius: 16px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)

        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)


class ModernButton(QPushButton):
    """Modern styled button with hover effects"""

    def __init__(self, text="", button_type="primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(48)
        self.update_style()

    def update_style(self):
        if self.button_type == "primary":
            self.setStyleSheet("""
                ModernButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #7C4DFF, stop:1 #651FFF);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-weight: 600;
                    padding: 12px 24px;
                }
                ModernButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #8E5AFF, stop:1 #7C3AFF);
                }
                ModernButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #6A1B9A, stop:1 #4A148C);
                }
            """)
        elif self.button_type == "secondary":
            self.setStyleSheet("""
                ModernButton {
                    background-color: rgba(124, 77, 255, 0.1);
                    color: #7C4DFF;
                    border: 2px solid #7C4DFF;
                    border-radius: 12px;
                    font-weight: 600;
                    padding: 12px 24px;
                }
                ModernButton:hover {
                    background-color: rgba(124, 77, 255, 0.2);
                    border-color: #8E5AFF;
                }
                ModernButton:pressed {
                    background-color: rgba(124, 77, 255, 0.3);
                }
            """)
        elif self.button_type == "success":
            self.setStyleSheet("""
                ModernButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #4CAF50, stop:1 #388E3C);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-weight: 600;
                    padding: 12px 24px;
                }
                ModernButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #66BB6A, stop:1 #43A047);
                }
            """)
        elif self.button_type == "danger":
            self.setStyleSheet("""
                ModernButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #F44336, stop:1 #D32F2F);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-weight: 600;
                    padding: 12px 24px;
                }
                ModernButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #EF5350, stop:1 #E53935);
                }
            """)


class ModernInput(QLineEdit):
    """Modern styled input field"""

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFont(QFont("Segoe UI", 11))
        self.setMinimumHeight(44)
        self.setStyleSheet("""
            ModernInput {
                border: 2px solid #E1E5E9;
                border-radius: 8px;
                padding: 12px 16px;
                background-color: #FAFBFC;
                color: #2D3748;
                font-size: 14px;
            }
            ModernInput:focus {
                border-color: #7C4DFF;
                background-color: white;
                outline: none;
            }
            ModernInput:hover {
                border-color: #CBD5E0;
            }
        """)


class ModernSpinBox(QDoubleSpinBox):
    """Modern styled spin box"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Segoe UI", 11))
        self.setMinimumHeight(44)
        self.setDecimals(3)
        self.setRange(-9999.999, 9999.999)
        self.setStyleSheet("""
            ModernSpinBox {
                border: 2px solid #E1E5E9;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: #FAFBFC;
                color: #2D3748;
                font-size: 14px;
            }
            ModernSpinBox:focus {
                border-color: #7C4DFF;
                background-color: white;
                outline: none;
            }
            ModernSpinBox:hover {
                border-color: #CBD5E0;
            }
            ModernSpinBox::up-button, ModernSpinBox::down-button {
                width: 0px;
                border: none;
            }
        """)


class PositionWidget(QWidget):
    """Widget for editing 6DOF position [X, Y, Z, RX, RY, RZ]"""

    valueChanged = pyqtSignal(list)

    def __init__(self, position=[0, 0, 0, 0, 0, 0], parent=None):
        super().__init__(parent)
        self.position = position[:]
        self.setup_ui()

    def setup_ui(self):
        layout = QGridLayout()
        layout.setSpacing(12)

        labels = ['X (mm)', 'Y (mm)', 'Z (mm)', 'RX (°)', 'RY (°)', 'RZ (°)']
        self.spinboxes = []

        for i, label in enumerate(labels):
            lbl = QLabel(label)
            lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
            lbl.setStyleSheet("color: #4A5568;")

            spinbox = ModernSpinBox()
            spinbox.setValue(self.position[i])
            spinbox.valueChanged.connect(self.on_value_changed)
            self.spinboxes.append(spinbox)

            row = i // 3
            col = (i % 3) * 2
            layout.addWidget(lbl, row, col)
            layout.addWidget(spinbox, row, col + 1)

        self.setLayout(layout)

    def on_value_changed(self):
        self.position = [spinbox.value() for spinbox in self.spinboxes]
        self.valueChanged.emit(self.position)

    def get_position(self):
        return self.position[:]

    def set_position(self, position):
        self.position = position[:]
        for i, spinbox in enumerate(self.spinboxes):
            spinbox.setValue(position[i])


class RobotConfigTab(QWidget):
    """Tab for robot configuration settings"""

    def __init__(self, config_data=None, parent=None):
        super().__init__(parent)
        self.config_data = config_data or {}
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Robot Connection Settings
        connection_card = ModernCard()
        connection_layout = QVBoxLayout(connection_card)
        connection_layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Robot Connection")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A202C; margin-bottom: 16px;")
        connection_layout.addWidget(title)

        form_layout = QGridLayout()
        form_layout.setSpacing(16)

        # Robot IP
        ip_label = QLabel("Robot IP Address:")
        ip_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        ip_label.setStyleSheet("color: #4A5568;")

        self.robot_ip_input = ModernInput(self.config_data.get('ROBOT_IP', '192.168.58.2'))

        form_layout.addWidget(ip_label, 0, 0)
        form_layout.addWidget(self.robot_ip_input, 0, 1)

        # Robot Tool
        tool_label = QLabel("Robot Tool:")
        tool_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        tool_label.setStyleSheet("color: #4A5568;")

        self.robot_tool_input = ModernSpinBox()
        self.robot_tool_input.setDecimals(0)
        self.robot_tool_input.setRange(0, 10)
        self.robot_tool_input.setValue(self.config_data.get('ROBOT_TOOL', 0))

        form_layout.addWidget(tool_label, 1, 0)
        form_layout.addWidget(self.robot_tool_input, 1, 1)

        # Robot User
        user_label = QLabel("Robot User:")
        user_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        user_label.setStyleSheet("color: #4A5568;")

        self.robot_user_input = ModernSpinBox()
        self.robot_user_input.setDecimals(0)
        self.robot_user_input.setRange(0, 10)
        self.robot_user_input.setValue(self.config_data.get('ROBOT_USER', 0))

        form_layout.addWidget(user_label, 2, 0)
        form_layout.addWidget(self.robot_user_input, 2, 1)

        connection_layout.addLayout(form_layout)
        main_layout.addWidget(connection_card)

        self.setLayout(main_layout)

    def get_config(self):
        return {
            'ROBOT_IP': self.robot_ip_input.text(),
            'ROBOT_TOOL': int(self.robot_tool_input.value()),
            'ROBOT_USER': int(self.robot_user_input.value())
        }


class PositionsTab(QWidget):
    """Tab for robot position settings"""

    def __init__(self, config_data=None, parent=None):
        super().__init__(parent)
        self.config_data = config_data or {}
        self.position_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)

        # Standard Positions
        positions = [
            ('LOGIN_POS', 'Login Position', [59.118, -334, 721.66, 180, 0, -90]),
            ('HOME_POS', 'Home Position', [-232.343, -93.902, 819.846, 180, 0, 90]),
            ('CALIBRATION_POS', 'Calibration Position', [-25.4, 370.001, 819.846, 180, 0, 0])
        ]

        standard_card = self.create_position_card("Standard Positions", positions)
        scroll_layout.addWidget(standard_card)

        # Nozzle Clean Positions
        clean_positions = [
            ('CLEAN_NOZZLE_1', 'Clean Position 1', [-165.037, -300.705, 298.201, 180, 0, 90]),
            ('CLEAN_NOZZLE_2', 'Clean Position 2', [-165.037, -431.735, 298.201, 180, 0, 90]),
            ('CLEAN_NOZZLE_3', 'Clean Position 3', [-165.037, -400, 298.201, 180, 0, 90])
        ]

        clean_card = self.create_position_card("Nozzle Clean Positions", clean_positions)
        scroll_layout.addWidget(clean_card)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def create_position_card(self, title, positions):
        card = ModernCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(20)

        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1A202C; margin-bottom: 8px;")
        card_layout.addWidget(title_label)

        # Positions
        for pos_key, pos_name, default_pos in positions:
            pos_frame = QFrame()
            pos_frame.setStyleSheet("""
                QFrame {
                    background-color: #F8F9FA;
                    border-radius: 12px;
                    border: 1px solid #E9ECEF;
                }
            """)
            pos_layout = QVBoxLayout(pos_frame)
            pos_layout.setContentsMargins(16, 16, 16, 16)

            # Position name
            name_label = QLabel(pos_name)
            name_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Medium))
            name_label.setStyleSheet("color: #495057; margin-bottom: 12px;")
            pos_layout.addWidget(name_label)

            # Position widget
            current_pos = self.config_data.get(pos_key, default_pos)
            pos_widget = PositionWidget(current_pos)
            self.position_widgets[pos_key] = pos_widget
            pos_layout.addWidget(pos_widget)

            card_layout.addWidget(pos_frame)

        return card

    def get_config(self):
        config = {}
        for key, widget in self.position_widgets.items():
            config[key] = widget.get_position()
        return config


class ToolChangerTab(QWidget):
    """Tab for tool changer slot positions"""

    def __init__(self, config_data=None, parent=None):
        super().__init__(parent)
        self.config_data = config_data or {}
        self.position_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)

        # Tool Changer Settings
        settings_card = self.create_settings_card()
        scroll_layout.addWidget(settings_card)

        # Slot configurations
        slots = [
            ('SLOT_0', 'Slot 0', {
                'PICKUP_0': [-98.555, -224.46, 300, 180, 0, 90],
                'PICKUP_1': [-98.555, -224.46, 181.11, 180, 0, 90],
                'PICKUP_2': [-98.555, -190.696, 181.11, 180, 0, 90],
                'PICKUP_3': [-98.555, -190.696, 300, 180, 0, 90],
                'DROPOFF_1': [-98.555, -190.696, 300, 180, 0, 90],
                'DROPOFF_2': [-98.555, -190.696, 181.11, 180, 0, 90],
                'DROPOFF_3': [-98.555, -224.46, 181.11, 180, 0, 90],
                'DROPOFF_4': [-98.555, -224.46, 300, 180, 0, 90]
            }),
            ('SLOT_1', 'Slot 1', {
                'PICKUP_0': [-247.871, -221.213, 300, 180, 0, 90],
                'PICKUP_1': [-247.871, -221.213, 180.278, 180, 0, 90],
                'PICKUP_2': [-247.871, -150, 180.278, 180, 0, 90],
                'DROPOFF_1': [-247.871, -150, 180.278, 180, 0, 90],
                'DROPOFF_2': [-247.871, -221.213, 180.278, 180, 0, 90],
                'DROPOFF_3': [-247.871, -221.213, 300, 180, 0, 90]
            }),
            ('SLOT_4', 'Slot 4', {
                'PICKUP_1': [-441.328, -280.786, 300, -180, 0, 90],
                'PICKUP_2': [-441.328, -280.786, 184.912, -180, 0, 90],
                'PICKUP_3': [-441.328, -201.309, 184.912, -180, 0, 90],
                'DROPOFF_1': [-441.328, -201.309, 184.912, -180, 0, 90],
                'DROPOFF_2': [-441.328, -280.786, 184.912, -180, 0, 90],
                'DROPOFF_3': [-441.328, -280.786, 300, -180, 0, 90]
            })
        ]

        for slot_prefix, slot_name, slot_positions in slots:
            slot_card = self.create_slot_card(slot_prefix, slot_name, slot_positions)
            scroll_layout.addWidget(slot_card)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def create_settings_card(self):
        card = ModernCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Tool Changer Settings")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A202C; margin-bottom: 16px;")
        card_layout.addWidget(title)

        form_layout = QGridLayout()
        form_layout.setSpacing(16)

        # Velocity
        vel_label = QLabel("Velocity:")
        vel_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        vel_label.setStyleSheet("color: #4A5568;")

        self.velocity_input = ModernSpinBox()
        self.velocity_input.setDecimals(0)
        self.velocity_input.setRange(1, 1000)
        self.velocity_input.setValue(self.config_data.get('TOOL_CHANGING_VELOCITY', 100))

        form_layout.addWidget(vel_label, 0, 0)
        form_layout.addWidget(self.velocity_input, 0, 1)

        # Acceleration
        acc_label = QLabel("Acceleration:")
        acc_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        acc_label.setStyleSheet("color: #4A5568;")

        self.acceleration_input = ModernSpinBox()
        self.acceleration_input.setDecimals(0)
        self.acceleration_input.setRange(1, 1000)
        self.acceleration_input.setValue(self.config_data.get('TOOL_CHANGING_ACCELERATION', 30))

        form_layout.addWidget(acc_label, 1, 0)
        form_layout.addWidget(self.acceleration_input, 1, 1)

        # Blending Radius
        blend_label = QLabel("Blending Radius:")
        blend_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        blend_label.setStyleSheet("color: #4A5568;")

        self.blending_input = ModernSpinBox()
        self.blending_input.setDecimals(1)
        self.blending_input.setRange(0, 100)
        self.blending_input.setValue(self.config_data.get('TOOL_CHANGING_BELNDING_RADIUS', 1))

        form_layout.addWidget(blend_label, 2, 0)
        form_layout.addWidget(self.blending_input, 2, 1)

        card_layout.addLayout(form_layout)
        return card

    def create_slot_card(self, slot_prefix, slot_name, slot_positions):
        card = ModernCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        # Title
        title_label = QLabel(slot_name)
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1A202C; margin-bottom: 8px;")
        card_layout.addWidget(title_label)

        # Create tabs for pickup and dropoff
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E9ECEF;
                border-radius: 8px;
                background-color: #F8F9FA;
            }
            QTabBar::tab {
                background-color: #E9ECEF;
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 4px 4px 0 0;
            }
            QTabBar::tab:selected {
                background-color: #7C4DFF;
                color: white;
            }
        """)

        # Pickup positions
        pickup_widget = QWidget()
        pickup_layout = QVBoxLayout(pickup_widget)
        pickup_layout.setSpacing(12)

        # Dropoff positions
        dropoff_widget = QWidget()
        dropoff_layout = QVBoxLayout(dropoff_widget)
        dropoff_layout.setSpacing(12)

        for pos_name, default_pos in slot_positions.items():
            pos_key = f"{slot_prefix}_{pos_name}"
            current_pos = self.config_data.get(pos_key, default_pos)

            pos_frame = QFrame()
            pos_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 8px;
                    border: 1px solid #DEE2E6;
                }
            """)
            pos_frame_layout = QVBoxLayout(pos_frame)
            pos_frame_layout.setContentsMargins(12, 12, 12, 12)

            name_label = QLabel(pos_name.replace('_', ' ').title())
            name_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
            name_label.setStyleSheet("color: #495057; margin-bottom: 8px;")
            pos_frame_layout.addWidget(name_label)

            pos_widget = PositionWidget(current_pos)
            self.position_widgets[pos_key] = pos_widget
            pos_frame_layout.addWidget(pos_widget)

            if 'PICKUP' in pos_name:
                pickup_layout.addWidget(pos_frame)
            else:
                dropoff_layout.addWidget(pos_frame)

        tab_widget.addTab(pickup_widget, "Pickup Positions")
        tab_widget.addTab(dropoff_widget, "Dropoff Positions")

        card_layout.addWidget(tab_widget)
        return card

    def get_config(self):
        config = {
            'TOOL_CHANGING_VELOCITY': int(self.velocity_input.value()),
            'TOOL_CHANGING_ACCELERATION': int(self.acceleration_input.value()),
            'TOOL_CHANGING_BELNDING_RADIUS': self.blending_input.value()
        }

        for key, widget in self.position_widgets.items():
            config[key] = widget.get_position()

        return config


class JogSettingsTab(QWidget):
    """Tab for jog and other movement settings"""

    def __init__(self, config_data=None, parent=None):
        super().__init__(parent)
        self.config_data = config_data or {}
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Jog Settings
        jog_card = ModernCard()
        jog_layout = QVBoxLayout(jog_card)
        jog_layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Jog Settings")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A202C; margin-bottom: 16px;")
        jog_layout.addWidget(title)

        jog_form = QGridLayout()
        jog_form.setSpacing(16)

        # Jog Velocity
        jog_vel_label = QLabel("Jog Velocity:")
        jog_vel_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        jog_vel_label.setStyleSheet("color: #4A5568;")

        self.jog_velocity_input = ModernSpinBox()
        self.jog_velocity_input.setDecimals(0)
        self.jog_velocity_input.setRange(1, 1000)
        self.jog_velocity_input.setValue(self.config_data.get('JOG_VELOCITY', 20))

        jog_form.addWidget(jog_vel_label, 0, 0)
        jog_form.addWidget(self.jog_velocity_input, 0, 1)

        # Jog Acceleration
        jog_acc_label = QLabel("Jog Acceleration:")
        jog_acc_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        jog_acc_label.setStyleSheet("color: #4A5568;")

        self.jog_acceleration_input = ModernSpinBox()
        self.jog_acceleration_input.setDecimals(0)
        self.jog_acceleration_input.setRange(1, 1000)
        self.jog_acceleration_input.setValue(self.config_data.get('JOG_ACCELERATION', 100))

        jog_form.addWidget(jog_acc_label, 1, 0)
        jog_form.addWidget(self.jog_acceleration_input, 1, 1)

        jog_layout.addLayout(jog_form)
        main_layout.addWidget(jog_card)

        # Nozzle Clean Settings
        clean_card = ModernCard()
        clean_layout = QVBoxLayout(clean_card)
        clean_layout.setContentsMargins(24, 24, 24, 24)

        clean_title = QLabel("Nozzle Clean Settings")
        clean_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        clean_title.setStyleSheet("color: #1A202C; margin-bottom: 16px;")
        clean_layout.addWidget(clean_title)

        clean_form = QGridLayout()
        clean_form.setSpacing(16)

        # Clean Velocity
        clean_vel_label = QLabel("Clean Velocity:")
        clean_vel_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        clean_vel_label.setStyleSheet("color: #4A5568;")

        self.clean_velocity_input = ModernSpinBox()
        self.clean_velocity_input.setDecimals(0)
        self.clean_velocity_input.setRange(1, 1000)
        self.clean_velocity_input.setValue(self.config_data.get('CLEAN_NOZZLE_VELOCITY', 30))

        clean_form.addWidget(clean_vel_label, 0, 0)
        clean_form.addWidget(self.clean_velocity_input, 0, 1)

        # Clean Acceleration
        clean_acc_label = QLabel("Clean Acceleration:")
        clean_acc_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        clean_acc_label.setStyleSheet("color: #4A5568;")

        self.clean_acceleration_input = ModernSpinBox()
        self.clean_acceleration_input.setDecimals(0)
        self.clean_acceleration_input.setRange(1, 1000)
        self.clean_acceleration_input.setValue(self.config_data.get('CLEAN_NOZZLE_ACCELERATION', 30))

        clean_form.addWidget(clean_acc_label, 1, 0)
        clean_form.addWidget(self.clean_acceleration_input, 1, 1)

        # Clean Blending Radius
        clean_blend_label = QLabel("Clean Blending Radius:")
        clean_blend_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        clean_blend_label.setStyleSheet("color: #4A5568;")

        self.clean_blending_input = ModernSpinBox()
        self.clean_blending_input.setDecimals(1)
        self.clean_blending_input.setRange(0, 100)
        self.clean_blending_input.setValue(self.config_data.get('CLEAN_NOZZLE_BLENDING_RADIUS', 1))

        clean_form.addWidget(clean_blend_label, 2, 0)
        clean_form.addWidget(self.clean_blending_input, 2, 1)

        clean_layout.addLayout(clean_form)
        main_layout.addWidget(clean_card)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def get_config(self):
        return {
            'JOG_VELOCITY': int(self.jog_velocity_input.value()),
            'JOG_ACCELERATION': int(self.jog_acceleration_input.value()),
            'CLEAN_NOZZLE_VELOCITY': int(self.clean_velocity_input.value()),
            'CLEAN_NOZZLE_ACCELERATION': int(self.clean_acceleration_input.value()),
            'CLEAN_NOZZLE_BLENDING_RADIUS': self.clean_blending_input.value()
        }


class RobotConfigWindow(QMainWindow):
    """Main window for robot configuration"""

    def __init__(self):
        super().__init__()
        self.config_data = self.load_default_config()
        self.setup_ui()

    def load_default_config(self):
        """Load default robot configuration"""
        return {
            'ROBOT_IP': '192.168.58.2',
            'ROBOT_TOOL': 0,
            'ROBOT_USER': 0,
            'LOGIN_POS': [59.118, -334, 721.66, 180, 0, -90],
            'HOME_POS': [-232.343, -93.902, 819.846, 180, 0, 90],
            'CALIBRATION_POS': [-25.4, 370.001, 819.846, 180, 0, 0],
            'JOG_VELOCITY': 20,
            'JOG_ACCELERATION': 100,
            'CLEAN_NOZZLE_1': [-165.037, -300.705, 298.201, 180, 0, 90],
            'CLEAN_NOZZLE_2': [-165.037, -431.735, 298.201, 180, 0, 90],
            'CLEAN_NOZZLE_3': [-165.037, -400, 298.201, 180, 0, 90],
            'CLEAN_NOZZLE_VELOCITY': 30,
            'CLEAN_NOZZLE_ACCELERATION': 30,
            'CLEAN_NOZZLE_BLENDING_RADIUS': 1,
            'TOOL_CHANGING_VELOCITY': 100,
            'TOOL_CHANGING_ACCELERATION': 30,
            'TOOL_CHANGING_BELNDING_RADIUS': 1,
            'SLOT_0_PICKUP_0': [-98.555, -224.46, 300, 180, 0, 90],
            'SLOT_0_PICKUP_1': [-98.555, -224.46, 181.11, 180, 0, 90],
            'SLOT_0_PICKUP_2': [-98.555, -190.696, 181.11, 180, 0, 90],
            'SLOT_0_PICKUP_3': [-98.555, -190.696, 300, 180, 0, 90],
            'SLOT_0_DROPOFF_1': [-98.555, -190.696, 300, 180, 0, 90],
            'SLOT_0_DROPOFF_2': [-98.555, -190.696, 181.11, 180, 0, 90],
            'SLOT_0_DROPOFF_3': [-98.555, -224.46, 181.11, 180, 0, 90],
            'SLOT_0_DROPOFF_4': [-98.555, -224.46, 300, 180, 0, 90],
            'SLOT_1_PICKUP_0': [-247.871, -221.213, 300, 180, 0, 90],
            'SLOT_1_PICKUP_1': [-247.871, -221.213, 180.278, 180, 0, 90],
            'SLOT_1_PICKUP_2': [-247.871, -150, 180.278, 180, 0, 90],
            'SLOT_1_DROPOFF_1': [-247.871, -150, 180.278, 180, 0, 90],
            'SLOT_1_DROPOFF_2': [-247.871, -221.213, 180.278, 180, 0, 90],
            'SLOT_1_DROPOFF_3': [-247.871, -221.213, 300, 180, 0, 90],
            'SLOT_4_PICKUP_1': [-441.328, -280.786, 300, -180, 0, 90],
            'SLOT_4_PICKUP_2': [-441.328, -280.786, 184.912, -180, 0, 90],
            'SLOT_4_PICKUP_3': [-441.328, -201.309, 184.912, -180, 0, 90],
            'SLOT_4_DROPOFF_1': [-441.328, -201.309, 184.912, -180, 0, 90],
            'SLOT_4_DROPOFF_2': [-441.328, -280.786, 184.912, -180, 0, 90],
            'SLOT_4_DROPOFF_3': [-441.328, -280.786, 300, -180, 0, 90]
        }

    def setup_ui(self):
        self.setWindowTitle("Robot Configuration Manager")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)

        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header
        header = self.create_header()
        main_layout.addWidget(header)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: white;
                padding: 12px 24px;
                margin-right: 4px;
                border-radius: 12px 12px 0 0;
                font-size: 14px;
                font-weight: 600;
                color: #6C757D;
                border: 2px solid #E9ECEF;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #7C4DFF;
                color: white;
                border-color: #7C4DFF;
            }
            QTabBar::tab:hover:!selected {
                background-color: #F8F9FA;
                border-color: #DEE2E6;
            }
        """)

        # Create tabs
        self.robot_tab = RobotConfigTab(self.config_data)
        self.positions_tab = PositionsTab(self.config_data)
        self.tool_changer_tab = ToolChangerTab(self.config_data)
        self.jog_tab = JogSettingsTab(self.config_data)

        self.tab_widget.addTab(self.robot_tab, "Robot Config")
        self.tab_widget.addTab(self.positions_tab, "Positions")
        self.tab_widget.addTab(self.tool_changer_tab, "Tool Changer")
        self.tab_widget.addTab(self.jog_tab, "Movement Settings")

        main_layout.addWidget(self.tab_widget)

        # Footer with action buttons
        footer = self.create_footer()
        main_layout.addWidget(footer)

    def create_header(self):
        """Create header with title and description"""
        header_card = ModernCard()
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(32, 24, 32, 24)

        # Title
        title = QLabel("Robot Configuration Manager")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A202C; margin-bottom: 8px;")
        header_layout.addWidget(title)

        # Description
        description = QLabel("Configure robot settings, positions, and movement parameters")
        description.setFont(QFont("Segoe UI", 14))
        description.setStyleSheet("color: #718096;")
        header_layout.addWidget(description)

        return header_card

    def create_footer(self):
        """Create footer with action buttons"""
        footer_card = ModernCard()
        footer_layout = QHBoxLayout(footer_card)
        footer_layout.setContentsMargins(24, 16, 24, 16)

        # Load button
        load_btn = ModernButton("Load Config", "secondary")
        load_btn.clicked.connect(self.load_config)
        footer_layout.addWidget(load_btn)

        # Save button
        save_btn = ModernButton("Save Config", "secondary")
        save_btn.clicked.connect(self.save_config)
        footer_layout.addWidget(save_btn)

        footer_layout.addStretch()

        # Reset button
        reset_btn = ModernButton("Reset to Defaults", "danger")
        reset_btn.clicked.connect(self.reset_config)
        footer_layout.addWidget(reset_btn)

        # Apply button
        apply_btn = ModernButton("Apply Changes", "success")
        apply_btn.clicked.connect(self.apply_config)
        footer_layout.addWidget(apply_btn)

        return footer_card

    def get_all_config(self):
        """Get configuration from all tabs"""
        config = {}
        config.update(self.robot_tab.get_config())
        config.update(self.positions_tab.get_config())
        config.update(self.tool_changer_tab.get_config())
        config.update(self.jog_tab.get_config())
        return config

    def load_config(self):
        """Load configuration from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Robot Configuration", "", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.config_data = json.load(f)

                # Recreate tabs with new data
                self.tab_widget.clear()
                self.robot_tab = RobotConfigTab(self.config_data)
                self.positions_tab = PositionsTab(self.config_data)
                self.tool_changer_tab = ToolChangerTab(self.config_data)
                self.jog_tab = JogSettingsTab(self.config_data)

                self.tab_widget.addTab(self.robot_tab, "Robot Config")
                self.tab_widget.addTab(self.positions_tab, "Positions")
                self.tab_widget.addTab(self.tool_changer_tab, "Tool Changer")
                self.tab_widget.addTab(self.jog_tab, "Movement Settings")

                QMessageBox.information(self, "Success", "Configuration loaded successfully!")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load configuration:\n{str(e)}")

    def save_config(self):
        """Save configuration to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Robot Configuration", "robot_config.json", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                config = self.get_all_config()
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=4)

                QMessageBox.information(self, "Success", "Configuration saved successfully!")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save configuration:\n{str(e)}")

    def reset_config(self):
        """Reset configuration to defaults"""
        reply = QMessageBox.question(
            self, "Reset Configuration",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.config_data = self.load_default_config()

            # Recreate tabs with default data
            self.tab_widget.clear()
            self.robot_tab = RobotConfigTab(self.config_data)
            self.positions_tab = PositionsTab(self.config_data)
            self.tool_changer_tab = ToolChangerTab(self.config_data)
            self.jog_tab = JogSettingsTab(self.config_data)

            self.tab_widget.addTab(self.robot_tab, "Robot Config")
            self.tab_widget.addTab(self.positions_tab, "Positions")
            self.tab_widget.addTab(self.tool_changer_tab, "Tool Changer")
            self.tab_widget.addTab(self.jog_tab, "Movement Settings")

            QMessageBox.information(self, "Reset Complete", "Configuration reset to default values!")

    def apply_config(self):
        """Apply current configuration"""
        config = self.get_all_config()

        # Here you would apply the configuration to your robot system
        # For now, just show a confirmation
        reply = QMessageBox.question(
            self, "Apply Configuration",
            "Apply the current configuration to the robot system?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Apply configuration logic here
            print("Applying configuration:")
            for key, value in config.items():
                print(f"  {key}: {value}")

            QMessageBox.information(self, "Success", "Configuration applied successfully!")

    def export_to_python(self):
        """Export configuration as Python constants file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Python Constants", "robot_constants.py", "Python Files (*.py);;All Files (*)"
        )

        if file_path:
            try:
                config = self.get_all_config()

                with open(file_path, 'w') as f:
                    f.write("#!/usr/bin/env python3\n")
                    f.write('"""\nRobot Configuration Constants\nGenerated by Robot Configuration Manager\n"""\n\n')

                    # Write robot connection settings
                    f.write("# Robot Connection Settings\n")
                    f.write(f"ROBOT_IP = '{config.get('ROBOT_IP', '192.168.58.2')}'\n")
                    f.write(f"ROBOT_TOOL = {config.get('ROBOT_TOOL', 0)}\n")
                    f.write(f"ROBOT_USER = {config.get('ROBOT_USER', 0)}\n\n")

                    # Write positions
                    f.write("# Standard Positions\n")
                    for key in ['LOGIN_POS', 'HOME_POS', 'CALIBRATION_POS']:
                        if key in config:
                            f.write(f"{key} = {config[key]}\n")
                    f.write("\n")

                    # Write movement settings
                    f.write("# Movement Settings\n")
                    for key in ['JOG_VELOCITY', 'JOG_ACCELERATION']:
                        if key in config:
                            f.write(f"{key} = {config[key]}\n")
                    f.write("\n")

                    # Write nozzle clean settings
                    f.write("# Nozzle Clean Settings\n")
                    for key in ['CLEAN_NOZZLE_1', 'CLEAN_NOZZLE_2', 'CLEAN_NOZZLE_3']:
                        if key in config:
                            f.write(f"{key} = {config[key]}\n")
                    for key in ['CLEAN_NOZZLE_VELOCITY', 'CLEAN_NOZZLE_ACCELERATION', 'CLEAN_NOZZLE_BLENDING_RADIUS']:
                        if key in config:
                            f.write(f"{key} = {config[key]}\n")
                    f.write("\n")

                    # Write tool changer settings
                    f.write("# Tool Changer Settings\n")
                    for key in ['TOOL_CHANGING_VELOCITY', 'TOOL_CHANGING_ACCELERATION',
                                'TOOL_CHANGING_BELNDING_RADIUS']:
                        if key in config:
                            f.write(f"{key} = {config[key]}\n")
                    f.write("\n")

                    # Write slot positions
                    slots = ['SLOT_0', 'SLOT_1', 'SLOT_4']
                    for slot in slots:
                        f.write(f"# {slot} Positions\n")
                        for key in config:
                            if key.startswith(slot):
                                f.write(f"{key} = {config[key]}\n")
                        f.write("\n")

                QMessageBox.information(self, "Success", "Configuration exported to Python file successfully!")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export configuration:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show window
    window = RobotConfigWindow()
    window.show()

    sys.exit(app.exec())
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.frontend.pl_ui.ui.widgets.virtualKeyboard.VirtualKeyboard import FocusDoubleSpinBox
import json
import os
from modules.shared.shared.settings.robotConfig.robotConfigModel import RobotConfig, get_default_config
from modules.shared.shared.settings.robotConfig.robotConfigModel import RobotConfig, get_default_config, OffsetDirectionMap


class TcpOffsetDialog(QDialog):
    """
    Standalone dialog for quickly viewing and editing TCP X and Y offsets.
    Can be triggered from anywhere in the application via keyboard shortcut.
    """
    
    tcp_offsets_updated = pyqtSignal(float, float)  # Signal emitted when offsets are saved
    
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.setWindowTitle("TCP Offset Settings")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(400, 200)
        
        # Store the controller for handling config operations
        self.controller = controller
        
        # Fallback file path for direct access if no controller available
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # From pl_ui/ui/widgets/, go up 3 levels to project root
        project_root = os.path.join(current_dir, '..', '..', '..')
        self.config_file = os.path.join(project_root, 'GlueDispensingApplication', 'storage', 'settings', 'robot_config.json')
        
        self.init_ui()
        self.load_current_values()

    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout()

        # === Title ===
        title_label = QLabel("TCP Offset Configuration")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 4px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # === Base TCP Offsets ===
        tcp_group = QGroupBox("Base TCP Offsets")
        tcp_layout = QGridLayout()

        tcp_layout.addWidget(QLabel("TCP X Offset:"), 0, 0)
        self.tcp_x_spinbox = FocusDoubleSpinBox()
        self.tcp_x_spinbox.setRange(-1000, 1000)
        self.tcp_x_spinbox.setDecimals(3)
        self.tcp_x_spinbox.setSuffix(" mm")
        tcp_layout.addWidget(self.tcp_x_spinbox, 0, 1)

        tcp_layout.addWidget(QLabel("TCP Y Offset:"), 1, 0)
        self.tcp_y_spinbox = FocusDoubleSpinBox()
        self.tcp_y_spinbox.setRange(-1000, 1000)
        self.tcp_y_spinbox.setDecimals(3)
        self.tcp_y_spinbox.setSuffix(" mm")
        tcp_layout.addWidget(self.tcp_y_spinbox, 1, 1)

        tcp_group.setLayout(tcp_layout)
        layout.addWidget(tcp_group)

        # === Step Settings ===
        step_group = QGroupBox("Step Settings")
        step_layout = QGridLayout()

        step_layout.addWidget(QLabel("X Step Offset (mm):"), 1, 0)
        self.x_step_offset_spinbox = FocusDoubleSpinBox()
        self.x_step_offset_spinbox.setRange(-1000, 1000)
        self.x_step_offset_spinbox.setDecimals(3)
        self.x_step_offset_spinbox.setSuffix(" mm")
        step_layout.addWidget(self.x_step_offset_spinbox, 1, 1)

        step_layout.addWidget(QLabel("Y Step Offset (mm):"), 3, 0)
        self.y_step_offset_spinbox = FocusDoubleSpinBox()
        self.y_step_offset_spinbox.setRange(-1000, 1000)
        self.y_step_offset_spinbox.setDecimals(3)
        self.y_step_offset_spinbox.setSuffix(" mm")
        step_layout.addWidget(self.y_step_offset_spinbox, 3, 1)

        step_group.setLayout(step_layout)
        layout.addWidget(step_group)



        # === Direction Map ===
        dir_group = QGroupBox("Direction Map")
        dir_layout = QGridLayout()
        self.dir_map_checkboxes = {}

        directions = {
            '+X': "Right",
            '-X': "Left",
            '+Y': "Down",
            '-Y': "Up"
        }

        for i, (key, label) in enumerate(directions.items()):
            dir_layout.addWidget(QLabel(f"{key} ({label})"), i, 0)
            btn = QPushButton("Follow Movement")
            btn.setCheckable(True)
            btn.setChecked(True)
            self.setup_direction_button(btn)
            dir_layout.addWidget(btn, i, 1)
            self.dir_map_checkboxes[key] = btn

        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)

        # === Current Values ===
        self.current_values_label = QLabel()
        self.current_values_label.setStyleSheet("""
            font-size: 12px;
            color: #666;
            padding: 5px;
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 3px;
        """)
        layout.addWidget(self.current_values_label)

        # === Buttons ===
        button_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset to 0")
        reset_btn.clicked.connect(self.reset_values)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save & Apply")
        save_btn.clicked.connect(self.save_and_apply)
        save_btn.setDefault(True)

        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #e9ecef; }
        """)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #5a6268; }
        """)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #218838; }
        """)

        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)

        # === Finalize Layout ===
        self.setLayout(layout)

        # Connect live updates
        self.tcp_x_spinbox.valueChanged.connect(self.update_display)
        self.tcp_y_spinbox.valueChanged.connect(self.update_display)

        self.x_step_offset_spinbox.valueChanged.connect(self.update_display)

        self.y_step_offset_spinbox.valueChanged.connect(self.update_display)

    def get_direction_map(self) -> OffsetDirectionMap:
        """Return current direction button states as an OffsetDirectionMap"""
        return OffsetDirectionMap(
            pos_x=self.dir_map_checkboxes['+X'].isChecked(),
            neg_x=self.dir_map_checkboxes['-X'].isChecked(),
            pos_y=self.dir_map_checkboxes['+Y'].isChecked(),
            neg_y=self.dir_map_checkboxes['-Y'].isChecked()
        )

    def set_direction_map(self, direction_map: OffsetDirectionMap):
        """Apply saved OffsetDirectionMap states to buttons"""
        self.dir_map_checkboxes['+X'].setChecked(direction_map.pos_x)
        self.dir_map_checkboxes['-X'].setChecked(direction_map.neg_x)
        self.dir_map_checkboxes['+Y'].setChecked(direction_map.pos_y)
        self.dir_map_checkboxes['-Y'].setChecked(direction_map.neg_y)

    def setup_direction_button(self, button: QPushButton):
        button.setCheckable(True)
        button.setChecked(True)
        # Connect the toggled signal to change style
        button.toggled.connect(lambda checked, b=button: self.update_button_color(b, checked))
        # Initialize style
        self.update_button_color(button, button.isChecked())

    def update_button_color(self, button: QPushButton, checked: bool):
        if checked:
            button.setStyleSheet("""
                QPushButton {
                    background-color: purple;
                    color: white;
                    border-radius: 4px;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    color: black;
                    border-radius: 4px;
                }
            """)

    def load_current_values(self):
        """Load current TCP offset values using the same approach as RobotConfigUI"""
        try:
            print(f"📁 Looking for config file at: {self.config_file}")
            print(f"📁 File exists: {os.path.exists(self.config_file)}")
            
            # Use the same loading approach as RobotConfigController
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                config = RobotConfig.from_dict(data)
            else:
                print(f"❌ Config file not found, using default config")
                config = get_default_config()
                
            print(f"📍 Found TCP offsets: X={config.tcp_x_offset}, Y={config.tcp_y_offset}")
            
            # Set the values in the spinboxes
            self.tcp_x_spinbox.setValue(config.tcp_x_offset)
            self.tcp_y_spinbox.setValue(config.tcp_y_offset)

            # # Set dynamic step values

            self.x_step_offset_spinbox.setValue(config.tcp_x_step_offset)

            self.y_step_offset_spinbox.setValue(config.tcp_y_step_offset)

            # Load direction map if present
            if hasattr(config, 'offset_direction_map') and config.offset_direction_map:
                self.set_direction_map(config.offset_direction_map)
            else:
                # Default: all directions enabled
                self.set_direction_map(OffsetDirectionMap())

            self.update_display()
                
        except Exception as e:
            print(f"Error loading TCP offset values: {e}")
            import traceback
            traceback.print_exc()
            self.current_values_label.setText("Error loading current values")
            
    def update_display(self):
        """Update the current values display"""
        x_value = self.tcp_x_spinbox.value()
        y_value = self.tcp_y_spinbox.value()
        
        self.current_values_label.setText(
            f"Current values: X = {x_value:.3f} mm, Y = {y_value:.3f} mm"
        )
        
    def reset_values(self):
        """Reset both TCP offsets to 0"""
        self.tcp_x_spinbox.setValue(0.0)
        self.tcp_y_spinbox.setValue(0.0)
        
    def save_and_apply(self):
        """Save the TCP offset values using the same approach as RobotConfigUI"""
        try:
            # Get new values
            tcp_x = self.tcp_x_spinbox.value()
            tcp_y = self.tcp_y_spinbox.value()
            # Read dynamic offset settings

            x_step_off = self.x_step_offset_spinbox.value()

            y_step_off = self.y_step_offset_spinbox.value()


            # Load current config using RobotConfig model (same as RobotConfigController)
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                config = RobotConfig.from_dict(data)
            else:
                config = get_default_config()
            
            # Update TCP offset values in the config object
            config.tcp_x_offset = tcp_x
            config.tcp_y_offset = tcp_y

            # Update config

            config.tcp_x_step_offset = x_step_off

            config.tcp_y_step_offset = y_step_off

            # Save direction map
            config.offset_direction_map = self.get_direction_map()

            # Save using the same method as RobotConfigController
            config_data = config.to_dict()
            
            # Save to file (same as save_config_to_file in RobotConfigController)
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
            
            print(f"🔄 TCP Offsets saved to: {self.config_file}")
            print(f"   └── X={tcp_x:.3f}mm, Y={tcp_y:.3f}mm")
            
            # Emit signal to notify other components (including MainWindow to send ROBOT_UPDATE_CONFIG)
            self.tcp_offsets_updated.emit(tcp_x, tcp_y)
            
            # Show success message
            QMessageBox.information(
                self, 
                "TCP Offsets Saved", 
                f"TCP offsets have been saved successfully:\n"
                f"X Offset: {tcp_x:.3f} mm\n"
                f"Y Offset: {tcp_y:.3f} mm\n\n"
                f"The robot configuration has been updated."
            )
            
            # Accept the dialog (close it)
            self.accept()
            
        except Exception as e:
            print(f"Error saving TCP offset values: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self, 
                "Error Saving TCP Offsets", 
                f"Failed to save TCP offset values:\n{str(e)}"
            )
            
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self.save_and_apply()
        else:
            super().keyPressEvent(event)


# Global reference to keep the dialog accessible
_tcp_offset_dialog = None


def show_tcp_offset_dialog(parent=None):
    """
    Global function to show the TCP offset dialog.
    This can be called from anywhere in the application.
    """
    global _tcp_offset_dialog
    
    if _tcp_offset_dialog is None:
        _tcp_offset_dialog = TcpOffsetDialog(parent)
    else:
        # Update parent and reload values
        _tcp_offset_dialog.setParent(parent)
        _tcp_offset_dialog.load_current_values()
    
    # Show the dialog
    _tcp_offset_dialog.show()
    _tcp_offset_dialog.raise_()
    _tcp_offset_dialog.activateWindow()
    
    return _tcp_offset_dialog


if __name__ == "__main__":
    # Test the dialog
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = TcpOffsetDialog()
    dialog.show()
    sys.exit(app.exec())
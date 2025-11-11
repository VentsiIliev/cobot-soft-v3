from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QSpinBox, QPushButton,
    QGridLayout, QGroupBox, QVBoxLayout, QHBoxLayout, QScrollArea,
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog
)
import sys


class RobotConfigUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robot Config UI")
        self.resize(800, 700)
        self.position_lists = {}  # Store lists for each movement group
        self.velocity_acceleration_widgets = {}  # Store vel/acc widgets
        self.init_ui()
        self.load_default_data()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # --- Robot Info ---
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
        main_layout.addWidget(robot_group)

        # --- Positions & related groups ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout()

        # Define movement groups with their velocity/acceleration settings
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

            # Add velocity/acceleration controls if needed
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
                # For LOGIN_POS, HOME_POS, CALIBRATION_POS - they have individual vel/acc
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

            # Create position display for single positions or list widget for multiple positions
            if config.get("single_position", False):
                # Single position display with edit button
                position_layout = QHBoxLayout()
                position_label = QLabel(f"{group_name} Position:")
                position_display = QLineEdit()
                position_display.setReadOnly(True)
                edit_position_btn = QPushButton("Edit Position")
                set_current_btn = QPushButton("Set Current")
                move_to_btn = QPushButton("Move To")

                edit_position_btn.clicked.connect(lambda checked, gn=group_name: self.edit_single_position(gn))
                set_current_btn.clicked.connect(lambda checked, gn=group_name: self.set_current_position(gn))
                move_to_btn.clicked.connect(lambda checked, gn=group_name: self.move_to_single_position(gn))

                position_layout.addWidget(position_display)
                position_layout.addWidget(edit_position_btn)
                position_layout.addWidget(set_current_btn)
                position_layout.addWidget(move_to_btn)

                group_layout.addWidget(position_label)
                group_layout.addLayout(position_layout)

                # Store the display widget for single positions
                self.position_lists[group_name] = position_display

            elif config.get("has_positions", True):
                position_list = QListWidget()
                position_list.setMaximumHeight(150)
                group_layout.addWidget(QLabel(f"{group_name} Points:"))
                group_layout.addWidget(position_list)

                # Add/Remove/Edit/Move buttons
                button_layout = QHBoxLayout()
                add_btn = QPushButton(f"Add Point")
                remove_btn = QPushButton(f"Remove Point")
                edit_btn = QPushButton(f"Edit Point")
                move_btn = QPushButton(f"Move to Point")
                add_btn.clicked.connect(lambda checked, gn=group_name: self.add_point(gn))
                remove_btn.clicked.connect(lambda checked, gn=group_name: self.remove_point(gn))
                edit_btn.clicked.connect(lambda checked, gn=group_name: self.edit_point(gn))
                move_btn.clicked.connect(lambda checked, gn=group_name: self.move_to_point(gn))
                button_layout.addWidget(add_btn)
                button_layout.addWidget(remove_btn)
                button_layout.addWidget(edit_btn)
                button_layout.addWidget(move_btn)
                button_layout.addStretch()
                group_layout.addLayout(button_layout)

                self.position_lists[group_name] = position_list

            group_box.setLayout(group_layout)
            content_layout.addWidget(group_box)

        content.setLayout(content_layout)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Save/Reset buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("Save")
        reset_btn = QPushButton("Reset")
        save_btn.clicked.connect(self.save)
        reset_btn.clicked.connect(self.reset)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(reset_btn)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def load_default_data(self):
        """Load default position data into the UI"""
        default_positions = {
            "LOGIN_POS": [
                [59.118, -334, 721.66, 180, 0, -90]
            ],
            "HOME_POS": [
                [-232.343, -93.902, 819.846, 180, 0, 90]
            ],
            "CALIBRATION_POS": [
                [-25.4, 370.001, 819.846, 180, 0, 0]
            ],
            "NOZZLE CLEAN": [
                [-165.037, -300.705, 298.201, 180, 0, 90],
                [-165.037, -431.735, 298.201, 180, 0, 90],
                [-165.037, -400, 298.201, 180, 0, 90]
            ],
            "TOOL CHANGER": [
                # No default positions provided, but keeping the structure
            ],
            "SLOT 0 PICKUP": [
                [-98.555, -224.46, 300, 180, 0, 90],
                [-98.555, -224.46, 181.11, 180, 0, 90],
                [-98.555, -190.696, 181.11, 180, 0, 90],
                [-98.555, -190.696, 300, 180, 0, 90]
            ],
            "SLOT 0 DROPOFF": [
                [-98.555, -190.696, 300, 180, 0, 90],
                [-98.555, -190.696, 181.11, 180, 0, 90],
                [-98.555, -224.46, 181.11, 180, 0, 90],
                [-98.555, -224.46, 300, 180, 0, 90]
            ],
            "SLOT 1 PICKUP": [
                [-247.871, -221.213, 300, 180, 0, 90],
                [-247.871, -221.213, 180.278, 180, 0, 90],
                [-247.871, -150, 180.278, 180, 0, 90]
            ],
            "SLOT 1 DROPOFF": [
                [-247.871, -150, 180.278, 180, 0, 90],
                [-247.871, -221.213, 180.278, 180, 0, 90],
                [-247.871, -221.213, 300, 180, 0, 90]
            ],
            "SLOT 4 PICKUP": [
                [-441.328, -280.786, 300, -180, 0, 90],
                [-441.328, -280.786, 184.912, -180, 0, 90],
                [-441.328, -201.309, 184.912, -180, 0, 90]
            ],
            "SLOT 4 DROPOFF": [
                [-441.328, -201.309, 184.912, -180, 0, 90],
                [-441.328, -280.786, 184.912, -180, 0, 90],
                [-441.328, -280.786, 300, -180, 0, 90]
            ]
        }

        # Load positions into the UI
        for group_name, positions in default_positions.items():
            if group_name in self.position_lists:
                widget = self.position_lists[group_name]

                # Handle single position groups (LOGIN_POS, HOME_POS, CALIBRATION_POS)
                if isinstance(widget, QLineEdit):
                    if positions:
                        widget.setText(str(positions[0]))
                # Handle multi-position groups
                elif isinstance(widget, QListWidget):
                    for position in positions:
                        item = QListWidgetItem(str(position))
                        widget.addItem(item)

    def edit_single_position(self, group_name):
        """Edit single position for LOGIN_POS, HOME_POS, CALIBRATION_POS"""
        position_widget = self.position_lists[group_name]
        current_text = position_widget.text()

        # Try to parse the current position
        try:
            # Remove brackets and split by comma
            position_str = current_text.strip("[]")
            position_values = [float(x.strip()) for x in position_str.split(",")]

            # Format the position for editing (one value per line for easier editing)
            formatted_position = "\n".join([f"{i}: {val}" for i, val in enumerate(position_values)])

        except:
            # If parsing fails, just use the raw text
            formatted_position = current_text

        # Show input dialog for editing
        new_text, ok = QInputDialog.getMultiLineText(
            self,
            f"Edit {group_name}",
            "Edit position values (format: 0: x, 1: y, 2: z, 3: rx, 4: ry, 5: rz):",
            formatted_position
        )

        if ok and new_text.strip():
            try:
                # Parse the edited text back to position format
                lines = new_text.strip().split('\n')
                new_values = []

                for line in lines:
                    if ':' in line:
                        # Extract value after the colon
                        value = float(line.split(':', 1)[1].strip())
                        new_values.append(value)
                    else:
                        # If no colon, try to parse as direct number
                        new_values.append(float(line.strip()))

                # Update the position display with the new position
                position_widget.setText(str(new_values))
                print(f"Updated {group_name}: {new_values}")

            except ValueError as e:
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    f"Could not parse the position values. Please ensure all values are valid numbers.\nError: {str(e)}"
                )

    def set_current_position(self, group_name):
        """Set current robot position for single position groups"""
        print("Getting current robot position...")
        # Here you would typically get the current robot position
        mock_position = [0, 0, 0, 0, 0, 0]  # Mock position for demonstration

        position_widget = self.position_lists[group_name]
        position_widget.setText(str(mock_position))
        print(f"Set current position for {group_name}: {mock_position}")

    def move_to_single_position(self, group_name):
        """Move to single position for LOGIN_POS, HOME_POS, CALIBRATION_POS"""
        position_widget = self.position_lists[group_name]
        position_text = position_widget.text()

        if position_text.strip():
            # Get velocity and acceleration if available for this group
            vel_acc_info = ""
            if group_name in self.velocity_acceleration_widgets:
                vel = self.velocity_acceleration_widgets[group_name]["velocity"].value()
                acc = self.velocity_acceleration_widgets[group_name]["acceleration"].value()
                vel_acc_info = f" (Velocity: {vel}, Acceleration: {acc})"

            print(f"Moving to {group_name}: {position_text}{vel_acc_info}")
        else:
            QMessageBox.information(self, "No Position", f"No position set for {group_name}.")

    def add_point(self, group_name):
        """Add a new point to the specified group"""
        print("Getting current robot position...")
        # Here you would typically get the current robot position
        mock_position = [0, 0, 0, 0, 0, 0]  # Mock position for demonstration

        # Add to the list widget
        list_widget = self.position_lists[group_name]
        item = QListWidgetItem(str(mock_position))
        list_widget.addItem(item)

    def edit_point(self, group_name):
        """Edit selected point in the specified group"""
        list_widget = self.position_lists[group_name]
        current_item = list_widget.currentItem()
        if current_item:
            current_text = current_item.text()

            # Try to parse the current position
            try:
                # Remove brackets and split by comma
                position_str = current_text.strip("[]")
                position_values = [float(x.strip()) for x in position_str.split(",")]

                # Format the position for editing (one value per line for easier editing)
                formatted_position = "\n".join([f"{i}: {val}" for i, val in enumerate(position_values)])

            except:
                # If parsing fails, just use the raw text
                formatted_position = current_text

            # Show input dialog for editing
            new_text, ok = QInputDialog.getMultiLineText(
                self,
                f"Edit Point in {group_name}",
                "Edit position values (format: 0: x, 1: y, 2: z, 3: rx, 4: ry, 5: rz):",
                formatted_position
            )

            if ok and new_text.strip():
                try:
                    # Parse the edited text back to position format
                    lines = new_text.strip().split('\n')
                    new_values = []

                    for line in lines:
                        if ':' in line:
                            # Extract value after the colon
                            value = float(line.split(':', 1)[1].strip())
                            new_values.append(value)
                        else:
                            # If no colon, try to parse as direct number
                            new_values.append(float(line.strip()))

                    # Update the list item with the new position
                    current_item.setText(str(new_values))
                    print(f"Updated point in {group_name}: {new_values}")

                except ValueError as e:
                    QMessageBox.warning(
                        self,
                        "Invalid Input",
                        f"Could not parse the position values. Please ensure all values are valid numbers.\nError: {str(e)}"
                    )
        else:
            QMessageBox.information(self, "No Selection", "Please select a point to edit.")

    def remove_point(self, group_name):
        """Remove selected point from the specified group"""
        list_widget = self.position_lists[group_name]
        current_item = list_widget.currentItem()
        if current_item:
            row = list_widget.row(current_item)
            list_widget.takeItem(row)
        else:
            QMessageBox.information(self, "No Selection", "Please select a point to remove.")

    def move_to_point(self, group_name):
        """Move to selected point in the specified group"""
        list_widget = self.position_lists[group_name]
        current_item = list_widget.currentItem()
        if current_item:
            point_name = current_item.text()
            # Get velocity and acceleration if available for this group
            vel_acc_info = ""
            if group_name in self.velocity_acceleration_widgets:
                vel = self.velocity_acceleration_widgets[group_name]["velocity"].value()
                acc = self.velocity_acceleration_widgets[group_name]["acceleration"].value()
                vel_acc_info = f" (Velocity: {vel}, Acceleration: {acc})"

            print(f"Moving to point: {point_name} in group: {group_name}{vel_acc_info}")
        else:
            QMessageBox.information(self, "No Selection", "Please select a point to move to.")

    def save(self):
        """Save all configuration data"""
        data_out = {
            "ROBOT_IP": self.ip_edit.text(),
            "ROBOT_TOOL": self.tool_edit.value(),
            "ROBOT_USER": self.user_edit.value(),
            "MOVEMENT_GROUPS": {}
        }

        # Save each movement group's data
        for group_name, widget in self.position_lists.items():
            group_data = {}

            # Handle single position groups
            if isinstance(widget, QLineEdit):
                position_text = widget.text().strip()
                if position_text:
                    group_data["position"] = position_text
            # Handle multi-position groups
            elif isinstance(widget, QListWidget):
                group_data["points"] = []
                # Get all points from the list
                for i in range(widget.count()):
                    item = widget.item(i)
                    group_data["points"].append(item.text())

            data_out["MOVEMENT_GROUPS"][group_name] = group_data

        # Add velocity/acceleration data for all groups that have it
        for group_name, widgets in self.velocity_acceleration_widgets.items():
            if group_name not in data_out["MOVEMENT_GROUPS"]:
                data_out["MOVEMENT_GROUPS"][group_name] = {}

            data_out["MOVEMENT_GROUPS"][group_name]["velocity"] = widgets["velocity"].value()
            data_out["MOVEMENT_GROUPS"][group_name]["acceleration"] = widgets["acceleration"].value()

        QMessageBox.information(self, "Saved Data", str(data_out))

    def reset(self):
        """Reset all data to defaults"""
        # Reset robot info
        self.ip_edit.setText("192.168.58.2")
        self.tool_edit.setValue(0)
        self.user_edit.setValue(0)

        # Clear all position displays and lists
        for widget in self.position_lists.values():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QListWidget):
                widget.clear()

        # Reset velocity/acceleration to defaults
        defaults = {
            "JOG": {"velocity": 20, "acceleration": 100},
            "NOZZLE CLEAN": {"velocity": 30, "acceleration": 30},
            "TOOL CHANGER": {"velocity": 100, "acceleration": 30},
            "LOGIN_POS": {"velocity": 0, "acceleration": 0},
            "HOME_POS": {"velocity": 0, "acceleration": 0},
            "CALIBRATION_POS": {"velocity": 0, "acceleration": 0},
        }

        for group_name, widgets in self.velocity_acceleration_widgets.items():
            if group_name in defaults:
                widgets["velocity"].setValue(defaults[group_name]["velocity"])
                widgets["acceleration"].setValue(defaults[group_name]["acceleration"])

        # Reload default position data
        self.load_default_data()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RobotConfigUI()
    window.show()
    sys.exit(app.exec())
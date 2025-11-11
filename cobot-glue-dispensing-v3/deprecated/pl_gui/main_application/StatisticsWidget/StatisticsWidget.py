import sys
import json
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QGroupBox, QGridLayout, QPushButton, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# Import your Statistics class
from GlueDispensingApplication.Statistics import *


class DataDisplayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('System Data Monitor')
        self.setGeometry(100, 100, 600, 500)

        # Main layout
        main_layout = QVBoxLayout()

        # Title
        title = QLabel('System Status Monitor')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Generator section
        generator_group = QGroupBox("Generator")
        generator_layout = QHBoxLayout()
        self.generator_label = QLabel("Runtime: 0.00 seconds")

        # Generator checkbox for reset selection
        self.generator_checkbox = QCheckBox("Select for reset")
        generator_layout.addWidget(self.generator_label)
        generator_layout.addWidget(self.generator_checkbox)
        generator_group.setLayout(generator_layout)
        main_layout.addWidget(generator_group)

        # Pumps section
        pumps_group = QGroupBox("Pumps Status")
        pumps_layout = QGridLayout()

        # Headers
        pumps_layout.addWidget(QLabel("Pump"), 0, 0)
        pumps_layout.addWidget(QLabel("Runtime (s)"), 0, 1)
        pumps_layout.addWidget(QLabel("RPM"), 0, 2)
        pumps_layout.addWidget(QLabel("Relay Clicks"), 0, 3)
        pumps_layout.addWidget(QLabel("Reset Select"), 0, 4)

        # Pump data labels and checkboxes
        self.pump_labels = {}
        self.pump_checkboxes = {}
        for i in range(1, 5):
            pumps_layout.addWidget(QLabel(f"Pump {i}"), i, 0)
            self.pump_labels[f'runtime_{i}'] = QLabel("0.00")
            self.pump_labels[f'rpm_{i}'] = QLabel("0")
            self.pump_labels[f'clicks_{i}'] = QLabel("0")

            pumps_layout.addWidget(self.pump_labels[f'runtime_{i}'], i, 1)
            pumps_layout.addWidget(self.pump_labels[f'rpm_{i}'], i, 2)
            pumps_layout.addWidget(self.pump_labels[f'clicks_{i}'], i, 3)

            # Checkbox for each pump
            self.pump_checkboxes[i] = QCheckBox()
            pumps_layout.addWidget(self.pump_checkboxes[i], i, 4)

        pumps_group.setLayout(pumps_layout)
        main_layout.addWidget(pumps_group)

        # Individual pump data section
        individual_group = QGroupBox("Individual Pump Data")
        individual_layout = QGridLayout()
        individual_layout.addWidget(QLabel("Pump 1 Runtime:"), 0, 0)
        self.individual_runtime = QLabel("0.00 seconds")
        individual_layout.addWidget(self.individual_runtime, 0, 1)

        individual_layout.addWidget(QLabel("Pump 1 RPM:"), 1, 0)
        self.individual_rpm = QLabel("0")
        individual_layout.addWidget(self.individual_rpm, 1, 1)

        # Checkbox for individual pump data
        self.individual_checkbox = QCheckBox("Select for reset")
        individual_layout.addWidget(self.individual_checkbox, 0, 2, 2, 1)

        individual_group.setLayout(individual_layout)
        main_layout.addWidget(individual_group)

        # Control buttons section
        controls_layout = QHBoxLayout()

        # Select/Deselect all buttons
        select_all_button = QPushButton("Select All")
        select_all_button.clicked.connect(self.select_all_checkboxes)
        controls_layout.addWidget(select_all_button)

        deselect_all_button = QPushButton("Deselect All")
        deselect_all_button.clicked.connect(self.deselect_all_checkboxes)
        controls_layout.addWidget(deselect_all_button)

        # Reset button
        reset_button = QPushButton("Reset Selected")
        reset_button.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; font-weight: bold; }")
        reset_button.clicked.connect(self.reset_selected_statistics)
        controls_layout.addWidget(reset_button)

        # Refresh button
        refresh_button = QPushButton("Refresh Data")
        refresh_button.clicked.connect(self.load_data_from_statistics)
        controls_layout.addWidget(refresh_button)

        main_layout.addWidget(QLabel())  # Spacer
        main_layout.addLayout(controls_layout)

        self.setLayout(main_layout)

        # Set up auto-refresh timer (updates every 1 second)
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data_from_statistics)
        self.timer.start(1000)  # 1000ms = 1 second

        # Load initial data
        self.load_data_from_statistics()

    def select_all_checkboxes(self):
        """Select all checkboxes for reset"""
        self.generator_checkbox.setChecked(True)
        for i in range(1, 5):
            self.pump_checkboxes[i].setChecked(True)
        self.individual_checkbox.setChecked(True)

    def deselect_all_checkboxes(self):
        """Deselect all checkboxes"""
        self.generator_checkbox.setChecked(False)
        for i in range(1, 5):
            self.pump_checkboxes[i].setChecked(False)
        self.individual_checkbox.setChecked(False)

    def reset_selected_statistics(self):
        """Reset the selected statistics to zero"""
        selected_items = []

        # Check which items are selected
        if self.generator_checkbox.isChecked():
            selected_items.append("Generator runtime")

        for i in range(1, 5):
            if self.pump_checkboxes[i].isChecked():
                selected_items.append(f"Pump {i} (runtime, RPM, relay clicks)")

        if self.individual_checkbox.isChecked():
            selected_items.append("Individual Pump 1 data")

        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select at least one item to reset.")
            return

        # Show confirmation dialog
        selected_text = "\n• ".join(selected_items)
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            f"Are you sure you want to reset the following statistics to zero?\n\n• {selected_text}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Get current statistics
                current_stats = Statistics.get_statistics()

                # Reset selected items
                if self.generator_checkbox.isChecked():
                    current_stats["generator_on_seconds"] = 0

                for i in range(1, 5):
                    if self.pump_checkboxes[i].isChecked():
                        pump_id = str(i)
                        # Reset in nested structure if exists
                        if "pump_on_seconds" in current_stats and isinstance(current_stats["pump_on_seconds"], dict):
                            current_stats["pump_on_seconds"][pump_id] = 0
                        if "pump_rpm" in current_stats and isinstance(current_stats["pump_rpm"], dict):
                            current_stats["pump_rpm"][pump_id] = 0
                        if "relays_click" in current_stats and isinstance(current_stats["relays_click"], dict):
                            current_stats["relays_click"][pump_id] = 0

                        # Also reset flattened keys
                        current_stats[f"pump_on_seconds_{pump_id}"] = 0
                        current_stats[f"pump_rpm_{pump_id}"] = 0
                        current_stats[f"relays_click_{pump_id}"] = 0

                if self.individual_checkbox.isChecked():
                    current_stats["pump_on_seconds_1"] = 0
                    current_stats["pump_rpm_1"] = 0

                # Update the statistics file
                Statistics.update_statistics(current_stats)

                # Refresh the display
                self.load_data_from_statistics()

                # Show success message
                QMessageBox.information(self, "Reset Complete", "Selected statistics have been reset to zero.")

                # Deselect all checkboxes after successful reset
                self.deselect_all_checkboxes()

            except Exception as e:
                QMessageBox.critical(self, "Reset Error", f"Failed to reset statistics:\n{str(e)}")

    def load_data_from_statistics(self):
        """Load data from Statistics class and update display"""
        try:
            # Get raw statistics
            raw_stats = Statistics.get_statistics()

            # Convert to the format expected by update_data
            data = {
                "generator_on_seconds": raw_stats.get("generator_on_seconds", 0),
                "pump_on_seconds": {},
                "pump_rpm": {},
                "relays_click": {},
                "pump_on_seconds_1": raw_stats.get("pump_on_seconds_1", 0),
                "pump_rpm_1": raw_stats.get("pump_rpm_1", 0)
            }

            # Handle nested pump data
            for i in range(1, 5):
                pump_id = str(i)
                # Try to get from nested structure first, then from flattened keys
                if "pump_on_seconds" in raw_stats and isinstance(raw_stats["pump_on_seconds"], dict):
                    data["pump_on_seconds"][pump_id] = raw_stats["pump_on_seconds"].get(pump_id, 0)
                else:
                    data["pump_on_seconds"][pump_id] = raw_stats.get(f"pump_on_seconds_{pump_id}", 0)

                if "pump_rpm" in raw_stats and isinstance(raw_stats["pump_rpm"], dict):
                    data["pump_rpm"][pump_id] = raw_stats["pump_rpm"].get(pump_id, 0)
                else:
                    data["pump_rpm"][pump_id] = raw_stats.get(f"pump_rpm_{pump_id}", 0)

                if "relays_click" in raw_stats and isinstance(raw_stats["relays_click"], dict):
                    data["relays_click"][pump_id] = raw_stats["relays_click"].get(pump_id, 0)
                else:
                    data["relays_click"][pump_id] = raw_stats.get(f"relays_click_{pump_id}", 0)

            # Update the display
            self.update_data(data)

        except Exception as e:
            print(f"Error loading statistics: {e}")
            # Set default values on error
            default_data = {
                "generator_on_seconds": 0,
                "pump_on_seconds": {"1": 0, "2": 0, "3": 0, "4": 0},
                "pump_rpm": {"1": 0, "2": 0, "3": 0, "4": 0},
                "relays_click": {"1": 0, "2": 0, "3": 0, "4": 0},
                "pump_on_seconds_1": 0,
                "pump_rpm_1": 0
            }
            self.update_data(default_data)

    def update_data(self, data):
        """Update the widget with new data"""
        # Update generator
        self.generator_label.setText(f"Runtime: {data['generator_on_seconds']:.2f} seconds")

        # Update pumps
        for i in range(1, 5):
            pump_key = str(i)
            runtime = data['pump_on_seconds'].get(pump_key, 0)
            rpm = data['pump_rpm'].get(pump_key, 0)
            clicks = data['relays_click'].get(pump_key, 0)

            self.pump_labels[f'runtime_{i}'].setText(f"{runtime:.2f}")
            self.pump_labels[f'rpm_{i}'].setText(str(rpm))
            self.pump_labels[f'clicks_{i}'].setText(str(clicks))

        # Update individual pump data
        self.individual_runtime.setText(f"{data['pump_on_seconds_1']:.2f} seconds")
        self.individual_rpm.setText(str(data['pump_rpm_1']))


def main():
    app = QApplication(sys.argv)
    widget = DataDisplayWidget()
    widget.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
import sys
import requests
from enum import Enum

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QScroller
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QApplication, QHBoxLayout,
                             QSizePolicy, QComboBox,
                             QScrollArea, QGroupBox, QGridLayout, QPushButton)
from src.frontend.pl_ui.ui.widgets.MaterialButton import MaterialButton
from src.frontend.pl_ui.localization import TranslationKeys, get_app_translator
from src.frontend.pl_ui.ui.widgets.SwitchButton import QToggle
from src.frontend.pl_ui.ui.widgets.ToastWidget import ToastWidget
from src.frontend.pl_ui.ui.windows.settings.BaseSettingsTabLayout import BaseSettingsTabLayout
from src.backend.system.tools.GlueCell import GlueCellsManagerSingleton, GlueDataFetcher, GlueType
import random
import json
from pathlib import Path
from modules.shared.MessageBroker import MessageBroker

class LoadCellsSettingsTabLayout(BaseSettingsTabLayout, QVBoxLayout):
    def __init__(self, parent_widget=None):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)
        print(f"Initializing {self.__class__.__name__} with parent widget: {parent_widget}")

        self.current_cell = 1  # Currently selected cell (1, 2, or 3)
        self.parent_widget = parent_widget
        self.translator = get_app_translator()
        self.translator.language_changed.connect(self.translate)
        
        # Initialize GlueCell components and message broker
        try:
            self.glue_cells_manager = GlueCellsManagerSingleton.get_instance()
            self.glue_data_fetcher = GlueDataFetcher()
            self.glue_data_fetcher.start()  # Start the data fetching thread
            self.use_real_data = True
            
            # Initialize message broker and subscribe to weight topics
            self.broker = MessageBroker()
            self.broker.subscribe("GlueMeter_1/VALUE", self._on_weight1_updated)
            self.broker.subscribe("GlueMeter_2/VALUE", self._on_weight2_updated)
            self.broker.subscribe("GlueMeter_3/VALUE", self._on_weight3_updated)
            print("Subscribed to GlueMeter weight topics")
            
        except Exception as e:
            print(f"Failed to initialize glue cell system: {e}")
            self.glue_cells_manager = None
            self.glue_data_fetcher = None
            self.use_real_data = False
            self.broker = None
        
        # Load configuration values
        # Current file is in pl_ui/ui/windows/settings/, need to go up to project root
        self.config_path = Path(__file__).parent.parent.parent.parent.parent / "system" / "storage" / "glueCells" / "glue_cell_config.json"
        self.load_config()

        self.create_main_content()

        # Connect to parent widget resize events if possible (like CalibrationSettingsTab does)
        if self.parent_widget:
            self.parent_widget.resizeEvent = self.on_parent_resize

        # Connect value change signals to auto-save
        self._connect_auto_save_signals()

    def __del__(self):
        """Cleanup when the widget is destroyed"""
        self._cleanup_message_broker()

    def _cleanup_message_broker(self):
        """Unsubscribe from message broker topics to prevent errors after widget destruction"""
        try:
            if hasattr(self, 'broker') and self.broker:
                self.broker.unsubscribe("GlueMeter_1/VALUE", self._on_weight1_updated)
                self.broker.unsubscribe("GlueMeter_2/VALUE", self._on_weight2_updated)
                self.broker.unsubscribe("GlueMeter_3/VALUE", self._on_weight3_updated)
                print("Unsubscribed from GlueMeter weight topics")
        except Exception as e:
            print(f"Error during message broker cleanup: {e}")

    def translate(self):
        """Update UI text based on current language"""
        self.setup_styling()
        
        # Update cell selection group
        if hasattr(self, 'cell_selection_group'):
            self.cell_selection_group.setTitle("Load Cell Selection")
            
        # Update calibration group
        if hasattr(self, 'calibration_group'):
            self.calibration_group.setTitle("Calibration Settings")
            
        # Update measurement group
        if hasattr(self, 'measurement_group'):
            self.measurement_group.setTitle("Measurement Settings")
            
        # Update monitoring group
        if hasattr(self, 'monitoring_group'):
            self.monitoring_group.setTitle("Real-time Monitoring")
    
    def on_parent_resize(self, event):
        """Handle parent widget resize events"""
        if hasattr(super(QWidget, self.parent_widget), 'resizeEvent'):
            super(QWidget, self.parent_widget).resizeEvent(event)

    def create_main_content(self):
        """Create the main scrollable content area with responsive layout"""
        # Since this is now a QVBoxLayout, we add directly to self
        self.setContentsMargins(0, 0, 0, 0)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        QScroller.grabGesture(scroll_area.viewport(), QScroller.ScrollerGestureType.TouchGesture)

        # Create main content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Add cell selection at the top
        self.add_cell_selection_group(content_layout)

        # Add settings groups
        self.add_settings_desktop(content_layout)

        # Add monitoring group
        self.add_monitoring_group(content_layout)

        # Add control buttons
        self.add_control_buttons_group(content_layout)

        # Add stretch at the end
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)

        # Add scroll area to this layout
        self.addWidget(scroll_area)

    def add_cell_selection_group(self, parent_layout):
        """Add cell selection dropdown group"""
        group = QGroupBox("Load Cell Selection")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)
        
        self.cell_selection_group = group

        # Cell selection dropdown
        row = 0
        label = QLabel("Select Load Cell:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.cell_dropdown = QComboBox()
        self.cell_dropdown.setMinimumHeight(40)
        self.cell_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cell_dropdown.addItems(["Load Cell 1", "Load Cell 2", "Load Cell 3"])
        self.cell_dropdown.setCurrentIndex(0)
        self.cell_dropdown.currentIndexChanged.connect(self.on_cell_changed)
        layout.addWidget(self.cell_dropdown, row, 1)

        # Cell status indicator
        row += 1
        label = QLabel("Status:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.cell_status_label = QLabel("Connected")
        self.cell_status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        layout.addWidget(self.cell_status_label, row, 1)

        layout.setColumnStretch(1, 1)
        parent_layout.addWidget(group)

    def add_settings_desktop(self, parent_layout):
        """Add settings in desktop layout"""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(15)

        groups = self.create_settings_control_groups()

        for group in groups:
            row_layout.addWidget(group)

        parent_layout.addLayout(row_layout)

    def create_settings_control_groups(self):
        """Create all settings groups"""
        connection_group = self.create_connection_settings_group()
        calibration_group = self.create_calibration_settings_group()
        measurement_group = self.create_measurement_settings_group()
        
        return [connection_group, calibration_group, measurement_group]

    def create_connection_settings_group(self):
        """Create connection and hardware-related settings group"""
        group = QGroupBox("Connection & Hardware Settings")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.connection_group = group

        # Mode Toggle (Test/Production)
        row = 0
        label = QLabel("Mode:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)

        mode_layout = QHBoxLayout()
        self.mode_label = QLabel("Production")
        self.mode_label.setStyleSheet("QLabel { font-weight: bold; color: #2E8B57; }")
        self.mode_toggle = QToggle()

        # Load current mode from config
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
                current_mode = config_data.get("MODE", "production")
                if current_mode == "test":
                    self.mode_toggle.setChecked(True)
                    self.mode_label.setText("Test (Mock Server)")
                    self.mode_label.setStyleSheet("QLabel { font-weight: bold; color: #FF8C00; }")
                else:
                    self.mode_toggle.setChecked(False)
                    self.mode_label.setText("Production")
                    self.mode_label.setStyleSheet("QLabel { font-weight: bold; color: #2E8B57; }")
        except Exception as e:
            print(f"Error loading mode: {e}")

        self.mode_toggle.stateChanged.connect(self.on_mode_changed)

        mode_layout.addWidget(self.mode_label)
        mode_layout.addWidget(self.mode_toggle)
        mode_layout.addStretch()

        layout.addLayout(mode_layout, row, 1)

        # Glue Type
        row += 1
        label = QLabel("Glue Type:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.glue_type_dropdown = QComboBox()
        self.glue_type_dropdown.setMinimumHeight(40)
        self.glue_type_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Populate with available glue types from config
        available_types = getattr(self, 'available_glue_types', ["TypeA", "TypeB", "TypeC", "TypeD"])
        self.glue_type_dropdown.addItems(available_types)
        layout.addWidget(self.glue_type_dropdown, row, 1)

        # Capacity
        row += 1
        label = QLabel("Capacity:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.capacity_input = self.create_spinbox(100, 50000, 10000, " g")
        layout.addWidget(self.capacity_input, row, 1)

        # URL
        row += 1
        label = QLabel("URL:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        from PyQt6.QtWidgets import QLineEdit
        self.url_input = QLineEdit("http://192.168.222.143/weight1")
        self.url_input.setMinimumHeight(40)
        layout.addWidget(self.url_input, row, 1)

        # IP Address (extracted from URL)
        row += 1
        label = QLabel("IP Address:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.ip_address_label = QLabel("192.168.222.143")
        self.ip_address_label.setStyleSheet("QLabel { font-family: monospace; color: #555555; }")
        layout.addWidget(self.ip_address_label, row, 1)

        # Fetch Timeout
        row += 1
        label = QLabel("Fetch Timeout:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.fetch_timeout_input = self.create_spinbox(1, 30, 5, " seconds")
        layout.addWidget(self.fetch_timeout_input, row, 1)

        # Connect URL change to IP update
        self.url_input.textChanged.connect(self.update_ip_from_url)

        layout.setColumnStretch(1, 1)
        return group

    def update_ip_from_url(self):
        """Extract and display IP address from URL"""
        try:
            url = self.url_input.text()
            # Extract IP from URL (e.g., "http://192.168.222.143/weight1" -> "192.168.222.143")
            if "://" in url:
                url_part = url.split("://")[1]
                if "/" in url_part:
                    ip = url_part.split("/")[0]
                else:
                    ip = url_part
                self.ip_address_label.setText(ip)
            else:
                self.ip_address_label.setText("Invalid URL")
        except Exception as e:
            self.ip_address_label.setText("Error parsing URL")

    def create_calibration_settings_group(self):
        """Create calibration-related settings group (loads current values from backend)"""
        group = QGroupBox("Calibration Settings")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.calibration_group = group

        # --- Fetch current config ---
        current_cell = getattr(self, "current_cell", None)
        calibration = self.fetch_calibration_config(current_cell)
        offset_val = float(calibration.get("offset"))
        scale_val = float(calibration.get("scale"))

        # --- Zero Offset ---
        row = 0
        label = QLabel("Zero Offset:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        print(f"Creating zero offset input with value: {offset_val}")
        self.zero_offset_input = self.create_double_spinbox(-100000000.0, 100000000.0, offset_val, " g")
        layout.addWidget(self.zero_offset_input, row, 1)

        # --- Scale Factor ---
        row += 1
        label = QLabel("Scale Factor:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        print(f"Creating zero Scale input with value: {scale_val}")
        self.scale_factor_input = self.create_double_spinbox(0.001, 1000.0, scale_val, " units")
        layout.addWidget(self.scale_factor_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    # def create_calibration_settings_group(self):
    #     """Create calibration-related settings group"""
    #     group = QGroupBox("Calibration Settings")
    #     layout = QGridLayout(group)
    #     layout.setSpacing(15)
    #     layout.setContentsMargins(20, 25, 20, 20)
    #
    #     self.calibration_group = group
    #
    #     # Zero Offset
    #     row = 0
    #     label = QLabel("Zero Offset:")
    #     label.setWordWrap(True)
    #     layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    #     self.zero_offset_input = self.create_double_spinbox(-1000.0, 1000.0, 0.0, " g")
    #     layout.addWidget(self.zero_offset_input, row, 1)
    #
    #     # Scale Factor
    #     row += 1
    #     label = QLabel("Scale Factor:")
    #     label.setWordWrap(True)
    #     layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
    #     self.scale_factor_input = self.create_double_spinbox(0.001, 10.0, 1.0, " g/unit")
    #     layout.addWidget(self.scale_factor_input, row, 1)
    #
    #     layout.setColumnStretch(1, 1)
    #     return group

    def create_measurement_settings_group(self):
        """Create measurement-related settings group"""
        group = QGroupBox("Measurement Settings")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.measurement_group = group

        # Sampling Rate
        row = 0
        label = QLabel("Sampling Rate:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.sampling_rate_input = self.create_spinbox(1, 1000, 10, " Hz")
        layout.addWidget(self.sampling_rate_input, row, 1)

        # Filter Cutoff Frequency
        row += 1
        label = QLabel("Filter Cutoff:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.filter_cutoff_input = self.create_double_spinbox(0.1, 100.0, 5.0, " Hz")
        layout.addWidget(self.filter_cutoff_input, row, 1)

        # Averaging Samples
        row += 1
        label = QLabel("Averaging Samples:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.averaging_samples_input = self.create_spinbox(1, 100, 5, " samples")
        layout.addWidget(self.averaging_samples_input, row, 1)

        # Min Weight Threshold
        row += 1
        label = QLabel("Min Weight Threshold:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.min_weight_threshold_input = self.create_double_spinbox(0.0, 100.0, 0.1, " g")
        layout.addWidget(self.min_weight_threshold_input, row, 1)

        # Max Weight Threshold
        row += 1
        label = QLabel("Max Weight Threshold:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.max_weight_threshold_input = self.create_double_spinbox(0.0, 10000.0, 1000.0, " g")
        layout.addWidget(self.max_weight_threshold_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def add_monitoring_group(self, parent_layout):
        """Add real-time monitoring group"""
        group = QGroupBox("Real-time Monitoring")
        layout = QGridLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        self.monitoring_group = group

        # Current Weight Display
        row = 0
        label = QLabel("Current Weight:")
        label.setWordWrap(True)
        label.setStyleSheet("QLabel { font-size: 14px; font-weight: bold; }")
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.current_weight_label = QLabel("0.00 g")
        self.current_weight_label.setStyleSheet("""
            QLabel { 
                font-size: 18px; 
                font-weight: bold; 
                color: #2E8B57; 
                background-color: #F0F8F0; 
                border: 2px solid #90EE90;
                border-radius: 8px;
                padding: 10px;
                min-height: 30px;
            }
        """)
        layout.addWidget(self.current_weight_label, row, 1)

        layout.setColumnStretch(1, 1)
        parent_layout.addWidget(group)

    def add_control_buttons_group(self, parent_layout):
        """Add control buttons group"""
        group = QGroupBox("Load Cell Controls")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Tare button
        tare_button = MaterialButton("Tare (Zero)")
        tare_button.setMinimumHeight(35)
        tare_button.clicked.connect(self.tare_load_cell)
        layout.addWidget(tare_button)



        # Reset button
        reset_button = MaterialButton("Reset Settings")
        reset_button.setMinimumHeight(35)
        reset_button.clicked.connect(self.reset_settings)
        layout.addWidget(reset_button)

        parent_layout.addWidget(group)

    # def on_cell_changed(self, index):
    #     """Handle cell selection change"""
    #     self.current_cell = index + 1
    #     self.update_cell_settings()
    #     self.showToast(f"Switched to Load Cell {self.current_cell}")

    def on_cell_changed(self, index):
        """Handle cell selection change"""
        self.current_cell = index + 1
        self.update_cell_settings()
        print(f"Cell changed to {self.current_cell}, fetching calibration...")
        # Fetch latest calibration from device in background and apply to UI when ready

        cal = self.fetch_calibration_config(self.current_cell)
        # Parse values here so the closure doesn't depend on 'cal' later
        offset_val = float(cal.get("offset", 0.0))
        scale_val = float(cal.get("scale", 1.0))
        cell_id = self.current_cell

        # Ensure we apply values only if the UI still represents the same cell
        if cell_id != getattr(self, "current_cell", None):
            print(f"Skipping apply: UI switched to cell {self.current_cell} before calibration applied")
            return

        if hasattr(self, "zero_offset_input"):
            self.zero_offset_input.setValue(offset_val)
        if hasattr(self, "scale_factor_input"):
            self.scale_factor_input.setValue(scale_val)
        self.showToast(f"Loaded calibration for Load Cell {cell_id}")



        self.showToast(f"Switched to Load Cell {self.current_cell}")

    def on_mode_changed(self, state):
        """Handle mode toggle change"""
        try:
            # Read current config
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)

            # Update mode based on toggle state
            if state:  # Toggle is ON = Test mode
                config_data["MODE"] = "test"
                self.mode_label.setText("Test (Mock Server)")
                self.mode_label.setStyleSheet("QLabel { font-weight: bold; color: #FF8C00; }")
                print("[Mode] Switched to TEST mode - reloading configuration now...")
            else:  # Toggle is OFF = Production mode
                config_data["MODE"] = "production"
                self.mode_label.setText("Production")
                self.mode_label.setStyleSheet("QLabel { font-weight: bold; color: #2E8B57; }")
                print("[Mode] Switched to PRODUCTION mode - reloading configuration now...")

            # Save config
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)

            # Reload the data fetcher with new configuration
            if self.glue_data_fetcher:
                self.glue_data_fetcher.reload_config()
                self.showToast("Mode switched - Configuration reloaded successfully")
            else:
                self.showToast("Mode switched - Restart required for changes to take effect")

        except Exception as e:
            print(f"Error changing mode: {e}")
            self.showToast(f"Error changing mode: {e}")

    def load_config(self):
        """Load configuration from the glue cell config file"""
        self.cell_configs = {}
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                print(f"Loaded config from {self.config_path}")
                # Print loaded config for debugging
                print(json.dumps(config_data, indent=2))
                # Load global configuration values from file
                self.default_capacity = config_data.get("GLUE_CELL_CAPACITY", 10000)
                self.base_url = config_data.get("BASE_URL", "http://192.168.222.143")
                self.weights_endpoint = config_data.get("WEIGHTS_ENDPOINT", "/weights")
                self.default_fetch_timeout = config_data.get("FETCH_TIMEOUT", 5)
                self.data_fetch_interval_ms = config_data.get("DATA_FETCH_INTERVAL_MS", 100)
                self.update_interval_ms = config_data.get("UI_UPDATE_INTERVAL_MS", 500)
                self.available_glue_types = config_data.get("AVAILABLE_GLUE_TYPES", ["TypeA", "TypeB", "TypeC", "TypeD"])
                
                # Load default settings from config
                default_calibration = config_data.get("DEFAULT_CALIBRATION", {})
                default_measurement = config_data.get("DEFAULT_MEASUREMENT", {})
                
                # Load individual cell configurations
                for cell_config in config_data.get("CELL_CONFIG", []):
                    cell_id = cell_config["id"]
                    
                    # Merge cell-specific calibration with defaults
                    cell_calibration = default_calibration.copy()
                    cell_calibration.update(cell_config.get("calibration", {}))
                    
                    # Merge cell-specific measurement with defaults
                    cell_measurement = default_measurement.copy()
                    cell_measurement.update(cell_config.get("measurement", {}))
                    
                    self.cell_configs[cell_id] = {
                        "id": cell_id,
                        "type": cell_config["type"],
                        "url": cell_config["url"],
                        "capacity": cell_config["capacity"],
                        "fetch_timeout": cell_config.get("fetch_timeout", self.default_fetch_timeout),
                        # Calibration settings from config
                        # "zero_offset": cell_calibration.get("zero_offset", 0.0),
                        # "scale_factor": cell_calibration.get("scale_factor", 1.0),
                        # Measurement settings from config
                        "sampling_rate": cell_measurement.get("sampling_rate", 10),
                        "filter_cutoff": cell_measurement.get("filter_cutoff", 5.0),
                        "averaging_samples": cell_measurement.get("averaging_samples", 5),
                        "min_weight_threshold": cell_measurement.get("min_weight_threshold", 0.1),
                        "max_weight_threshold": cell_config["capacity"]  # Use capacity as max threshold
                    }
                
            else:
                raise FileNotFoundError(f"Config file not found at {self.config_path}. Cannot initialize without configuration.")
                
        except Exception as e:
            print(f"Error loading config: {e}")
            raise RuntimeError(f"Failed to load configuration: {e}. System requires valid config file to operate.")

    def update_cell_settings(self):
        """Update settings display for the selected cell"""
        if self.current_cell in self.cell_configs:
            config = self.cell_configs[self.current_cell]
            
            # Update connection fields with real config values
            glue_type_index = self.glue_type_dropdown.findText(config["type"])
            if glue_type_index >= 0:
                self.glue_type_dropdown.setCurrentIndex(glue_type_index)
            
            self.capacity_input.setValue(config["capacity"])
            self.url_input.setText(config["url"])
            self.fetch_timeout_input.setValue(config.get("fetch_timeout", 5))
            
            # Update IP display from URL
            self.update_ip_from_url()
            
            # Update calibration and measurement fields with cell-specific values

            self.sampling_rate_input.setValue(config.get("sampling_rate", 10))
            self.filter_cutoff_input.setValue(config.get("filter_cutoff", 5.0))
            self.averaging_samples_input.setValue(config.get("averaging_samples", 5))
            self.min_weight_threshold_input.setValue(config.get("min_weight_threshold", 0.1))
            self.max_weight_threshold_input.setValue(config.get("max_weight_threshold", config["capacity"]))
            
            # Update cell info display
            cell_type_label = f"Load Cell {self.current_cell} ({config['type']})"
            self.cell_dropdown.setItemText(self.current_cell - 1, cell_type_label)
            
            # Update status based on real glue meter state if available
            status = "Disconnected"
            color = "red"
            
            if self.use_real_data and self.glue_cells_manager:
                try:
                    cell = self.glue_cells_manager.getCellById(self.current_cell)
                    if cell and cell.glueMeter:
                        meter_state = cell.glueMeter.getState()
                        if meter_state == "READY":
                            status = "Connected"
                            color = "green"
                        elif meter_state == "DISCONNECTED":
                            status = "Disconnected"
                            color = "red"
                        elif meter_state == "ERROR":
                            status = "Error"
                            color = "orange"
                        else:
                            status = meter_state
                            color = "blue"
                except Exception as e:
                    print(f"Error getting cell status: {e}")
            else:
                # Fallback status for demo
                if self.current_cell <= 2:
                    status = "Connected"
                    color = "green"
            
            self.cell_status_label.setText(status)
            self.cell_status_label.setStyleSheet(f"QLabel {{ color: {color}; font-weight: bold; }}")
        else:
            print(f"Cell {self.current_cell} not found in configuration")

    def update_weight_display(self):
        """Update the weight display with real or mock data"""
        current_weight = None
        
        # Try to get real weight data from GlueDataFetcher
        if self.use_real_data and self.glue_data_fetcher:
            try:
                if self.current_cell == 1:
                    current_weight = self.glue_data_fetcher.weight1
                elif self.current_cell == 2:
                    current_weight = self.glue_data_fetcher.weight2
                elif self.current_cell == 3:
                    current_weight = self.glue_data_fetcher.weight3
                    
                # Check if cell is connected by verifying we got valid data
                if current_weight is not None and current_weight != 0:
                    # Real data available
                    self.current_weight_label.setText(f"{current_weight:.2f} g")
                    

                    
                    # Update weight label styling based on thresholds
                    min_threshold = self.min_weight_threshold_input.value()
                    max_threshold = self.max_weight_threshold_input.value()
                    
                    if current_weight < min_threshold:
                        # Below minimum - red
                        self.current_weight_label.setStyleSheet("""
                            QLabel { 
                                font-size: 18px; 
                                font-weight: bold; 
                                color: #B22222; 
                                background-color: #FFE4E1; 
                                border: 2px solid #FF6B6B;
                                border-radius: 8px;
                                padding: 10px;
                                min-height: 30px;
                            }
                        """)
                    elif current_weight > max_threshold:
                        # Above maximum - orange
                        self.current_weight_label.setStyleSheet("""
                            QLabel { 
                                font-size: 18px; 
                                font-weight: bold; 
                                color: #FF8C00; 
                                background-color: #FFF8DC; 
                                border: 2px solid #FFD700;
                                border-radius: 8px;
                                padding: 10px;
                                min-height: 30px;
                            }
                        """)
                    else:
                        # Normal range - green
                        self.current_weight_label.setStyleSheet("""
                            QLabel { 
                                font-size: 18px; 
                                font-weight: bold; 
                                color: #2E8B57; 
                                background-color: #F0F8F0; 
                                border: 2px solid #90EE90;
                                border-radius: 8px;
                                padding: 10px;
                                min-height: 30px;
                            }
                        """)
                    return
                    
            except Exception as e:
                print(f"Error getting real weight data: {e}")
        
        # Fallback: Check if this cell should be disconnected based on status
        if self.current_cell in self.cell_configs:
            # Check cell status for disconnected state
            try:
                if self.use_real_data and self.glue_cells_manager:
                    cell = self.glue_cells_manager.getCellById(self.current_cell)
                    if cell and cell.glueMeter and cell.glueMeter.getState() != "READY":
                        # Cell is disconnected/error
                        self.current_weight_label.setText("-- g")

                        
                        # Set disconnected styling
                        self.current_weight_label.setStyleSheet("""
                            QLabel { 
                                font-size: 18px; 
                                font-weight: bold; 
                                color: #696969; 
                                background-color: #F5F5F5; 
                                border: 2px solid #D3D3D3;
                                border-radius: 8px;
                                padding: 10px;
                                min-height: 30px;
                            }
                        """)
                        return
            except Exception as e:
                print(f"Error checking cell status: {e}")
                
        # Generate mock data for connected cells when real data is not available
        config = self.cell_configs.get(self.current_cell, {})
        capacity = config.get("capacity", 1000)
        
        # Generate realistic mock weight based on cell type and capacity
        if config.get("type") == "TypeA":
            base_weight = capacity * 0.3  # 30% full
        elif config.get("type") == "TypeB":
            base_weight = capacity * 0.6  # 60% full  
        elif config.get("type") == "TypeC":
            base_weight = capacity * 0.8  # 80% full
        else:
            base_weight = capacity * 0.5  # 50% full
            
        weight_variation = random.uniform(-capacity * 0.02, capacity * 0.02)  # 2% variation
        current_weight = base_weight + weight_variation
        

        
        self.current_weight_label.setText(f"{current_weight:.2f} g")

        
        # Set normal styling for mock data
        self.current_weight_label.setStyleSheet("""
            QLabel { 
                font-size: 18px; 
                font-weight: bold; 
                color: #2E8B57; 
                background-color: #F0F8F0; 
                border: 2px solid #90EE90;
                border-radius: 8px;
                padding: 10px;
                min-height: 30px;
            }
        """)

    def fetch_calibration_config(self, load_cell_id: int):
        from src.backend.system.tools.GlueCell import GET_CONFIG_ENDPOINT
        """Fetch calibration settings (offset and scale) for the given load cell."""
        import requests

        if not self.glue_cells_manager or not hasattr(self.glue_cells_manager, 'config_data'):
            print("Error: Glue cells manager not available - cannot fetch calibration config")
            self.showToast("Error: Glue cells manager not available")
            return {"offset": 0.0, "scale": 1.0}  # safe fallback

        config = self.glue_cells_manager.config_data
        base_url = config.get("BASE_URL")
        timeout = config.get("FETCH_TIMEOUT", 5)

        endpoint = GET_CONFIG_ENDPOINT.format(current_cell=load_cell_id)
        url = f"{base_url}{endpoint}"

        print(f"Fetching calibration config from: {url}")
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                offset = data.get("offset", 0.0)
                scale = data.get("scale", 1.0)
                print(f"Calibration fetched: offset={offset}, scale={scale}")
                return {"offset": offset, "scale": scale}
            else:
                print(f"Failed to fetch calibration config: {response.status_code}")
                self.showToast(f"Fetch failed: {response.status_code}")
                return {"offset": 0.0, "scale": 1.0}
        except Exception as e:
            print(f"Error fetching calibration config: {e}")
            self.showToast(f"Calibration fetch error: {e}")
            return {"offset": 0.0, "scale": 1.0}

    def tare_load_cell(self):
        """Tare (zero) the selected load cell"""
        import requests
        from GlueDispensingApplication.tools.GlueCell import TARE_ENDPOINT
        print(f"Taring Load Cell {self.current_cell}...")
        self.showToast(f"Taring Load Cell {self.current_cell}...")
        try:
            # Get base URL from the already loaded configuration
            if self.glue_cells_manager and hasattr(self.glue_cells_manager, 'config_data'):
                config = self.glue_cells_manager.config_data
                base_url = config.get("BASE_URL")
                timeout = config.get("FETCH_TIMEOUT")
            else:
                print("Error: Glue cells manager not available - cannot perform tare operation")
                self.showToast("Error: Glue cells manager not available")
                return

            endpoint= TARE_ENDPOINT.format(current_cell=self.current_cell)
            url = f"{base_url}{endpoint}"

            print(f"Tare URL: {url}")
            response = requests.get(url, timeout=timeout)
            print(f"Tare response: {response.status_code}, {response.text}")
            if response.status_code == 200:
                calibration = self.fetch_calibration_config(self.current_cell)
                offset_val = float(calibration.get("offset"))

                self.zero_offset_input.setValue(offset_val)
                print(f"Load Cell {self.current_cell} tared successfully.")
                self.showToast(f"Load Cell {self.current_cell} tared successfully.")
            else:
                print(f"Tare failed with status code: {response.status_code}")
                self.showToast(f"Tare failed: {response.status_code}")
        except Exception as e:
            print(f"Error during tare: {e}")
            self.showToast(f"Tare error: {e}")

    def reset_settings(self):
        """Reset settings for the selected load cell"""
        self.showToast(f"Resetting Load Cell {self.current_cell} settings...")
        # Reset to default values
        self.zero_offset_input.setValue(0.0)
        self.scale_factor_input.setValue(1.0)
        self.sampling_rate_input.setValue(10)
        self.filter_cutoff_input.setValue(5.0)
        self.averaging_samples_input.setValue(5)
        self.min_weight_threshold_input.setValue(0.1)
        self.max_weight_threshold_input.setValue(1000.0)

    def connectValueChangeCallbacks(self, callback):
        """Connect value change signals to callback methods"""
        self.zero_offset_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_zero_offset", value, "LoadCellsSettingsTabLayout"))
        self.scale_factor_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_scale_factor", value, "LoadCellsSettingsTabLayout"))

        self.sampling_rate_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_sampling_rate", value, "LoadCellsSettingsTabLayout"))
        self.filter_cutoff_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_filter_cutoff", value, "LoadCellsSettingsTabLayout"))
        self.averaging_samples_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_averaging_samples", value, "LoadCellsSettingsTabLayout"))
        self.min_weight_threshold_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_min_weight_threshold", value, "LoadCellsSettingsTabLayout"))
        self.max_weight_threshold_input.valueChanged.connect(
            lambda value: callback(f"load_cell_{self.current_cell}_max_weight_threshold", value, "LoadCellsSettingsTabLayout"))

        self.cell_dropdown.currentIndexChanged.connect(
            lambda index: callback("selected_load_cell", index + 1, "LoadCellsSettingsTabLayout"))

    def getValues(self):
        """Returns a dictionary of current values from all input fields"""
        return {
            f"load_cell_{self.current_cell}_zero_offset": self.zero_offset_input.value(),
            f"load_cell_{self.current_cell}_scale_factor": self.scale_factor_input.value(),
            f"load_cell_{self.current_cell}_sampling_rate": self.sampling_rate_input.value(),
            f"load_cell_{self.current_cell}_filter_cutoff": self.filter_cutoff_input.value(),
            f"load_cell_{self.current_cell}_averaging_samples": self.averaging_samples_input.value(),
            f"load_cell_{self.current_cell}_min_weight_threshold": self.min_weight_threshold_input.value(),
            f"load_cell_{self.current_cell}_max_weight_threshold": self.max_weight_threshold_input.value(),
            "selected_load_cell": self.current_cell,
        }

    def showToast(self, message):
        """Show toast notification"""
        if self.parent_widget:
            toast = ToastWidget(self.parent_widget, message, 3)
            toast.show()

    def _connect_auto_save_signals(self):
        """Connect all input fields to auto-save configuration"""
        # Connection settings
        self.glue_type_dropdown.currentTextChanged.connect(self._on_glue_type_changed)
        self.capacity_input.valueChanged.connect(self._on_capacity_changed)
        self.url_input.textChanged.connect(self._on_url_changed)
        self.fetch_timeout_input.valueChanged.connect(self._on_fetch_timeout_changed)

        # Calibration settings
        self.zero_offset_input.valueChanged.connect(self._on_zero_offset_changed)
        self.scale_factor_input.valueChanged.connect(self._on_scale_factor_changed)

        # Measurement settings
        self.sampling_rate_input.valueChanged.connect(self._on_sampling_rate_changed)
        self.filter_cutoff_input.valueChanged.connect(self._on_filter_cutoff_changed)
        self.averaging_samples_input.valueChanged.connect(self._on_averaging_samples_changed)
        self.min_weight_threshold_input.valueChanged.connect(self._on_min_threshold_changed)
        self.max_weight_threshold_input.valueChanged.connect(self._on_max_threshold_changed)

    def _on_glue_type_changed(self, value):
        """Handle glue type change"""
        self._update_cell_config("type", value)
        print(f"[Config] Cell {self.current_cell} glue type changed to: {value}")

    def _on_capacity_changed(self, value):
        """Handle capacity change"""
        self._update_cell_config("capacity", value)
        print(f"[Config] Cell {self.current_cell} capacity changed to: {value}")

    def _on_url_changed(self, value):
        """Handle URL change"""
        self._update_cell_config("url", value)
        print(f"[Config] Cell {self.current_cell} URL changed to: {value}")

    def _on_fetch_timeout_changed(self, value):
        """Handle fetch timeout change"""
        self._update_cell_config("fetch_timeout", value)
        print(f"[Config] Cell {self.current_cell} fetch timeout changed to: {value}")

    def _on_zero_offset_changed(self, value):
        from GlueDispensingApplication.tools.GlueCell import UPDATE_OFFSET_ENDPOINT
        """Handle zero offset change"""

        try:
            # Get base URL from the already loaded configuration
            if self.glue_cells_manager and hasattr(self.glue_cells_manager, 'config_data'):
                config = self.glue_cells_manager.config_data
                base_url = config.get("BASE_URL")
                timeout = config.get("FETCH_TIMEOUT")
            else:
                print("Error: Glue cells manager not available - cannot perform tare operation")
                self.showToast("Error: Glue cells manager not available")
                return

            endpoint = UPDATE_OFFSET_ENDPOINT.format(current_cell=self.current_cell,
                                                     offset=self.zero_offset_input.value())

            url = f"{base_url}{endpoint}"
            print(f"Updating zero offset via URL: {url}")
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                self._update_cell_calibration("zero_offset", value)
                print(f"[Config] Cell {self.current_cell} zero offset changed to: {value}")
            else:
                self.showToast(f"Offset update failed: {response.status_code}")
                print(f"[Config] Offset update failed with status code: {response.status_code}")
        except Exception as e:
            print(f"[Config] Error updating zero offset: {e}")
            self.showToast(f"Offset update error: {e}")


    def _on_scale_factor_changed(self, value):
        from GlueDispensingApplication.tools.GlueCell import UPDATE_SCALE_ENDPOINT
        try:
            # Get base URL from the already loaded configuration
            if self.glue_cells_manager and hasattr(self.glue_cells_manager, 'config_data'):
                config = self.glue_cells_manager.config_data
                base_url = config.get("BASE_URL")
                timeout = config.get("FETCH_TIMEOUT")
            else:
                print("Error: Glue cells manager not available - cannot perform tare operation")
                self.showToast("Error: Glue cells manager not available")
                return

            endpoint = UPDATE_SCALE_ENDPOINT.format(current_cell=self.current_cell,scale=self.scale_factor_input.value())
            url = f"{base_url}{endpoint}"
            print(f"Updating scale factor via URL: {url}")
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                """Handle scale factor change"""
                self._update_cell_calibration("scale_factor", value)
                print(f"[Config] Cell {self.current_cell} scale factor changed to: {value}")
            else:
                self.showToast(f"Scale update failed: {response.status_code}")
                print(f"[Config] Scale update failed with status code: {response.status_code}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[Config] Error updating zero scale: {e}")
            self.showToast(f"Scale update error: {e}")


    def _on_sampling_rate_changed(self, value):
        """Handle sampling rate change"""
        self._update_cell_measurement("sampling_rate", value)
        print(f"[Config] Cell {self.current_cell} sampling rate changed to: {value}")

    def _on_filter_cutoff_changed(self, value):
        """Handle filter cutoff change"""
        self._update_cell_measurement("filter_cutoff", value)
        print(f"[Config] Cell {self.current_cell} filter cutoff changed to: {value}")

    def _on_averaging_samples_changed(self, value):
        """Handle averaging samples change"""
        self._update_cell_measurement("averaging_samples", value)
        print(f"[Config] Cell {self.current_cell} averaging samples changed to: {value}")

    def _on_min_threshold_changed(self, value):
        """Handle min threshold change"""
        self._update_cell_measurement("min_weight_threshold", value)
        print(f"[Config] Cell {self.current_cell} min threshold changed to: {value}")

    def _on_max_threshold_changed(self, value):
        """Handle max threshold change"""
        self._update_cell_measurement("max_weight_threshold", value)
        print(f"[Config] Cell {self.current_cell} max threshold changed to: {value}")

    def _update_cell_config(self, key, value):
        """Update a cell config value in memory and persist to file"""
        try:
            # Update in-memory config
            if self.current_cell in self.cell_configs:
                self.cell_configs[self.current_cell][key] = value

            # Load full config from file
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)

            # Update the specific cell's config
            for cell_config in config_data.get("CELL_CONFIG", []):
                if cell_config["id"] == self.current_cell:
                    cell_config[key] = value
                    break

            # Save back to file
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)

        except Exception as e:
            print(f"[Config] Error updating {key}: {e}")

    def _update_cell_calibration(self, key, value):
        """Update a cell calibration value in memory and persist to file"""
        try:
            # Update in-memory config
            if self.current_cell in self.cell_configs:
                self.cell_configs[self.current_cell][key] = value

            # Load full config from file
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)

            # Update the specific cell's calibration config
            for cell_config in config_data.get("CELL_CONFIG", []):
                if cell_config["id"] == self.current_cell:
                    if "calibration" not in cell_config:
                        cell_config["calibration"] = {}
                    cell_config["calibration"][key] = value
                    break

            # Save back to file
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)

        except Exception as e:
            print(f"[Config] Error updating calibration {key}: {e}")

    def _update_cell_measurement(self, key, value):
        """Update a cell measurement value in memory and persist to file"""
        try:
            # Update in-memory config
            if self.current_cell in self.cell_configs:
                self.cell_configs[self.current_cell][key] = value

            # Load full config from file
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)

            # Update the specific cell's measurement config
            for cell_config in config_data.get("CELL_CONFIG", []):
                if cell_config["id"] == self.current_cell:
                    if "measurement" not in cell_config:
                        cell_config["measurement"] = {}
                    cell_config["measurement"][key] = value
                    break

            # Save back to file
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)

        except Exception as e:
            print(f"[Config] Error updating measurement {key}: {e}")

    def _on_weight1_updated(self, weight_value):
        """Handle weight update for Load Cell 1 via message broker"""
        try:
            weight = float(weight_value)
            if self.current_cell == 1:
                self._update_weight_display(weight)
            # print(f"[MessageBroker] Weight 1 updated: {weight:.2f}g")
        except (ValueError, TypeError) as e:
            print(f"[MessageBroker] Error processing weight 1 update: {e}")

    def _on_weight2_updated(self, weight_value):
        """Handle weight update for Load Cell 2 via message broker"""
        try:
            weight = float(weight_value)
            if self.current_cell == 2:
                self._update_weight_display(weight)
            # print(f"[MessageBroker] Weight 2 updated: {weight:.2f}g")
        except (ValueError, TypeError) as e:
            print(f"[MessageBroker] Error processing weight 2 update: {e}")

    def _on_weight3_updated(self, weight_value):
        """Handle weight update for Load Cell 3 via message broker"""
        try:
            weight = float(weight_value)
            if self.current_cell == 3:
                self._update_weight_display(weight)
            # print(f"[MessageBroker] Weight 3 updated: {weight:.2f}g")
        except (ValueError, TypeError) as e:
            print(f"[MessageBroker] Error processing weight 3 update: {e}")

    def _update_weight_display(self, weight):
        """Update the weight display with real-time weight value from message broker"""
        if not hasattr(self, 'current_weight_label'):
            return
            
        # Update the weight display
        self.current_weight_label.setText(f"{weight:.2f} g")
        
        # Update styling based on thresholds
        try:
            min_threshold = self.min_weight_threshold_input.value()
            max_threshold = self.max_weight_threshold_input.value()
            
            if weight < min_threshold:
                # Below minimum - red
                self.current_weight_label.setStyleSheet("""
                    QLabel { 
                        font-size: 18px; 
                        font-weight: bold; 
                        color: #B22222; 
                        background-color: #FFE4E1; 
                        border: 2px solid #FF6B6B;
                        border-radius: 8px;
                        padding: 10px;
                        min-height: 30px;
                    }
                """)
            elif weight > max_threshold:
                # Above maximum - orange
                self.current_weight_label.setStyleSheet("""
                    QLabel { 
                        font-size: 18px; 
                        font-weight: bold; 
                        color: #FF8C00; 
                        background-color: #FFF8DC; 
                        border: 2px solid #FFD700;
                        border-radius: 8px;
                        padding: 10px;
                        min-height: 30px;
                    }
                """)
            else:
                # Normal range - green
                self.current_weight_label.setStyleSheet("""
                    QLabel { 
                        font-size: 18px; 
                        font-weight: bold; 
                        color: #2E8B57; 
                        background-color: #F0F8F0; 
                        border: 2px solid #90EE90;
                        border-radius: 8px;
                        padding: 10px;
                        min-height: 30px;
                    }
                """)
        except Exception as e:
            print(f"Error updating weight display styling: {e}")


# Example usage:
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_widget = QWidget()

    layout = LoadCellsSettingsTabLayout(main_widget)

    def settingsChangeCallback(key, value, className):
        print(f"Settings changed in {className}: {key} = {value}")

    layout.connectValueChangeCallbacks(settingsChangeCallback)

    main_widget.setLayout(layout)
    main_widget.resize(1200, 800)
    main_widget.show()

    sys.exit(app.exec())
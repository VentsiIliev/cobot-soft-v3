import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QLabel, QTextEdit, QGroupBox,
                             QGridLayout, QCheckBox, QSpinBox, QProgressBar,
                             QTableWidget, QTableWidgetItem, QTabWidget,
                             QSplitter, QFrame, QScrollArea, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPen, QColor, QImage
import threading
import time
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum


class CalibrationState(Enum):
    INITIALIZING = "INITIALIZING"
    LOOKING_FOR_CHESSBOARD = "LOOKING_FOR_CHESSBOARD"
    CHESSBOARD_FOUND = "CHESSBOARD_FOUND"
    LOOKING_FOR_ARUCO_MARKERS = "LOOKING_FOR_ARUCO_MARKERS"
    ALL_ARUCO_FOUND = "ALL_ARUCO_FOUND"
    COMPUTE_OFFSETS = "COMPUTE_OFFSETS"
    ALIGN_ROBOT = "ALIGN_ROBOT"
    DONE = "DONE"


@dataclass
class MarkerData:
    marker_id: int
    center_px: Optional[Tuple[int, int]] = None
    center_mm: Optional[Tuple[float, float]] = None
    offset_mm: Optional[Tuple[float, float]] = None
    robot_position: Optional[List[float]] = None
    is_detected: bool = False
    is_aligned: bool = False


@dataclass
class CalibrationData:
    current_state: CalibrationState = CalibrationState.INITIALIZING
    current_marker_id: int = 0
    ppm: Optional[float] = None
    bottom_left_corner_px: Optional[Tuple[float, float]] = None
    image_center_mm: Optional[Tuple[float, float]] = None
    z_current: float = 0.0
    z_target: float = 150.0
    ppm_scale: float = 1.0
    detected_marker_ids: Set[int] = None
    current_frame: Optional[np.ndarray] = None

    def __post_init__(self):
        if self.detected_marker_ids is None:
            self.detected_marker_ids = set()


class IPipelineController:
    """Interface for controlling the calibration pipeline"""

    def start_calibration(self, required_ids: List[int]) -> None:
        raise NotImplementedError

    def stop_calibration(self) -> None:
        raise NotImplementedError

    def pause_calibration(self) -> None:
        raise NotImplementedError

    def resume_calibration(self) -> None:
        raise NotImplementedError

    def get_current_data(self) -> CalibrationData:
        raise NotImplementedError

    def get_marker_data(self) -> Dict[int, MarkerData]:
        raise NotImplementedError


class MockPipelineController(IPipelineController):
    """Mock implementation for demonstration purposes"""

    def __init__(self):
        self._is_running = False
        self._is_paused = False
        self._required_ids = []
        self._calibration_data = CalibrationData()
        self._marker_data = {}
        self._worker_thread = None
        self._frame_counter = 0

    def start_calibration(self, required_ids: List[int]) -> None:
        self._required_ids = required_ids
        self._is_running = True
        self._is_paused = False
        self._calibration_data = CalibrationData()
        self._marker_data = {mid: MarkerData(mid) for mid in required_ids}
        self._frame_counter = 0

        # Start mock worker thread
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._worker_thread = threading.Thread(target=self._mock_calibration_process)
            self._worker_thread.daemon = True
            self._worker_thread.start()

    def stop_calibration(self) -> None:
        self._is_running = False
        self._is_paused = False

    def pause_calibration(self) -> None:
        self._is_paused = True

    def resume_calibration(self) -> None:
        self._is_paused = False

    def get_current_data(self) -> CalibrationData:
        # Generate mock camera frame
        self._generate_mock_frame()
        return self._calibration_data

    def get_marker_data(self) -> Dict[int, MarkerData]:
        return self._marker_data.copy()

    def _generate_mock_frame(self):
        """Generate a mock camera frame for demonstration"""
        self._frame_counter += 1

        # Create a simple mock frame (640x480, 3 channels)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 50  # Dark gray background

        # Add some visual elements based on current state
        state = self._calibration_data.current_state

        if state == CalibrationState.LOOKING_FOR_CHESSBOARD or state == CalibrationState.CHESSBOARD_FOUND:
            # Draw mock chessboard pattern
            for i in range(8):
                for j in range(6):
                    if (i + j) % 2 == 0:
                        x1, y1 = 100 + j * 30, 80 + i * 30
                        x2, y2 = x1 + 30, y1 + 30
                        frame[y1:y2, x1:x2] = [255, 255, 255]  # White squares

        if state in [CalibrationState.LOOKING_FOR_ARUCO_MARKERS, CalibrationState.ALL_ARUCO_FOUND,
                     CalibrationState.ALIGN_ROBOT, CalibrationState.DONE]:
            # Draw mock ArUco markers
            for i, marker_id in enumerate(self._required_ids[:4]):  # Show up to 4 markers
                x = 150 + (i % 2) * 200
                y = 150 + (i // 2) * 150

                # Draw marker square
                frame[y:y + 60, x:x + 60] = [0, 255, 0]  # Green marker

                # Add marker ID text (simplified)
                center_x, center_y = x + 30, y + 30
                frame[center_y - 10:center_y + 10, center_x - 10:center_x + 10] = [255, 255, 255]

        # Add image center cross
        center_x, center_y = 320, 240
        frame[center_y - 5:center_y + 5, center_x - 1:center_x + 1] = [255, 0, 0]  # Red cross
        frame[center_y - 1:center_y + 1, center_x - 5:center_x + 5] = [255, 0, 0]

        # Add some noise to make it look more realistic
        noise = np.random.randint(-20, 20, frame.shape, dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        self._calibration_data.current_frame = frame

    def _mock_calibration_process(self):
        """Mock calibration process for demonstration"""
        states = list(CalibrationState)
        state_index = 0

        while self._is_running and state_index < len(states):
            if self._is_paused:
                time.sleep(0.1)
                continue

            self._calibration_data.current_state = states[state_index]

            # Simulate state-specific behavior
            if states[state_index] == CalibrationState.CHESSBOARD_FOUND:
                self._calibration_data.ppm = 3.245
                self._calibration_data.bottom_left_corner_px = (100.0, 200.0)

            elif states[state_index] == CalibrationState.ALL_ARUCO_FOUND:
                # Simulate finding markers
                for i, marker_id in enumerate(self._required_ids):
                    self._marker_data[marker_id].is_detected = True
                    self._marker_data[marker_id].center_px = (150 + i * 50, 180 + i * 30)
                    self._marker_data[marker_id].center_mm = (10.5 + i * 5, 12.3 + i * 3)
                    self._calibration_data.detected_marker_ids.add(marker_id)

            elif states[state_index] == CalibrationState.ALIGN_ROBOT:
                if self._calibration_data.current_marker_id < len(self._required_ids):
                    current_id = self._required_ids[self._calibration_data.current_marker_id]
                    self._marker_data[current_id].is_aligned = True
                    self._marker_data[current_id].robot_position = [100.0, 200.0, 150.0, 0.0, 0.0, 0.0]
                    self._calibration_data.current_marker_id += 1

            time.sleep(2)  # Simulate processing time
            state_index += 1

        if self._is_running:
            self._calibration_data.current_state = CalibrationState.DONE


class MarkerSelectionWidget(QWidget):
    """Widget for selecting required markers"""

    markers_changed = pyqtSignal(list)  # Emits list of selected marker IDs

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checkboxes = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Required Markers")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Add marker input section
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Add Marker ID:"))

        self._marker_id_input = QSpinBox()
        self._marker_id_input.setRange(0, 999)  # Allow markers 0-999
        self._marker_id_input.setValue(0)
        input_layout.addWidget(self._marker_id_input)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_marker)
        input_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_marker)
        input_layout.addWidget(remove_btn)

        input_layout.addStretch()
        layout.addLayout(input_layout)

        # Scrollable area for checkboxes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)

        self._checkbox_widget = QWidget()
        self._checkbox_layout = QGridLayout(self._checkbox_widget)
        scroll_area.setWidget(self._checkbox_widget)
        layout.addWidget(scroll_area)

        # Control buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        deselect_all_btn = QPushButton("Deselect All")
        clear_all_btn = QPushButton("Clear All")

        select_all_btn.clicked.connect(self._select_all)
        deselect_all_btn.clicked.connect(self._deselect_all)
        clear_all_btn.clicked.connect(self._clear_all)

        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(deselect_all_btn)
        button_layout.addWidget(clear_all_btn)
        layout.addLayout(button_layout)

        # Quick preset buttons
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Presets:"))

        preset_0_8_btn = QPushButton("0-8")
        preset_0_8_btn.clicked.connect(lambda: self._set_preset(list(range(9))))
        preset_layout.addWidget(preset_0_8_btn)

        preset_0_4_btn = QPushButton("0-4")
        preset_0_4_btn.clicked.connect(lambda: self._set_preset(list(range(5))))
        preset_layout.addWidget(preset_0_4_btn)

        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        # Initialize with default markers 0-8
        self._set_preset(list(range(9)))

    def _add_marker(self):
        """Add a new marker checkbox"""
        marker_id = self._marker_id_input.value()

        if marker_id in self._checkboxes:
            QMessageBox.information(self, "Info", f"Marker {marker_id} already exists.")
            return

        checkbox = QCheckBox(f"Marker {marker_id}")
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(self._on_selection_changed)
        self._checkboxes[marker_id] = checkbox

        self._update_checkbox_layout()
        self._on_selection_changed()

    def _remove_marker(self):
        """Remove a marker checkbox"""
        marker_id = self._marker_id_input.value()

        if marker_id not in self._checkboxes:
            QMessageBox.information(self, "Info", f"Marker {marker_id} does not exist.")
            return

        checkbox = self._checkboxes.pop(marker_id)
        checkbox.deleteLater()

        self._update_checkbox_layout()
        self._on_selection_changed()

    def _update_checkbox_layout(self):
        """Update the grid layout of checkboxes"""
        # Clear layout
        while self._checkbox_layout.count():
            child = self._checkbox_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

        # Re-add checkboxes in sorted order
        sorted_markers = sorted(self._checkboxes.items())
        cols = 3

        for i, (marker_id, checkbox) in enumerate(sorted_markers):
            row = i // cols
            col = i % cols
            self._checkbox_layout.addWidget(checkbox, row, col)

    def _set_preset(self, marker_ids: List[int]):
        """Set a preset of marker IDs"""
        # Clear existing markers
        self._clear_all()

        # Add preset markers
        for marker_id in marker_ids:
            checkbox = QCheckBox(f"Marker {marker_id}")
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._on_selection_changed)
            self._checkboxes[marker_id] = checkbox

        self._update_checkbox_layout()
        self._on_selection_changed()

    def _clear_all(self):
        """Remove all marker checkboxes"""
        for checkbox in self._checkboxes.values():
            checkbox.deleteLater()
        self._checkboxes.clear()
        self._on_selection_changed()

    def _on_selection_changed(self):
        selected_ids = [mid for mid, cb in self._checkboxes.items() if cb.isChecked()]
        self.markers_changed.emit(selected_ids)

    def _select_all(self):
        for checkbox in self._checkboxes.values():
            checkbox.setChecked(True)

    def _deselect_all(self):
        for checkbox in self._checkboxes.values():
            checkbox.setChecked(False)

    def get_selected_markers(self) -> List[int]:
        return [mid for mid, cb in self._checkboxes.items() if cb.isChecked()]

    def set_enabled(self, enabled: bool):
        for checkbox in self._checkboxes.values():
            checkbox.setEnabled(enabled)
        self._marker_id_input.setEnabled(enabled)

    def add_markers(self, marker_ids: List[int]):
        """Programmatically add multiple markers"""
        for marker_id in marker_ids:
            if marker_id not in self._checkboxes:
                checkbox = QCheckBox(f"Marker {marker_id}")
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(self._on_selection_changed)
                self._checkboxes[marker_id] = checkbox

        self._update_checkbox_layout()
        self._on_selection_changed()

    def get_all_marker_ids(self) -> List[int]:
        """Get all marker IDs (both selected and unselected)"""
        return list(self._checkboxes.keys())


class StateDisplayWidget(QWidget):
    """Widget for displaying current calibration state"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Calibration State")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Current state
        self._state_label = QLabel("State: Not Started")
        self._state_label.setFont(QFont("Arial", 10))
        layout.addWidget(self._state_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, len(CalibrationState))
        layout.addWidget(self._progress_bar)

        # Current marker
        self._current_marker_label = QLabel("Current Marker: None")
        layout.addWidget(self._current_marker_label)

        # Additional info
        self._info_layout = QVBoxLayout()
        layout.addLayout(self._info_layout)

    def update_state(self, calibration_data: CalibrationData):
        # Update state label
        state_name = calibration_data.current_state.value.replace('_', ' ').title()
        self._state_label.setText(f"State: {state_name}")

        # Update progress
        state_progress = list(CalibrationState).index(calibration_data.current_state)
        self._progress_bar.setValue(state_progress)

        # Update current marker
        if calibration_data.current_marker_id is not None:
            self._current_marker_label.setText(f"Current Marker: {calibration_data.current_marker_id}")

        # Clear and update info
        self._clear_info_layout()

        # Add relevant info based on state
        if calibration_data.ppm is not None:
            self._add_info(f"PPM: {calibration_data.ppm:.3f} px/mm")

        if calibration_data.bottom_left_corner_px is not None:
            corner = calibration_data.bottom_left_corner_px
            self._add_info(f"Chessboard Corner: ({corner[0]:.1f}, {corner[1]:.1f}) px")

        if calibration_data.detected_marker_ids:
            detected_str = ", ".join(map(str, sorted(calibration_data.detected_marker_ids)))
            self._add_info(f"Detected Markers: {detected_str}")

    def _clear_info_layout(self):
        while self._info_layout.count():
            child = self._info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _add_info(self, text: str):
        label = QLabel(text)
        label.setFont(QFont("Arial", 9))
        self._info_layout.addWidget(label)


class CameraViewWidget(QLabel):
    """Widget for displaying live camera feed with overlays"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._current_frame = None
        self._show_overlays = True

    def _setup_ui(self):
        self.setMinimumSize(640, 480)
        self.setMaximumSize(800, 600)
        self.setScaledContents(True)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                background-color: #f0f0f0;
                border-radius: 5px;
            }
        """)
        self.setText("Camera View\n(No feed)")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_frame(self, frame: np.ndarray):
        """Update the displayed frame"""
        if frame is None:
            return

        self._current_frame = frame.copy()
        self._display_frame()

    def _display_frame(self):
        """Convert numpy array to QPixmap and display"""
        if self._current_frame is None:
            return

        # Convert BGR to RGB (OpenCV uses BGR)
        if len(self._current_frame.shape) == 3:
            rgb_frame = self._current_frame[:, :, ::-1]  # BGR to RGB
        else:
            rgb_frame = self._current_frame

        height, width = rgb_frame.shape[:2]

        # Convert numpy array to bytes
        if len(rgb_frame.shape) == 3:
            bytes_per_line = 3 * width
            # Ensure the array is contiguous
            rgb_frame = np.ascontiguousarray(rgb_frame)
            q_image = QImage(rgb_frame.data.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
        else:
            bytes_per_line = width
            # Ensure the array is contiguous
            rgb_frame = np.ascontiguousarray(rgb_frame)
            q_image = QImage(rgb_frame.data.tobytes(), width, height, bytes_per_line, QImage.Format.Format_Grayscale8)

        pixmap = QPixmap.fromImage(q_image)
        self.setPixmap(pixmap)

    def set_overlay_visibility(self, visible: bool):
        """Toggle overlay visibility"""
        self._show_overlays = visible
        self._display_frame()

    def clear_view(self):
        """Clear the camera view"""
        self.clear()
        self.setText("Camera View\n(No feed)")


class CameraControlWidget(QWidget):
    """Widget for camera view controls"""

    overlay_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Camera Controls")
        title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title)

        # Overlay toggle
        self._overlay_checkbox = QCheckBox("Show Overlays")
        self._overlay_checkbox.setChecked(True)
        self._overlay_checkbox.stateChanged.connect(self._on_overlay_changed)
        layout.addWidget(self._overlay_checkbox)

        # Camera info
        self._info_label = QLabel("Resolution: N/A\nFPS: N/A")
        self._info_label.setFont(QFont("Arial", 8))
        layout.addWidget(self._info_label)

        layout.addStretch()

    def _on_overlay_changed(self, state):
        self.overlay_toggled.emit(state == Qt.CheckState.Checked.value)

    def update_info(self, width: int, height: int, fps: float = None):
        """Update camera info display"""
        info_text = f"Resolution: {width}x{height}"
        if fps is not None:
            info_text += f"\nFPS: {fps:.1f}"
        else:
            info_text += "\nFPS: N/A"
        self._info_label.setText(info_text)


class MarkerDataTableWidget(QTableWidget):
    """Table widget for displaying marker data"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Set up columns
        headers = ["ID", "Detected", "Center (px)", "Center (mm)", "Offset (mm)", "Aligned", "Robot Position"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        # Set table properties
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)

    def update_marker_data(self, marker_data: Dict[int, MarkerData]):
        # Clear existing rows
        self.setRowCount(0)

        # Add rows for each marker
        sorted_markers = sorted(marker_data.items())
        self.setRowCount(len(sorted_markers))

        for row, (marker_id, data) in enumerate(sorted_markers):
            # ID
            self.setItem(row, 0, QTableWidgetItem(str(marker_id)))

            # Detected
            detected_item = QTableWidgetItem("✓" if data.is_detected else "✗")
            detected_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 1, detected_item)

            # Center (px)
            center_px_text = f"({data.center_px[0]}, {data.center_px[1]})" if data.center_px else "N/A"
            self.setItem(row, 2, QTableWidgetItem(center_px_text))

            # Center (mm)
            center_mm_text = f"({data.center_mm[0]:.2f}, {data.center_mm[1]:.2f})" if data.center_mm else "N/A"
            self.setItem(row, 3, QTableWidgetItem(center_mm_text))

            # Offset (mm)
            offset_mm_text = f"({data.offset_mm[0]:.2f}, {data.offset_mm[1]:.2f})" if data.offset_mm else "N/A"
            self.setItem(row, 4, QTableWidgetItem(offset_mm_text))

            # Aligned
            aligned_item = QTableWidgetItem("✓" if data.is_aligned else "✗")
            aligned_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 5, aligned_item)

            # Robot Position
            if data.robot_position:
                pos_text = f"({data.robot_position[0]:.1f}, {data.robot_position[1]:.1f}, {data.robot_position[2]:.1f})"
            else:
                pos_text = "N/A"
            self.setItem(row, 6, QTableWidgetItem(pos_text))

        self.resizeColumnsToContents()


class LogWidget(QTextEdit):
    """Widget for displaying calibration logs"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.document().setMaximumBlockCount(1000)  # Limit log size

    def add_log(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}"
        self.append(formatted_message)

        # Auto-scroll to bottom
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.setTextCursor(cursor)


class CalibrationWorkerThread(QThread):
    """Worker thread for running calibration updates"""

    state_updated = pyqtSignal(object)  # CalibrationData
    marker_data_updated = pyqtSignal(dict)  # Dict[int, MarkerData]
    frame_updated = pyqtSignal(object)  # np.ndarray
    log_message = pyqtSignal(str, str)  # message, level

    def __init__(self, controller: IPipelineController):
        super().__init__()
        self._controller = controller
        self._is_running = False

    def start_monitoring(self):
        self._is_running = True
        self.start()

    def stop_monitoring(self):
        self._is_running = False
        self.quit()
        self.wait()

    def run(self):
        while self._is_running:
            try:
                # Get current data from controller
                calibration_data = self._controller.get_current_data()
                marker_data = self._controller.get_marker_data()

                # Emit updates
                self.state_updated.emit(calibration_data)
                self.marker_data_updated.emit(marker_data)

                # Emit frame update if available
                if calibration_data.current_frame is not None:
                    self.frame_updated.emit(calibration_data.current_frame)

                # Sleep briefly to avoid overwhelming the GUI
                self.msleep(100)

            except Exception as e:
                self.log_message.emit(f"Error in worker thread: {str(e)}", "ERROR")
                self.msleep(1000)


class CalibrationControlWidget(QWidget):
    """Control buttons for calibration process"""

    calibration_started = pyqtSignal(list)  # required_ids
    calibration_stopped = pyqtSignal()
    calibration_paused = pyqtSignal()
    calibration_resumed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = False
        self._is_paused = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        self._start_btn = QPushButton("Start Calibration")
        self._stop_btn = QPushButton("Stop")
        self._pause_btn = QPushButton("Pause")
        self._resume_btn = QPushButton("Resume")

        # Connect signals
        self._start_btn.clicked.connect(self._on_start_clicked)
        self._stop_btn.clicked.connect(self._on_stop_clicked)
        self._pause_btn.clicked.connect(self._on_pause_clicked)
        self._resume_btn.clicked.connect(self._on_resume_clicked)

        # Add buttons
        layout.addWidget(self._start_btn)
        layout.addWidget(self._stop_btn)
        layout.addWidget(self._pause_btn)
        layout.addWidget(self._resume_btn)

        # Initial state
        self._update_button_states()

    def _on_start_clicked(self):
        # Get required markers from parent
        if hasattr(self.parent(), 'get_required_markers'):
            required_ids = self.parent().get_required_markers()
            if not required_ids:
                QMessageBox.warning(self, "Warning", "Please select at least one marker.")
                return
            self.calibration_started.emit(required_ids)
            self._is_running = True
            self._is_paused = False
            self._update_button_states()

    def _on_stop_clicked(self):
        self.calibration_stopped.emit()
        self._is_running = False
        self._is_paused = False
        self._update_button_states()

    def _on_pause_clicked(self):
        self.calibration_paused.emit()
        self._is_paused = True
        self._update_button_states()

    def _on_resume_clicked(self):
        self.calibration_resumed.emit()
        self._is_paused = False
        self._update_button_states()

    def _update_button_states(self):
        self._start_btn.setEnabled(not self._is_running)
        self._stop_btn.setEnabled(self._is_running)
        self._pause_btn.setEnabled(self._is_running and not self._is_paused)
        self._resume_btn.setEnabled(self._is_running and self._is_paused)


class CalibrationPipelineGUI(QMainWindow):
    """Main GUI window for calibration pipeline"""

    def __init__(self, controller: IPipelineController = None):
        super().__init__()
        self._controller = controller or MockPipelineController()
        self._worker_thread = None
        self._setup_ui()
        self._connect_signals()
        self._start_monitoring()

    def _setup_ui(self):
        self.setWindowTitle("Calibration Pipeline Control Center")
        self.setGeometry(100, 100, 1600, 900)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create control widget
        self._control_widget = CalibrationControlWidget(self)
        main_layout.addWidget(self._control_widget)

        # Create main content splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        # Left panel
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)

        # Center panel (Camera view)
        center_panel = self._create_center_panel()
        main_splitter.addWidget(center_panel)

        # Right panel (tabs)
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)

        # Set splitter proportions (left:center:right = 300:600:700)
        main_splitter.setSizes([300, 600, 700])

    def _create_left_panel(self) -> QWidget:
        """Create left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Marker selection
        self._marker_selection = MarkerSelectionWidget()
        layout.addWidget(self._marker_selection)

        # State display
        self._state_display = StateDisplayWidget()
        layout.addWidget(self._state_display)

        # Stretch
        layout.addStretch()

        return panel

    def _create_center_panel(self) -> QWidget:
        """Create center panel with camera view"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Camera view title
        title = QLabel("Camera View")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Camera view widget
        self._camera_view = CameraViewWidget()
        layout.addWidget(self._camera_view)

        # Camera controls
        self._camera_controls = CameraControlWidget()
        layout.addWidget(self._camera_controls)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create right panel with tabs"""
        tab_widget = QTabWidget()

        # Marker data tab
        self._marker_table = MarkerDataTableWidget()
        tab_widget.addTab(self._marker_table, "Marker Data")

        # Log tab
        self._log_widget = LogWidget()
        tab_widget.addTab(self._log_widget, "Logs")

        return tab_widget

    def _connect_signals(self):
        """Connect all GUI signals"""
        # Control signals
        self._control_widget.calibration_started.connect(self._on_calibration_started)
        self._control_widget.calibration_stopped.connect(self._on_calibration_stopped)
        self._control_widget.calibration_paused.connect(self._on_calibration_paused)
        self._control_widget.calibration_resumed.connect(self._on_calibration_resumed)

        # Marker selection signals
        self._marker_selection.markers_changed.connect(self._on_markers_changed)

        # Camera control signals
        self._camera_controls.overlay_toggled.connect(self._camera_view.set_overlay_visibility)

    def _start_monitoring(self):
        """Start the worker thread for monitoring calibration"""
        if self._worker_thread is None:
            self._worker_thread = CalibrationWorkerThread(self._controller)
            self._worker_thread.state_updated.connect(self._on_state_updated)
            self._worker_thread.marker_data_updated.connect(self._on_marker_data_updated)
            self._worker_thread.frame_updated.connect(self._on_frame_updated)
            self._worker_thread.log_message.connect(self._on_log_message)
            self._worker_thread.start_monitoring()

    def _on_calibration_started(self, required_ids: List[int]):
        """Handle calibration start"""
        self._log_widget.add_log(f"Starting calibration with markers: {required_ids}")
        self._marker_selection.set_enabled(False)
        self._controller.start_calibration(required_ids)

    def _on_calibration_stopped(self):
        """Handle calibration stop"""
        self._log_widget.add_log("Stopping calibration")
        self._marker_selection.set_enabled(True)
        self._controller.stop_calibration()

    def _on_calibration_paused(self):
        """Handle calibration pause"""
        self._log_widget.add_log("Pausing calibration")
        self._controller.pause_calibration()

    def _on_calibration_resumed(self):
        """Handle calibration resume"""
        self._log_widget.add_log("Resuming calibration")
        self._controller.resume_calibration()

    def _on_markers_changed(self, selected_ids: List[int]):
        """Handle marker selection change"""
        self._log_widget.add_log(f"Marker selection changed: {selected_ids}")

    def _on_state_updated(self, calibration_data: CalibrationData):
        """Handle state update from worker thread"""
        self._state_display.update_state(calibration_data)

    def _on_marker_data_updated(self, marker_data: Dict[int, MarkerData]):
        """Handle marker data update from worker thread"""
        self._marker_table.update_marker_data(marker_data)

    def _on_frame_updated(self, frame: np.ndarray):
        """Handle frame update from worker thread"""
        self._camera_view.update_frame(frame)
        if frame is not None:
            height, width = frame.shape[:2]
            self._camera_controls.update_info(width, height)

    def _on_log_message(self, message: str, level: str):
        """Handle log message from worker thread"""
        self._log_widget.add_log(message, level)

    def get_required_markers(self) -> List[int]:
        """Get currently selected required markers"""
        return self._marker_selection.get_selected_markers()

    def closeEvent(self, event):
        """Handle window close event"""
        if self._worker_thread:
            self._worker_thread.stop_monitoring()
        event.accept()


# Adapter class to integrate with your existing pipeline
class PipelineControllerAdapter(IPipelineController):
    """Adapter to integrate with your existing CalibrationPipeline"""

    def __init__(self, pipeline_class):
        self._pipeline_class = pipeline_class
        self._pipeline = None
        self._pipeline_thread = None
        self._is_running = False

    def start_calibration(self, required_ids: List[int]) -> None:
        if not self._is_running:
            self._pipeline = self._pipeline_class(required_ids=required_ids)
            self._pipeline_thread = threading.Thread(target=self._pipeline.run)
            self._pipeline_thread.daemon = True
            self._pipeline_thread.start()
            self._is_running = True

    def stop_calibration(self) -> None:
        if self._pipeline:
            # You'd need to add a stop method to your pipeline
            # self._pipeline.stop()
            pass
        self._is_running = False

    def pause_calibration(self) -> None:
        if self._pipeline:
            # You'd need to add pause functionality to your pipeline
            # self._pipeline.pause()
            pass

    def resume_calibration(self) -> None:
        if self._pipeline:
            # You'd need to add resume functionality to your pipeline
            # self._pipeline.resume()
            pass

    def get_current_data(self) -> CalibrationData:
        if self._pipeline:
            # Extract data from your pipeline and convert to CalibrationData
            return CalibrationData(
                current_state=CalibrationState(self._pipeline.current_state),
                current_marker_id=self._pipeline.current_marker_id,
                ppm=self._pipeline.PPM,
                # ... map other fields
            )
        return CalibrationData()

    def get_marker_data(self) -> Dict[int, MarkerData]:
        if self._pipeline:
            # Extract marker data from your pipeline and convert to MarkerData objects
            marker_data = {}
            for marker_id in self._pipeline.required_ids:
                marker_data[marker_id] = MarkerData(
                    marker_id=marker_id,
                    center_px=self._pipeline.marker_centers.get(marker_id),
                    center_mm=self._pipeline.marker_centers_mm.get(marker_id),
                    offset_mm=self._pipeline.markers_offsets_mm.get(marker_id),
                    robot_position=self._pipeline.robot_positions_for_calibration.get(marker_id),
                    is_detected=marker_id in self._pipeline.detected_ids,
                    # ... map other fields
                )
            return marker_data
        return {}


def main():
    app = QApplication(sys.argv)

    # Use mock controller for demonstration
    # To use with your actual pipeline, uncomment the following:
    # from your_pipeline_module import CalibrationPipeline
    # controller = PipelineControllerAdapter(CalibrationPipeline)

    controller = MockPipelineController()

    gui = CalibrationPipelineGUI(controller)
    gui.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
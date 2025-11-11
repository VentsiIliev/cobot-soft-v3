from PyQt6 import QtCore
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QHBoxLayout,
                             QSizePolicy, QComboBox, QScrollArea, QGroupBox, QGridLayout, QPushButton)

from API.shared.settings.conreateSettings.CameraSettings import CameraSettings
from API.shared.settings.conreateSettings.enums.CameraSettingKey import CameraSettingKey
from deprecated.pl_gui.ToastWidget import ToastWidget
from deprecated.pl_gui.customWidgets.SwitchButton import QToggle
from deprecated.pl_gui.settings_view.BaseSettingsTabLayout import BaseSettingsTabLayout
from PyQt6.QtWidgets import QScroller
from PyQt6.QtCore import Qt


class CameraSettingsTabLayout(BaseSettingsTabLayout, QVBoxLayout):
    update_camera_feed_signal = QtCore.pyqtSignal()
    star_camera_requested = QtCore.pyqtSignal()
    stop_camera_requested = QtCore.pyqtSignal()
    capture_image_requested = QtCore.pyqtSignal()
    raw_mode_requested = QtCore.pyqtSignal(bool)
    show_processed_image_requested = QtCore.pyqtSignal()
    start_calibration_requested = QtCore.pyqtSignal()
    save_calibration_requested = QtCore.pyqtSignal()
    load_calibration_requested = QtCore.pyqtSignal()
    test_contour_detection_requested = QtCore.pyqtSignal()
    test_aruco_detection_requested = QtCore.pyqtSignal()
    save_settings_requested = QtCore.pyqtSignal()
    load_settings_requested = QtCore.pyqtSignal()
    reset_settings_requested = QtCore.pyqtSignal()

    def __init__(self, parent_widget, camera_settings: CameraSettings = None, update_camera_feed_callback=None):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)
        print(f"Initializing {self.__class__.__name__} with parent widget: {parent_widget}")
        self.raw_mode_active = False
        self.parent_widget = parent_widget
        self.camera_settings = camera_settings or CameraSettings()
        print(f"CameraSettingsTabLayout initialized with camera settings: {self.camera_settings}")
        self.update_camera_feed_callback = update_camera_feed_callback

        # Create main content with new layout
        self.create_main_content()

        self.updateFrequency = 30  # in milliseconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.update_camera_feed_signal.emit())
        self.timer.start(self.updateFrequency)

        # Connect to parent widget resize events if possible
        if self.parent_widget:
            self.parent_widget.resizeEvent = self.on_parent_resize

    def update_camera_feed(self, frame):
        try:
            if frame is not None:
                self.update_camera_preview_from_cv2(frame)
            else:
                return
        except Exception as e:
            print(f"Exception occurred: {e}")
        finally:
            pass

    def create_camera_preview_section(self):
        """Create the camera preview section with preview and controls"""
        preview_widget = QWidget()
        preview_widget.setFixedWidth(500)
        preview_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 8px;
            }
        """)

        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(20, 20, 20, 20)
        preview_layout.setSpacing(15)

        # Status label
        self.camera_status_label = QLabel("Camera Status: Disconnected")
        self.camera_status_label.setStyleSheet("font-weight: bold; color: #d32f2f;")
        preview_layout.addWidget(self.camera_status_label)

        # Camera preview area
        self.camera_preview_label = QLabel("Camera Preview")
        self.camera_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_preview_label.setStyleSheet("""
            QLabel {
                background-color: #333;
                color: white;
                font-size: 16px;
                border: 1px solid #666;
                border-radius: 4px;
            }
        """)
        self.camera_preview_label.setFixedSize(460, 259)
        self.camera_preview_label.setScaledContents(False)
        preview_layout.addWidget(self.camera_preview_label)

        # Control buttons grid
        button_grid = QGridLayout()
        button_grid.setSpacing(10)

        # Row 0: Camera buttons
        self.capture_image_button = QPushButton("Capture Image")
        self.show_raw_button = QPushButton("Raw Mode")
        self.show_raw_button.setCheckable(True)
        self.show_raw_button.setChecked(self.raw_mode_active)

        cam_buttons = [self.capture_image_button, self.show_raw_button]
        for i, btn in enumerate(cam_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 0, i)

        # Row 1: Calibration buttons
        self.start_calibration_button = QPushButton("Start Calibration")
        self.save_calibration_button = QPushButton("Save Calibration")

        calib_buttons = [self.start_calibration_button, self.save_calibration_button]
        for i, btn in enumerate(calib_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 1, i)

        # Row 2: More buttons
        self.load_calibration_button = QPushButton("Load Calibration")
        self.test_contour_button = QPushButton("Test Contour")

        more_buttons = [self.load_calibration_button, self.test_contour_button]
        for i, btn in enumerate(more_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 2, i)

        # Row 3: Detection and ArUco
        self.test_aruco_button = QPushButton("Test ArUco")
        spacer_btn = QWidget()

        detect_buttons = [self.test_aruco_button, spacer_btn]
        for i, widget in enumerate(detect_buttons):
            if isinstance(widget, QPushButton):
                widget.setMinimumHeight(40)
            button_grid.addWidget(widget, 3, i)

        # Row 4: Settings buttons
        self.save_settings_button = QPushButton("Save Settings")
        self.load_settings_button = QPushButton("Load Settings")

        settings_buttons = [self.save_settings_button, self.load_settings_button]
        for i, btn in enumerate(settings_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 4, i)

        # Row 5: Reset button
        self.reset_settings_button = QPushButton("Reset Defaults")
        self.reset_settings_button.setMinimumHeight(40)
        button_grid.addWidget(self.reset_settings_button, 5, 0, 1, 2)

        preview_layout.addLayout(button_grid)
        preview_layout.addStretch()

        self.connect_default_callbacks()
        return preview_widget

    def update_camera_preview(self, pixmap):
        """Update the camera preview with a new frame, maintaining 16:9 aspect ratio"""
        if hasattr(self, 'camera_preview_label'):
            label_size = self.camera_preview_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.camera_preview_label.setPixmap(scaled_pixmap)
            self.camera_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_camera_preview_from_cv2(self, cv2_image):
        if hasattr(self, 'camera_preview_label'):
            rgb_image = cv2_image[:, :, ::-1] if len(cv2_image.shape) == 3 else cv2_image
            height, width = rgb_image.shape[:2]
            bytes_per_line = 3 * width if len(rgb_image.shape) == 3 else width

            img_bytes = rgb_image.tobytes()

            if len(rgb_image.shape) == 3:
                q_image = QImage(img_bytes, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            else:
                q_image = QImage(img_bytes, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)

            pixmap = QPixmap.fromImage(q_image)
            self.update_camera_preview(pixmap)

    def update_camera_status(self, status, is_connected=False):
        """Update the camera status label"""
        if hasattr(self, 'camera_status_label'):
            color = "#4caf50" if is_connected else "#d32f2f"
            self.camera_status_label.setText(f"Camera Status: {status}")
            self.camera_status_label.setStyleSheet(f"font-weight: bold; color: {color};")

    def on_parent_resize(self, event):
        """Handle parent widget resize events"""
        if hasattr(super(QWidget, self.parent_widget), 'resizeEvent'):
            super(QWidget, self.parent_widget).resizeEvent(event)

    def update_layout_for_screen_size(self):
        """Update layout based on current screen size"""
        self.clear_layout()
        self.create_main_content()

    def clear_layout(self):
        """Clear all widgets from the layout"""
        while self.count():
            child = self.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def create_main_content(self):
        """Create the main content with settings on left and preview on right"""
        main_horizontal_layout = QHBoxLayout()
        main_horizontal_layout.setSpacing(20)
        main_horizontal_layout.setContentsMargins(0, 0, 0, 0)

        # Create settings scroll area (left side)
        settings_scroll_area = QScrollArea()
        settings_scroll_area.setWidgetResizable(True)
        settings_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        settings_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        QScroller.grabGesture(settings_scroll_area.viewport(), QScroller.ScrollerGestureType.TouchGesture)

        settings_content_widget = QWidget()
        settings_content_layout = QVBoxLayout(settings_content_widget)
        settings_content_layout.setSpacing(20)
        settings_content_layout.setContentsMargins(0, 0, 0, 0)

        self.add_settings_to_layout(settings_content_layout)
        settings_content_layout.addStretch()

        settings_scroll_area.setWidget(settings_content_widget)

        # Create camera preview section (right side)
        preview_widget = self.create_camera_preview_section()

        # Add both sections to main horizontal layout
        main_horizontal_layout.addWidget(preview_widget, 2)
        main_horizontal_layout.addWidget(settings_scroll_area, 1)

        main_widget = QWidget()
        main_widget.setLayout(main_horizontal_layout)
        self.addWidget(main_widget)

    def add_settings_to_layout(self, parent_layout):
        """Add all settings groups to the layout in vertical arrangement"""
        # First row of settings
        first_row = QHBoxLayout()
        first_row.setSpacing(15)

        self.core_group = self.create_core_settings_group()
        self.contour_group = self.create_contour_settings_group()

        first_row.addWidget(self.core_group)
        first_row.addWidget(self.contour_group)

        parent_layout.addLayout(first_row)

        # Second row of settings
        second_row = QHBoxLayout()
        second_row.setSpacing(15)

        self.preprocessing_group = self.create_preprocessing_settings_group()
        self.calibration_group = self.create_calibration_settings_group()

        second_row.addWidget(self.preprocessing_group)
        second_row.addWidget(self.calibration_group)

        parent_layout.addLayout(second_row)

        # Third row of settings
        third_row = QHBoxLayout()
        third_row.setSpacing(15)

        self.brightness_group = self.create_brightness_settings_group()
        self.aruco_group = self.create_aruco_settings_group()

        third_row.addWidget(self.brightness_group)
        third_row.addWidget(self.aruco_group)

        parent_layout.addLayout(third_row)

    def create_core_settings_group(self):
        """Create core camera settings group"""
        group = QGroupBox("Camera Settings")
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Camera Index
        label = QLabel("Camera Index:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.camera_index_input = self.create_spinbox(0, 10, self.camera_settings.get_camera_index())
        layout.addWidget(self.camera_index_input, row, 1)

        # Width
        row += 1
        label = QLabel("Width:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.width_input = self.create_spinbox(320, 4096, self.camera_settings.get_camera_width(), " px")
        layout.addWidget(self.width_input, row, 1)

        # Height
        row += 1
        label = QLabel("Height:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.height_input = self.create_spinbox(240, 2160, self.camera_settings.get_camera_height(), " px")
        layout.addWidget(self.height_input, row, 1)

        # Skip Frames
        row += 1
        label = QLabel("Skip Frames:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.skip_frames_input = self.create_spinbox(0, 100, self.camera_settings.get_skip_frames())
        layout.addWidget(self.skip_frames_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_contour_settings_group(self):
        """Create contour detection settings group"""
        group = QGroupBox("Contour Detection")
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Contour Detection Toggle
        label = QLabel("Enable Detection:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.contour_detection_toggle = QToggle("Enable")
        self.contour_detection_toggle.setCheckable(True)
        self.contour_detection_toggle.setMinimumHeight(35)
        self.contour_detection_toggle.setChecked(self.camera_settings.get_contour_detection())
        layout.addWidget(self.contour_detection_toggle, row, 1)

        # Draw Contours Toggle
        row += 1
        label = QLabel("Draw Contours:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.draw_contours_toggle = QToggle("Draw")
        self.draw_contours_toggle.setCheckable(True)
        self.draw_contours_toggle.setMinimumHeight(35)
        self.draw_contours_toggle.setChecked(self.camera_settings.get_draw_contours())
        layout.addWidget(self.draw_contours_toggle, row, 1)

        # Threshold
        row += 1
        label = QLabel("Threshold:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.threshold_input = self.create_spinbox(0, 255, self.camera_settings.get_threshold())
        layout.addWidget(self.threshold_input, row, 1)

        # Epsilon
        row += 1
        label = QLabel("Epsilon:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.epsilon_input = self.create_double_spinbox(0.0, 1.0, self.camera_settings.get_epsilon())
        layout.addWidget(self.epsilon_input, row, 1)

        row+=1
        label = QLabel("Min Contour Area:")
        label.setWordWrap(True)
        layout.addWidget(label,row,0, Qt.AlignmentFlag.AlignLeft)
        self.min_contour_area_input = self.create_spinbox(0, 100000, self.camera_settings.get_min_contour_area())
        layout.addWidget(self.min_contour_area_input)

        row+=1
        label = QLabel("Max Contour Area:")
        label.setWordWrap(True)
        layout.addWidget(label,row,0, Qt.AlignmentFlag.AlignLeft)
        self.max_contour_area_input = self.create_spinbox(0, 10000000, self.camera_settings.get_max_contour_area())
        layout.addWidget(self.max_contour_area_input)

        layout.setColumnStretch(1, 1)
        return group

    def create_preprocessing_settings_group(self):
        """Create preprocessing settings group"""
        group = QGroupBox("Preprocessing")
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Gaussian Blur
        label = QLabel("Gaussian Blur:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.gaussian_blur_toggle = QToggle("Blur")
        self.gaussian_blur_toggle.setCheckable(True)
        self.gaussian_blur_toggle.setMinimumHeight(35)
        self.gaussian_blur_toggle.setChecked(self.camera_settings.get_gaussian_blur())
        layout.addWidget(self.gaussian_blur_toggle, row, 1)

        # Blur Kernel Size
        row += 1
        label = QLabel("Blur Kernel Size:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.blur_kernel_input = self.create_spinbox(1, 31, self.camera_settings.get_blur_kernel_size())
        layout.addWidget(self.blur_kernel_input, row, 1)

        # Threshold Type
        row += 1
        label = QLabel("Threshold Type:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.threshold_type_combo = QComboBox()
        self.threshold_type_combo.setMinimumHeight(40)
        self.threshold_type_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.threshold_type_combo.addItems(["binary", "binary_inv", "trunc", "tozero", "tozero_inv"])
        self.threshold_type_combo.setCurrentText(self.camera_settings.get_threshold_type())
        layout.addWidget(self.threshold_type_combo, row, 1)

        # Dilate Enabled
        row += 1
        label = QLabel("Dilate:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.dilate_enabled_toggle = QToggle("Dilate")
        self.dilate_enabled_toggle.setCheckable(True)
        self.dilate_enabled_toggle.setMinimumHeight(35)
        self.dilate_enabled_toggle.setChecked(self.camera_settings.get_dilate_enabled())
        layout.addWidget(self.dilate_enabled_toggle, row, 1)

        # Dilate Kernel Size
        row += 1
        label = QLabel("Dilate Kernel:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.dilate_kernel_input = self.create_spinbox(1, 31, self.camera_settings.get_dilate_kernel_size())
        layout.addWidget(self.dilate_kernel_input, row, 1)

        # Dilate Iterations
        row += 1
        label = QLabel("Dilate Iterations:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.dilate_iterations_input = self.create_spinbox(0, 20, self.camera_settings.get_dilate_iterations())
        layout.addWidget(self.dilate_iterations_input, row, 1)

        # Erode Enabled
        row += 1
        label = QLabel("Erode:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.erode_enabled_toggle = QToggle("Erode")
        self.erode_enabled_toggle.setCheckable(True)
        self.erode_enabled_toggle.setMinimumHeight(35)
        self.erode_enabled_toggle.setChecked(self.camera_settings.get_erode_enabled())
        layout.addWidget(self.erode_enabled_toggle, row, 1)

        # Erode Kernel Size
        row += 1
        label = QLabel("Erode Kernel:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.erode_kernel_input = self.create_spinbox(1, 31, self.camera_settings.get_erode_kernel_size())
        layout.addWidget(self.erode_kernel_input, row, 1)

        # Erode Iterations
        row += 1
        label = QLabel("Erode Iterations:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.erode_iterations_input = self.create_spinbox(0, 20, self.camera_settings.get_erode_iterations())
        layout.addWidget(self.erode_iterations_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_calibration_settings_group(self):
        """Create calibration settings group"""
        group = QGroupBox("Calibration")
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Chessboard Width
        label = QLabel("Chessboard Width:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.chessboard_width_input = self.create_spinbox(1, 100, self.camera_settings.get_chessboard_width())
        layout.addWidget(self.chessboard_width_input, row, 1)

        # Chessboard Height
        row += 1
        label = QLabel("Chessboard Height:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.chessboard_height_input = self.create_spinbox(1, 100, self.camera_settings.get_chessboard_height())
        layout.addWidget(self.chessboard_height_input, row, 1)

        # Square Size
        row += 1
        label = QLabel("Square Size:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.square_size_input = self.create_double_spinbox(1.0, 1000.0, self.camera_settings.get_square_size_mm(),
                                                            " mm")
        layout.addWidget(self.square_size_input, row, 1)

        # Calibration Skip Frames
        row += 1
        label = QLabel("Skip Frames:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.calib_skip_frames_input = self.create_spinbox(0, 100, self.camera_settings.get_calibration_skip_frames())
        layout.addWidget(self.calib_skip_frames_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_brightness_settings_group(self):
        """Create brightness control settings group"""
        group = QGroupBox("Brightness Control")
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Auto Brightness
        label = QLabel("Auto Brightness:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.brightness_auto_toggle = QToggle("Auto")
        self.brightness_auto_toggle.setCheckable(True)
        self.brightness_auto_toggle.setMinimumHeight(35)
        self.brightness_auto_toggle.setChecked(self.camera_settings.get_brightness_auto())
        layout.addWidget(self.brightness_auto_toggle, row, 1)

        # Kp
        row += 1
        label = QLabel("Kp:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.kp_input = self.create_double_spinbox(0.0, 10.0, self.camera_settings.get_brightness_kp())
        layout.addWidget(self.kp_input, row, 1)

        # Ki
        row += 1
        label = QLabel("Ki:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.ki_input = self.create_double_spinbox(0.0, 10.0, self.camera_settings.get_brightness_ki())
        layout.addWidget(self.ki_input, row, 1)

        # Kd
        row += 1
        label = QLabel("Kd:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.kd_input = self.create_double_spinbox(0.0, 10.0, self.camera_settings.get_brightness_kd())
        layout.addWidget(self.kd_input, row, 1)

        # Target Brightness
        row += 1
        label = QLabel("Target Brightness:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.target_brightness_input = self.create_spinbox(0, 255, self.camera_settings.get_target_brightness())
        layout.addWidget(self.target_brightness_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_aruco_settings_group(self):
        """Create ArUco detection settings group"""
        group = QGroupBox("ArUco Detection")
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # ArUco Enabled
        label = QLabel("Enable ArUco:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.aruco_enabled_toggle = QToggle("ArUco")
        self.aruco_enabled_toggle.setCheckable(True)
        self.aruco_enabled_toggle.setMinimumHeight(35)
        self.aruco_enabled_toggle.setChecked(self.camera_settings.get_aruco_enabled())
        layout.addWidget(self.aruco_enabled_toggle, row, 1)

        # ArUco Dictionary
        row += 1
        label = QLabel("Dictionary:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.aruco_dictionary_combo = QComboBox()
        self.aruco_dictionary_combo.setMinimumHeight(40)
        self.aruco_dictionary_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.aruco_dictionary_combo.addItems([
            "DICT_4X4_50", "DICT_4X4_100", "DICT_4X4_250", "DICT_4X4_1000",
            "DICT_5X5_50", "DICT_5X5_100", "DICT_5X5_250", "DICT_5X5_1000",
            "DICT_6X6_50", "DICT_6X6_100", "DICT_6X6_250", "DICT_6X6_1000",
            "DICT_7X7_50", "DICT_7X7_100", "DICT_7X7_250", "DICT_7X7_1000"
        ])
        self.aruco_dictionary_combo.setCurrentText(self.camera_settings.get_aruco_dictionary())
        layout.addWidget(self.aruco_dictionary_combo, row, 1)

        # Flip Image
        row += 1
        label = QLabel("Flip Image:")
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.aruco_flip_toggle = QToggle("Flip")
        self.aruco_flip_toggle.setCheckable(True)
        self.aruco_flip_toggle.setMinimumHeight(35)
        self.aruco_flip_toggle.setChecked(self.camera_settings.get_aruco_flip_image())
        layout.addWidget(self.aruco_flip_toggle, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def connectValueChangeCallbacks(self, callback):
        """Connect value change signals to callback methods with key, value, and className."""
        # Core settings
        self.camera_index_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.INDEX.value, value, "CameraSettingsTabLayout"))
        self.width_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.WIDTH.value, value, "CameraSettingsTabLayout"))
        self.height_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.HEIGHT.value, value, "CameraSettingsTabLayout"))
        self.skip_frames_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.SKIP_FRAMES.value, value, "CameraSettingsTabLayout"))

        # Contour detection
        self.contour_detection_toggle.toggled.connect(
            lambda value: callback(CameraSettingKey.CONTOUR_DETECTION.value, value, "CameraSettingsTabLayout"))
        self.draw_contours_toggle.toggled.connect(
            lambda value: callback(CameraSettingKey.DRAW_CONTOURS.value, value, "CameraSettingsTabLayout"))
        self.threshold_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.THRESHOLD.value, value, "CameraSettingsTabLayout"))
        self.epsilon_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.EPSILON.value, value, "CameraSettingsTabLayout"))
        self.min_contour_area_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.MIN_CONTOUR_AREA.value, value, "CameraSettingsTabLayout"))
        self.max_contour_area_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.MAX_CONTOUR_AREA.value, value, "CameraSettingsTabLayout"))

        # Preprocessing
        self.gaussian_blur_toggle.toggled.connect(
            lambda value: callback(CameraSettingKey.GAUSSIAN_BLUR.value, value, "CameraSettingsTabLayout"))
        self.blur_kernel_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.BLUR_KERNEL_SIZE.value, value, "CameraSettingsTabLayout"))
        self.threshold_type_combo.currentTextChanged.connect(
            lambda value: callback(CameraSettingKey.THRESHOLD_TYPE.value, value, "CameraSettingsTabLayout"))
        self.dilate_enabled_toggle.toggled.connect(
            lambda value: callback(CameraSettingKey.DILATE_ENABLED.value, value, "CameraSettingsTabLayout"))
        self.dilate_kernel_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.DILATE_KERNEL_SIZE.value, value, "CameraSettingsTabLayout"))
        self.dilate_iterations_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.DILATE_ITERATIONS.value, value, "CameraSettingsTabLayout"))
        self.erode_enabled_toggle.toggled.connect(
            lambda value: callback(CameraSettingKey.ERODE_ENABLED.value, value, "CameraSettingsTabLayout"))
        self.erode_kernel_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.ERODE_KERNEL_SIZE.value, value, "CameraSettingsTabLayout"))
        self.erode_iterations_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.ERODE_ITERATIONS.value, value, "CameraSettingsTabLayout"))

        # Calibration
        self.chessboard_width_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.CHESSBOARD_WIDTH.value, value, "CameraSettingsTabLayout"))
        self.chessboard_height_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.CHESSBOARD_HEIGHT.value, value, "CameraSettingsTabLayout"))
        self.square_size_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.SQUARE_SIZE_MM.value, value, "CameraSettingsTabLayout"))
        self.calib_skip_frames_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.CALIBRATION_SKIP_FRAMES.value, value, "CameraSettingsTabLayout"))

        # Brightness control
        self.brightness_auto_toggle.toggled.connect(
            lambda value: callback(CameraSettingKey.BRIGHTNESS_AUTO.value, value, "CameraSettingsTabLayout"))
        self.kp_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.BRIGHTNESS_KP.value, value, "CameraSettingsTabLayout"))
        self.ki_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.BRIGHTNESS_KI.value, value, "CameraSettingsTabLayout"))
        self.kd_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.BRIGHTNESS_KD.value, value, "CameraSettingsTabLayout"))
        self.target_brightness_input.valueChanged.connect(
            lambda value: callback(CameraSettingKey.TARGET_BRIGHTNESS.value, value, "CameraSettingsTabLayout"))

        # ArUco detection
        self.aruco_enabled_toggle.toggled.connect(
            lambda value: callback(CameraSettingKey.ARUCO_ENABLED.value, value, "CameraSettingsTabLayout"))
        self.aruco_dictionary_combo.currentTextChanged.connect(
            lambda value: callback(CameraSettingKey.ARUCO_DICTIONARY.value, value, "CameraSettingsTabLayout"))
        self.aruco_flip_toggle.toggled.connect(
            lambda value: callback(CameraSettingKey.ARUCO_FLIP_IMAGE.value, value, "CameraSettingsTabLayout"))

    def connect_default_callbacks(self):
        self.capture_image_button.clicked.connect(lambda: self.capture_image_requested.emit())
        self.show_raw_button.toggled.connect(self.toggle_raw_mode)
        self.start_calibration_button.clicked.connect(lambda: self.start_calibration_requested.emit())
        self.save_calibration_button.clicked.connect(lambda: self.save_calibration_requested.emit())
        self.load_calibration_button.clicked.connect(lambda: self.load_calibration_requested.emit())
        self.test_contour_button.clicked.connect(lambda: self.test_contour_detection_requested.emit())
        self.test_aruco_button.clicked.connect(lambda: self.test_aruco_detection_requested.emit())
        self.save_settings_button.clicked.connect(lambda: self.save_settings_requested.emit())
        self.load_settings_button.clicked.connect(lambda: self.load_settings_requested.emit())
        self.reset_settings_button.clicked.connect(lambda: self.reset_settings_requested.emit())

    def toggle_raw_mode(self, checked):
        """Toggle raw mode on/off"""
        self.raw_mode_active = checked

        if checked:
            self.show_raw_button.setText("Exit Raw Mode")
            self.show_raw_button.setStyleSheet("QPushButton { background-color: #ff6b6b; }")
        else:
            self.show_raw_button.setText("Raw Mode")
            self.show_raw_button.setStyleSheet("")

        self.raw_mode_requested.emit(self.raw_mode_active)

    def updateValues(self, camera_settings: CameraSettings):
        print("Updating input fields from CameraSettings object...")
        """Updates input field values from camera settings object."""
        # Core settings
        self.camera_index_input.setValue(camera_settings.get_camera_index())
        self.width_input.setValue(camera_settings.get_camera_width())
        self.height_input.setValue(camera_settings.get_camera_height())
        self.skip_frames_input.setValue(camera_settings.get_skip_frames())

        # Contour detection
        self.contour_detection_toggle.setChecked(camera_settings.get_contour_detection())
        self.draw_contours_toggle.setChecked(camera_settings.get_draw_contours())
        self.threshold_input.setValue(camera_settings.get_threshold())
        self.epsilon_input.setValue(camera_settings.get_epsilon())
        self.min_contour_area_input.setValue(camera_settings.get_min_contour_area())
        self.max_contour_area_input.setValue(camera_settings.get_max_contour_area())

        # Preprocessing
        self.gaussian_blur_toggle.setChecked(camera_settings.get_gaussian_blur())
        self.blur_kernel_input.setValue(camera_settings.get_blur_kernel_size())
        self.threshold_type_combo.setCurrentText(camera_settings.get_threshold_type())
        self.dilate_enabled_toggle.setChecked(camera_settings.get_dilate_enabled())
        self.dilate_kernel_input.setValue(camera_settings.get_dilate_kernel_size())
        self.dilate_iterations_input.setValue(camera_settings.get_dilate_iterations())
        self.erode_enabled_toggle.setChecked(camera_settings.get_erode_enabled())
        self.erode_kernel_input.setValue(camera_settings.get_erode_kernel_size())
        self.erode_iterations_input.setValue(camera_settings.get_erode_iterations())

        # Calibration
        self.chessboard_width_input.setValue(camera_settings.get_chessboard_width())
        self.chessboard_height_input.setValue(camera_settings.get_chessboard_height())
        self.square_size_input.setValue(camera_settings.get_square_size_mm())
        self.calib_skip_frames_input.setValue(camera_settings.get_calibration_skip_frames())

        # Brightness control
        self.brightness_auto_toggle.setChecked(camera_settings.get_brightness_auto())
        self.kp_input.setValue(camera_settings.get_brightness_kp())
        self.ki_input.setValue(camera_settings.get_brightness_ki())
        self.kd_input.setValue(camera_settings.get_brightness_kd())
        self.target_brightness_input.setValue(camera_settings.get_target_brightness())

        # ArUco detection
        self.aruco_enabled_toggle.setChecked(camera_settings.get_aruco_enabled())
        self.aruco_dictionary_combo.setCurrentText(camera_settings.get_aruco_dictionary())
        self.aruco_flip_toggle.setChecked(camera_settings.get_aruco_flip_image())
        print("Camera settings updated from CameraSettings object.")

    def getInputFields(self):
        """Returns the list of input fields."""
        return self.input_fields

    def getValues(self):
        """Returns a dictionary of current values from all input fields."""
        return {
            # Core settings
            CameraSettingKey.INDEX.value: self.camera_index_input.value(),
            CameraSettingKey.WIDTH.value: self.width_input.value(),
            CameraSettingKey.HEIGHT.value: self.height_input.value(),
            CameraSettingKey.SKIP_FRAMES.value: self.skip_frames_input.value(),

            # Contour detection
            CameraSettingKey.CONTOUR_DETECTION.value: self.contour_detection_toggle.isChecked(),
            CameraSettingKey.DRAW_CONTOURS.value: self.draw_contours_toggle.isChecked(),
            CameraSettingKey.THRESHOLD.value: self.threshold_input.value(),
            CameraSettingKey.EPSILON.value: self.epsilon_input.value(),
            CameraSettingKey.MIN_CONTOUR_AREA.value: self.min_contour_area_input.value(),
            CameraSettingKey.MAX_CONTOUR_AREA.value: self.max_contour_area_input.value(),

            # Preprocessing
            CameraSettingKey.GAUSSIAN_BLUR.value: self.gaussian_blur_toggle.isChecked(),
            CameraSettingKey.BLUR_KERNEL_SIZE.value: self.blur_kernel_input.value(),
            CameraSettingKey.THRESHOLD_TYPE.value: self.threshold_type_combo.currentText(),
            CameraSettingKey.DILATE_ENABLED.value: self.dilate_enabled_toggle.isChecked(),
            CameraSettingKey.DILATE_KERNEL_SIZE.value: self.dilate_kernel_input.value(),
            CameraSettingKey.DILATE_ITERATIONS.value: self.dilate_iterations_input.value(),
            CameraSettingKey.ERODE_ENABLED.value: self.erode_enabled_toggle.isChecked(),
            CameraSettingKey.ERODE_KERNEL_SIZE.value: self.erode_kernel_input.value(),
            CameraSettingKey.ERODE_ITERATIONS.value: self.erode_iterations_input.value(),

            # Calibration
            CameraSettingKey.CHESSBOARD_WIDTH.value: self.chessboard_width_input.value(),
            CameraSettingKey.CHESSBOARD_HEIGHT.value: self.chessboard_height_input.value(),
            CameraSettingKey.SQUARE_SIZE_MM.value: self.square_size_input.value(),
            CameraSettingKey.CALIBRATION_SKIP_FRAMES.value: self.calib_skip_frames_input.value(),

            # Brightness control
            CameraSettingKey.BRIGHTNESS_AUTO.value: self.brightness_auto_toggle.isChecked(),
            CameraSettingKey.BRIGHTNESS_KP.value: self.kp_input.value(),
            CameraSettingKey.BRIGHTNESS_KI.value: self.ki_input.value(),
            CameraSettingKey.BRIGHTNESS_KD.value: self.kd_input.value(),
            CameraSettingKey.TARGET_BRIGHTNESS.value: self.target_brightness_input.value(),

            # ArUco detection
            CameraSettingKey.ARUCO_ENABLED.value: self.aruco_enabled_toggle.isChecked(),
            CameraSettingKey.ARUCO_DICTIONARY.value: self.aruco_dictionary_combo.currentText(),
            CameraSettingKey.ARUCO_FLIP_IMAGE.value: self.aruco_flip_toggle.isChecked(),
        }



    def showToast(self, message):
        """Show toast notification"""
        if self.parent_widget:
            toast = ToastWidget(self.parent_widget, message, 5)
            toast.show()
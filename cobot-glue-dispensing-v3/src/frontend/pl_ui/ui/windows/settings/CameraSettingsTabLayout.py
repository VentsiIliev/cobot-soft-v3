from PyQt6 import QtCore
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QScroller
from PyQt6.QtWidgets import (QVBoxLayout, QLabel, QWidget, QHBoxLayout,
                             QSizePolicy, QComboBox, QScrollArea, QGroupBox, QGridLayout, QPushButton)

from frontend.pl_ui.ui.widgets.ClickableLabel import ClickableLabel
from frontend.pl_ui.ui.widgets.MaterialButton import MaterialButton
from modules.shared.core.settings.conreateSettings.CameraSettings import CameraSettings
from modules.shared.core.settings.conreateSettings.enums.CameraSettingKey import CameraSettingKey
from frontend.pl_ui.ui.widgets.SwitchButton import QToggle
from frontend.pl_ui.ui.widgets.ToastWidget import ToastWidget
from frontend.pl_ui.ui.windows.settings.BaseSettingsTabLayout import BaseSettingsTabLayout
import cv2
from frontend.pl_ui.localization import TranslationKeys, get_app_translator
from PyQt6.QtWidgets import QSpinBox, QDoubleSpinBox
from modules.shared.MessageBroker import MessageBroker
from modules.shared.v1.topics import VisionTopics

class CameraSettingsTabLayout(BaseSettingsTabLayout, QVBoxLayout):
    # Unified signal for all value changes - eliminates callback duplication
    value_changed_signal = pyqtSignal(str, object, str)  # key, value, component_type
    
    # Action signals
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
        self.translator = get_app_translator()
        self.translator.language_changed.connect(self.translate)
        print(f"CameraSettingsTabLayout initialized with camera settings: {self.camera_settings}")
        self.update_camera_feed_callback = update_camera_feed_callback

        # Create main content with new layout
        self.create_main_content()
        
        # Connect all widget signals to unified emission pattern
        self._connect_widget_signals()

        self.updateFrequency = 30  # in milliseconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.update_camera_feed_signal.emit())
        self.timer.start(self.updateFrequency)

        # Connect to parent widget resize events if possible
        if self.parent_widget:
            self.parent_widget.resizeEvent = self.on_parent_resize

        broker = MessageBroker()
        broker.subscribe(topic=VisionTopics.SERVICE_STATE,
                         callback=self.onVisionSystemStateUpdate)
        broker.subscribe(topic=VisionTopics.THRESHOLD_IMAGE,
                          callback= self.update_threshold_preview_from_cv2)

    """CAMERA PREVIEW METHODS"""

    def onVisionSystemStateUpdate(self,message):

        # Check if we need to initialize the current state
        if not hasattr(self, 'current_camera_state'):
            self.current_camera_state = None

        # Only update if state has changed
        if self.current_camera_state == message.value:
            return  # No change, skip update

        self.current_camera_state = message.value


        if hasattr(self, 'camera_status_label') and self.camera_status_label is not None:
            self.camera_status_label.setText(f"{self.translator.get(TranslationKeys.CameraSettings.CAMERA_STATUS)}: {message.value}")

            # Set label color based on state
            if message.value == "running":
                self.camera_status_label.setStyleSheet("color: green; font-weight: bold;")
            elif message.value == "initializing":
                self.camera_status_label.setStyleSheet("color: #FFA500; font-weight: bold;")  # Orange/yellow
            else:
                self.camera_status_label.setStyleSheet("color: red; font-weight: bold;")  # Default for other states
        else:
            print(f"Camera status update received but label not ready: {message.value}")

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
        self.camera_preview_label = ClickableLabel("Calibration Preview")
        self.camera_preview_label.clicked.connect(self.on_preview_clicked)
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

        # Threshold preview area
        self.threshold_preview_label = ClickableLabel("Threshold Preview")
        self.threshold_preview_label.clicked.connect(self.on_threshold_preview_clicked)
        self.threshold_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.threshold_preview_label.setStyleSheet("""
            QLabel {
                background-color: #222;
                color: white;
                font-size: 16px;
                border: 1px solid #666;
                border-radius: 4px;
            }
        """)
        self.threshold_preview_label.setFixedSize(460, 259)
        self.threshold_preview_label.setScaledContents(False)
        preview_layout.addWidget(self.threshold_preview_label)

        # Control buttons grid
        button_grid = QGridLayout()
        button_grid.setSpacing(10)

        # Row 0: Camera buttons
        self.capture_image_button = MaterialButton("Capture Image")
        self.show_raw_button = MaterialButton("Raw Mode")
        self.show_raw_button.setCheckable(True)
        self.show_raw_button.setChecked(self.raw_mode_active)

        cam_buttons = [self.capture_image_button, self.show_raw_button]
        for i, btn in enumerate(cam_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 0, i)

        # Row 1: Calibration buttons
        self.start_calibration_button = MaterialButton("Start Calibration")
        self.save_calibration_button = MaterialButton("Save Calibration")

        calib_buttons = [self.start_calibration_button, self.save_calibration_button]
        for i, btn in enumerate(calib_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 1, i)

        # Row 2: More buttons
        self.load_calibration_button = MaterialButton("Load Calibration")
        self.test_contour_button = MaterialButton("Test Contour")

        more_buttons = [self.load_calibration_button, self.test_contour_button]
        for i, btn in enumerate(more_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 2, i)

        # Row 3: Detection and ArUco
        self.test_aruco_button = MaterialButton("Test ArUco")
        spacer_btn = QWidget()

        detect_buttons = [self.test_aruco_button, spacer_btn]
        for i, widget in enumerate(detect_buttons):
            if isinstance(widget, MaterialButton):
                widget.setMinimumHeight(40)
            button_grid.addWidget(widget, 3, i)

        # Row 4: Settings buttons
        self.save_settings_button = MaterialButton("Save Settings")
        self.load_settings_button = MaterialButton("Load Settings")

        settings_buttons = [self.save_settings_button, self.load_settings_button]
        for i, btn in enumerate(settings_buttons):
            btn.setMinimumHeight(40)
            button_grid.addWidget(btn, 4, i)

        # Row 5: Reset button
        self.reset_settings_button = MaterialButton("Reset Defaults")
        self.reset_settings_button.setMinimumHeight(40)
        button_grid.addWidget(self.reset_settings_button, 5, 0, 1, 2)

        # preview_layout.addLayout(button_grid)
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

    def update_threshold_preview_from_cv2(self, cv2_threshold_image):
        """Update the threshold preview with a threshold image"""
        if not self._is_widget_valid('threshold_preview_label'):
            return
            
        try:
            # Convert to RGB if needed
            if len(cv2_threshold_image.shape) == 3:
                rgb_image = cv2_threshold_image[:, :, ::-1]  # BGR to RGB
                height, width = rgb_image.shape[:2]
                bytes_per_line = 3 * width
                q_image = QImage(rgb_image.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
            else:
                # Grayscale threshold image
                height, width = cv2_threshold_image.shape[:2]
                bytes_per_line = width
                q_image = QImage(cv2_threshold_image.tobytes(), width, height, bytes_per_line, QImage.Format.Format_Grayscale8)

            pixmap = QPixmap.fromImage(q_image)
            self.update_threshold_preview(pixmap)
        except RuntimeError as e:
            # Widget was deleted during execution
            print(f"Widget deleted during threshold preview update: {e}")
            self._cleanup_if_destroyed()

    def update_threshold_preview(self, pixmap):
        """Update the threshold preview with a new pixmap, maintaining aspect ratio"""
        if not self._is_widget_valid('threshold_preview_label'):
            return
            
        try:
            label_size = self.threshold_preview_label.size()
            scaled_pixmap = pixmap.scaled(
                label_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.threshold_preview_label.setPixmap(scaled_pixmap)
            self.threshold_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except RuntimeError as e:
            # Widget was deleted during execution
            print(f"Widget deleted during threshold preview update: {e}")
            self._cleanup_if_destroyed()

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

    def _is_widget_valid(self, widget_name):
        """Check if a widget exists and is still valid (not deleted)"""
        if not hasattr(self, widget_name):
            return False
        widget = getattr(self, widget_name)
        try:
            # Try to access a basic property to see if widget is still valid
            _ = widget.isVisible()
            return True
        except RuntimeError:
            # Widget has been deleted
            return False
    
    def _cleanup_if_destroyed(self):
        """Clean up MessageBroker subscriptions if widget is destroyed"""
        try:
            broker = MessageBroker()
            broker.unsubscribe(VisionTopics.SERVICE_STATE, self.onVisionSystemStateUpdate)
            broker.unsubscribe(VisionTopics.THRESHOLD_IMAGE, self.update_threshold_preview_from_cv2)
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def clean_up(self):
        broker = MessageBroker()
        broker.unsubscribe(VisionTopics.SERVICE_STATE, self.onVisionSystemStateUpdate)
        broker.unsubscribe(VisionTopics.THRESHOLD_IMAGE, self.update_threshold_preview_from_cv2)

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
        self.translate()

    def on_preview_clicked(self, x, y):
        try:
            label = getattr(self, "camera_preview_label", None)
            pixmap = label.pixmap() if label is not None else None
            if pixmap is None:
                print(f"Preview Clicked on {x}:{y} - no image available")
                return

            label_w = label.width()
            label_h = label.height()
            img_w = pixmap.width()
            img_h = pixmap.height()

            # Calculate top-left of the drawn pixmap inside the label (centered alignment)
            left = (label_w - img_w) // 2
            top = (label_h - img_h) // 2

            # Map click coordinates to pixmap coordinates
            ix = int(x - left)
            iy = int(y - top)

            if not (0 <= ix < img_w and 0 <= iy < img_h):
                print(f"Preview Clicked on {x}:{y} - outside image area")
                return

            qimage = pixmap.toImage()
            color = qimage.pixelColor(ix, iy)
            r, g, b = color.red(), color.green(), color.blue()

            # Use OpenCV to convert the RGB pixel to grayscale
            import numpy as np
            arr = np.uint8([[[r, g, b]]])  # shape (1,1,3)
            gray = int(cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)[0, 0])

            # Print RGB and grayscale value
            print(f"Preview Clicked on {x}:{y} - pixel (R,G,B) = ({r},{g},{b}) - Grayscale = {gray}")

            self.showToast(f"(R,G,B) = ({r},{g},{b}) ; Grayscale = {gray}")
        except Exception as e:
            print(f"Exception in on_preview_clicked: {e}")

    def on_threshold_preview_clicked(self, x, y):
        """Handle threshold preview clicks"""
        try:
            label = getattr(self, "threshold_preview_label", None)
            pixmap = label.pixmap() if label is not None else None
            if pixmap is None:
                print(f"Threshold Preview Clicked on {x}:{y} - no image available")
                return

            label_w = label.width()
            label_h = label.height()
            img_w = pixmap.width()
            img_h = pixmap.height()

            # Calculate top-left of the drawn pixmap inside the label (centered alignment)
            left = (label_w - img_w) // 2
            top = (label_h - img_h) // 2

            # Map click coordinates to pixmap coordinates
            ix = int(x - left)
            iy = int(y - top)

            if not (0 <= ix < img_w and 0 <= iy < img_h):
                print(f"Threshold Preview Clicked on {x}:{y} - outside image area")
                return

            qimage = pixmap.toImage()
            color = qimage.pixelColor(ix, iy)
            r, g, b = color.red(), color.green(), color.blue()

            # For threshold images, typically they are grayscale
            gray = r  # Since it's a threshold image, R=G=B
            threshold_value = "255" if gray > 127 else "0"
            
            print(f"Threshold Preview Clicked on {x}:{y} - pixel value = {gray}, threshold = {threshold_value}")
            self.showToast(f"Threshold value: {threshold_value} (gray: {gray})")
        except Exception as e:
            print(f"Exception in on_threshold_preview_clicked: {e}")

    def showToast(self, message):
        """Show toast notification"""
        if self.parent_widget:
            toast = ToastWidget(self.parent_widget, message, 5)
            toast.show()

    def create_core_settings_group(self):
        """Create core camera settings group"""
        group = QGroupBox("Camera Settings") # TODO TRANSLATE
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Camera Index
        label = QLabel("Camera Index:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.camera_index_input = self.create_spinbox(0, 10, self.camera_settings.get_camera_index())
        layout.addWidget(self.camera_index_input, row, 1)

        # Width
        row += 1
        label = QLabel("Width:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.width_input = self.create_spinbox(320, 4096, self.camera_settings.get_camera_width(), " px")
        layout.addWidget(self.width_input, row, 1)

        # Height
        row += 1
        label = QLabel("Height:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.height_input = self.create_spinbox(240, 2160, self.camera_settings.get_camera_height(), " px")
        layout.addWidget(self.height_input, row, 1)

        # Skip Frames
        row += 1
        label = QLabel("Skip Frames:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.skip_frames_input = self.create_spinbox(0, 100, self.camera_settings.get_skip_frames())
        layout.addWidget(self.skip_frames_input, row, 1)

        row += 1
        label = QLabel("Capture Pos Offset:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.capture_pos_offset_input = self.create_spinbox(-100, 100, self.camera_settings.get_capture_pos_offset(), " mm")
        layout.addWidget(self.capture_pos_offset_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_contour_settings_group(self):
        """Create contour detection settings group"""
        group = QGroupBox("Contour Detection") # TODO TRANSLATE
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Contour Detection Toggle
        label = QLabel("Enable Detection:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.contour_detection_toggle = QToggle()
        self.contour_detection_toggle.setCheckable(True)
        self.contour_detection_toggle.setMinimumHeight(35)
        self.contour_detection_toggle.setChecked(self.camera_settings.get_contour_detection())
        layout.addWidget(self.contour_detection_toggle, row, 1)

        # Draw Contours Toggle
        row += 1
        label = QLabel("Draw Contours:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.draw_contours_toggle = QToggle()
        self.draw_contours_toggle.setCheckable(True)
        self.draw_contours_toggle.setMinimumHeight(35)
        self.draw_contours_toggle.setChecked(self.camera_settings.get_draw_contours())
        layout.addWidget(self.draw_contours_toggle, row, 1)

        # Threshold
        row += 1
        label = QLabel("Threshold:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.threshold_input = self.create_spinbox(0, 255, self.camera_settings.get_threshold())
        layout.addWidget(self.threshold_input, row, 1)

        row+=1
        label = QLabel("Threshold 2:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.threshold_pickup_area_input = self.create_spinbox(0, 255, self.camera_settings.get_threshold_pickup_area())
        layout.addWidget(self.threshold_pickup_area_input, row, 1)

        # Epsilon
        row += 1
        label = QLabel("Epsilon:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.epsilon_input = self.create_double_spinbox(0.0, 1.0, self.camera_settings.get_epsilon())
        layout.addWidget(self.epsilon_input, row, 1)

        row += 1
        label = QLabel("Min Contour Area:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.min_contour_area_input = self.create_spinbox(0, 100000, self.camera_settings.get_min_contour_area())
        layout.addWidget(self.min_contour_area_input)

        row += 1
        label = QLabel("Max Contour Area:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.max_contour_area_input = self.create_spinbox(0, 10000000, self.camera_settings.get_max_contour_area())
        layout.addWidget(self.max_contour_area_input)

        layout.setColumnStretch(1, 1)
        return group

    def create_preprocessing_settings_group(self):
        """Create preprocessing settings group"""
        group = QGroupBox("Preprocessing") # TODO TRANSLATE
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Gaussian Blur
        label = QLabel("Gaussian Blur:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.gaussian_blur_toggle = QToggle()
        self.gaussian_blur_toggle.setCheckable(True)
        self.gaussian_blur_toggle.setMinimumHeight(35)
        self.gaussian_blur_toggle.setChecked(self.camera_settings.get_gaussian_blur())
        layout.addWidget(self.gaussian_blur_toggle, row, 1)

        # Blur Kernel Size
        row += 1
        label = QLabel("Blur Kernel Size:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.blur_kernel_input = self.create_spinbox(1, 31, self.camera_settings.get_blur_kernel_size())
        layout.addWidget(self.blur_kernel_input, row, 1)

        # Threshold Type
        row += 1
        label = QLabel("Threshold Type:") # TODO TRANSLATE
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
        label = QLabel("Dilate:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.dilate_enabled_toggle = QToggle()
        self.dilate_enabled_toggle.setCheckable(True)
        self.dilate_enabled_toggle.setMinimumHeight(35)
        self.dilate_enabled_toggle.setChecked(self.camera_settings.get_dilate_enabled())
        layout.addWidget(self.dilate_enabled_toggle, row, 1)

        # Dilate Kernel Size
        row += 1
        label = QLabel("Dilate Kernel:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.dilate_kernel_input = self.create_spinbox(1, 31, self.camera_settings.get_dilate_kernel_size())
        layout.addWidget(self.dilate_kernel_input, row, 1)

        # Dilate Iterations
        row += 1
        label = QLabel("Dilate Iterations:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.dilate_iterations_input = self.create_spinbox(0, 20, self.camera_settings.get_dilate_iterations())
        layout.addWidget(self.dilate_iterations_input, row, 1)

        # Erode Enabled
        row += 1
        label = QLabel("Erode:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.erode_enabled_toggle = QToggle()
        self.erode_enabled_toggle.setCheckable(True)
        self.erode_enabled_toggle.setMinimumHeight(35)
        self.erode_enabled_toggle.setChecked(self.camera_settings.get_erode_enabled())
        layout.addWidget(self.erode_enabled_toggle, row, 1)

        # Erode Kernel Size
        row += 1
        label = QLabel("Erode Kernel:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.erode_kernel_input = self.create_spinbox(1, 31, self.camera_settings.get_erode_kernel_size())
        layout.addWidget(self.erode_kernel_input, row, 1)

        # Erode Iterations
        row += 1
        label = QLabel("Erode Iterations:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.erode_iterations_input = self.create_spinbox(0, 20, self.camera_settings.get_erode_iterations())
        layout.addWidget(self.erode_iterations_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_calibration_settings_group(self):
        """Create calibration settings group"""
        group = QGroupBox("Calibration") # TODO TRANSLATE
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Chessboard Width
        label = QLabel("Chessboard Width:")  # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.chessboard_width_input = self.create_spinbox(1, 100, self.camera_settings.get_chessboard_width())
        layout.addWidget(self.chessboard_width_input, row, 1)

        # Chessboard Height
        row += 1
        label = QLabel("Chessboard Height:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.chessboard_height_input = self.create_spinbox(1, 100, self.camera_settings.get_chessboard_height())
        layout.addWidget(self.chessboard_height_input, row, 1)

        # Square Size
        row += 1
        label = QLabel("Square Size:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.square_size_input = self.create_double_spinbox(1.0, 1000.0, self.camera_settings.get_square_size_mm(),
                                                            " mm")
        layout.addWidget(self.square_size_input, row, 1)

        # Calibration Skip Frames
        row += 1
        label = QLabel("Skip Frames:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.calib_skip_frames_input = self.create_spinbox(0, 100, self.camera_settings.get_calibration_skip_frames())
        layout.addWidget(self.calib_skip_frames_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_brightness_settings_group(self):
        """Create brightness control settings group"""
        group = QGroupBox("Brightness Control") # TODO TRANSLATE
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # Auto Brightness
        label = QLabel("Auto Brightness:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.brightness_auto_toggle = QToggle()
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
        label = QLabel("Target Brightness:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.target_brightness_input = self.create_spinbox(0, 255, self.camera_settings.get_target_brightness())
        layout.addWidget(self.target_brightness_input, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def create_aruco_settings_group(self):
        """Create ArUco detection settings group"""
        group = QGroupBox("ArUco Detection") # TODO TRANSLATE
        layout = QGridLayout(group)

        layout.setSpacing(15)
        layout.setContentsMargins(20, 25, 20, 20)

        row = 0

        # ArUco Enabled
        label = QLabel("Enable ArUco:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.aruco_enabled_toggle = QToggle()
        self.aruco_enabled_toggle.setCheckable(True)
        self.aruco_enabled_toggle.setMinimumHeight(35)
        self.aruco_enabled_toggle.setChecked(self.camera_settings.get_aruco_enabled())
        layout.addWidget(self.aruco_enabled_toggle, row, 1)

        # ArUco Dictionary
        row += 1
        label = QLabel("Dictionary:") # TODO TRANSLATE
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
        label = QLabel("Flip Image:") # TODO TRANSLATE
        label.setWordWrap(True)
        layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignLeft)
        self.aruco_flip_toggle = QToggle()
        self.aruco_flip_toggle.setCheckable(True)
        self.aruco_flip_toggle.setMinimumHeight(35)
        self.aruco_flip_toggle.setChecked(self.camera_settings.get_aruco_flip_image())
        layout.addWidget(self.aruco_flip_toggle, row, 1)

        layout.setColumnStretch(1, 1)
        return group

    def _connect_widget_signals(self):
        """
        Connect all widget signals to the unified value_changed_signal.
        This eliminates callback duplication while maintaining the same interface.
        """
        widget_mappings = [
            # Core settings
            (self.camera_index_input, CameraSettingKey.INDEX.value, 'valueChanged'),
            (self.width_input, CameraSettingKey.WIDTH.value, 'valueChanged'),
            (self.height_input, CameraSettingKey.HEIGHT.value, 'valueChanged'),
            (self.skip_frames_input, CameraSettingKey.SKIP_FRAMES.value, 'valueChanged'),
            (self.capture_pos_offset_input, CameraSettingKey.CAPTURE_POS_OFFSET.value, 'valueChanged'),
            
            # Contour detection
            (self.contour_detection_toggle, CameraSettingKey.CONTOUR_DETECTION.value, 'toggled'),
            (self.draw_contours_toggle, CameraSettingKey.DRAW_CONTOURS.value, 'toggled'),
            (self.threshold_input, CameraSettingKey.THRESHOLD.value, 'valueChanged'),
            (self.threshold_pickup_area_input, CameraSettingKey.THRESHOLD_PICKUP_AREA.value, 'valueChanged'),
            (self.epsilon_input, CameraSettingKey.EPSILON.value, 'valueChanged'),
            (self.min_contour_area_input, CameraSettingKey.MIN_CONTOUR_AREA.value, 'valueChanged'),
            (self.max_contour_area_input, CameraSettingKey.MAX_CONTOUR_AREA.value, 'valueChanged'),
            
            # Preprocessing
            (self.gaussian_blur_toggle, CameraSettingKey.GAUSSIAN_BLUR.value, 'toggled'),
            (self.blur_kernel_input, CameraSettingKey.BLUR_KERNEL_SIZE.value, 'valueChanged'),
            (self.threshold_type_combo, CameraSettingKey.THRESHOLD_TYPE.value, 'currentTextChanged'),
            (self.dilate_enabled_toggle, CameraSettingKey.DILATE_ENABLED.value, 'toggled'),
            (self.dilate_kernel_input, CameraSettingKey.DILATE_KERNEL_SIZE.value, 'valueChanged'),
            (self.dilate_iterations_input, CameraSettingKey.DILATE_ITERATIONS.value, 'valueChanged'),
            (self.erode_enabled_toggle, CameraSettingKey.ERODE_ENABLED.value, 'toggled'),
            (self.erode_kernel_input, CameraSettingKey.ERODE_KERNEL_SIZE.value, 'valueChanged'),
            (self.erode_iterations_input, CameraSettingKey.ERODE_ITERATIONS.value, 'valueChanged'),
            
            # Calibration
            (self.chessboard_width_input, CameraSettingKey.CHESSBOARD_WIDTH.value, 'valueChanged'),
            (self.chessboard_height_input, CameraSettingKey.CHESSBOARD_HEIGHT.value, 'valueChanged'),
            (self.square_size_input, CameraSettingKey.SQUARE_SIZE_MM.value, 'valueChanged'),
            (self.calib_skip_frames_input, CameraSettingKey.CALIBRATION_SKIP_FRAMES.value, 'valueChanged'),
            
            # Brightness control
            (self.brightness_auto_toggle, CameraSettingKey.BRIGHTNESS_AUTO.value, 'toggled'),
            (self.kp_input, CameraSettingKey.BRIGHTNESS_KP.value, 'valueChanged'),
            (self.ki_input, CameraSettingKey.BRIGHTNESS_KI.value, 'valueChanged'),
            (self.kd_input, CameraSettingKey.BRIGHTNESS_KD.value, 'valueChanged'),
            (self.target_brightness_input, CameraSettingKey.TARGET_BRIGHTNESS.value, 'valueChanged'),
            
            # ArUco detection
            (self.aruco_enabled_toggle, CameraSettingKey.ARUCO_ENABLED.value, 'toggled'),
            (self.aruco_dictionary_combo, CameraSettingKey.ARUCO_DICTIONARY.value, 'currentTextChanged'),
            (self.aruco_flip_toggle, CameraSettingKey.ARUCO_FLIP_IMAGE.value, 'toggled'),
        ]
        
        for widget, setting_key, signal_name in widget_mappings:
            if hasattr(widget, signal_name):
                signal = getattr(widget, signal_name)
                signal.connect(
                    lambda value, key=setting_key: self._emit_setting_change(key, value)
                )
    
    def _emit_setting_change(self, key: str, value):
        """
        Emit the unified value_changed_signal with setting information.
        
        Args:
            key: The setting key
            value: The new value
        """
        self.value_changed_signal.emit(key, value, self.__class__.__name__)
    
    def connectValueChangeCallbacks(self, callback):
        """
        Legacy method for backward compatibility.
        Now connects the unified signal to the provided callback.
        """
        self.value_changed_signal.connect(lambda key, value, component_type: callback(key, value, component_type))

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
            self.show_raw_button.setText(self.translator.get(TranslationKeys.CameraSettings.EXIT_RAW_MODE))
            self.show_raw_button.setStyleSheet("QPushButton { background-color: #ff6b6b; }")
        else:
            self.show_raw_button.setText(self.translator.get(TranslationKeys.CameraSettings.RAW_MODE))
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
        self.capture_pos_offset_input.setValue(camera_settings.get_capture_pos_offset())

        # Contour detection
        self.contour_detection_toggle.setChecked(camera_settings.get_contour_detection())
        self.draw_contours_toggle.setChecked(camera_settings.get_draw_contours())
        self.threshold_input.setValue(camera_settings.get_threshold())
        self.threshold_pickup_area_input.setValue(camera_settings.get_threshold_pickup_area())
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

    def translate(self):
        """Update UI text based on current language"""
        print(f"Translating CameraSettingsTabLayout...")
        
        # Update styling to ensure responsive fonts are applied
        self.setup_styling()
        
        # Core settings group
        if hasattr(self, 'core_group'):
            self.core_group.setTitle(self.translator.get(TranslationKeys.CameraSettings.CAMERA_SETTINGS))
            # Update core settings labels by accessing the layout
            core_layout = self.core_group.layout()
            if core_layout:
                # Camera Index
                if core_layout.itemAtPosition(0, 0):
                    core_layout.itemAtPosition(0, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.CAMERA_INDEX))
                # Width
                if core_layout.itemAtPosition(1, 0):
                    core_layout.itemAtPosition(1, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.WIDTH))
                # Height
                if core_layout.itemAtPosition(2, 0):
                    core_layout.itemAtPosition(2, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.HEIGHT))
                # Skip Frames
                if core_layout.itemAtPosition(3, 0):
                    core_layout.itemAtPosition(3, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.SKIP_FRAMES))
            
        # Contour settings group  
        if hasattr(self, 'contour_group'):
            self.contour_group.setTitle(self.translator.get(TranslationKeys.CameraSettings.CONTOUR_DETECTION))
            # Update contour settings labels
            contour_layout = self.contour_group.layout()
            if contour_layout:
                # Enable Detection
                if contour_layout.itemAtPosition(0, 0):
                    contour_layout.itemAtPosition(0, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.ENABLE_DETECTION))
                # Draw Contours
                if contour_layout.itemAtPosition(1, 0):
                    contour_layout.itemAtPosition(1, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.DRAW_CONTOURS))
                # Threshold
                if contour_layout.itemAtPosition(2, 0):
                    contour_layout.itemAtPosition(2, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.THRESHOLD))
                # Threshold Pickup Area
                if contour_layout.itemAtPosition(3, 0):
                    contour_layout.itemAtPosition(3, 0).widget().setText(
                        f"{self.translator.get(TranslationKeys.CameraSettings.THRESHOLD)} 2")
                # Epsilon
                if contour_layout.itemAtPosition(4, 0):
                    contour_layout.itemAtPosition(5, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.EPSILON))
                # Min Contour Area
                if contour_layout.itemAtPosition(5, 0):
                    contour_layout.itemAtPosition(5, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.MIN_CONTOUR_AREA))
                # Max Contour Area
                if contour_layout.itemAtPosition(6, 0):
                    contour_layout.itemAtPosition(6, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.MAX_CONTOUR_AREA))
            
        # Preprocessing settings group
        if hasattr(self, 'preprocessing_group'):
            self.preprocessing_group.setTitle(self.translator.get(TranslationKeys.CameraSettings.PREPROCESSING))
            # Update preprocessing settings labels
            preprocessing_layout = self.preprocessing_group.layout()
            if preprocessing_layout:
                # Gaussian Blur
                if preprocessing_layout.itemAtPosition(0, 0):
                    preprocessing_layout.itemAtPosition(0, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.GAUSSIAN_BLUR))
                # Blur Kernel Size
                if preprocessing_layout.itemAtPosition(1, 0):
                    preprocessing_layout.itemAtPosition(1, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.BLUR_KERNEL_SIZE))
                # Threshold Type
                if preprocessing_layout.itemAtPosition(2, 0):
                    preprocessing_layout.itemAtPosition(2, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.THRESHOLD_TYPE))
                # Dilate
                if preprocessing_layout.itemAtPosition(3, 0):
                    preprocessing_layout.itemAtPosition(3, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.DILATE))
                # Dilate Kernel
                if preprocessing_layout.itemAtPosition(4, 0):
                    preprocessing_layout.itemAtPosition(4, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.DILATE_KERNEL))
                # Dilate Iterations
                if preprocessing_layout.itemAtPosition(5, 0):
                    preprocessing_layout.itemAtPosition(5, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.DILATE_ITERATIONS))
                # Erode
                if preprocessing_layout.itemAtPosition(6, 0):
                    preprocessing_layout.itemAtPosition(6, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.ERODE))
                # Erode Kernel
                if preprocessing_layout.itemAtPosition(7, 0):
                    preprocessing_layout.itemAtPosition(7, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.ERODE_KERNEL))
                # Erode Iterations
                if preprocessing_layout.itemAtPosition(8, 0):
                    preprocessing_layout.itemAtPosition(8, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.ERODE_ITERATIONS))
            
        # Calibration settings group
        if hasattr(self, 'calibration_group'):
            self.calibration_group.setTitle(self.translator.get(TranslationKeys.CameraSettings.CALIBRATION))
            # Update calibration settings labels
            calibration_layout = self.calibration_group.layout()
            if calibration_layout:
                # Chessboard Width
                if calibration_layout.itemAtPosition(0, 0):
                    calibration_layout.itemAtPosition(0, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.CHESSBOARD_WIDTH))
                # Chessboard Height
                if calibration_layout.itemAtPosition(1, 0):
                    calibration_layout.itemAtPosition(1, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.CHESSBOARD_HEIGHT))
                # Square Size
                if calibration_layout.itemAtPosition(2, 0):
                    calibration_layout.itemAtPosition(2, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.SQUARE_SIZE))
                # Skip Frames (calibration)
                if calibration_layout.itemAtPosition(3, 0):
                    calibration_layout.itemAtPosition(3, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.SKIP_FRAMES))
            
        # Brightness settings group
        if hasattr(self, 'brightness_group'):
            self.brightness_group.setTitle(self.translator.get(TranslationKeys.CameraSettings.BRIGHTNESS_CONTROL))
            # Update brightness settings labels
            brightness_layout = self.brightness_group.layout()
            if brightness_layout:
                # Auto Brightness
                if brightness_layout.itemAtPosition(0, 0):
                    brightness_layout.itemAtPosition(0, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.AUTO_BRIGHTNESS))
                # Kp (keep as is, technical term)
                # Ki (keep as is, technical term)
                # Kd (keep as is, technical term)
                # Target Brightness
                if brightness_layout.itemAtPosition(4, 0):
                    brightness_layout.itemAtPosition(4, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.TARGET_BRIGHTNESS))
            
        # ArUco settings group
        if hasattr(self, 'aruco_group'):
            self.aruco_group.setTitle(self.translator.get(TranslationKeys.CameraSettings.ARUCO_DETECTION))
            # Update ArUco settings labels
            aruco_layout = self.aruco_group.layout()
            if aruco_layout:
                # Enable ArUco
                if aruco_layout.itemAtPosition(0, 0):
                    aruco_layout.itemAtPosition(0, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.ENABLE_ARUCO))
                # Dictionary
                if aruco_layout.itemAtPosition(1, 0):
                    aruco_layout.itemAtPosition(1, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.DICTIONARY))
                # Flip Image
                if aruco_layout.itemAtPosition(2, 0):
                    aruco_layout.itemAtPosition(2, 0).widget().setText(
                        self.translator.get(TranslationKeys.CameraSettings.FLIP_IMAGE))
            
        # Update camera status label (dynamic content)
        if hasattr(self, 'camera_status_label') and hasattr(self, 'current_camera_state'):
            self.camera_status_label.setText(
                f"{self.translator.get(TranslationKeys.CameraSettings.CAMERA_STATUS)}: {self.current_camera_state}")
            
        # Update camera preview label

        # # Update button texts
        # if hasattr(self, 'capture_image_button'):
        #     self.capture_image_button.setText(self.translator.get(TranslationKeys.CameraSettings.CAPTURE_IMAGE))
        if hasattr(self, 'show_raw_button'):
            if self.raw_mode_active:
                self.show_raw_button.setText(self.translator.get(TranslationKeys.CameraSettings.EXIT_RAW_MODE))
            else:
                self.show_raw_button.setText(self.translator.get(TranslationKeys.CameraSettings.RAW_MODE))
        # if hasattr(self, 'start_calibration_button'):
        #     self.start_calibration_button.setText(self.translator.get(TranslationKeys.CameraSettings.START_CALIBRATION))
        # if hasattr(self, 'save_calibration_button'):
        #     self.save_calibration_button.setText(self.translator.get(TranslationKeys.CameraSettings.SAVE_CALIBRATION))
        # if hasattr(self, 'load_calibration_button'):
        #     self.load_calibration_button.setText(self.translator.get(TranslationKeys.CameraSettings.LOAD_CALIBRATION))
        # if hasattr(self, 'test_contour_button'):
        #     self.test_contour_button.setText(self.translator.get(TranslationKeys.CameraSettings.TEST_CONTOUR))
        # if hasattr(self, 'test_aruco_button'):
        #     self.test_aruco_button.setText(self.translator.get(TranslationKeys.CameraSettings.TEST_ARUCO))
        # if hasattr(self, 'save_settings_button'):
        #     self.save_settings_button.setText(self.translator.get(TranslationKeys.CameraSettings.SAVE_SETTINGS))
        # if hasattr(self, 'load_settings_button'):
        #     self.load_settings_button.setText(self.translator.get(TranslationKeys.CameraSettings.LOAD_SETTINGS))
        # if hasattr(self, 'reset_settings_button'):
        #     self.reset_settings_button.setText(self.translator.get(TranslationKeys.CameraSettings.RESET_DEFAULTS))

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget

    app = QApplication(sys.argv)
    main_widget = QWidget()
    layout = CameraSettingsTabLayout(main_widget)
    main_widget.setLayout(layout)
    main_widget.show()
    sys.exit(app.exec())

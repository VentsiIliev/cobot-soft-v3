import os
from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSizePolicy,
    QMessageBox, QApplication, QSpacerItem
)
from frontend.pl_ui.utils.IconLoader import PICKUP_POINT_ICON

ICON_WIDTH = 64
ICON_HEIGHT = 64

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","icons")
print("Resource Directory:", RESOURCE_DIR)
REMOVE_ICON = os.path.join(RESOURCE_DIR, "remove.png")
UNDO_ICON = os.path.join(RESOURCE_DIR, "undo.png")
REDO_ICON = os.path.join(RESOURCE_DIR, "redo.png")
DRAG_ICON = os.path.join(RESOURCE_DIR, "drag.png")
PREVIEW_ICON = os.path.join(RESOURCE_DIR, "preview.png")
RESET_ZOOM_ICON = os.path.join(RESOURCE_DIR, "reset_zoom.png")
ZIGZAG_ICON = os.path.join(RESOURCE_DIR, "zigzag.png")
OFFSET_ICON = os.path.join(RESOURCE_DIR, "offset.png")
POINTER_ICON = os.path.join(RESOURCE_DIR, "pointer.png")
SAVE_ICON = os.path.join(RESOURCE_DIR, "SAVE_BUTTON.png")
ZOOM_IN = os.path.join(RESOURCE_DIR, "zoom_in.png")
ZOOM_OUT = os.path.join(RESOURCE_DIR, "zoom_out.png")
CAPTURE_IMAGE = os.path.join(RESOURCE_DIR, "CAPTURE_IMAGE.png")

SETTINGS_ICON = os.path.join(RESOURCE_DIR, "SETTINGS_BUTTON.png")
TOOLS_ICON = os.path.join(RESOURCE_DIR, "TOOLS.png")
START_ICON = os.path.join(RESOURCE_DIR, "START_BUTTON.png")



ACTIVE_BUTTON_STYLE = """
    border: none;
    padding: 5px;
    margin: 5px;
    background-color: #6750A4;
"""
NORMAL_BUTTON_STYLE = """
    border: none;
    padding: 5px;
    margin: 5px;
"""


class TopBarWidget(QWidget):
    capture_requested = pyqtSignal()
    save_requested = pyqtSignal()
    start_requested = pyqtSignal()
    zigzag_requested = pyqtSignal()
    offset_requested = pyqtSignal()
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    preview_requested = pyqtSignal()

    multi_select_mode_requested = pyqtSignal()  # Signal to toggle multi-select mode
    remove_points_requested = pyqtSignal()  # Signal to request point deletion
    settings_requested = pyqtSignal()

    tools_requested = pyqtSignal()
    def __init__(self, contour_editor=None, point_manager=None):
        super().__init__()
        self.contour_editor = contour_editor
        self.point_manager = point_manager

        self.setMinimumHeight(50)
        self.setMaximumHeight(150)
        self.setMinimumWidth(300)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left section (Undo/Redo)
        self.left_layout = QHBoxLayout()
        self.left_layout.setSpacing(0)
        self.left_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.undo_button = self.create_button(UNDO_ICON, self.undo_requested.emit)
        self.redo_button = self.create_button(REDO_ICON, self.redo_requested.emit)
        self.left_layout.addWidget(self.undo_button)
        self.left_layout.addWidget(self.redo_button)

        # Center section (other buttons)
        self.center_layout = QHBoxLayout()
        self.center_layout.setSpacing(0)
        self.center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.remove_button = self.create_button(REMOVE_ICON, self.dummy_remove_action)
        self.remove_button.setToolTip("Remove selected point(s)\nLong press to enter multi-selection mode")
        self.capture_image_button = self.create_button(CAPTURE_IMAGE, self.on_capture_image)

        self.settings_button = self.create_button(SETTINGS_ICON, self.settings_requested.emit)
        self.tools_button = self.create_button(TOOLS_ICON, self.tools_requested.emit)

        # Pickup point
        self.pickup_point_button = self.create_button(PICKUP_POINT_ICON, self.toggle_pickup_point_mode)
        self.pickup_point_button.setCheckable(True)

        self.preview_path_button = self.create_button(PREVIEW_ICON, self.preview_requested.emit)

        self.zigzag_button = self.create_button(ZIGZAG_ICON, self.zigzag_requested.emit)
        self.offset_button = self.create_button(OFFSET_ICON,self.offset_requested.emit)

        # Group of mutually exclusive mode buttons
        self.exclusive_buttons = [
            self.pickup_point_button,
        ]
        for btn in self.exclusive_buttons:
            btn.toggled.connect(lambda checked, b=btn: self.handle_exclusive_toggle(b, checked))

        self.center_layout.addWidget(self.tools_button)
        self.center_layout.addWidget(self.settings_button)
        self.center_layout.addWidget(self.capture_image_button)
        self.center_layout.addWidget(self.remove_button)
        self.center_layout.addWidget(self.pickup_point_button)
        self.center_layout.addWidget(self.preview_path_button)

        self.center_layout.addWidget(self.zigzag_button)
        self.center_layout.addWidget(self.offset_button)

        self.center_layout.addStretch()

        # Right section (Save)
        self.right_layout = QHBoxLayout()
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)


        self.startButton = self.create_button(START_ICON, self.start_requested.emit,"")
        self.save_button = self.create_button(SAVE_ICON, self.save_requested.emit)

        self.right_layout.addWidget(self.startButton)
        self.right_layout.addWidget(self.save_button)

        # Add all to main layout
        main_layout.addLayout(self.left_layout)
        main_layout.addStretch()
        main_layout.addLayout(self.center_layout)
        main_layout.addStretch()
        main_layout.addLayout(self.right_layout)

        self.buttons = [self.remove_button, self.pickup_point_button, self.preview_path_button,
                        self.zigzag_button, self.offset_button, self.undo_button,
                        self.redo_button, self.save_button]

        self.setLayout(main_layout)

        self.multi_select_mode_active = False

        # Setup long press functionality for remove button
        self.setup_remove_button_long_press()

    def handle_exclusive_toggle(self, toggled_button, checked):
        """Ensure only one checkable mode button stays active at a time."""
        if checked:
            # Uncheck all other buttons in the exclusive group
            for btn in self.exclusive_buttons:
                if btn is not toggled_button:
                    btn.blockSignals(True)
                    btn.setChecked(False)
                    btn.blockSignals(False)
                    self.update_checkable_style(btn, False)

            # Apply active style to the toggled one
            self.update_checkable_style(toggled_button, True)
        else:
            # Return to normal style if unchecked manually
            self.update_checkable_style(toggled_button, False)

    def update_checkable_style(self, button, checked):
        """Apply consistent styling for active (checked) and normal (unchecked) buttons."""
        if checked:
            button.setStyleSheet(ACTIVE_BUTTON_STYLE)
        else:
            button.setStyleSheet(NORMAL_BUTTON_STYLE)


    def dummy_remove_action(self):
        """Dummy action for remove button - actual logic handled in mouse events"""
        pass

    def on_capture_image(self):
        self.capture_requested.emit()


    def add_spacer(self, layout=None, width=20):
        if layout is None:
            layout = self.center_layout  # Default to center if none provided
        spacer = QWidget()
        spacer.setFixedWidth(width)
        layout.addWidget(spacer)

    def create_button(self, icon_path, click_handler, text=None):
        button = QPushButton("")
        if icon_path:
            button.setIcon(QIcon(icon_path))
        if text:
            button.setText(text)
        button.setStyleSheet("border: none; padding: 5px; margin: 5px;")
        button.setIconSize(QSize(ICON_WIDTH, ICON_HEIGHT))
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.clicked.connect(click_handler)
        return button


    def toggle_pickup_point_mode(self):
        """Toggle pickup point mode on/off"""
        if not self.contour_editor:
            QMessageBox.warning(self, "Error", "Contour editor is not set.")
            return

        try:
            is_pickup_mode = self.pickup_point_button.isChecked()

            if is_pickup_mode:
                # Exit multi-select mode if active
                if hasattr(self.contour_editor, 'multi_select_mode_active') and self.contour_editor.multi_select_mode_active:
                    self.multi_select_mode_requested.emit()  # Toggle off via signal

                # Switch to pickup point mode
                self.contour_editor.set_cursor_mode("pickup_point")
                self.update_checkable_style(self.pickup_point_button, is_pickup_mode)

                print("Pickup point mode activated")
            else:
                # Switch back to edit mode
                self.contour_editor.set_cursor_mode("edit")
                self.update_checkable_style(self.pickup_point_button, is_pickup_mode)

                print("Pickup point mode deactivated")

        except Exception as e:
            QMessageBox.critical(self, "Pickup Point Mode Toggle Failed", str(e))

    def setup_remove_button_long_press(self):
        """Setup long press functionality for the remove button"""
        self.long_press_timer = QTimer()
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self.enter_multi_select_mode)

        # Override the remove button's mouse events
        self.remove_button.mousePressEvent = self.remove_button_mouse_press
        self.remove_button.mouseReleaseEvent = self.remove_button_mouse_release

    def remove_button_mouse_press(self, event):
        """Handle mouse press on remove button - start long press timer"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.long_press_timer.start(800)  # 800ms for long press
            # Call the original press event
            QPushButton.mousePressEvent(self.remove_button, event)

    def remove_button_mouse_release(self, event):
        """Handle mouse release on remove button"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.long_press_timer.isActive():
                # Short press - request point removal via signal
                self.long_press_timer.stop()
                self.remove_points_requested.emit()
            # Call the original release event
            QPushButton.mouseReleaseEvent(self.remove_button, event)

    def enter_multi_select_mode(self):
        """Toggle multi-selection mode via long press - emit signal"""
        # Emit signal to toggle multi-select mode
        # The actual logic is handled by the handler connected to this signal
        self.multi_select_mode_requested.emit()

    def update_multi_select_ui(self, is_active):
        """Update UI to reflect multi-select mode state (called from handler)"""
        self.multi_select_mode_active = is_active

        if is_active:
            self.remove_button.setStyleSheet("border: none; padding: 5px; margin: 5px; background-color: #6750A4;")
            self.remove_button.setToolTip("Multi-Selection Mode Active\nClick points to select/deselect\nShort press to delete selected points\nLong press again to exit")

            # Exit pickup point mode if active
            if self.pickup_point_button.isChecked():
                self.pickup_point_button.setChecked(False)
                self.pickup_point_button.setStyleSheet("border: none; padding: 5px; margin: 5px;")
        else:
            self.remove_button.setStyleSheet("border: none; padding: 5px; margin: 5px;")
            self.remove_button.setToolTip("Remove selected point(s)\nLong press to enter multi-selection mode")


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    widget = TopBarWidget()
    widget.show()
    sys.exit(app.exec())

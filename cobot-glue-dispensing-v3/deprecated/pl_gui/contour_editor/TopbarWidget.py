import os
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSizePolicy,
    QMessageBox, QApplication, QSpacerItem
)

ICON_WIDTH = 64
ICON_HEIGHT = 64

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

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


class TopBarWidget(QWidget):
    def __init__(self, contour_editor=None, point_manager=None, save_button_callback=None,onStartCallback = None,zigzag_callback=None, offset_callback=None):
        super().__init__()

        self.zigzag_callback = zigzag_callback
        self.offset_callback = offset_callback
        self.contour_editor = contour_editor
        self.point_manager = point_manager
        self.save_button_callback = save_button_callback
        self.onStartCallback = onStartCallback
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
        self.undo_button = self.create_button(UNDO_ICON, self.undo_action)
        self.redo_button = self.create_button(REDO_ICON, self.redo_action)
        self.left_layout.addWidget(self.undo_button)
        self.left_layout.addWidget(self.redo_button)

        # Center section (other buttons)
        self.center_layout = QHBoxLayout()
        self.center_layout.setSpacing(0)
        self.center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.remove_button = self.create_button(REMOVE_ICON, self.remove_selected_point)
        self.mode_toggle_button = self.create_button(DRAG_ICON, self.toggle_cursor_mode)
        self.preview_path_button = self.create_button(PREVIEW_ICON, self.on_preview)
        self.zigzag_button = self.create_button(ZIGZAG_ICON, self.on_zigzag)
        self.offset_button = self.create_button(OFFSET_ICON, self.on_offset)

        self.add_spacer(self.center_layout)

        self.zoom_out_button = self.create_button(ZOOM_OUT, self.on_zoom_out)
        self.reset_zoom_button = self.create_button(RESET_ZOOM_ICON, self.reset_zoom)
        self.zoom_in_button = self.create_button(ZOOM_IN, self.on_zoom_in)

        self.center_layout.addWidget(self.remove_button)
        self.center_layout.addWidget(self.mode_toggle_button)
        self.center_layout.addWidget(self.preview_path_button)
        self.center_layout.addWidget(self.zigzag_button)
        self.center_layout.addWidget(self.offset_button)

        self.center_layout.addStretch()

        self.center_layout.addWidget(self.zoom_out_button)
        self.center_layout.addWidget(self.reset_zoom_button)
        self.center_layout.addWidget(self.zoom_in_button)

        # for btn in [
        #     self.remove_button, self.mode_toggle_button, self.preview_path_button,
        #     self.zigzag_button, self.offset_button,
        #     self.zoom_out_button, self.reset_zoom_button, self.zoom_in_button
        # ]:
        #     self.center_layout.addWidget(btn)

        # Right section (Save)
        self.right_layout = QHBoxLayout()
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.startButton = QPushButton("Start")

        self.startButton.setStyleSheet("border: none; padding: 5px; margin: 5px;")


        self.startButton.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.startButton.clicked.connect(self.onStart)

        self.save_button = self.create_button(SAVE_ICON, save_button_callback or self.on_save)
        self.right_layout.addWidget(self.startButton)
        self.right_layout.addWidget(self.save_button)

        # Add all to main layout
        main_layout.addLayout(self.left_layout)
        main_layout.addStretch()
        main_layout.addLayout(self.center_layout)
        main_layout.addStretch()
        main_layout.addLayout(self.right_layout)

        self.buttons = [self.remove_button, self.mode_toggle_button, self.preview_path_button,
                        self.zigzag_button, self.offset_button,
                        self.zoom_out_button, self.reset_zoom_button, self.zoom_in_button, self.undo_button,
                        self.redo_button, self.save_button]

        self.setLayout(main_layout)

        self.is_drag_mode = False

    def onStart(self):
        print("Start button pressed")

        if self.onStartCallback:

            self.onStartCallback()

    def add_spacer(self, layout=None, width=20):
        if layout is None:
            layout = self.center_layout  # Default to center if none provided
        spacer = QWidget()
        spacer.setFixedWidth(width)
        layout.addWidget(spacer)

    def set_save_button_callback(self, callback):
        self.save_button.clicked.connect(callback)

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

    def on_zoom_in(self):
        print("Zooming in")
        self.contour_editor.zoom_in()

    def on_zoom_out(self):
        print("Zooming out")
        self.contour_editor.zoom_out()

    def on_save(self):
        print("Save button pressed")

    def on_zigzag(self):
        print("Zigzag button clicked")
        if self.zigzag_callback is not None:
            self.zigzag_callback()

    def on_offset(self):
        print("Offset button clicked")
        if self.offset_callback is not None:
            self.offset_callback()

    def on_preview(self):
        self.contour_editor.save_robot_path_to_txt("preview.txt", samples_per_segment=5)
        self.contour_editor.plot_robot_path("preview.txt")

    def reset_zoom(self):
        if not self.contour_editor:
            QMessageBox.warning(self, "Error", "Contour editor is not set.")
            return
        try:
            self.contour_editor.reset_zoom()
            self.contour_editor.update()
        except Exception as e:
            QMessageBox.critical(self, "Reset Zoom Failed", str(e))

    def toggle_cursor_mode(self):
        if not self.contour_editor:
            QMessageBox.warning(self, "Error", "Contour editor is not set.")
            return

        self.is_drag_mode = not self.is_drag_mode
        new_mode = "drag" if self.is_drag_mode else "edit"

        try:
            self.contour_editor.set_cursor_mode(new_mode)
            icon = POINTER_ICON if self.is_drag_mode else DRAG_ICON
            self.mode_toggle_button.setIcon(QIcon(icon))
        except Exception as e:
            QMessageBox.critical(self, "Mode Toggle Failed", str(e))

    def undo_action(self):
        if not self.contour_editor:
            QMessageBox.warning(self, "Error", "Contour editor is not set.")
            return
        try:
            self.contour_editor.manager.undo()
            self.point_manager.refresh_points()
            self.contour_editor.update()
        except Exception as e:
            QMessageBox.critical(self, "Undo Failed", str(e))

    def redo_action(self):
        if not self.contour_editor:
            QMessageBox.warning(self, "Error", "Contour editor is not set.")
            return
        try:
            self.contour_editor.manager.redo()
            self.point_manager.refresh_points()
            self.contour_editor.update()
        except Exception as e:
            QMessageBox.critical(self, "Redo Failed", str(e))

    def remove_selected_point(self):
        item = self.point_manager.tree.currentItem()
        if not item or not self.contour_editor or not item.parent():
            return
        try:
            seg_index = int(item.parent().text(0)[1:])
            label = item.text(0)
            if label.startswith("P"):
                idx = int(label[1:])
                self.contour_editor.manager.remove_point('anchor', seg_index, idx)
            elif label.startswith("C"):
                idx = int(label[1:])
                self.contour_editor.manager.remove_point('control', seg_index, idx)
            self.point_manager.refresh_points()
            self.contour_editor.update()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    widget = TopBarWidget()
    widget.show()
    sys.exit(app.exec())

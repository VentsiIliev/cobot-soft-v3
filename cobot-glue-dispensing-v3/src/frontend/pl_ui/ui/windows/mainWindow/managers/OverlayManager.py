from PyQt6.QtCore import QTimer

from src.frontend.pl_ui.ui.windows.mainWindow.FolderOverlay import FolderOverlay


class OverlayManager:
    """Handles overlay creation and styling - WITH DEBUG"""

    def __init__(self, parent_widget, overlay_parent, overlay_callback):
        self.parent_widget = parent_widget
        self.overlay_parent = overlay_parent
        # print(f"OverlayManager: Initializing with parent_widget={parent_widget}, overlay_parent={overlay_parent}")
        self.overlay = FolderOverlay(overlay_parent)
        self.overlay.mouse_pressed_outside.connect(overlay_callback)

    def show_overlay(self):
        """Create and show overlay - WITH DEBUG"""
        try:
            self.overlay.resize(self.overlay_parent.size())
            self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.32);")
            self.overlay.fade_in()
        except Exception as e:
            import traceback
            traceback.print_exc()
            # print(f"OverlayManager: Exception during overlay setup: {e}")
            return None
        # print("OverlayManager: Overlay created and shown successfully")
        return self.overlay

    def set_style(self, style):
        # print(f"OverlayManager: Setting overlay style: {style}")
        if self.overlay:
            self.overlay.setStyleSheet(style)

    def hide_overlay(self):
        # print("OverlayManager: Hiding overlay")
        if self.overlay:
            self.overlay.fade_out()
            # QTimer.singleShot(300, self._cleanup)

    def _cleanup(self):
        # print("OverlayManager: Cleaning up overlay")
        if self.overlay:
            self.overlay.deleteLater()
            self.overlay = None

    def _get_main_window(self):
        parent = self.parent_widget.parent()
        while parent and parent.parent():
            parent = parent.parent()
        return parent

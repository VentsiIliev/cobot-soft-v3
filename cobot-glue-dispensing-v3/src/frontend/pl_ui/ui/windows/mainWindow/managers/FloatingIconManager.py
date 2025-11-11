from PyQt6.QtCore import QTimer


class FloatingIconManager:
    """Fixed floating icon manager"""

    def __init__(self, parent_widget):
        self.parent_widget = parent_widget
        self.floating_icon = None
        self._cleanup_timer = None

    def show_floating_icon(self, folder_name, on_click_callback):
        """Create and show floating icon with safer cleanup"""
        if self.floating_icon:
            self._safe_cleanup()

        main_window = self._get_main_window()
        if not main_window:
            return

        from src.frontend.pl_ui.ui.windows.mainWindow.FloatingFolderIcon import FloatingFolderIcon
        self.floating_icon = FloatingFolderIcon(folder_name, main_window)
        self.floating_icon.move(10, 10)
        self.floating_icon.clicked_signal.connect(on_click_callback)
        self.floating_icon.show_with_animation()

    def hide_floating_icon(self):
        """Hide and cleanup floating icon safely"""
        if self.floating_icon and not self.floating_icon.isHidden():
            self.floating_icon.hide_with_animation()
            # Schedule cleanup after animation
            self._cleanup_timer = QTimer()
            self._cleanup_timer.setSingleShot(True)
            self._cleanup_timer.timeout.connect(self._safe_cleanup)
            self._cleanup_timer.start(300)

    def _safe_cleanup(self):
        """Safer cleanup"""
        if self.floating_icon:
            try:
                self.floating_icon.clicked_signal.disconnect()
            except:
                pass

            self.floating_icon.deleteLater()
            self.floating_icon = None

        if self._cleanup_timer:
            self._cleanup_timer.stop()
            self._cleanup_timer = None
        # print("FloatingIconManager: Floating icon cleaned up")

    def _get_main_window(self):
        parent = self.parent_widget.parent()
        while parent and parent.parent():
            parent = parent.parent()
        return parent
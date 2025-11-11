from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QWidget

from src.frontend.pl_ui.ui.windows.mainWindow.managers.AnimationManager import AnimationManager


class FolderOverlay(QWidget):
    """Overlay widget that appears when folder is opened"""

    # close_requested = pyqtSignal()
    mouse_pressed_outside = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.disable_overlay_close = False
        self.animation_manager = AnimationManager(self)

    def fade_in(self):
        """Animate overlay appearance"""
        self.animation_manager.fade_in(
            start_opacity=0.0,
            end_opacity=1.0
        )

    def fade_out(self):
        """Animate overlay disappearance"""
        self.animation_manager.fade_out(
            hide_on_finish=True
        )

    def mousePressEvent(self, event):
        """Close folder when clicking outside, unless disabled"""
        self.mouse_pressed_outside.emit()



if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    overlay = FolderOverlay()
    overlay.resize(800, 600)
    overlay.fade_in()
    overlay.show()
    sys.exit(app.exec())
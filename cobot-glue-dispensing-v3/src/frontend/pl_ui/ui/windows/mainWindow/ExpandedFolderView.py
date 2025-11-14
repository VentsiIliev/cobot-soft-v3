# ========================================
# REFACTORED ExpandedFolderView.py - Step 1
# ========================================
# Remove folder_ref dependency and FloatingIcon logic
# Make it a simpler, more focused component

from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QFrame, QScrollArea,
    QGraphicsDropShadowEffect, QPushButton
)
from PyQt6.QtGui import QFont, QColor

from frontend.pl_ui.localization.mixins import TranslatableQFrame
from frontend.pl_ui.localization import TranslationKeys
from frontend.pl_ui.ui.windows.mainWindow.managers.AnimationManager import AnimationManager


class ExpandedFolderView(TranslatableQFrame):
    """Material Design 3 expanded folder view - simplified without folder_ref dependency"""

    # Simplified signals
    close_requested = pyqtSignal()
    app_selected = pyqtSignal(str)
    close_current_app_requested = pyqtSignal()
    minimize_requested = pyqtSignal()  # NEW: Request minimize to floating icon

    def __init__(self, folder_name, parent=None):
        super().__init__(parent)
        self.setObjectName("ExpandedFolderView")
        self.folder_name = folder_name  # Just store the name, no reference
        self.setFixedSize(580, 680)  # Material Design proportions

        # Simplified state management
        self._is_closing = False
        self._current_app_name = None

        self.close_app_button = None

        self.setup_ui()
        self.animation_manager = AnimationManager(self)
        self.animation_manager.animation_finished.connect(self._on_animation_finished)

        self.init_translations()

    def setup_ui(self):
        """Material Design 3 surface styling"""
        self.setStyleSheet("""
            QFrame {
                background: #FFFBFE;
                border: 1px solid #E7E0EC;
                border-radius: 28px;
            }
        """)

        # Material Design elevation shadow
        try:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(32)
            shadow.setColor(QColor(0, 0, 0, 30))  # Material elevation 3
            shadow.setOffset(0, 6)
            self.setGraphicsEffect(shadow)
        except:
            pass

        # Material Design layout with proper spacing
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(24)  # Material Design spacing
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Header with Material Design typography
        header_layout = QHBoxLayout()

        # Material Design headline typography
        self.title_label = QLabel(self.folder_name)
        self.title_label.setObjectName("FolderTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Material Design typography
        try:
            font = QFont("Roboto", 28, QFont.Weight.Medium)
            if not font.exactMatch():
                font = QFont("Segoe UI", 28, QFont.Weight.Medium)
            self.title_label.setFont(font)
        except:
            pass

        self.title_label.setStyleSheet("""
            QLabel {
                color: #1D1B20;
                background-color: transparent;
                padding-bottom: 8px;
                font-weight: 500;
                letter-spacing: 0px;
            }
        """)

        # Material Design filled button for close app
        self.close_app_button = QPushButton("Close App")
        self.close_app_button.setFixedSize(140, 40)
        self.close_app_button.setStyleSheet("""
            QPushButton {
                background: #6750A4;
                border: none;
                border-radius: 20px;
                color: white;
                font-size: 14px;
                font-weight: 500;
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background: #7965AF;
            }
            QPushButton:pressed {
                background: #5A3D99;
            }
        """)
        self.close_app_button.clicked.connect(self.on_close_app_clicked)
        self.close_app_button.hide()

        # Material Design button shadow
        try:
            close_button_shadow = QGraphicsDropShadowEffect()
            close_button_shadow.setBlurRadius(8)
            close_button_shadow.setColor(QColor(0, 0, 0, 40))
            close_button_shadow.setOffset(0, 2)
            self.close_app_button.setGraphicsEffect(close_button_shadow)
        except:
            pass

        header_layout.addStretch(1)
        # header_layout.addWidget(self.title_label, 2)
        header_layout.addWidget(self.close_app_button, 0, Qt.AlignmentFlag.AlignRight)

        main_layout.addLayout(header_layout)

        # Material Design scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("ExpandedScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent; 
            }
            QScrollBar:vertical {
                background-color: #F7F2FA;
                width: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background-color: #CAC4D0;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #79747E;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
        """)

        grid_widget = QWidget()
        grid_widget.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(16)  # Material Design grid spacing
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        self.scroll_area.setWidget(grid_widget)
        main_layout.addWidget(self.scroll_area)

    def add_app_icon(self, app_icon_widget, row, col):
        """Add an app icon to the grid - called by Folder class"""
        self.grid_layout.addWidget(app_icon_widget, row, col)

    def safe_close(self):
        """Material Design close transition"""
        if self._is_closing:
            return

        self._is_closing = True
        self.fade_out()

    def fade_in(self, center_pos):
        """Material Design scale-in animation"""
        # print(f"Material fade_in called with center_pos: {center_pos}")

        # Stop any existing animations
        self.animation_manager.stop_all_animations()

        # Use AnimationManager for consistent behavior
        self.animation_manager.combined_fade_and_scale_in(
            center_pos=center_pos,
            callback=self.animation_finished
        )

    def fade_out(self):
        """Material Design scale-out animation"""
        if self.animation_manager.has_active_animations():
            return

        self.animation_manager.combined_fade_and_scale_out(
            hide_on_finish=True,
            callback=self.animation_finished
        )

    def on_app_clicked(self, app_name):
        """Handle app selection - simplified without FloatingIcon logic"""
        # print(f"Material Design app selected: {app_name}")
        self._current_app_name = app_name
        self.app_selected.emit(app_name)
        self.show_close_app_button()

        # CHANGED: Request minimize instead of handling FloatingIcon internally
        self.minimize_requested.emit()

    def show_close_app_button(self):
        """Material Design button reveal animation"""
        if self.close_app_button and self._current_app_name:
            self.close_app_button.setText(f"BACK")
            self.close_app_button.show()

            # Material Design fade-in
            self.close_app_button.setWindowOpacity(0.0)
            button_animation = QPropertyAnimation(self.close_app_button, b"windowOpacity")
            button_animation.setDuration(200)
            button_animation.setStartValue(0.0)
            button_animation.setEndValue(1.0)
            button_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            button_animation.start()

    def hide_close_app_button(self):
        """Hide close button with Material Design transition"""
        if self.close_app_button:
            self.close_app_button.hide()
        self._current_app_name = None

    def on_close_app_clicked(self):
        """Handle close app button click - simplified"""
        # print(f"Material Design close app: {self._current_app_name}")
        self.close_current_app_requested.emit()
        self.hide_close_app_button()

        # Close the entire folder view when back button is pressed
        self.close_requested.emit()

    def set_app_running_state(self, app_name=None):
        """Update app state with Material Design consistency"""
        if app_name:
            self._current_app_name = app_name
            self.show_close_app_button()
        else:
            self.hide_close_app_button()

    def animation_finished(self):
        """Animation completion handler"""
        if self._is_closing:
            QTimer.singleShot(0, self.safe_hide)

    def _on_animation_finished(self, animation_id: str):
        """Handle specific animation completion"""
        # print(f"Animation completed: {animation_id}")
        pass


    def safe_hide(self):
        """Safe hide with Material Design cleanup"""
        if self._is_closing:
            QTimer.singleShot(0, self.hide)

    def mousePressEvent(self, event):
        """Accept mouse events to prevent propagation"""
        event.accept()

    def closeEvent(self, event):
        """Material Design close event handling"""
        self._is_closing = True

        # Clean up grid layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()
        event.accept()


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton

    app = QApplication(sys.argv)

    # Material Design application styling
    app.setStyle('Fusion')
    app.setStyleSheet("""
        QApplication {
            font-family: 'Roboto', 'Segoe UI', sans-serif;
            background: #FFFBFE;
        }
    """)

    main_window = QMainWindow()
    main_window.resize(900, 700)
    main_window.setStyleSheet("""
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #FFFBFE,
                stop:1 #F7F2FA);
        }
    """)

    # Test the refactored ExpandedFolderView
    folder_view = ExpandedFolderView("Material Apps", main_window)

    # Connect test signals
    folder_view.close_requested.connect(lambda: print("Close requested"))
    folder_view.app_selected.connect(lambda name: print(f"App selected: {name}"))
    folder_view.minimize_requested.connect(lambda: print("Minimize requested"))

    folder_view.fade_in(main_window.rect().center())
    main_window.setCentralWidget(folder_view)
    main_window.show()

    # Test button to trigger minimize
    test_button = QPushButton("Test Minimize", main_window)
    test_button.setGeometry(10, 10, 200, 48)
    test_button.setStyleSheet("""
        QPushButton {
            background: #6750A4;
            border: none;
            border-radius: 24px;
            color: white;
            font-size: 14px;
            font-weight: 500;
            font-family: 'Roboto', 'Segoe UI', sans-serif;
        }
        QPushButton:hover {
            background: #7965AF;
        }
    """)
    test_button.clicked.connect(folder_view.minimize_requested.emit)
    test_button.show()

    sys.exit(app.exec())
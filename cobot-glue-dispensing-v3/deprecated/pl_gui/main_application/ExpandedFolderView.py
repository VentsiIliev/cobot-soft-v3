from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QTimer, QParallelAnimationGroup
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QFrame, QScrollArea,
    QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QFont, QColor

from deprecated.pl_gui.main_application.FloatingFolderIcon import FloatingFolderIcon
from deprecated.pl_gui.main_application.MenuIcon import MenuIcon


class ExpandedFolderView(QFrame):
    """Material Design 3 expanded folder view with modern animations"""

    close_requested = pyqtSignal()
    app_selected = pyqtSignal(str)

    close_current_app_requested = pyqtSignal()

    def __init__(self, folder_ref, parent=None):
        super().__init__(parent)
        self.setObjectName("ExpandedFolderView")
        self.folder_ref = folder_ref
        self.setFixedSize(580, 680)  # Material Design proportions
        self._is_closing = False
        self._is_transitioning = False
        self._is_hidden_mode = False
        self._current_app_name = None

        self.floating_icon = None
        self.close_app_button = None

        self.setup_ui()
        self.setup_smooth_animations()

    def close_from_outside(self):
        """Handle close request from outside (clicking outside the folder)"""
        if self._current_app_name:
            # If app is running, don't remove floating icon, just hide expanded view
            if not self._is_hidden_mode:
                self.hide_and_show_floating_icon()
        else:
            # No app running, normal close behavior
            self.safe_close()
    def setup_smooth_animations(self):
        """Material Design animation system"""
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(300)  # Material standard duration
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(300)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim_group = QParallelAnimationGroup(self)
        self.anim_group.addAnimation(self.opacity_animation)
        self.anim_group.addAnimation(self.scale_animation)
        self.anim_group.finished.connect(self.animation_finished)

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
        self.title_label = QLabel(self.folder_ref.folder_name)
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
        header_layout.addWidget(self.title_label, 2)
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

        self.update_apps()

    def safe_close(self):
        """Material Design close transition"""
        if self._is_closing or self._is_transitioning:
            return

        if self._is_hidden_mode and self.floating_icon:
            self.floating_icon.hide_with_animation()
            QTimer.singleShot(200, self._complete_close)
        else:
            self._is_closing = True
            self.fade_out()

    def _complete_close(self):
        """Complete the Material Design close sequence"""
        if self.floating_icon:
            self.floating_icon.deleteLater()
            self.floating_icon = None

        self._is_closing = True
        self.close_requested.emit()

    def fade_in(self, center_pos):
        """Material Design scale-in animation"""
        print(f"Material fade_in called with center_pos: {center_pos}")

        self.anim_group.stop()

        final_x = int(center_pos.x() - self.width() // 2)
        final_y = int(center_pos.y() - self.height() // 2)

        # Material Design scale factor
        scale_factor = 0.8
        start_width = int(self.width() * scale_factor)
        start_height = int(self.height() * scale_factor)
        start_x = int(center_pos.x() - start_width // 2)
        start_y = int(center_pos.y() - start_height // 2)

        self.setGeometry(start_x, start_y, start_width, start_height)
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()

        # Material Design animation curves
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        start_rect = QRect(start_x, start_y, start_width, start_height)
        final_rect = QRect(final_x, final_y, self.width(), self.height())
        self.scale_animation.setStartValue(start_rect)
        self.scale_animation.setEndValue(final_rect)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim_group.start()

    def fade_out(self):
        """Material Design scale-out animation"""
        if self._is_closing or self._is_transitioning:
            return
        self._is_closing = True

        self.anim_group.stop()

        current_rect = self.geometry()
        center_x, center_y = current_rect.center().x(), current_rect.center().y()

        scale_factor = 0.8
        end_width = int(self.width() * scale_factor)
        end_height = int(self.height() * scale_factor)
        end_x = int(center_x - end_width // 2)
        end_y = int(center_y - end_height // 2)

        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.InCubic)

        end_rect = QRect(end_x, end_y, end_width, end_height)
        self.scale_animation.setStartValue(current_rect)
        self.scale_animation.setEndValue(end_rect)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.InCubic)

        self.anim_group.start()

    def hide_and_show_floating_icon(self):
        """Material Design transition to floating action button"""
        if self._is_closing or self._is_transitioning:
            return

        print("Material Design transition to FAB")
        self._is_transitioning = True
        self._is_hidden_mode = True

        main_window = self.parent()
        while main_window and main_window.parent():
            main_window = main_window.parent()
        parent = main_window

        # Material Design floating action button
        self.floating_icon = FloatingFolderIcon(self.folder_ref.folder_name, parent)
        self.position_floating_icon()
        self.floating_icon.clicked_signal.connect(self.restore_from_floating_icon)

        self.hide()
        self.setWindowOpacity(0.0)

        QTimer.singleShot(50, self.floating_icon.show_with_animation)
        QTimer.singleShot(300, lambda: setattr(self, '_is_transitioning', False))

        # Material Design scrim update
        if hasattr(self.folder_ref, "overlay") and self.folder_ref.overlay:
            self.folder_ref.overlay.disable_overlay_close = True
            self.folder_ref.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.05);")

    def position_floating_icon(self):
        """Position FAB according to Material Design guidelines"""
        if not self.floating_icon or not self.floating_icon.parent():
            return

        parent_rect = self.floating_icon.parent().rect()
        margin = 24  # Material Design FAB margin

        # x = margin
        # y = parent_rect.height() - self.floating_icon.height() - margin
        x = 10
        y = 10

        self.floating_icon.move(x, y)

    def restore_from_floating_icon(self):
        """Material Design restoration from FAB"""
        print("Material Design FAB clicked - restoring")

        if self._is_transitioning:
            return

        self._is_transitioning = True
        self._is_hidden_mode = False

        if self.floating_icon:
            self.floating_icon.hide_with_animation()

        # Restore Material Design scrim
        if hasattr(self.folder_ref, "overlay") and self.folder_ref.overlay:
            self.folder_ref.overlay.disable_overlay_close = False
            self.folder_ref.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.32);")  # Material scrim
            self.folder_ref.overlay.show()
            self.folder_ref.overlay.raise_()

        main_window = None
        if hasattr(self.folder_ref, "overlay") and self.folder_ref.overlay:
            main_window = self.folder_ref.overlay.parent()

        if not main_window:
            main_window = self.floating_icon.parent() if self.floating_icon else None
            while main_window and main_window.parent():
                main_window = main_window.parent()

        if main_window:
            if hasattr(self.folder_ref, "overlay") and self.folder_ref.overlay:
                self.setParent(self.folder_ref.overlay)

            center_pos = main_window.rect().center()
            QTimer.singleShot(100, lambda: self.fade_in(center_pos))

            if self._current_app_name:
                QTimer.singleShot(400, self.show_close_app_button)

        QTimer.singleShot(300, self._cleanup_floating_icon)
        QTimer.singleShot(500, lambda: setattr(self, '_is_transitioning', False))

    def _cleanup_floating_icon(self):
        """Clean up floating action button"""
        if self.floating_icon:
            self.floating_icon.deleteLater()
            self.floating_icon = None

    def update_apps(self):
        """Update app grid with Material Design styling"""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)
                item.widget().deleteLater()

        cols = 4
        if hasattr(self.folder_ref, 'buttons'):
            for i, button in enumerate(self.folder_ref.buttons):
                row, col = divmod(i, cols)
                button_copy = MenuIcon(button.icon_label, button.icon_path, button.icon_text, button.callback)
                button_copy.button_clicked.connect(self.on_app_clicked)
                self.grid_layout.addWidget(button_copy, row, col)

    def on_app_clicked(self, app_name):
        """Handle app selection with Material Design feedback"""
        print(f"Material Design app selected: {app_name}")
        self._current_app_name = app_name
        self.app_selected.emit(app_name)
        self.show_close_app_button()
        self.hide_and_show_floating_icon()

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
        """Handle close app with Material Design interaction"""
        print(f"Material Design close app: {self._current_app_name}")
        self.close_current_app_requested.emit()
        self.hide_close_app_button()

        # When back button is pressed, fully close the folder
        if self._is_hidden_mode and self.floating_icon:
            self.floating_icon.hide_with_animation()
            QTimer.singleShot(200, self._complete_close)
        else:
            # Not in hidden mode, trigger normal close
            self.close_requested.emit()

    def set_app_running_state(self, app_name=None):
        """Update app state with Material Design consistency"""
        if app_name:
            self._current_app_name = app_name
            self.show_close_app_button()
        else:
            self.hide_close_app_button()

    def animation_finished(self):
        """Material Design animation completion handler"""
        if self._is_closing:
            QTimer.singleShot(0, self.safe_hide)

    def safe_hide(self):
        """Safe hide with Material Design cleanup"""
        if self._is_closing:
            QTimer.singleShot(0, self.hide)
            if self.floating_icon:
                self.floating_icon.deleteLater()
                self.floating_icon = None

    def mousePressEvent(self, event):
        event.accept()

    def closeEvent(self, event):
        """Material Design close event handling"""
        self._is_closing = True
        self.anim_group.stop()

        if self.floating_icon:
            self.floating_icon.deleteLater()
            self.floating_icon = None

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

    folder_view = ExpandedFolderView(
        folder_ref=type('Folder', (), {'folder_name': 'Material Apps', 'buttons': []}),
        parent=main_window
    )
    folder_view.fade_in(main_window.rect().center())
    main_window.setCentralWidget(folder_view)
    main_window.show()

    # Material Design test button
    test_button = QPushButton("Test Material FAB", main_window)
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
    test_button.clicked.connect(folder_view.hide_and_show_floating_icon)
    test_button.show()

    sys.exit(app.exec())
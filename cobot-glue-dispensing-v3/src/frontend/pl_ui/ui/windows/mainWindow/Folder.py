# ========================================
# FIXED: FolderController - Make it a QObject to use signals properly
# ========================================

from dataclasses import dataclass
from typing import Optional, List
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QTimer, QSize, QObject
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QGraphicsDropShadowEffect, QSizePolicy
)

from src.frontend.pl_ui.ui.windows.mainWindow.MenuIcon import MenuIcon
from src.frontend.pl_ui.ui.windows.mainWindow.managers.ExpandedViewManager import ExpandedViewManager
from src.frontend.pl_ui.ui.windows.mainWindow.managers.FloatingIconManager import FloatingIconManager
from src.frontend.pl_ui.ui.windows.mainWindow.managers.OverlayManager import OverlayManager


@dataclass
class FolderState:
    """Simple folder state data"""
    is_open: bool = False
    is_grayed_out: bool = False
    app_running: bool = False
    current_app_name: Optional[str] = None


class LayoutManager:
    """Material Design 3 layout management"""

    def __init__(self, folder_widget):
        self.folder = folder_widget
        self.min_size = QSize(300, 340)
        self.max_size = QSize(480, 520)
        self.preferred_aspect_ratio = 0.88
        self._resize_timer = None

    def setup_responsive_sizing(self):
        self.folder.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.folder.setMinimumSize(self.min_size)
        self.folder.setMaximumSize(self.max_size)

    def update_main_layout_margins(self):
        current_width = self.folder.width() if self.folder.width() > 0 else self.min_size.width()
        margin = max(16, min(24, int(current_width * 0.05)))
        spacing = max(12, min(20, int(current_width * 0.04)))
        self.folder.main_layout.setContentsMargins(margin, margin, margin, margin)
        self.folder.main_layout.setSpacing(spacing)

    def update_header_layout_spacing(self):
        self.folder.header_layout.setSpacing(16)

    def update_preview_layout_margins(self):
        preview_width = self.folder.folder_preview.width() if self.folder.folder_preview.width() > 0 else 200
        margin = max(16, min(28, int(preview_width * 0.08)))
        spacing = max(8, min(16, int(preview_width * 0.04)))
        self.folder.preview_layout.setContentsMargins(margin, margin, margin, margin)
        self.folder.preview_layout.setSpacing(spacing)

    def calculate_icon_size(self):
        preview_width = self.folder.folder_preview.width() if self.folder.folder_preview.width() > 0 else 200
        preview_height = self.folder.folder_preview.height() if self.folder.folder_preview.height() > 0 else 200
        available_size = min(preview_width, preview_height)
        margins = self.folder.preview_layout.contentsMargins()
        total_margin = margins.left() + margins.right()
        spacing = self.folder.preview_layout.spacing()
        icon_size = max(64, min(96, int((available_size - total_margin - spacing) / 2.2)))
        return icon_size

    def update_typography(self):
        current_width = self.folder.width() if self.folder.width() > 0 else self.min_size.width()
        font_size = max(18, min(28, int(current_width * 0.06)))
        font = QFont("Roboto", font_size, QFont.Weight.Medium)
        if not font.exactMatch():
            font = QFont("Segoe UI", font_size, QFont.Weight.Medium)
        self.folder.title_label.setFont(font)

    def handle_resize_event(self):
        if self.folder.parent():
            available_width = self.folder.parent().width()
            target_width = max(self.min_size.width(),
                               min(int(available_width * 0.3), self.max_size.width()))
            target_height = int(target_width / self.preferred_aspect_ratio)
            self.folder.setFixedSize(QSize(target_width, target_height))

        self.update_main_layout_margins()
        self.update_typography()

        if self._resize_timer:
            self._resize_timer.stop()
        else:
            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self.folder.update_folder_preview)
        self._resize_timer.start(150)


# ========================================
# Pure UI Component - Folder Widget (unchanged)
# ========================================

class FolderWidget(QFrame):
    """Pure UI component - only handles visual presentation"""

    clicked = pyqtSignal()
    outside_clicked = pyqtSignal()

    def __init__(self, ID,folder_name="Apps", parent=None):
        super().__init__(parent)
        self.ID = ID
        self.folder_name = folder_name
        self.buttons = []
        self.is_grayed_out = False
        self.layout_manager = LayoutManager(self)
        self.setup_ui()
        self.setAcceptDrops(True)
        self.translate_fn= None


    def update_title_label(self,message=None):
        if self.translate_fn:
            title = self.translate_fn(self.folder_name)
        else:
            return

        self.title_label.setText(title)

    def folder_clicked(self, event):
        """Handle folder preview click - just emit signal"""
        if not self.is_grayed_out:
            self.clicked.emit()

    def setup_ui(self):
        """Material Design 3 UI setup - pure presentation"""
        self.layout_manager.setup_responsive_sizing()

        self.setStyleSheet("""
            QFrame {
                background: #FFFBFE;
                border: 1px solid #E7E0EC;
                border-radius: 24px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        self.main_layout = QVBoxLayout(self)
        self.layout_manager.update_main_layout_margins()

        self.header_widget = QFrame()
        self.header_layout = QVBoxLayout(self.header_widget)
        self.layout_manager.update_header_layout_spacing()

        self.folder_preview = QFrame()
        self.folder_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.folder_preview.setStyleSheet("""
            QFrame {
                background: #FFFBFE;
                border: 1px solid #E7E0EC;
                border-radius: 28px;
            }
        """)

        preview_shadow = QGraphicsDropShadowEffect()
        preview_shadow.setBlurRadius(20)
        preview_shadow.setColor(QColor(103, 80, 164, 30))
        preview_shadow.setOffset(0, 4)
        self.folder_preview.setGraphicsEffect(preview_shadow)
        self.folder_preview.mousePressEvent = self.folder_clicked

        self.preview_layout = QGridLayout(self.folder_preview)
        self.layout_manager.update_preview_layout_margins()

        self.title_label = QLabel(self.folder_name)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.title_label.setWordWrap(True)
        self.layout_manager.update_typography()

        self.title_label.setStyleSheet("""
            QLabel {
                color: #1D1B20;
                background-color: transparent;
                border: none;
                padding: 12px 16px;
                font-weight: 500;
                letter-spacing: 0px;
            }
        """)

        self.header_layout.addWidget(self.folder_preview, 1)
        self.header_layout.addWidget(self.title_label, 0)
        self.main_layout.addWidget(self.header_widget)
        self.update_folder_preview()

    def update_folder_preview(self):
        """Update folder preview icons - pure UI operation"""
        for i in reversed(range(self.preview_layout.count())):
            child = self.preview_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        self.layout_manager.update_preview_layout_margins()
        icon_size = self.layout_manager.calculate_icon_size()
        inner_icon_size = max(48, int(icon_size * 0.7))

        preview_apps = self.buttons[:4]
        for i, app in enumerate(preview_apps):
            row, col = divmod(i, 2)

            mini_icon = QLabel()
            mini_icon.setFixedSize(icon_size, icon_size)
            mini_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

            border_radius = max(16, min(28, int(icon_size * 0.25)))
            mini_icon.setStyleSheet(f"""
                QLabel {{
                    background: #6750A4;
                    border: none;
                    border-radius: {border_radius}px;
                    font-size: {max(12, int(icon_size * 0.18))}px;
                    font-weight: 500;
                    color: white;
                    font-family: 'Roboto', 'Segoe UI', sans-serif;
                }}
            """)

            try:
                mini_shadow = QGraphicsDropShadowEffect()
                mini_shadow.setBlurRadius(8)
                mini_shadow.setColor(QColor(103, 80, 164, 40))
                mini_shadow.setOffset(0, 2)
                mini_icon.setGraphicsEffect(mini_shadow)
            except:
                pass

            icon_loaded = False
            try:
                pixmap = QPixmap(app.icon_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        inner_icon_size, inner_icon_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    mini_icon.setPixmap(scaled_pixmap)
                    icon_loaded = True
            except Exception:
                pass

            if not icon_loaded:
                mini_icon.setText("📱")
                placeholder_font_size = max(20, int(icon_size * 0.35))
                mini_icon.setStyleSheet(mini_icon.styleSheet() + f"font-size: {placeholder_font_size}px;")

            self.preview_layout.addWidget(mini_icon, row, col)

    def set_grayed_out(self, grayed_out):
        """Update visual disabled state"""
        self.is_grayed_out = grayed_out

        if grayed_out:
            # Outer frame
            self.setStyleSheet("""
                QFrame {
                    background: #EDE7F6;
                    border: 1px dashed #B0A7BC;
                    border-radius: 24px;
                }
            """)

            # Title text
            self.title_label.setStyleSheet("""
                QLabel {
                    color: #9C9A9E;
                    background-color: transparent;
                    border: none;
                    padding: 12px 16px;
                    font-weight: 500;
                    letter-spacing: 0px;
                }
            """)

            # Folder preview (icons background dimmed)
            self.folder_preview.setStyleSheet("""
                QFrame {
                    background: #F3EDF7;
                    border: 1px solid #C4C0CA;
                    border-radius: 28px;
                }
            """)

            # Dim all child icons
            for i in range(self.preview_layout.count()):
                child = self.preview_layout.itemAt(i).widget()
                if child:
                    child.setGraphicsEffect(None)  # remove shadows
                    child.setStyleSheet(child.styleSheet() + "opacity: 0.4;")

        else:
            # Outer frame
            self.setStyleSheet("""
                QFrame {
                    background: #FFFBFE;
                    border: 1px solid #E7E0EC;
                    border-radius: 24px;
                }
            """)

            # Reset title
            self.title_label.setStyleSheet("""
                QLabel {
                    color: #1D1B20;
                    background-color: transparent;
                    border: none;
                    padding: 12px 16px;
                    font-weight: 500;
                    letter-spacing: 0px;
                }
            """)

            # Reset preview
            self.folder_preview.setStyleSheet("""
                QFrame {
                    background: #FFFBFE;
                    border: 1px solid #E7E0EC;
                    border-radius: 28px;
                }
            """)

            # Reset icons (restore drop shadow + normal look)
            self.update_folder_preview()

    def add_app(self, app_name, icon_path="", callback=None):
        """Add app to UI - no business logic"""
        app_icon = MenuIcon(app_name, icon_path, "", callback)
        self.buttons.append(app_icon)
        self.update_folder_preview()

    def sizeHint(self):
        return QSize(380, 420)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.layout_manager.handle_resize_event()


# ========================================
# FIXED: Controller/Coordinator - Now inherits from QObject
# ========================================

class FolderController(QObject):
    """Handles all folder business logic and orchestration - NOW A QOBJECT"""

    # Now these signals will work properly
    folder_opened = pyqtSignal()
    folder_closed = pyqtSignal()
    app_selected = pyqtSignal(str)
    close_current_app_signal = pyqtSignal()

    def __init__(self, folder_widget: FolderWidget, main_window=None, parent=None):
        super().__init__(parent)  # Initialize QObject
        self.folder_widget = folder_widget
        self.main_window = main_window

        # Business state
        self.state = FolderState()

        # Managers for complex operations
        self.floating_icon_manager = FloatingIconManager(folder_widget)
        self.overlay_manager = OverlayManager(folder_widget,overlay_parent=self.main_window,overlay_callback=self.handle_outside_click)
        self.expanded_view_manager = ExpandedViewManager(folder_widget)

        # Connect to UI events
        self.folder_widget.clicked.connect(self.handle_folder_click)

    def set_main_window(self, main_window):
        """Set main window reference"""
        self.main_window = main_window

    def handle_folder_click(self):
        """Handle folder click - business logic"""
        # print(
        #     f"FolderController: Folder clicked. Current state: open={self.state.is_open}, grayed_out={self.state.is_grayed_out}, app_running={self.state.app_running}")

        if self.state.is_grayed_out or self.state.app_running:
            # print("FolderController: Folder click ignored - grayed out or app running")
            return

        self.state.is_open = not self.state.is_open
        if self.state.is_open:
            try:
                self.open_folder()
            except Exception as e:
                import traceback
                traceback.print_exc()
                # print(f"FolderController: Exception during folder open: {e}")
                self.state.is_open = False
        else:
            self.close_folder()

    def open_folder(self):
        """Business logic for opening folder"""
        # print("FolderController: Opening folder")
        if not self.main_window:
            # print("FolderController: ERROR - main_window is not set. Cannot open folder.")
            self.state.is_open = False
            return

        # CRITICAL FIX: Pass the correct callback
        overlay = self.overlay_manager.show_overlay()
        if not overlay:
            # print("FolderController: Failed to create overlay")
            self.state.is_open = False
            return

        # print("FolderController: Overlay created successfully")

        expanded_view = self.expanded_view_manager.show_expanded_view(
            self.folder_widget.folder_name,
            overlay,
            self.close_folder,
            self.handle_app_selected,
            self.minimize_to_floating_icon,
            self.handle_close_app
        )
        # print("FolderController: Expanded view created successfully")
        self.expanded_view_manager.populate_apps(self.folder_widget.buttons)

        screen_center = self.main_window.rect().center()
        self.expanded_view_manager.fade_in(screen_center)

        # Now this will work since we inherit from QObject
        self.folder_opened.emit()
        # print("FolderController: Folder opened successfully")

    def handle_outside_click(self):
        """Handle clicking outside folder - CRITICAL METHOD"""
        # print("FolderController: Outside click detected!")
        # print(f"FolderController: Current app: {self.state.current_app_name}")

        if self.state.current_app_name:
            # print("FolderController: App running - minimizing to floating icon")
            self.minimize_to_floating_icon()
        else:
            # print("FolderController: No app running - closing folder")
            self.close_folder()

    def minimize_to_floating_icon(self):
        """Business logic for minimizing to floating icon"""
        # print("FolderController: Minimizing to floating icon")
        self.overlay_manager.hide_overlay()
        self.expanded_view_manager.fade_out()
        self.overlay_manager.set_style("background-color: rgba(0, 0, 0, 0.05);")
        self.floating_icon_manager.show_floating_icon(
            self.folder_widget.folder_name,
            self.restore_from_floating_icon
        )

    def restore_from_floating_icon(self):
        """Business logic for restoring from floating icon"""
        # print("FolderController: Restoring from floating icon")
        self.overlay_manager.show_overlay()
        self.floating_icon_manager.hide_floating_icon()
        self.overlay_manager.set_style("background-color: rgba(0, 0, 0, 0.32);")

        if self.main_window:
            center = self.main_window.rect().center()
            self.expanded_view_manager.fade_in(center)

            if self.state.current_app_name:
                self.expanded_view_manager.show_close_button()

    def close_folder(self):
        """Business logic for closing folder"""
        # print("FolderController: Closing folder")

        if not self.state.current_app_name:
            self.state.app_running = False

        self.expanded_view_manager.fade_out()
        self.overlay_manager.hide_overlay()
        self.floating_icon_manager.hide_floating_icon()

        self.state.is_open = False
        self.state.current_app_name = None

        # Now this will work since we inherit from QObject
        self.folder_closed.emit()
        # print("FolderController: Folder closed successfully")


    def handle_app_selected(self, app_name):
        """Business logic for app selection"""
        # print(f"FolderController: App selected - {app_name}")
        self.state.app_running = True
        self.state.current_app_name = app_name

        # Now this will work since we inherit from QObject
        self.app_selected.emit(app_name)

        self.expanded_view_manager.show_close_button()
        self.overlay_manager.set_style("background-color: rgba(0, 0, 0, 0.16);")
        self.overlay_manager.hide_overlay()
        QTimer.singleShot(300, self.minimize_to_floating_icon)

    def handle_close_app(self):
        """Business logic for closing app"""
        # print("FolderController: Closing app")
        self.state.app_running = False
        self.state.current_app_name = None
        self.expanded_view_manager.hide_close_button()
        self.close_current_app_signal.emit()
        self.close_folder()

    def set_disabled(self, disabled):
        """Update business and UI state"""
        self.state.is_grayed_out = disabled
        self.folder_widget.set_grayed_out(disabled)
        self.folder_widget.setVisible(not disabled)

# ========================================
# Usage Example - Updated
# ========================================

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout

    app = QApplication(sys.argv)

    main_window = QWidget()
    main_window.setWindowTitle("FIXED MVC Folder Interface")
    main_window.resize(1000, 800)
    main_window.setStyleSheet("""
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #FFFBFE,
                stop:1 #F7F2FA);
            font-family: 'Roboto', 'Segoe UI', sans-serif;
        }
    """)

    # Create UI component
    folder_widget = FolderWidget("Fixed Apps")
    folder_widget.add_app("Visual Studio Code", "📱")
    folder_widget.add_app("Adobe Creative Suite", "🎨")
    folder_widget.add_app("Microsoft Office", "📊")
    folder_widget.add_app("Development Tools", "⚙️")

    # Create controller for business logic - NOW WORKS WITH SIGNALS
    folder_controller = FolderController(folder_widget, main_window)

    # Test the signals
    folder_controller.folder_opened.connect(lambda: print("SIGNAL: Folder opened!"))
    folder_controller.folder_closed.connect(lambda: print("SIGNAL: Folder closed!"))
    folder_controller.app_selected.connect(lambda app: print(f"SIGNAL: App selected - {app}"))

    # Layout
    layout = QVBoxLayout(main_window)
    layout.setContentsMargins(48, 48, 48, 48)
    layout.setSpacing(24)
    layout.addStretch(1)

    h_layout = QHBoxLayout()
    h_layout.addStretch(1)
    h_layout.addWidget(folder_widget)
    h_layout.addStretch(1)

    layout.addLayout(h_layout)
    layout.addStretch(1)

    main_window.show()
    sys.exit(app.exec())
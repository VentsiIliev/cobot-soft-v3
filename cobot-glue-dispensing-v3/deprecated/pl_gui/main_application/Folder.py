import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QGridLayout, QFrame, QGraphicsDropShadowEffect,
                             QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QTimer, QSize
from PyQt6.QtGui import QPixmap, QFont, QColor

from deprecated.pl_gui.main_application.ExpandedFolderView import ExpandedFolderView
from deprecated.pl_gui.main_application.FolderOverlay import FolderOverlay

# Resource paths
RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
PLACEHOLDER_ICON = os.path.join(RESOURCES_DIR, "placeholder_icon.png")


class Folder(QFrame):
    """Material Design 3 folder widget with responsive layout and modern animations"""

    folder_opened = pyqtSignal(object)
    folder_closed = pyqtSignal()
    app_selected = pyqtSignal(str)
    back_to_main_requested = pyqtSignal()
    close_current_app_signal = pyqtSignal()

    def __init__(self, folder_name="Apps", parent=None):
        super().__init__(parent)
        self.folder_name = folder_name
        self.buttons = []
        self.is_open = False
        self.is_grayed_out = False
        self.app_running = False

        # Material Design responsive sizing
        self.min_size = QSize(300, 340)
        self.max_size = QSize(480, 520)
        self.preferred_aspect_ratio = 0.88  # Material Design proportions

        self.overlay = None
        self.expanded_view = None
        self.main_window = None
        self.setup_ui()
        self.setAcceptDrops(True)

    def set_main_window(self, main_window):
        """Set reference to main window for overlay"""
        self.main_window = main_window

    def folder_clicked(self, event):
        """Handle folder preview click with Material Design interaction"""
        if not self.is_grayed_out and not self.app_running:
            self.toggle_folder()

    def setup_ui(self):
        """Material Design 3 setup with tokens and elevation"""
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setMinimumSize(self.min_size)
        self.setMaximumSize(self.max_size)

        # Material Design 3 surface styling
        self.setStyleSheet("""
            QFrame {
                background: #FFFBFE;
                border: 1px solid #E7E0EC;
                border-radius: 24px;
            }
        """)

        # Material Design elevation shadow (level 1)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        # Material Design layout spacing
        self.main_layout = QVBoxLayout(self)
        self.update_layout_margins()

        # Header container
        self.header_widget = QWidget()
        self.header_layout = QVBoxLayout(self.header_widget)
        self.header_layout.setSpacing(16)  # Material Design spacing

        # Material Design folder preview with elevation
        self.folder_preview = QFrame()
        self.folder_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.folder_preview.setStyleSheet("""
            QFrame {
                background: #FFFBFE;
                border: 1px solid #E7E0EC;
                border-radius: 28px;
            }
        """)

        # Material Design preview shadow (level 2)
        preview_shadow = QGraphicsDropShadowEffect()
        preview_shadow.setBlurRadius(20)
        preview_shadow.setColor(QColor(103, 80, 164, 30))  # Primary color shadow
        preview_shadow.setOffset(0, 4)
        self.folder_preview.setGraphicsEffect(preview_shadow)

        self.folder_preview.mousePressEvent = self.folder_clicked

        # Material Design grid for preview icons
        self.preview_layout = QGridLayout(self.folder_preview)
        self.preview_layout.setSpacing(12)  # Material grid spacing

        # Material Design typography - Display Small
        self.title_label = QLabel(self.folder_name)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.title_label.setWordWrap(True)

        self.update_font_size()

        # Material Design text styling
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

    def update_layout_margins(self):
        """Material Design spacing system"""
        current_width = self.width() if self.width() > 0 else self.min_size.width()

        # Material Design spacing scale: 16dp base
        margin = max(16, min(24, int(current_width * 0.05)))
        spacing = max(12, min(20, int(current_width * 0.04)))

        self.main_layout.setContentsMargins(margin, margin, margin, margin)
        self.main_layout.setSpacing(spacing)

    def update_font_size(self):
        """Material Design typography scale"""
        current_width = self.width() if self.width() > 0 else self.min_size.width()

        # Material Design type scale - Body Large to Headline Small
        font_size = max(18, min(28, int(current_width * 0.06)))

        # Material Design font family
        font = QFont("Roboto", font_size, QFont.Weight.Medium)
        if not font.exactMatch():
            font = QFont("Segoe UI", font_size, QFont.Weight.Medium)

        self.title_label.setFont(font)

    def update_preview_layout_margins(self):
        """Material Design preview spacing"""
        preview_width = self.folder_preview.width() if self.folder_preview.width() > 0 else 200

        # Material Design 16dp grid system
        margin = max(16, min(28, int(preview_width * 0.08)))
        spacing = max(8, min(16, int(preview_width * 0.04)))

        self.preview_layout.setContentsMargins(margin, margin, margin, margin)
        self.preview_layout.setSpacing(spacing)

    def calculate_icon_size(self):
        """Material Design icon sizing - 64dp to 96dp range"""
        preview_width = self.folder_preview.width() if self.folder_preview.width() > 0 else 200
        preview_height = self.folder_preview.height() if self.folder_preview.height() > 0 else 200

        available_size = min(preview_width, preview_height)
        margins = self.preview_layout.contentsMargins()
        total_margin = margins.left() + margins.right()
        spacing = self.preview_layout.spacing()

        # Material Design icon sizes: 64dp standard
        icon_size = max(64, min(96, int((available_size - total_margin - spacing) / 2.2)))
        return icon_size

    def update_folder_preview(self):
        """Material Design preview with proper elevation and tokens"""
        # Clear existing preview icons
        for i in reversed(range(self.preview_layout.count())):
            child = self.preview_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        self.update_preview_layout_margins()
        icon_size = self.calculate_icon_size()
        inner_icon_size = max(48, int(icon_size * 0.7))  # Material Design proportion

        # Show up to 4 app icons in Material Design grid
        preview_apps = self.buttons[:4]
        for i, app in enumerate(preview_apps):
            row = i // 2
            col = i % 2

            # Material Design surface container
            mini_icon = QLabel()
            mini_icon.setFixedSize(icon_size, icon_size)
            mini_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Material Design shape tokens - rounded corners
            border_radius = max(16, min(28, int(icon_size * 0.25)))

            # Material Design color tokens
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

            # Material Design elevation shadow for icons
            try:
                mini_shadow = QGraphicsDropShadowEffect()
                mini_shadow.setBlurRadius(8)
                mini_shadow.setColor(QColor(103, 80, 164, 40))  # Primary shadow
                mini_shadow.setOffset(0, 2)
                mini_icon.setGraphicsEffect(mini_shadow)
            except:
                pass

            # Load icon with Material Design sizing
            icon_loaded = False

            if hasattr(app, 'icon_path') and app.icon_path and app.icon_path not in ["◉", "PLACEHOLDER ICON"]:
                if os.path.exists(app.icon_path):
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
                    except Exception as e:
                        print(f"Error loading pixmap: {e}")

            # Fallback with Material Design icon
            if not icon_loaded:
                mini_icon.setText("📱")  # Material Design app icon
                placeholder_font_size = max(20, int(icon_size * 0.35))
                mini_icon.setStyleSheet(mini_icon.styleSheet() + f"font-size: {placeholder_font_size}px;")

            self.preview_layout.addWidget(mini_icon, row, col)

    def resizeEvent(self, event):
        """Material Design responsive resize handling"""
        super().resizeEvent(event)

        self.update_layout_margins()
        self.update_font_size()

        # Debounced preview update for performance
        if hasattr(self, '_resize_timer'):
            self._resize_timer.stop()
        else:
            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self.update_folder_preview)

        self._resize_timer.start(150)  # Material Design timing

    def sizeHint(self):
        if self.parent():
            parent_size = self.parent().size()
            preferred_width = max(
                self.min_size.width(),
                min(self.max_size.width(), int(parent_size.width() * 0.32))
            )
            preferred_height = int(preferred_width / self.preferred_aspect_ratio)
            return QSize(preferred_width, preferred_height)
        return QSize(380, 420)

    def minimumSizeHint(self):
        """Material Design minimum size"""
        return self.min_size

    def toggle_folder(self):
        """Material Design state toggle"""
        if self.app_running:
            return

        self.is_open = not self.is_open

        if self.is_open:
            self.open_folder()
        else:
            self.close_folder()

    def open_folder(self):
        """Material Design folder opening with elevation transition"""
        if not self.main_window or self.app_running:
            return

        # Material Design motion easing
        rect = self.folder_preview.geometry()
        center = rect.center()

        # Material Design scale transition
        scale_factor_expand = 1.08
        scaled_rect_expand = QRect(
            center.x() - int(rect.width() * scale_factor_expand / 2),
            center.y() - int(rect.height() * scale_factor_expand / 2),
            int(rect.width() * scale_factor_expand),
            int(rect.height() * scale_factor_expand)
        )

        # Material Design overlay with scrim
        screen_center = self.main_window.rect().center()
        self.overlay = FolderOverlay(self.main_window)
        self.overlay.close_requested.connect(self.close_folder)
        self.overlay.resize(self.main_window.size())

        # Material Design scrim styling
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.32);")
        self.overlay.fade_in()

        # Material Design expanded view
        self.expanded_view = ExpandedFolderView(self, self.overlay)
        self.expanded_view.close_requested.connect(self.close_folder)
        self.expanded_view.app_selected.connect(self.on_app_selected)
        self.expanded_view.close_current_app_requested.connect(self.on_close_current_app_requested)
        self.expanded_view.fade_in(screen_center)
        self.folder_opened.emit(self)

    def close_folder(self):
        """Material Design folder closing with elevation transition"""
        # Don't reset app_running if we're just collapsing to floating icon
        if not (self.expanded_view and self.expanded_view._current_app_name):
            self.app_running = False

        rect = self.folder_preview.geometry()
        center = rect.center()

        # Material Design scale transition
        scale_factor_contract = 0.92
        scaled_rect_contract = QRect(
            center.x() - int(rect.width() * scale_factor_contract / 2),
            center.y() - int(rect.height() * scale_factor_contract / 2),
            int(rect.width() * scale_factor_contract),
            int(rect.height() * scale_factor_contract)
        )

        if self.expanded_view:
            # Only fade out if not transitioning to floating icon
            if not (self.expanded_view._current_app_name and not self.expanded_view._is_hidden_mode):
                self.expanded_view.fade_out()

        if self.overlay:
            # Only fade out overlay if no app is running or floating icon isn't shown
            if not (self.expanded_view and self.expanded_view._current_app_name and self.expanded_view._is_hidden_mode):
                self.overlay.fade_out()
                QTimer.singleShot(300, self._cleanup_views)  # Material timing
            else:
                # Keep overlay but make it more transparent
                self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.05);")

        self.is_open = False

        # Only emit folder_closed if we're actually fully closing (no floating icon)
        if not (self.expanded_view and self.expanded_view._current_app_name):
            self.folder_closed.emit()

    def on_close_current_app_requested(self):
        """Material Design app close handling"""
        print("Material Design: Close current app requested")
        self.close_current_app_signal.emit()

    def on_back_to_main_requested(self):
        """Material Design navigation back"""
        print("Material Design: Back button pressed")
        self.back_to_main_requested.emit()

    def on_app_selected(self, app_name):
        """Material Design app selection with state management"""
        print(f"Material Design: App selected - {app_name}")
        self.app_running = True
        self.app_selected.emit(app_name)

        if self.expanded_view:
            self.expanded_view.set_app_running_state(app_name)

        # Material Design scrim update
        if self.overlay:
            self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.16);")

    def close_app(self):
        """Material Design app closure"""
        print("Material Design: Closing app and restoring state")
        self.app_running = False

        if self.expanded_view:
            self.expanded_view.set_app_running_state(None)

        self.close_folder()

    def _cleanup_views(self):
        """Material Design view cleanup"""
        if self.overlay:
            self.overlay.deleteLater()
            self.overlay = None

        if self.expanded_view:
            self.expanded_view.deleteLater()
            self.expanded_view = None

    def set_grayed_out(self, grayed_out):
        """Material Design disabled state styling"""
        self.is_grayed_out = grayed_out

        if grayed_out:
            # Material Design disabled state tokens
            self.setStyleSheet("""
                QFrame {
                    background: #F7F2FA;
                    border: 1px solid #E7E0EC;
                    border-radius: 24px;
                    opacity: 0.38;
                }
            """)
            self.folder_preview.setStyleSheet("""
                QFrame {
                    background: #F7F2FA;
                    border: 1px solid #E7E0EC;
                    border-radius: 28px;
                    opacity: 0.38;
                }
            """)
            self.title_label.setStyleSheet("""
                QLabel {
                    color: #49454F;
                    background-color: transparent;
                    border: none;
                    padding: 12px 16px;
                    font-weight: 500;
                    letter-spacing: 0px;
                    opacity: 0.38;
                }
            """)
        else:
            # Restore Material Design normal state
            self.setStyleSheet("""
                QFrame {
                    background: #FFFBFE;
                    border: 1px solid #E7E0EC;
                    border-radius: 24px;
                }
            """)
            self.folder_preview.setStyleSheet("""
                QFrame {
                    background: #FFFBFE;
                    border: 1px solid #E7E0EC;
                    border-radius: 28px;
                }
            """)
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

    def add_app(self, app_name, icon_path="📱", callback=None):
        """Add app with Material Design consistency"""
        from deprecated.pl_gui.main_application.MenuIcon import MenuIcon
        app_icon = MenuIcon(app_name, icon_path, "📱", callback)
        self.buttons.append(app_icon)
        self.update_folder_preview()

    def remove_app(self, app_name):
        """Remove app with Material Design cleanup"""
        for i, app in enumerate(self.buttons):
            if app.icon_label == app_name:
                app.setParent(None)
                app.deleteLater()
                del self.buttons[i]
                break
        self.update_folder_preview()

    def on_button_clicked(self, app_name):
        """Material Design app launch handling"""
        print(f"Material Design: Launching application: {app_name}")

    def dragEnterEvent(self, event):
        """Material Design drag interaction"""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """Material Design drag movement"""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Material Design drop handling"""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        # Dynamically size based on parent space
        if self.parent():
            available_width = self.parent().width()
            # We aim for about 1/3 of available width in a row
            target_width = max(self.min_size.width(),
                               min(int(available_width * 0.3), self.max_size.width()))
            target_height = int(target_width / self.preferred_aspect_ratio)
            self.setFixedSize(QSize(target_width, target_height))

        self.update_layout_margins()
        self.update_font_size()

        if hasattr(self, '_resize_timer'):
            self._resize_timer.stop()
        else:
            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self.update_folder_preview)

        self._resize_timer.start(150)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Material Design application setup
    app.setStyle('Fusion')

    # Material Design typography
    font = QFont("Roboto")
    if not font.exactMatch():
        font = QFont("Segoe UI")
    app.setFont(font)

    main_window = QWidget()
    main_window.setWindowTitle("Material Design 3 Folder Interface")
    main_window.resize(1000, 800)

    # Material Design background
    main_window.setStyleSheet("""
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #FFFBFE,
                stop:1 #F7F2FA);
            font-family: 'Roboto', 'Segoe UI', sans-serif;
        }
    """)

    folder = Folder("Material Apps")
    folder.set_main_window(main_window)
    folder.add_app("Visual Studio Code", "📱")
    folder.add_app("Adobe Creative Suite", "🎨")
    folder.add_app("Microsoft Office", "📊")
    folder.add_app("Development Tools", "⚙️")

    # Material Design layout
    layout = QVBoxLayout(main_window)
    layout.setContentsMargins(48, 48, 48, 48)  # Material Design margins
    layout.setSpacing(24)

    layout.addStretch(1)

    # Center the folder with Material Design spacing
    h_layout = QHBoxLayout()
    h_layout.addStretch(1)
    h_layout.addWidget(folder)
    h_layout.addStretch(1)

    layout.addLayout(h_layout)
    layout.addStretch(1)

    main_window.show()
    sys.exit(app.exec())
import os

from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy

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
RULER_ICON = os.path.join(RESOURCE_DIR, "RULER_ICON.png")

class BottomToolBar(QWidget):
    """Widget that provides zoom and pan controls positioned at the bottom center"""
    zoom_in_requested = pyqtSignal()
    zoom_out_requested = pyqtSignal()
    reset_zoom_requested = pyqtSignal()
    pan_mode_toggle_requested = pyqtSignal()
    hide_points_requested = pyqtSignal()
    show_points_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_drag_mode = False
        self.setupUI()

    def setupUI(self):
        # Create horizontal layout for buttons
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Create zoom buttons
        # Create hide points button with custom drawn icons (circle and circle-with-diagonal)
        self._hide_points_shown = True
        # Use the requested purple color #905BA9 for the icons
        hide_icon = self._make_circle_icon(size=48, color=QColor("#905BA9"), diagonal=False)
        hide_disabled_icon = self._make_circle_icon(size=48, color=QColor("#905BA9"), diagonal=True)
        self.hide_points_button = self.create_button(hide_icon, self._toggle_hide_points, "Hide Points", "hide_points")
        self.zoom_out_button = self.create_button(ZOOM_OUT, self.zoom_out_requested.emit, "Zoom Out", "zoom_out")
        self.reset_zoom_button = self.create_button(RESET_ZOOM_ICON, self.reset_zoom_requested.emit, "Reset Zoom",
                                                    "reset_zoom")
        self.zoom_in_button = self.create_button(ZOOM_IN, self.zoom_in_requested.emit, "Zoom In", "zoom_in")

        # Create pan/edit toggle button
        self.pan_toggle_button = self.create_button(DRAG_ICON, self.toggle_pan_mode, "Toggle Pan/Edit Mode",
                                                    "pan_toggle")

        # Add buttons to layout (include hide points button)
        layout.addWidget(self.hide_points_button)
        layout.addWidget(self.zoom_out_button)
        layout.addWidget(self.reset_zoom_button)
        layout.addWidget(self.zoom_in_button)
        layout.addWidget(self.pan_toggle_button)

        # Set widget properties
        self.setFixedHeight(80)
        self.setFixedWidth(340)  # Increased width for additional button

    def create_button(self, icon_path, click_handler, tooltip, button_type):
        button = QPushButton()

        # Set up icon and text
        # icon_path can be a filesystem path (str), a QIcon, or a QPixmap
        if isinstance(icon_path, QIcon):
            button.setIcon(icon_path)
            button.setIconSize(QSize(32, 32))
        elif isinstance(icon_path, QPixmap):
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(32, 32))
        elif isinstance(icon_path, str) and os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(32, 32))
        else:
            # Fallback text if icon doesn't exist
            if button_type == "zoom_in":
                button.setText("+")
            elif button_type == "zoom_out":
                button.setText("-")
            elif button_type == "reset_zoom":
                button.setText("⌂")  # Reset symbol
            elif button_type == "pan_toggle":
                button.setText("👆")  # Pointing finger for edit mode (default)

        button.setStyleSheet("""
        QPushButton {
            border: 2px solid #6750A4;
            border-radius: 6px;
            background-color: #ffffff;
            min-width: 60px;
            min-height: 60px;
            font-size: 18px;
            font-weight: bold;
            color: #000000;
        }
        QPushButton:pressed {
            background-color: #f0f0f0;
            color: #000000;
        }
        QPushButton:hover {
            border: 2px solid #4b2e86;
            color: #000000;
        }
        """)
        button.setToolTip(tooltip)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.clicked.connect(click_handler)
        return button

    def toggle_pan_mode(self):
        """Toggle between pan mode and edit mode"""
        self.is_drag_mode = not self.is_drag_mode

        # Update button icon based on mode
        if self.is_drag_mode:
            if os.path.exists(POINTER_ICON):
                self.pan_toggle_button.setIcon(QIcon(POINTER_ICON))
            else:
                self.pan_toggle_button.setText("🖐")  # Raised hand for pan mode
            self.pan_toggle_button.setToolTip("Switch to Edit Mode (Pan Mode Active)")
        else:
            if os.path.exists(DRAG_ICON):
                self.pan_toggle_button.setIcon(QIcon(DRAG_ICON))
            else:
                self.pan_toggle_button.setText("👆")  # Pointing finger for edit mode
            self.pan_toggle_button.setToolTip("Switch to Pan Mode (Edit Mode Active)")

        # Emit signal for mode change
        self.pan_mode_toggle_requested.emit()

    def set_zoom_controls_visible(self, visible):
        """Toggle visibility of zoom controls"""
        self.zoom_out_button.setVisible(visible)
        self.zoom_in_button.setVisible(visible)
        self.reset_zoom_button.setVisible(visible)

        # Adjust widget width based on visible buttons
        if visible:
            self.setFixedWidth(290 if self.pan_toggle_button.isVisible() else 220)
        else:
            self.setFixedWidth(70 if self.pan_toggle_button.isVisible() else 0)

    def set_pan_controls_visible(self, visible):
        """Toggle visibility of pan/edit toggle button"""
        self.pan_toggle_button.setVisible(visible)

        # Adjust widget width based on visible buttons
        zoom_visible = self.zoom_out_button.isVisible()
        if visible:
            self.setFixedWidth(290 if zoom_visible else 70)
        else:
            self.setFixedWidth(220 if zoom_visible else 0)

    def are_zoom_controls_visible(self):
        """Check if zoom controls are visible"""
        return self.zoom_out_button.isVisible()

    def are_pan_controls_visible(self):
        """Check if pan controls are visible"""
        return self.pan_toggle_button.isVisible()

    def _make_circle_icon(self, size=48, color=QColor(0, 0, 0), diagonal=False):
        """Create a QIcon showing a circle. If diagonal=True, draw a diagonal line across it.
        Returns a QIcon.
        """
        pix = QPixmap(size, size)
        pix.fill(QColor(0, 0, 0, 0))  # transparent

        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw circle outline
        pen = QPen(color)
        pen.setWidth(max(2, size // 12))
        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0, 0))
        margin = size // 8
        painter.drawEllipse(margin, margin, size - 2 * margin, size - 2 * margin)

        if diagonal:
            pen2 = QPen(color)
            pen2.setWidth(max(2, size // 10))
            painter.setPen(pen2)
            # draw diagonal from top-left to bottom-right across the circle
            painter.drawLine(margin + 2, margin + 2, size - margin - 2, size - margin - 2)

        painter.end()
        return QIcon(pix)

    def _toggle_hide_points(self):
        """Toggle hide/show state for points and update the button icon, then emit signal with new state."""
        self._hide_points_shown = not getattr(self, '_hide_points_shown', True)
        # Update icon accordingly
        if self._hide_points_shown:
            # Points are currently shown, so user wants to hide them
            icon = self._make_circle_icon(size=48, color=QColor("#905BA9"), diagonal=False)
            self.hide_points_requested.emit()
        else:
            # Points are currently hidden, so user wants to show them
            icon = self._make_circle_icon(size=48, color=QColor("#905BA9"), diagonal=True)
            self.show_points_requested.emit()
        self.hide_points_button.setIcon(icon)

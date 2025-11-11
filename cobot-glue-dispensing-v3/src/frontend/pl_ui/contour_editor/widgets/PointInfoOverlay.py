"""
Point info overlay that appears next to a selected point,
showing quick actions as a radial menu.
"""
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtWidgets import QPushButton, QLabel
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from src.frontend.pl_ui.contour_editor.test import RadialMenu
import math


class PointInfoOverlay(RadialMenu):
    """Radial menu overlay showing point info and quick actions"""

    delete_requested = pyqtSignal()
    line_segment_clicked = pyqtSignal(int, int)  # (seg_index, line_index)
    set_length_requested = pyqtSignal(int, int)  # (seg_index, line_index)

    def __init__(self, parent=None):
        # Initialize with empty tools - will be populated dynamically
        super().__init__([], center_icon="📍", radius=70, parent=parent)

        # Hide the center button since we want direct access to tools
        self.center_btn.hide()

        # Setup as a floating top-level overlay
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Make background transparent
        self.setStyleSheet("background-color: transparent;")

        # Reduce size for compact overlay
        self.resize(200, 200)

        # Track connected segments for display
        self.connected_segments = []
        self.current_seg_index = None  # Track which bezier segment this point belongs to
        self.selected_line_button = None  # Track which line button is currently selected
        self.selected_line_id = None  # Track the selected line ID

        # Create "Set Length" button (shown when a line is selected)
        self.set_length_btn = QPushButton("📏", self)
        self.set_length_btn.setFont(QFont("Arial", 20))
        self.set_length_btn.setFixedSize(50, 50)
        self.set_length_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 25px;
                border: 2px solid white;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
        """)
        self.set_length_btn.setToolTip("Set Line Length")
        self.set_length_btn.clicked.connect(self._on_set_length_clicked)
        self.set_length_btn.hide()

    def _on_delete_clicked(self):
        """Handle delete button click"""
        self.delete_requested.emit()
        self.hide()

    def _on_set_length_clicked(self):
        """Handle set length button click"""
        if self.selected_line_id is not None:
            self.set_length_requested.emit(self.current_seg_index, self.selected_line_id)

    def _on_line_clicked(self, line_id, button):
        """Handle line segment button click - toggle selection"""
        # If clicking the same button, deselect it
        if self.selected_line_button == button:
            self._deselect_line_button()
            self.line_segment_clicked.emit(self.current_seg_index, -1)  # -1 means deselect
            # Hide set length button
            self.set_length_btn.hide()
            self.selected_line_id = None
        else:
            # Deselect previous button if any
            self._deselect_line_button()

            # Select new button
            self.selected_line_button = button
            self.selected_line_id = line_id
            button.setStyleSheet("""
                QPushButton {
                    background-color: #FFA500;
                    color: white;
                    border-radius: 25px;
                    border: 3px solid #FFD700;
                }
                QPushButton:hover {
                    background-color: #FFB732;
                }
            """)

            # Show and position set length button at center
            center_x = self.width() // 2 - self.set_length_btn.width() // 2
            center_y = self.height() // 2 - self.set_length_btn.height() // 2
            self.set_length_btn.setGeometry(center_x, center_y, self.set_length_btn.width(), self.set_length_btn.height())
            self.set_length_btn.show()
            self.set_length_btn.raise_()

            # Emit signal with segment and line index
            self.line_segment_clicked.emit(self.current_seg_index, line_id)

    def _deselect_line_button(self):
        """Deselect the currently selected line button"""
        if self.selected_line_button:
            self.selected_line_button.setStyleSheet("""
                QPushButton {
                    background-color: #6750A4;
                    color: white;
                    border-radius: 25px;
                    border: 2px solid white;
                }
                QPushButton:hover {
                    background-color: #7860B4;
                }
                QPushButton:pressed {
                    background-color: #FFA500;
                }
            """)
            self.selected_line_button = None

    def set_point_info(self, role, seg_index, point_index, connected_segments=None):
        """
        Set the point information to display - creates buttons for each connected line

        Args:
            role: "anchor" or "control"
            seg_index: Index of the segment containing this point
            point_index: Index of the point within the segment
            connected_segments: List of line segment indices this point connects to
        """
        # Store segment info
        self.connected_segments = connected_segments if connected_segments else []
        self.current_seg_index = seg_index
        self.selected_line_button = None  # Reset selection

        # Clear existing tool buttons
        for btn in self.tool_buttons:
            btn.deleteLater()
        self.tool_buttons.clear()

        # Create buttons for each connected line segment
        for line_id in self.connected_segments:
            btn = QPushButton(f"L{line_id}", self)
            btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            btn.setFixedSize(50, 50)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #6750A4;
                    color: white;
                    border-radius: 25px;
                    border: 2px solid white;
                }
                QPushButton:hover {
                    background-color: #7860B4;
                }
                QPushButton:pressed {
                    background-color: #FFA500;
                }
            """)
            btn.setToolTip(f"Line segment {line_id}")
            btn.setProperty("line_id", line_id)  # Store line ID in button
            btn.clicked.connect(lambda checked, lid=line_id, b=btn: self._on_line_clicked(lid, b))
            btn.hide()
            self.tool_buttons.append(btn)

        # Add delete button at the end
        delete_btn = QPushButton("🗑️", self)
        delete_btn.setFont(QFont("Arial", 20))
        delete_btn.setFixedSize(50, 50)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5252;
                color: white;
                border-radius: 25px;
                border: 2px solid white;
            }
            QPushButton:hover {
                background-color: #FF6666;
            }
        """)
        delete_btn.setToolTip("Delete Point")
        delete_btn.clicked.connect(self._on_delete_clicked)
        delete_btn.hide()
        self.tool_buttons.append(delete_btn)

        # Reset menu state
        self.menu_open = False

    def show_at(self, screen_pos: QPoint, offset_x=0, offset_y=0):
        """
        Show the radial overlay centered on the point

        Args:
            screen_pos: Position in screen coordinates (global)
            offset_x: Horizontal offset from the point (not used, centered)
            offset_y: Vertical offset from the point (not used, centered)
        """
        # Center the widget on the point
        center_offset = QPoint(self.width() // 2, self.height() // 2)
        self.move(screen_pos - center_offset)

        # Show the widget
        self.show()
        self.raise_()
        self.activateWindow()

        # Automatically open the radial menu (show tools immediately)
        if not self.menu_open:
            self._show_tools_immediately()

    def _show_tools_immediately(self):
        """Show tools without animation, directly positioned"""
        self.menu_open = True
        center_x, center_y = self.width() // 2, self.height() // 2
        count = len(self.tool_buttons)

        if count == 0:
            return

        angle_step = 360 / count

        # Position buttons directly without animation
        for i, btn in enumerate(self.tool_buttons):
            btn.show()
            angle_deg = i * angle_step - 90  # Start from top
            angle_rad = math.radians(angle_deg)
            target_x = center_x + self.radius * math.cos(angle_rad) - btn.width() / 2
            target_y = center_y + self.radius * math.sin(angle_rad) - btn.height() / 2

            # Set geometry directly (no animation) - use the button's actual size
            btn.setGeometry(int(target_x), int(target_y), btn.width(), btn.height())

    def hideEvent(self, event):
        """Clear highlighted line when overlay hides"""
        if self.selected_line_button:
            # Emit deselect signal
            self.line_segment_clicked.emit(self.current_seg_index, -1)
            self._deselect_line_button()
        # Hide set length button
        self.set_length_btn.hide()
        self.selected_line_id = None
        super().hideEvent(event)
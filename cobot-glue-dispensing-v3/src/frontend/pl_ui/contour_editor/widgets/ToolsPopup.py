import os
from PyQt6.QtWidgets import (
    QApplication, QDialog, QLabel, QVBoxLayout, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.frontend.pl_ui.contour_editor.widgets.ToolIconWidget import ToolIconWidget

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icons")
print(f"Resource directory: {RESOURCE_DIR}")
MAGNIFIER_ICON = os.path.join(RESOURCE_DIR, "MAGNIFIER.png")
RULER_ICON = os.path.join(RESOURCE_DIR, "RULER_ICON.png")
RECTANGLE_SELECTION_ICON = os.path.join(RESOURCE_DIR, "RECTANGLE_SELECTION.png")


class ToolsPopup(QDialog):
    """Reusable Material Design Tools Popup with signal and callback support."""

    # Qt signal for tool selection
    toolSelected = pyqtSignal(str)

    def __init__(self, parent=None, on_tool_selected=None, active_states=None,auto_close_on_select=False):
        super().__init__(parent)

        # Optional Python callback (for non-slot usage)
        self.on_tool_selected = on_tool_selected or (lambda tool: None)
        self.active_states = active_states or {}
        self.auto_close_on_select = auto_close_on_select
        # Dialog configuration
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setModal(True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # Load icons
        resource_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icons")
        self.icons = {
            "magnifier": os.path.join(resource_dir, "MAGNIFIER.png"),
            "ruler": os.path.join(resource_dir, "RULER_ICON.png"),
            "rectangle_select": os.path.join(resource_dir, "RECTANGLE_SELECTION.png"),
        }

        self._setup_ui()

    # -------------------------------------------------------------------------
    # UI SETUP
    # -------------------------------------------------------------------------
    def _setup_ui(self):
        """Initialize all UI elements."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Title
        title = QLabel("Tools")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #1D1B20;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                margin-bottom: 8px;
            }
        """)
        main_layout.addWidget(title)

        # Tools grid
        tools_layout = QGridLayout()
        tools_layout.setSpacing(12)

        # Create and add icons
        self._ruler_icon = self._create_tool_icon(
            "Ruler", self.icons["ruler"], "📏",
            is_active=self.active_states.get("ruler", False)
        )
        self._magnifier_icon = self._create_tool_icon(
            "Magnifier", self.icons["magnifier"], "🔍",
            is_active=self.active_states.get("magnifier", False)
        )
        self._rectangle_select_icon = self._create_tool_icon(
            "Rectangle Select", self.icons["rectangle_select"], "▭",
            is_active=self.active_states.get("rectangle_select", False)
        )

        tools_layout.addWidget(self._ruler_icon, 0, 0)
        tools_layout.addWidget(self._magnifier_icon, 0, 1)
        tools_layout.addWidget(self._rectangle_select_icon, 0, 2)

        main_layout.addLayout(tools_layout)

        # Apply Material Design styling
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFBFE;
                border: 1px solid #CAC4D0;
                border-radius: 12px;
            }
        """)

    # -------------------------------------------------------------------------
    # TOOL ICON CREATION
    # -------------------------------------------------------------------------
    def _create_tool_icon(self, name, icon_path, emoji_fallback, is_active=False):
        icon_widget = ToolIconWidget(
            name,
            icon_path=icon_path,
            emoji_fallback=emoji_fallback,
            is_active=is_active
        )
        icon_widget.clicked.connect(lambda tool=name: self._on_tool_clicked(tool))
        return icon_widget

    # -------------------------------------------------------------------------
    # TOOL CLICK HANDLER
    # -------------------------------------------------------------------------
    def _on_tool_clicked(self, tool_name):
        """Handle tool selection, emit signal, invoke callback, and close popup."""
        print(f"ToolsPopup: Tool clicked: {tool_name}")
        
        # Emit Qt signal for connected slots
        self.toolSelected.emit(tool_name)

        selected_tool = None
        if tool_name == "Ruler":
            self._rectangle_select_icon.set_active(active=False)
            selected_tool = self._ruler_icon
        elif tool_name == "Magnifier":
            selected_tool = self._magnifier_icon
        elif tool_name == "Rectangle Select":
            self._ruler_icon.set_active(active=False)
            selected_tool = self._rectangle_select_icon
        else:
            raise ValueError(f"Unknown tool selected: {tool_name}")

        selected_tool.toggle_active()

        if self.auto_close_on_select:
            self.close()

    # -------------------------------------------------------------------------
    # DIALOG DISPLAY
    # -------------------------------------------------------------------------
    def show_centered(self):
        """Center the dialog on the primary screen and show."""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        dialog_size = self.sizeHint()

        center_x = screen_geometry.center().x() - dialog_size.width() // 2
        center_y = screen_geometry.center().y() - dialog_size.height() // 2

        self.move(center_x, center_y)
        self.exec()

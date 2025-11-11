import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QFrame


class ToolIconWidget(QFrame):
    """Material Design tool icon widget for ExpandedFolderView"""
    clicked = pyqtSignal(str)  # Emits tool name when clicked

    def __init__(self, tool_name, icon_path=None, emoji_fallback="🔧", is_active=False, parent=None):
        super().__init__(parent)
        self.tool_name = tool_name
        self.icon_path = icon_path
        self.emoji_fallback = emoji_fallback
        self.is_active = is_active

        self.setFixedSize(80, 100)  # Material Design app icon size
        self.setObjectName("ToolIcon")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setup_ui()

    def setup_ui(self):
        """Setup Material Design 3 tool icon layout"""
        # Only create layout if it doesn't exist
        if self.layout() is None:
            layout = QVBoxLayout(self)
            layout.setSpacing(8)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Icon container with Material Design styling
            self.icon_container = QFrame()
            self.icon_container.setFixedSize(56, 56)  # Material Design icon container
            self.icon_container.setObjectName("ToolIconContainer")

            # Icon layout
            icon_layout = QVBoxLayout(self.icon_container)
            icon_layout.setContentsMargins(0, 0, 0, 0)
            icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Icon label
            self.icon_label = QLabel()
            self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            icon_layout.addWidget(self.icon_label)
            layout.addWidget(self.icon_container)

            # Tool name label
            self.name_label = QLabel(self.tool_name)
            self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.name_label.setWordWrap(True)
            self.name_label.setStyleSheet("""
                QLabel {
                    color: #1D1B20;
                    font-size: 12px;
                    font-weight: 500;
                    background: transparent;
                    font-family: 'Roboto', 'Segoe UI', sans-serif;
                }
            """)
            layout.addWidget(self.name_label)
        
        # Always update styling and content
        self.update_styling()

    def update_styling(self):
        """Update styling based on active state without recreating layout"""
        # Apply active/inactive styling to icon container
        if self.is_active:
            self.icon_container.setStyleSheet("""
                QFrame#ToolIconContainer {
                    background: #6750A4;
                    border: none;
                    border-radius: 28px;
                }
            """)
        else:
            self.icon_container.setStyleSheet("""
                QFrame#ToolIconContainer {
                    background: #F7F2FA;
                    border: none;
                    border-radius: 28px;
                }
                QFrame#ToolIconContainer:hover {
                    background: #E8DEF8;
                }
            """)

        # Update icon/emoji and its styling
        if self.icon_path and os.path.exists(self.icon_path):
            self.icon_label.setPixmap(QIcon(self.icon_path).pixmap(32, 32))
        else:
            self.icon_label.setText(self.emoji_fallback)
            self.icon_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 24px;
                    color: {'white' if self.is_active else '#1D1B20'};
                    background: transparent;
                }}
            """)

    def mousePressEvent(self, event):
        """Handle tool selection"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.tool_name)
        super().mousePressEvent(event)

    def set_active(self, active):
        """Update visual state"""
        self.is_active = active
        self.update_styling()  # Update styling without recreating layout

    def toggle_active(self):
        """Toggle active state"""
        self.is_active = not self.is_active
        self.update_styling()  # Update styling without recreating layout

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout

    app = QApplication(sys.argv)

    window = QWidget()
    layout = QHBoxLayout(window)

    tool1 = ToolIconWidget("Select", icon_path="icons/select.png", emoji_fallback="🖱️", is_active=True)
    tool2 = ToolIconWidget("Brush", icon_path="icons/brush.png", emoji_fallback="🖌️")
    tool3 = ToolIconWidget("Eraser", icon_path="icons/eraser.png", emoji_fallback="🩹")

    layout.addWidget(tool1)
    layout.addWidget(tool2)
    layout.addWidget(tool3)

    window.show()
    sys.exit(app.exec())
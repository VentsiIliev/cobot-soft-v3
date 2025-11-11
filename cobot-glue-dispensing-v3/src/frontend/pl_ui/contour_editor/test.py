import sys
import math
from typing import List, Union
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton
from PyQt6.QtCore import QRect, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont

class RadialMenu(QWidget):
    def __init__(
        self,
        tools: Union[List[str], List[QPushButton]],
        center_icon: str = "⚙️",
        radius: int = 150,
        parent=None
    ):
        """
        Reusable radial menu widget.

        :param tools: List of emoji strings OR QPushButtons
        :param center_icon: Icon for the central toggle button
        :param radius: Distance of tool buttons from center
        """
        super().__init__(parent)
        self.setStyleSheet("background-color: #111;")
        self.resize(500, 500)

        self.radius = radius
        self.menu_open = False

        # Central toggle button
        self.center_btn = QPushButton(center_icon, self)
        self.center_btn.setGeometry(230, 230, 80, 80)
        self.center_btn.setStyleSheet("""
            QPushButton {
                background-color: #905BA9;
                color: white;
                border-radius: 40px;
                font-size: 28px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.center_btn.clicked.connect(self.toggle_menu)

        # Handle incoming tools (icons or QPushButtons)
        self.tool_buttons = []
        for item in tools:
            if isinstance(item, QPushButton):
                btn = item
                btn.setParent(self)
            else:
                btn = QPushButton(str(item), self)
                btn.setFont(QFont("Arial", 20))
                btn.setFixedSize(60, 60)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #905BA9;
                        color: white;
                        border-radius: 30px;
                    }
                    QPushButton:hover {
                        background-color: #3399ff;
                    }
                """)
                btn.clicked.connect(lambda checked=False, i=item: self.on_tool_clicked(i))

            btn.hide()
            self.tool_buttons.append(btn)

    def toggle_menu(self):
        """Expand or collapse the radial tool menu."""
        self.menu_open = not self.menu_open
        center_x, center_y = 270, 270
        count = len(self.tool_buttons)
        angle_step = 360 / count if count else 0

        if self.menu_open:
            # Animate buttons outward
            for i, btn in enumerate(self.tool_buttons):
                btn.show()
                angle_deg = i * angle_step - 90
                angle_rad = math.radians(angle_deg)
                target_x = center_x + self.radius * math.cos(angle_rad) - btn.width() / 2
                target_y = center_y + self.radius * math.sin(angle_rad) - btn.height() / 2

                anim = QPropertyAnimation(btn, b"geometry", self)
                anim.setDuration(300)
                anim.setEasingCurve(QEasingCurve.Type.OutBack)
                anim.setStartValue(QRect(230, 230, 60, 60))
                anim.setEndValue(QRect(int(target_x), int(target_y), 60, 60))
                anim.start()
                btn.anim = anim
        else:
            # Animate inward then hide
            for btn in self.tool_buttons:
                anim = QPropertyAnimation(btn, b"geometry", self)
                anim.setDuration(250)
                anim.setEasingCurve(QEasingCurve.Type.InBack)
                anim.setEndValue(QRect(230, 230, 60, 60))
                anim.start()
                btn.anim = anim
            QTimer.singleShot(260, lambda: [b.hide() for b in self.tool_buttons])

    def on_tool_clicked(self, tool):
        """Triggered when a tool is clicked — override or connect externally."""
        print(f"Tool selected: {tool}")

# Example usage
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # # You can pass a list of strings (emojis or labels)
    # 🎨 Updated tool set with Rectangle & Multi-Point selection tools
    tools = [
        "🖊️",  # Pen
        "✂️",  # Scissors
        "🧭",  # Compass
        "🎨",  # Paint
        "📐",  # Ruler
        "🔍",  # Zoom
        "💡",  # Light / idea
        "⚒️",  # Hammer
        "🔳",  # Rectangle selection
        "🔼",  # Multi-point selection (custom placeholder icon)
        "🗑️"  # Delete / trash
    ]
    menu = RadialMenu(tools, center_icon="🔧", radius=150)
    menu.setWindowTitle("Reusable Radial Menu Example")
    menu.show()

    # OR: pass custom QPushButtons if you want custom behavior/styles
    # from PyQt6.QtWidgets import QPushButton
    # custom_tools = [QPushButton("A"), QPushButton("B"), QPushButton("C")]
    # custom_menu = RadialMenu(custom_tools, center_icon="🔧")
    # custom_menu.show()
    #
    sys.exit(app.exec())

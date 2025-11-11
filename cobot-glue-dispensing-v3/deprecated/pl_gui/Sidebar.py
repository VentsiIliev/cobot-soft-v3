from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QFrame
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from deprecated.pl_gui.customWidgets.Drawer import Drawer

class Sidebar(Drawer,QFrame):
    def __init__(self, screen_width, upperButtonsConfigList, lowerButtonsConfigList=None):
        super().__init__()
        self.side= "left"  # Default side
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: white;")  # Default background color
        self.setContentsMargins(0, 0, 0, 0)
        self.upperButtonsConfigList = upperButtonsConfigList
        self.lowerButtonsConfigList = lowerButtonsConfigList
        self.buttons = []
        self.buttonsDict = {}
        self.screen_width = screen_width

        print("Sidebar initialized with screen width:", self.screen_width)
        self.setFixedWidth(int(self.screen_width * 0.10))

        # Layout for sidebar
        self.sidebar_layout = QVBoxLayout(self)
        self.sidebar_layout.setSpacing(2)  # Adjust spacing here as needed
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)

        # Create all sidebar buttons
        self.create_sidebar_buttons()

    def hide_button(self, key):
        print("IN HIDE BUTTON")
        """Hide a button by its key."""
        if key in self.buttonsDict:
            self.buttonsDict[key].setVisible(False)
            print("Button hidden")
        else:
            print(f"Button {key} not found")


    def show_button(self, key):
        """Hide a button by its key."""
        if key in self.buttonsDict:
            self.buttonsDict[key].setVisible(True)


    def create_sidebar_buttons(self):
        """Create all sidebar buttons and add them to the layout."""
        for config in self.upperButtonsConfigList:
            button = QPushButton()
            button.setCheckable(True)  # Enables toggle behavior
            button.setAutoExclusive(True)
            button.setIcon(QIcon(config.normalIconPath))
            button.normal_icon = config.normalIconPath  # Store normal icon
            button.pressed_icon = config.pressedIconPath  # Store pressed icon
            # button.setToolTip(config.tooltip)
            button.button_key = config.tooltip  # <-- Assign a key for permission lookup
            # print(f"[DEBUG] Button created: {config.tooltip}")
            # print("Button tooltip: ",config.tooltip)
            button.clicked.connect(config.callback)
            button.toggled.connect(lambda checked, btn=button: self.update_icon(btn, checked))  # Change icon on toggle
            button.setStyleSheet("border: none; background: transparent; padding: 0px;")
            self.buttonsDict[config.tooltip] = button
            self.buttons.append(button)
            self.sidebar_layout.addWidget(button)

        self.sidebar_layout.addStretch()

        if self.lowerButtonsConfigList is None:
            return

        for config in self.lowerButtonsConfigList:
            button = QPushButton()
            button.setCheckable(True)  # Enables toggle behavior
            button.setAutoExclusive(True)
            button.setIcon(QIcon(config.normalIconPath))
            button.normal_icon = config.normalIconPath  # Store normal icon
            button.pressed_icon = config.pressedIconPath  # Store pressed icon
            # button.setToolTip(config.tooltip)
            button.button_key = config.tooltip  # <-- Assign a key for permission lookup
            # print(f"[DEBUG] Button created: {config.tooltip}")

            button.clicked.connect(config.callback)
            button.toggled.connect(lambda checked, btn=button: self.update_icon(btn, checked))  # Change icon on toggle
            button.setStyleSheet("border: none; background: transparent; padding: 0px;")
            self.buttons.append(button)
            self.sidebar_layout.addWidget(button)

    def update_icon(self, button, checked):
        """Update icon based on button's checked state."""
        if checked:
            button.setIcon(QIcon(button.pressed_icon))
        else:
            button.setIcon(QIcon(button.normal_icon))

    def update_button_states(self):
        """Ensure only one button remains checked at a time."""
        for button in self.buttons:
            if button.isChecked():
                button.setIcon(QIcon(button.pressed_icon))
            else:
                button.setIcon(QIcon(button.normal_icon))
                button.setChecked(False)  # Uncheck others

    def alignItemsLeft(self):
        for button in self.buttons:
            self.sidebar_layout.setAlignment(button, Qt.AlignmentFlag.AlignLeft)

    def alignItemsCenter(self):
        for button in self.buttons:
            self.sidebar_layout.setAlignment(button, Qt.AlignmentFlag.AlignCenter)

    def uncheck_all_buttons(self):
        """Uncheck all buttons in the sidebar."""
        for button in self.buttons:
            button.setChecked(False)

if  __name__ == "__main__":
    # Example usage
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    sidebar = Sidebar(800, [])
    sidebar.show()
    sys.exit(app.exec())
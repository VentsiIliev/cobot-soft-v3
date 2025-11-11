from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QGridLayout,
    QLineEdit, QApplication, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer
import sys
import json
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve


class KeyboardConfig:
    """Configuration manager for the virtual keyboard"""

    def __init__(self, config_path="keyboard_config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load config file {self.config_path}: {e}")
            return self._get_default_config()

    def _get_default_config(self):
        """Return default configuration if file cannot be loaded"""
        return {
            "screen_categories": {
                "mobile": {
                    "width_threshold": 600,
                    "keyboard_width_percent": 0.95,
                    "keyboard_height_percent": 0.4,
                    "button_height": 35,
                    "font_size": 12,
                    "spacing": 3,
                    "margins": 4,
                    "border_radius": 4,
                    "border_width": 1
                },
                "tablet": {
                    "width_threshold": 1024,
                    "keyboard_width_percent": 0.8,
                    "keyboard_height_percent": 0.45,
                    "button_height": 40,
                    "font_size": 14,
                    "spacing": 6,
                    "margins": 8,
                    "border_radius": 6,
                    "border_width": 2
                },
                "desktop": {
                    "keyboard_width_max": 1200,
                    "keyboard_width_percent": 0.7,
                    "keyboard_height_percent": 0.5,
                    "button_height": 45,
                    "font_size": 16,
                    "spacing": 8,
                    "margins": 12,
                    "border_radius": 8,
                    "border_width": 3
                }
            },
            "colors": {
                "background": "#FFFFFF",
                "border": "#999999",
                "button_text": "#905BA9",
                "button_border": "#905BA9",
                "button_background": "#FFFFFF",
                "button_hover_background": "#905BA9",
                "button_hover_text": "#FFFFFF",
                "button_pressed_background": "#905BA9",
                "button_pressed_text": "#FFFFFF",
                "hide_button_background": "#905BA9",
                "hide_button_hover": "#7A4A8A",
                "hide_button_pressed": "#6A3A7A",
                "hide_button_text": "#FFFFFF"
            },
            "style": {
                "font_weight": "bold",
                "button_border_radius_offset": 2,
                "hide_button_font_size_offset": 2
            },
            "shadow": {
                "blur_radius": 20,
                "x_offset": 0,
                "y_offset": 2,
                "color": "rgba(0, 0, 0, 80)"
            },
            "animation": {
                "slide_duration": 300,
                "slide_curve_in": "InCubic",
                "slide_curve_out": "OutCubic"
            }
        }

    def get_screen_config(self, category):
        """Get configuration for a specific screen category"""
        return self.config["screen_categories"].get(category, self.config["screen_categories"]["mobile"])

    def get_colors(self):
        """Get color configuration"""
        return self.config["colors"]

    def get_style(self):
        """Get style configuration"""
        return self.config["style"]

    def get_shadow(self):
        """Get shadow configuration"""
        return self.config["shadow"]

    def get_animation(self):
        """Get animation configuration"""
        return self.config["animation"]


# ----- Virtual Keyboard Singleton -----
class VirtualKeyboardSingleton:
    __instance = None
    suppress_next_show = False

    @staticmethod
    def getInstance(target_input=None, parent=None) -> 'VirtualKeyboard':
        if VirtualKeyboardSingleton.__instance is None:
            VirtualKeyboardSingleton.__instance = VirtualKeyboard(target_input=target_input, parent=parent)
        else:
            if target_input:
                VirtualKeyboardSingleton.__instance.update_target_input(target_input)
            # Check if parent changed — reparent if necessary
            if parent is not None and VirtualKeyboardSingleton.__instance.parent() != parent:
                VirtualKeyboardSingleton.__instance.setParent(parent)
        return VirtualKeyboardSingleton.__instance

    @staticmethod
    def suppress_once():
        VirtualKeyboardSingleton.suppress_next_show = True

    @staticmethod
    def should_suppress():
        val = VirtualKeyboardSingleton.suppress_next_show
        VirtualKeyboardSingleton.suppress_next_show = False
        return val


# ----- Custom Input Field -----
class FocusLineEdit(QLineEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        print("fle: ", self.parent)

    def focusInEvent(self, event):
        print("FocusEvent")
        super().focusInEvent(event)
        if VirtualKeyboardSingleton.should_suppress():
            return

        # Get the top-level window (main window)
        main_window = self.window()
        keyboard = VirtualKeyboardSingleton.getInstance(self, main_window)
        keyboard.update_target_input(self)

        # Only slide in if keyboard is not already visible
        if not keyboard.isVisible():
            keyboard.slide_in("bottom-left")


# ----- Virtual Keyboard -----
class VirtualKeyboard(QWidget):
    def __init__(self, target_input=None, parent=None):
        super().__init__(parent)
        self.setObjectName("VirtualKeyboard")

        # Load configuration
        self.config_manager = KeyboardConfig()

        self.target_input = target_input
        self.setWindowTitle(" ")
        self.is_sliding = False  # Track animation state

        # FIXED: Remove FramelessWindowHint and use proper flags for child widget
        if parent:
            # If we have a parent, make it a child widget
            self.setWindowFlags(Qt.WindowType.Widget)
        else:
            # If no parent, make it a tool window that stays on top
            self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)

        # Force the widget to have a solid background - MULTIPLE METHODS
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)

        # Set background using palette as backup
        from PyQt6.QtGui import QPalette, QColor
        palette = self.palette()
        colors = self.config_manager.get_colors()
        palette.setColor(QPalette.ColorRole.Window, QColor(colors["background"]))
        self.setPalette(palette)

        # Responsive sizing - no fixed minimum size
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.drag_position = QPoint()
        self.mode = 'letters'

        # Get base configuration for layout spacing
        mobile_config = self.config_manager.get_screen_config("mobile")

        # Responsive layout with dynamic margins and spacing
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(mobile_config["margins"], mobile_config["margins"],
                                       mobile_config["margins"], mobile_config["margins"])
        self.layout.setSpacing(mobile_config["spacing"])
        self.setLayout(self.layout)

        self.grid_layout = QGridLayout()
        self.grid_layout.setContentsMargins(mobile_config["margins"] // 2, mobile_config["margins"] // 2,
                                            mobile_config["margins"] // 2, mobile_config["margins"] // 2)
        self.grid_layout.setSpacing(mobile_config["spacing"])

        self.layout.addLayout(self.grid_layout)

        # Responsive hide button
        self.hide_button = QPushButton("▼")  # Down arrow
        self.hide_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.hide_button.clicked.connect(self.hideKeyboard)
        self.layout.addWidget(self.hide_button)

        self.key_buttons = []
        self.build_keyboard()
        self.apply_styles()
        self.update_responsive_sizing()

        # Add shadow effect from config
        self._setup_shadow()

        # Override paintEvent to ensure background
        self.paintEvent = self.custom_paint_event

        # Connect to parent resize events
        if parent:
            parent.resizeEvent = self._wrap_parent_resize(parent.resizeEvent)

    def _setup_shadow(self):
        """Setup shadow effect based on configuration"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor

        shadow_config = self.config_manager.get_shadow()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(shadow_config["blur_radius"])
        shadow.setXOffset(shadow_config["x_offset"])
        shadow.setYOffset(shadow_config["y_offset"])

        # Parse color from config (assuming rgba format)
        color_str = shadow_config["color"]
        if color_str.startswith("rgba"):
            # Extract rgba values
            rgba_values = color_str.replace("rgba(", "").replace(")", "").split(",")
            r, g, b, a = [int(x.strip()) for x in rgba_values]
            shadow.setColor(QColor(r, g, b, a))
        else:
            shadow.setColor(QColor(color_str))

        self.setGraphicsEffect(shadow)

    def _wrap_parent_resize(self, original_resize):
        """Wrap parent's resize event to update keyboard sizing"""

        def wrapped_resize(event):
            original_resize(event)
            if self.isVisible():
                QTimer.singleShot(10, self.update_responsive_sizing)

        return wrapped_resize

    def get_screen_size_category(self):
        """Determine screen size category for responsive behavior"""
        if self.parent():
            width = self.parent().width()
            height = self.parent().height()
        else:
            screen = QApplication.primaryScreen().geometry()
            width = screen.width()
            height = screen.height()

        # Get thresholds from config
        mobile_threshold = self.config_manager.get_screen_config("mobile")["width_threshold"]
        tablet_threshold = self.config_manager.get_screen_config("tablet")["width_threshold"]

        # Categorize screen sizes
        if width < mobile_threshold:
            return 'mobile'
        elif width < tablet_threshold:
            return 'tablet'
        else:
            return 'desktop'

    def update_responsive_sizing(self):
        """Update keyboard size and layout based on screen size"""
        category = self.get_screen_size_category()
        config = self.config_manager.get_screen_config(category)

        if self.parent():
            parent_width = self.parent().width()
            parent_height = self.parent().height()
        else:
            screen = QApplication.primaryScreen().geometry()
            parent_width = screen.width()
            parent_height = screen.height()

        # Calculate responsive dimensions from config
        if category == 'desktop' and 'keyboard_width_max' in config:
            keyboard_width = min(config["keyboard_width_max"],
                                 int(parent_width * config["keyboard_width_percent"]))
        else:
            keyboard_width = int(parent_width * config["keyboard_width_percent"])

        keyboard_height = int(parent_height * config["keyboard_height_percent"])

        # Use config values with fallbacks for dynamic calculations
        button_height = max(config["button_height"], int(parent_height * 0.05))
        font_size = max(config["font_size"], int(parent_width * 0.015))
        spacing = config["spacing"]
        margins = config["margins"]

        # Update widget size
        self.setFixedSize(keyboard_width, keyboard_height)

        # Update layouts
        self.layout.setContentsMargins(margins, margins, margins, margins)
        self.layout.setSpacing(spacing)
        self.grid_layout.setContentsMargins(margins // 2, margins // 2, margins // 2, margins // 2)
        self.grid_layout.setSpacing(spacing)

        # Update hide button
        self.hide_button.setMinimumHeight(button_height)
        self.hide_button.setMaximumHeight(button_height)

        # Update button sizes and fonts
        for button in self.key_buttons:
            button.setMinimumHeight(button_height)
            font = button.font()
            font.setPointSize(font_size)
            button.setFont(font)

        # Update hide button font
        style_config = self.config_manager.get_style()
        hide_font = self.hide_button.font()
        hide_font.setPointSize(font_size + style_config["hide_button_font_size_offset"])
        self.hide_button.setFont(hide_font)

        # Update styles with responsive values
        self.apply_responsive_styles(category, font_size, button_height)

    def apply_responsive_styles(self, category, font_size, button_height):
        """Apply responsive styles based on screen category"""
        config = self.config_manager.get_screen_config(category)
        colors = self.config_manager.get_colors()
        style_config = self.config_manager.get_style()

        border_radius = config["border_radius"]
        border_width = config["border_width"]
        button_border_radius = border_radius - style_config["button_border_radius_offset"]

        self.setStyleSheet(f"""
            #VirtualKeyboard {{
                background-color: {colors["background"]} !important;
                border: {border_width}px solid {colors["border"]};
                border-radius: {border_radius}px;
            }}

            QPushButton {{
                background-color: {colors["button_background"]} !important;
                color: {colors["button_text"]};
                border: 1px solid {colors["button_border"]};
                border-radius: {button_border_radius}px;
                font-size: {font_size}px;
                font-weight: {style_config["font_weight"]};
                min-height: {button_height}px;
                max-height: {button_height}px;
            }}

            QPushButton:pressed {{
                background-color: {colors["button_pressed_background"]} !important;
                color: {colors["button_pressed_text"]};
            }}

            QPushButton:hover {{
                background-color: {colors["button_hover_background"]} !important;
                color: {colors["button_hover_text"]};
            }}
        """)

        # Update hide button specific styles
        hide_font_size = font_size + style_config["hide_button_font_size_offset"]
        self.hide_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["hide_button_background"]} !important;
                color: {colors["hide_button_text"]} !important;
                border: 2px solid {colors["hide_button_background"]};
                border-radius: {border_radius}px;
                font-size: {hide_font_size}px;
                font-weight: {style_config["font_weight"]};
                min-height: {button_height}px;
                max-height: {button_height}px;
            }}
            QPushButton:hover {{
                background-color: {colors["hide_button_hover"]} !important;
            }}
            QPushButton:pressed {{
                background-color: {colors["hide_button_pressed"]} !important;
            }}
        """)

        self.update()
        self.repaint()

    def build_keyboard(self):
        for btn in self.key_buttons:
            btn.deleteLater()
        self.key_buttons.clear()

        # Always show number row
        number_keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        for col, key in enumerate(number_keys):
            button = QPushButton(key)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            button.clicked.connect(lambda _, k=key: self.key_pressed(k))
            self.key_buttons.append(button)
            self.grid_layout.addWidget(button, 0, col)

        # Define layout based on mode
        if self.mode in ['letters', 'shift']:
            keys = [
                ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
                ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
                ['⇧', 'z', 'x', 'c', 'v', 'b', 'n', 'm', '⌫'],
                ['SYM', 'space', '⏎']
            ]
            if self.mode == 'shift':
                keys = [[k.upper() if k not in ['⇧', '⌫', 'SYM', 'space', '⏎'] else k for k in row] for row in keys]
        elif self.mode == 'symbols':
            keys = [
                ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')'],
                ['_', '+', '=', '-', '/', ':', ';', '"', "'"],
                ['ABC', '\\', '|', '<', '>', '[', ']', '{', '}', '⌫'],
                ['.', ',', '⏎']
            ]

        # Add remaining keys with special handling for space
        for row_offset, row in enumerate(keys, start=1):
            for col, key in enumerate(row):
                button = QPushButton(key if key != 'space' else '⎵')  # Space symbol
                button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                button.clicked.connect(lambda _, k=key: self.key_pressed(k))
                self.key_buttons.append(button)

                # Special handling for space bar - make it wider
                if key == 'space':
                    self.grid_layout.addWidget(button, row_offset, col, 1, 3)  # Span 3 columns
                else:
                    self.grid_layout.addWidget(button, row_offset, col)

    def key_pressed(self, key):
        if not self.target_input:
            return
        if key == '⌫':
            self.target_input.backspace()
        elif key == '⏎':
            self.hideKeyboard()
        elif key == '⇧':
            self.mode = 'shift' if self.mode != 'shift' else 'letters'
            self.build_keyboard()
            self.update_responsive_sizing()  # Update after rebuilding
        elif key == 'SYM':
            self.mode = 'symbols'
            self.build_keyboard()
            self.update_responsive_sizing()  # Update after rebuilding
        elif key == 'ABC':
            self.mode = 'letters'
            self.build_keyboard()
            self.update_responsive_sizing()  # Update after rebuilding
        elif key == 'space':
            self.target_input.insert(' ')
        else:
            self.target_input.insert(key)
            if self.mode == 'shift':
                self.mode = 'letters'
                self.build_keyboard()
                self.update_responsive_sizing()  # Update after rebuilding

    def hideKeyboard(self):
        if self.target_input:
            self.target_input.clearFocus()
        self.slide_out_to_bottom()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_position
            self.move(self.pos() + delta)
            self.drag_position = event.globalPosition().toPoint()

    def update_target_input(self, target_input):
        self.target_input = target_input

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update responsive sizing when keyboard itself is resized
        QTimer.singleShot(10, self.update_responsive_sizing)

    def apply_styles(self):
        # Initial styles - will be updated by responsive sizing
        colors = self.config_manager.get_colors()
        style_config = self.config_manager.get_style()

        self.setStyleSheet(f"""
            #VirtualKeyboard {{
                background-color: {colors["background"]} !important;
                border: 3px solid {colors["border"]};
                border-radius: 8px;
            }}

            QPushButton {{
                background-color: {colors["button_background"]} !important;
                color: {colors["button_text"]};
                border: 1px solid {colors["button_border"]};
                border-radius: 6px;
                font-size: 16px;
                font-weight: {style_config["font_weight"]};
                min-height: 30px;
            }}

            QPushButton:pressed {{
                background-color: {colors["button_pressed_background"]} !important;
                color: {colors["button_pressed_text"]};
            }}

            QPushButton:hover {{
                background-color: {colors["button_hover_background"]} !important;
                color: {colors["button_hover_text"]};
            }}
        """)

    def _get_easing_curve(self, curve_name):
        """Convert string curve name to QEasingCurve.Type"""
        curve_map = {
            "InCubic": QEasingCurve.Type.InCubic,
            "OutCubic": QEasingCurve.Type.OutCubic,
            "InOutCubic": QEasingCurve.Type.InOutCubic,
            "Linear": QEasingCurve.Type.Linear,
            "InQuad": QEasingCurve.Type.InQuad,
            "OutQuad": QEasingCurve.Type.OutQuad,
            "InOutQuad": QEasingCurve.Type.InOutQuad
        }
        return curve_map.get(curve_name, QEasingCurve.Type.OutCubic)

    def _calculate_slide_positions(self, corner: str):
        """Calculate start and end positions for sliding in/out from the given corner."""
        if self.parent():
            parent_geom: QRect = self.parent().geometry()
            parent_pos: QPoint = self.parent().mapToGlobal(QPoint(0, 0))
        else:
            parent_geom: QRect = QApplication.primaryScreen().geometry()
            parent_pos: QPoint = QPoint(0, 0)

        kw, kh = self.width(), self.height()
        px, py, pw, ph = parent_pos.x(), parent_pos.y(), parent_geom.width(), parent_geom.height()

        if corner == "bottom-left":
            start = QPoint(px, py + ph)
            end = QPoint(px, py + ph - kh)
        elif corner == "bottom-right":
            start = QPoint(px + pw, py + ph)
            end = QPoint(px + pw - kw, py + ph - kh)
        elif corner == "top-left":
            start = QPoint(px, py - kh)
            end = QPoint(px, py)
        elif corner == "top-right":
            start = QPoint(px + pw, py - kh)
            end = QPoint(px + pw - kw, py)
        else:
            # default fallback bottom-left
            start = QPoint(px, py + ph)
            end = QPoint(px, py + ph - kh)

        return start, end

    def slide_in(self, corner="bottom-left"):
        if self.is_sliding or self.isVisible():
            return
        self.is_sliding = True

        # Update sizing before sliding in
        self.update_responsive_sizing()

        start_pos, end_pos = self._calculate_slide_positions(corner)
        self.move(start_pos)
        self.show()
        self.raise_()
        self.activateWindow()

        animation_config = self.config_manager.get_animation()
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(animation_config["slide_duration"])
        self.anim.setStartValue(start_pos)
        self.anim.setEndValue(end_pos)
        self.anim.setEasingCurve(self._get_easing_curve(animation_config["slide_curve_out"]))
        self.anim.finished.connect(lambda: setattr(self, 'is_sliding', False))
        self.anim.start()

    def slide_out_to_bottom(self):
        if self.is_sliding:
            return
        self.is_sliding = True

        start_pos = self.pos()
        _, end_pos = self._calculate_slide_positions("bottom-left")
        end_pos = QPoint(end_pos.x(), end_pos.y() + self.height())

        animation_config = self.config_manager.get_animation()
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(animation_config["slide_duration"])
        self.anim.setStartValue(start_pos)
        self.anim.setEndValue(end_pos)
        self.anim.setEasingCurve(self._get_easing_curve(animation_config["slide_curve_in"]))
        self.anim.finished.connect(self._on_slide_out_finished)
        self.anim.start()

    def _on_slide_out_finished(self):
        self.hide()
        self.is_sliding = False

    def custom_paint_event(self, event):
        """Custom paint event to ensure background from config"""
        from PyQt6.QtGui import QPainter, QBrush, QColor
        painter = QPainter(self)
        colors = self.config_manager.get_colors()
        painter.fillRect(self.rect(), QBrush(QColor(colors["background"])))
        painter.end()
        # Call the original paintEvent
        super().paintEvent(event)


# ----- Main Application -----
if __name__ == "__main__":
    app = QApplication(sys.argv)

    main_window = QWidget()
    main_window.setStyleSheet("background-color: white;")
    main_window.resize(800, 600)  # Use resize instead of setFixedSize for testing

    input1 = FocusLineEdit(main_window)
    input1.setGeometry(50, 50, 300, 40)

    input2 = FocusLineEdit(main_window)
    input2.setGeometry(50, 120, 300, 40)

    input3 = FocusLineEdit(main_window)
    input3.setGeometry(50, 190, 300, 40)

    main_window.show()
    sys.exit(app.exec())
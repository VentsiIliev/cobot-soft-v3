from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QGridLayout,
    QLineEdit, QApplication, QSizePolicy,QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer
import sys
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve


# ----- Virtual Keyboard Singleton -----
class VirtualKeyboardSingleton:
    __instance = None
    suppress_next_show = False

    @staticmethod
    def getInstance(target_input=None, parent=None) -> 'VirtualKeyboard':
        try:
            if VirtualKeyboardSingleton.__instance is None:
                VirtualKeyboardSingleton.__instance = VirtualKeyboard(target_input=target_input, parent=parent)
            else:
                if target_input:
                    VirtualKeyboardSingleton.__instance.update_target_input(target_input)
                if parent is not None and VirtualKeyboardSingleton.__instance.parent() != parent:
                    VirtualKeyboardSingleton.__instance.setParent(parent)
        except RuntimeError:
            # Instance was deleted, recreate it
            VirtualKeyboardSingleton.__instance = VirtualKeyboard(target_input=target_input, parent=parent)
        return VirtualKeyboardSingleton.__instance

    @staticmethod
    def suppress_once():
        VirtualKeyboardSingleton.suppress_next_show = True

    @staticmethod
    def should_suppress():
        val = VirtualKeyboardSingleton.suppress_next_show
        VirtualKeyboardSingleton.suppress_next_show = False
        return val

from PyQt6.QtWidgets import QSpinBox
from PyQt6.QtCore import Qt


class FocusSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def focusInEvent(self, event):
        print("FocusSpinBox FocusEvent")
        super().focusInEvent(event)
        if VirtualKeyboardSingleton.should_suppress():
            return

        main_window = self.window()
        keyboard = VirtualKeyboardSingleton.getInstance(self, main_window)
        keyboard.update_target_input(self)

        if not keyboard.isVisible():
            keyboard.slide_in("bottom-left")

    def insert(self, text: str):
        """Insert text at cursor position in the spinbox line edit"""
        line_edit = self.lineEdit()
        if line_edit:
            cursor_pos = line_edit.cursorPosition()
            current_text = line_edit.text()
            new_text = current_text[:cursor_pos] + text + current_text[cursor_pos:]
            line_edit.setText(new_text)
            line_edit.setCursorPosition(cursor_pos + len(text))

    def backspace(self):
        """Remove character before cursor position in the spinbox line edit"""
        line_edit = self.lineEdit()
        if line_edit:
            cursor_pos = line_edit.cursorPosition()
            current_text = line_edit.text()
            if cursor_pos > 0:
                new_text = current_text[:cursor_pos - 1] + current_text[cursor_pos:]
                line_edit.setText(new_text)
                line_edit.setCursorPosition(cursor_pos - 1)

class FocusDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent


    def focusInEvent(self, event):
        print("FocusEvent")
        super().focusInEvent(event)
        if VirtualKeyboardSingleton.should_suppress():
            return

        main_window = self.window()
        keyboard = VirtualKeyboardSingleton.getInstance(self, main_window)
        keyboard.update_target_input(self)

        if not keyboard.isVisible():
            keyboard.slide_in("bottom-left")


    def insert(self, text: str):
        line_edit = self.lineEdit()
        if line_edit:
            cursor_pos = line_edit.cursorPosition()
            current_text = line_edit.text()
            new_text = current_text[:cursor_pos] + text + current_text[cursor_pos:]
            line_edit.setText(new_text)
            line_edit.setCursorPosition(cursor_pos + len(text))

    def backspace(self):
        line_edit = self.lineEdit()
        if line_edit:
            cursor_pos = line_edit.cursorPosition()
            current_text = line_edit.text()
            if cursor_pos > 0:
                new_text = current_text[:cursor_pos - 1] + current_text[cursor_pos:]
                line_edit.setText(new_text)
                line_edit.setCursorPosition(cursor_pos - 1)


# ----- Custom Input Field -----
class FocusLineEdit(QLineEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

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
        from PyQt6.QtGui import QPalette
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.white)
        self.setPalette(palette)

        # Responsive sizing - no fixed minimum size
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.drag_position = QPoint()
        self.mode = 'letters'

        # Responsive layout with dynamic margins and spacing
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(8, 8, 8, 8)  # Smaller base margins
        self.layout.setSpacing(6)  # Smaller base spacing
        self.setLayout(self.layout)

        self.grid_layout = QGridLayout()
        self.grid_layout.setContentsMargins(4, 4, 4, 4)  # Smaller base margins
        self.grid_layout.setSpacing(4)  # Smaller base spacing

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

        # Add shadow effect
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)  # Smaller shadow for mobile
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        # Override paintEvent to ensure background
        self.paintEvent = self.custom_paint_event

        # Connect to parent resize events
        if parent:
            parent.resizeEvent = self._wrap_parent_resize(parent.resizeEvent)

    def focus_next_input(self):
        if not self.target_input:
            print("No target input set for focus_next_input")
            return False

        main_window = self.target_input.window()
        inputs = main_window.findChildren(FocusLineEdit)

        if not inputs:
            return False

        try:
            current_index = inputs.index(self.target_input)
        except ValueError:
            return False

        # If current input is last in list, no next input to move to
        if current_index == len(inputs) - 1:
            return False

        next_index = current_index + 1
        next_input = inputs[next_index]
        next_input.setFocus()
        self.update_target_input(next_input)
        return True

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

        # Categorize screen sizes
        if width < 600:
            return 'mobile'
        elif width < 1024:
            return 'tablet'
        else:
            return 'desktop'

    def update_responsive_sizing(self):
        """Update keyboard size and layout based on screen size"""
        category = self.get_screen_size_category()

        if self.parent():
            parent_width = self.parent().width()
            parent_height = self.parent().height()
        else:
            screen = QApplication.primaryScreen().geometry()
            parent_width = screen.width()
            parent_height = screen.height()

        # Responsive dimensions
        if category == 'mobile':
            keyboard_width = int(parent_width * 0.95)
            keyboard_height = int(parent_height * 0.4)
            button_height = max(35, int(parent_height * 0.05))
            font_size = max(12, int(parent_width * 0.025))
            spacing = 3
            margins = 4
        elif category == 'tablet':
            keyboard_width = int(parent_width * 0.8)
            keyboard_height = int(parent_height * 0.45)
            button_height = max(40, int(parent_height * 0.055))
            font_size = max(14, int(parent_width * 0.02))
            spacing = 6
            margins = 8
        else:  # desktop
            keyboard_width = min(1200, int(parent_width * 0.7))
            keyboard_width = int(parent_width * 1)
            keyboard_height = int(parent_height * 0.43)
            button_height = max(45, int(parent_height * 0.06))
            font_size = max(16, int(parent_width * 0.015))
            spacing = 8
            margins = 12

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
        hide_font = self.hide_button.font()
        hide_font.setPointSize(font_size + 2)
        self.hide_button.setFont(hide_font)

        # Update styles with responsive values
        self.apply_responsive_styles(category, font_size, button_height)

    def apply_responsive_styles(self, category, font_size, button_height):
        """Apply responsive styles based on screen category"""
        border_radius = 4 if category == 'mobile' else 6 if category == 'tablet' else 8
        border_width = 1 if category == 'mobile' else 2 if category == 'tablet' else 3

        self.setStyleSheet(f"""
            #VirtualKeyboard {{
                background-color: white !important;
                border: {border_width}px solid #999999;
                border-radius: {border_radius}px;
            }}

            QPushButton {{
                background-color: white !important;
                color: #905BA9;
                border: 1px solid #905BA9;
                border-radius: {border_radius - 2}px;
                font-size: {font_size}px;
                font-weight: bold;
                min-height: {button_height}px;
                max-height: {button_height}px;
            }}

            QPushButton:pressed {{
                background-color: #905BA9 !important;
                color: white;
            }}

            QPushButton:hover {{
                background-color: #905BA9 !important;
                color: white;
            }}
        """)

        # Update hide button specific styles
        hide_font_size = font_size + 2
        self.hide_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #905BA9 !important;
                color: white !important;
                border: 2px solid #905BA9;
                border-radius: {border_radius}px;
                font-size: {hide_font_size}px;
                font-weight: bold;
                min-height: {button_height}px;
                max-height: {button_height}px;
            }}
            QPushButton:hover {{
                background-color: #7A4A8A !important;
            }}
            QPushButton:pressed {{
                background-color: #6A3A7A !important;
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
            if not self.focus_next_input():
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
        self.setStyleSheet("""
            #VirtualKeyboard {
                background-color: white !important;
                border: 3px solid #999999;
                border-radius: 8px;
            }

            QPushButton {
                background-color: white !important;
                color: #905BA9;
                border: 1px solid #905BA9;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                min-height: 30px;
            }

            QPushButton:pressed {
                background-color: #905BA9 !important;
                color: white;
            }

            QPushButton:hover {
                background-color: #905BA9 !important;
                color: white;
            }
        """)

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

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setStartValue(start_pos)
        self.anim.setEndValue(end_pos)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.finished.connect(lambda: setattr(self, 'is_sliding', False))
        self.anim.start()

    def slide_out_to_bottom(self):
        if self.is_sliding:
            return
        self.is_sliding = True

        start_pos = self.pos()
        _, end_pos = self._calculate_slide_positions("bottom-left")
        end_pos = QPoint(end_pos.x(), end_pos.y() + self.height())

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setStartValue(start_pos)
        self.anim.setEndValue(end_pos)
        self.anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim.finished.connect(self._on_slide_out_finished)
        self.anim.start()

    def _on_slide_out_finished(self):
        self.hide()
        self.is_sliding = False

    def custom_paint_event(self, event):
        """Custom paint event to ensure white background"""
        from PyQt6.QtGui import QPainter, QBrush
        painter = QPainter(self)
        painter.fillRect(self.rect(), QBrush(Qt.GlobalColor.white))
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
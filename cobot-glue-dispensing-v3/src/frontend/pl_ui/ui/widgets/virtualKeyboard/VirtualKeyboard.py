from PyQt6.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QGridLayout,
    QLineEdit, QApplication, QSizePolicy, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal
import sys
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QSpinBox
from PyQt6.QtCore import Qt


# ----- Virtual Keyboard Singleton -----
class VirtualKeyboardSingleton:
    __instance = None
    suppress_next_show = False

    @staticmethod
    def getInstance(target_input=None, parent=None) -> 'VirtualKeyboard':
        try:
            if VirtualKeyboardSingleton.__instance is None:
                # print("DEBUG: Creating new keyboard instance")
                VirtualKeyboardSingleton.__instance = VirtualKeyboard(target_input=target_input, parent=parent)
            else:
                # print("DEBUG: Reusing existing keyboard instance")
                if target_input:
                    VirtualKeyboardSingleton.__instance.update_target_input(target_input)
                # NEVER change parent after creation to avoid segfaults
                # Just update the target input
                # print(f"DEBUG: Keeping existing parent: {VirtualKeyboardSingleton.__instance.parent()}")
        except RuntimeError as e:
            # Instance was deleted, recreate it
            # print(f"DEBUG: RuntimeError, recreating keyboard: {e}")
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

    @staticmethod
    def get_current_instance():
        """Get current instance if it exists, None otherwise"""
        return VirtualKeyboardSingleton.__instance


class FocusSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def focusInEvent(self, event):
        # print("FocusSpinBox FocusEvent")
        super().focusInEvent(event)
        if VirtualKeyboardSingleton.should_suppress():
            return

        main_window = self.window()
        # print("Main window focusSpinBox:", main_window)
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
        # print("FocusEvent")
        super().focusInEvent(event)
        if VirtualKeyboardSingleton.should_suppress():
            return

        # main_window = self.window()
        main_window = self.parent if self.parent else self.window()
        # print("Main window focusSpinBox:", main_window)
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
        # print("FocusEvent")
        super().focusInEvent(event)
        if VirtualKeyboardSingleton.should_suppress():
            return

        # Get the main application window for positioning
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        main_window = None
        current_window = self.window()

        # Detect if current window is a modal dialog
        is_modal_dialog = (
                hasattr(current_window, 'isModal') and current_window.isModal() or
                'Dialog' in type(current_window).__name__ and current_window.width() < 800
        )

        # print(f"DEBUG: Is modal dialog: {is_modal_dialog}")
        # print(f"DEBUG: Current window modal: {getattr(current_window, 'isModal', lambda: False)()}")

        # Find the main window for positioning reference
        main_window = None
        for widget in app.topLevelWidgets():
            if widget.isVisible() and widget != current_window:
                # Check for MainWindow class or large window size, but exclude VirtualKeyboard
                is_main_window = (
                        'VirtualKeyboard' not in type(widget).__name__ and (
                        hasattr(widget, 'centralWidget') or
                        'MainWindow' in type(widget).__name__ or
                        widget.width() > 800  # Assume main windows are large
                )
                )
                if is_main_window:
                    main_window = widget
                    break

        # If current window is main window, use it
        if main_window is None and ('MainWindow' in type(current_window).__name__ or current_window.width() > 800):
            main_window = current_window

        # print(f"DEBUG: Main window found: {main_window}")

        parent_changed = False
        # SIMPLE FIX: Always use no parent and use screen positioning
        keyboard = VirtualKeyboardSingleton.getInstance(self, None)
        # print("DEBUG: Using simplified no-parent approach")

        keyboard.update_target_input(self)

        # Always ensure keyboard is visible and positioned correctly
        # print(f"DEBUG: Keyboard visible before show logic: {keyboard.isVisible()}")

        # Always show keyboard (simplified approach)
        if not keyboard.isVisible():
            keyboard.slide_in("bottom-left")
        else:
            # If keyboard is already visible, just update the target without hiding
            # print("DEBUG: Keyboard already visible, just updating target")
            keyboard.update_target_input(self)


# ----- Virtual Keyboard -----
class VirtualKeyboard(QWidget):
    shown = pyqtSignal()
    hidden = pyqtSignal()
    def __init__(self, target_input=None, parent=None):
        super().__init__(parent)
        self.setObjectName("VirtualKeyboard")

        self.target_input = target_input
        self.setWindowTitle(" ")
        self.is_sliding = False  # Track animation state

        # SIMPLE FIX: Use minimal window flags and no parent dependency
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        # Set window modality to allow interaction
        self.setWindowModality(Qt.WindowModality.NonModal)

        # Force no parent to make it truly independent
        self.setParent(None)

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

        # Responsive layout with NO margins for flush bottom positioning
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(8, 8, 8, 0)  # No bottom margin for flush positioning
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
            # print("No target input set for focus_next_input")
            return False

        # Check if target input object still exists
        try:
            # Try to access a property to check if object is still valid
            _ = self.target_input.isVisible()
        except RuntimeError:
            # print("Target input has been deleted!")
            return False

        main_window = self.target_input.window()

        # Find all focus-enabled input widgets
        line_edits = main_window.findChildren(FocusLineEdit)
        spin_boxes = main_window.findChildren(FocusSpinBox)
        double_spin_boxes = main_window.findChildren(FocusDoubleSpinBox)

        # Combine all inputs and sort by their position (top to bottom, left to right)
        all_inputs = line_edits + spin_boxes + double_spin_boxes

        if not all_inputs:
            # print("No input widgets found for next focus")
            return False

        # Sort inputs by their y position (top to bottom) then x position (left to right)
        all_inputs.sort(key=lambda widget: (widget.y(), widget.x()))

        try:
            current_index = all_inputs.index(self.target_input)
        except ValueError:
            # print("Current input not found in inputs list")
            return False

        # If current input is last in list, no next input to move to
        if current_index == len(all_inputs) - 1:
            # print("Current input is the last input")
            return False

        next_index = current_index + 1
        next_input = all_inputs[next_index]
        # print(f"Moving focus from {type(self.target_input).__name__} to {type(next_input).__name__}")
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
        # Use positioning reference if available (for modal dialogs)
        if hasattr(self, 'positioning_reference') and self.positioning_reference:
            width = self.positioning_reference.width()
            height = self.positioning_reference.height()
        elif self.parent():
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

        # Use positioning reference if available (for modal dialogs)
        if hasattr(self, 'positioning_reference') and self.positioning_reference:
            parent_width = self.positioning_reference.width()
            parent_height = self.positioning_reference.height()
        elif self.parent():
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

        # Update layouts with no bottom margin for flush positioning
        self.layout.setContentsMargins(margins, margins, margins, 0)  # No bottom margin
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
                margin: 0px;
                padding: 0px;
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
                ['SYM', 'space', '⏎', '←', '↑', '↓', '→']
            ]
            if self.mode == 'shift':
                keys = [[k.upper() if k not in ['⇧', '⌫', 'SYM', 'space', '⏎'] else k for k in row] for row in keys]
        elif self.mode == 'symbols':
            keys = [
                ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')'],
                ['_', '+', '=', '-', '/', ':', ';', '"', "'"],
                ['ABC', '\\', '|', '<', '>', '[', ']', '{', '}', '⌫'],
                ['.', ',', '⏎', '←', '↑', '↓', '→']
            ]

        # Add remaining keys with special handling for space
        for row_offset, row in enumerate(keys, start=1):
            col_index = 0
            for key in row:
                button = QPushButton(key if key != 'space' else '⎵')  # Space symbol
                button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                button.clicked.connect(lambda _, k=key: self.key_pressed(k))
                self.key_buttons.append(button)

                # Special handling for space bar - make it wider and shift subsequent buttons
                if key == 'space':
                    self.grid_layout.addWidget(button, row_offset, col_index, 1, 3)  # Span 3 columns
                    col_index += 3
                else:
                    self.grid_layout.addWidget(button, row_offset, col_index)
                    col_index += 1

    def key_pressed(self, key):
        # print(f"DEBUG: Key pressed: {key}")
        # print(f"DEBUG: Target input: {self.target_input}")

        if not self.target_input:
            # print("DEBUG: No target input!")
            return

        # Check if target input object still exists
        try:
            # Try to access a property to check if object is still valid
            _ = self.target_input.isVisible()
        except RuntimeError:
            # print("DEBUG: Target input has been deleted!")
            return

        # print(f"DEBUG: Target input type: {type(self.target_input)}")
        # print(f"DEBUG: Target input has focus: {self.target_input.hasFocus()}")

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
            print("DEBUG: Inserting space")
            self.target_input.insert(' ')
        elif key == '←':  # Left Arrow
            self.move_cursor_left()
        elif key == '→':  # Right Arrow
            self.move_cursor_right()
        elif key == '↑':  # Up Arrow
            self.move_cursor_up()
        elif key == '↓':  # Down Arrow
            self.move_cursor_down()
        else:
            print(f"DEBUG: Inserting character: {key}")
            self.target_input.insert(key)
            if self.mode == 'shift':
                self.mode = 'letters'
                self.build_keyboard()
                self.update_responsive_sizing()  # Update after rebuilding

    def _get_line_edit(self):
        """Return a QLineEdit if the current target_input exposes one, else None."""
        from PyQt6.QtWidgets import QLineEdit
        if not self.target_input:
            return None
        if isinstance(self.target_input, QLineEdit):
            return self.target_input
        if hasattr(self.target_input, "lineEdit"):
            try:
                le = self.target_input.lineEdit()
                if isinstance(le, QLineEdit):
                    return le
            except RuntimeError:
                return None
        return None

    def _move_lineedit_cursor(self, delta: int) -> bool:
        """Move QLineEdit cursor by delta chars. Return True if handled."""
        le = self._get_line_edit()
        if not le:
            return False
        pos = le.cursorPosition()
        text_len = len(le.text())
        new_pos = max(0, min(text_len, pos + delta))
        le.setCursorPosition(new_pos)
        return True

    def move_cursor_left(self):
        """Move cursor left; supports QLineEdit and QText-like widgets."""
        if self._move_lineedit_cursor(-1):
            return
        try:
            cursor = self.target_input.textCursor()
        except Exception:
            return
        cursor.movePosition(cursor.Left)
        self.target_input.setTextCursor(cursor)

    def move_cursor_right(self):
        """Move cursor right; supports QLineEdit and QText-like widgets."""
        if self._move_lineedit_cursor(1):
            return
        try:
            cursor = self.target_input.textCursor()
        except Exception:
            return
        cursor.movePosition(cursor.Right)
        self.target_input.setTextCursor(cursor)

    def move_cursor_up(self):
        """Move cursor up (for QLineEdit: move to start)."""
        le = self._get_line_edit()
        if le:
            le.setCursorPosition(0)
            return
        try:
            cursor = self.target_input.textCursor()
        except Exception:
            return
        cursor.movePosition(cursor.Up)
        self.target_input.setTextCursor(cursor)

    def move_cursor_down(self):
        """Move cursor down (for QLineEdit: move to end)."""
        le = self._get_line_edit()
        if le:
            le.setCursorPosition(len(le.text()))
            return
        try:
            cursor = self.target_input.textCursor()
        except Exception:
            return
        cursor.movePosition(cursor.Down)
        self.target_input.setTextCursor(cursor)

    def hideKeyboard(self):
        try:
            if self.target_input:
                # Try to access a property to check if object is still valid
                _ = self.target_input.isVisible()
                self.target_input.clearFocus()
        except RuntimeError:
            pass  # Object already deleted
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
        # Check if the new target input is valid before setting it
        try:
            if target_input:
                # Try to access a property to check if object is still valid
                _ = target_input.isVisible()
                self.target_input = target_input
            else:
                # print("DEBUG: Invalid target input provided")
                self.target_input = None
        except RuntimeError:
            # print("DEBUG: RuntimeError with target input")
            self.target_input = None

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
        # Use positioning reference if available (for modal dialogs)
        if hasattr(self, 'positioning_reference') and self.positioning_reference:
            positioning_widget = self.positioning_reference
            parent_pos: QPoint = positioning_widget.mapToGlobal(QPoint(0, 0))
            pw = positioning_widget.width()
            ph = positioning_widget.height()
        elif self.parent():
            # Get parent's global position and size
            parent_pos: QPoint = self.parent().mapToGlobal(QPoint(0, 0))
            pw = self.parent().width()
            ph = self.parent().height()
        else:
            # Detect which screen the target input (or its window) is on
            target_window = None
            try:
                if self.target_input and hasattr(self.target_input, 'window'):
                    target_window = self.target_input.window()
                elif self.parent():
                    target_window = self.parent()
            except RuntimeError:
                # Target input widget has been deleted, fall back to parent
                target_window = self.parent() if self.parent() else None

            if target_window:
                screen = QApplication.screenAt(target_window.mapToGlobal(QPoint(0, 0)))
            else:
                screen = QApplication.primaryScreen()

            # Get screen geometry safely
            if screen:
                parent_geom = screen.geometry()
            else:
                parent_geom = QApplication.primaryScreen().geometry()

            parent_pos = QPoint(parent_geom.x(), parent_geom.y())
            pw = parent_geom.width()
            ph = parent_geom.height()

        kw, kh = self.width(), self.height()
        px, py = parent_pos.x(), parent_pos.y()

        # Get screen geometry to ensure we don't go off-screen
        screen_geom = QApplication.primaryScreen().geometry()
        screen_bottom = screen_geom.y() + screen_geom.height()  # Fix: actual bottom coordinate
        screen_top = screen_geom.y()

        # Calculate bottom position, but clamp to screen bounds
        parent_bottom = py + ph

        # For dialogs or small windows, ensure keyboard appears on screen
        if parent_bottom > screen_bottom:
            # If parent extends beyond screen, use screen bottom
            parent_bottom = screen_bottom

        # Always position keyboard at the very bottom of the screen for touch screen use
        keyboard_end_y = screen_bottom - kh

        # Ensure keyboard doesn't go above screen top (fallback for very small screens)
        if keyboard_end_y < screen_top:
            keyboard_end_y = screen_top + 10

        print(f"DEBUG: Screen geometry: {screen_geom}")
        print(f"DEBUG: Screen top: {screen_top}, Screen bottom: {screen_bottom}")
        print(f"DEBUG: Keyboard height: {kh}")
        print(f"DEBUG: Calculated keyboard_end_y: {keyboard_end_y}")
        print(f"DEBUG: This should position keyboard from Y={keyboard_end_y} to Y={keyboard_end_y + kh}")
        print(f"DEBUG: Expected keyboard bottom Y: {keyboard_end_y + kh}, Screen bottom Y: {screen_bottom}")

        if corner == "bottom-left":
            start = QPoint(px, parent_bottom)
            end = QPoint(px, keyboard_end_y)
        elif corner == "bottom-right":
            start = QPoint(px + pw, parent_bottom)
            end = QPoint(px + pw - kw, keyboard_end_y)
        elif corner == "top-left":
            start = QPoint(px, py - kh)
            end = QPoint(px, py)
        elif corner == "top-right":
            start = QPoint(px + pw, py - kh)
            end = QPoint(px + pw - kw, py)
        else:
            # default fallback bottom-left
            start = QPoint(px, parent_bottom)
            end = QPoint(px, keyboard_end_y)

        return start, end

    def slide_in(self, corner="bottom-left"):
        # print(f"DEBUG: slide_in called - is_sliding: {self.is_sliding}, isVisible: {self.isVisible()}")
        if self.is_sliding or self.isVisible():
            # print("DEBUG: Exiting slide_in - already sliding or visible")
            return

        # Check for login window first and apply special handling if needed
        if self._handle_login_window_display():
            return  # Special login handling applied, no need for normal slide animation

        # print("DEBUG: Starting slide_in")
        self.is_sliding = True

        # Update sizing before sliding in
        # print("DEBUG: Updating responsive sizing")
        self.update_responsive_sizing()
        # print(f"DEBUG: Keyboard size after update: {self.size()}")

        # print("DEBUG: Calculating slide positions")
        start_pos, end_pos = self._calculate_slide_positions(corner)
        # print(f"DEBUG: Start pos: {start_pos}, End pos: {end_pos}")

        # print("DEBUG: Moving to start position")
        self.move(start_pos)
        # print(f"DEBUG: Position after move: {self.pos()}")

        # print("DEBUG: Calling show()")
        self.show()
        # print(f"DEBUG: After show() - isVisible: {self.isVisible()}")
        # print(f"DEBUG: After show() - geometry: {self.geometry()}")

        # print("DEBUG: Raising and activating")
        self.raise_()
        self.activateWindow()

        # Force to front with multiple methods
        self.setWindowState(Qt.WindowState.WindowActive)

        # print("DEBUG: Starting animation")
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(300)
        self.anim.setStartValue(start_pos)
        self.anim.setEndValue(end_pos)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.finished.connect(lambda: setattr(self, 'is_sliding', False))
        self.anim.start()
        self.shown.emit()
        # print("DEBUG: Animation started")

    def _handle_login_window_display(self):
        """Special handling for LoginWindow z-order issues"""
        current_window = None
        try:
            if self.target_input and hasattr(self.target_input, 'window'):
                current_window = self.target_input.window()
        except RuntimeError:
            # Target input widget has been deleted
            current_window = None

        # Check if we're in a LoginWindow specifically (not other dialogs)
        if (current_window and
                current_window.__class__.__name__ == 'LoginWindow' and
                hasattr(current_window, 'login_tab')):  # Extra check to ensure it's really LoginWindow

            print("DEBUG: Detected LoginWindow - applying special z-order handling")

            # Update sizing before showing
            self.update_responsive_sizing()

            # Position the keyboard (use existing calculation)
            start_pos, end_pos = self._calculate_slide_positions("bottom-left")
            self.move(end_pos)  # Move directly to end position for login

            # Use stronger window flags for LoginWindow
            self.setWindowFlags(
                Qt.WindowType.Tool |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowDoesNotAcceptFocus |
                Qt.WindowType.X11BypassWindowManagerHint  # Bypass window manager
            )

            # Set LoginWindow as parent for proper z-order relationship
            self.setParent(current_window)
            self.show()
            self.raise_()
            self.activateWindow()

            # Multiple z-order fixes with different delays
            from PyQt6.QtCore import QTimer

            def fix_z_order_1():
                print("DEBUG: Z-order fix 1")
                current_window.raise_()
                current_window.activateWindow()
                self.raise_()
                self.activateWindow()
                self.show()  # Ensure still visible

            def fix_z_order_2():
                print("DEBUG: Z-order fix 2")
                self.raise_()
                self.activateWindow()
                self.show()  # Ensure still visible

            def fix_z_order_3():
                print("DEBUG: Z-order fix 3")
                self.raise_()
                self.show()  # Final ensure visible
                print(f"DEBUG: Final keyboard visible state: {self.isVisible()}")

            # Apply fixes at different intervals to ensure stability
            QTimer.singleShot(50, fix_z_order_1)
            QTimer.singleShot(150, fix_z_order_2)
            QTimer.singleShot(300, fix_z_order_3)
            return True
        else:
            # Reset keyboard to default state for non-LoginWindow dialogs
            self._reset_to_default_state()
        return False

    def _reset_to_default_state(self):
        """Reset keyboard to default window flags and parent for non-LoginWindow dialogs"""
        print("DEBUG: Resetting keyboard to default state for non-LoginWindow dialog")

        # Reset to default window flags
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )

        # Reset parent to None for independence
        self.setParent(None)

        # Ensure window modality is set correctly
        self.setWindowModality(Qt.WindowModality.NonModal)

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
        self.hidden.emit()

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
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QFont, QPainter, QColor


class SelectionActionBar(QWidget):
    """Android-style action bar for multi-selection mode"""

    # Signals
    exitRequested = pyqtSignal()
    showDetailsRequested = pyqtSignal()
    editItemRequested = pyqtSignal()
    deleteRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_count = 0
        self.setup_ui()

    def setup_ui(self):
        """Initialize the action bar UI"""
        # Set background color using palette for reliable display
        from PyQt6.QtGui import QPalette, QColor
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#905BA9"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.applyStyles()


        # Create layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 8, 16, 8)
        self.layout.setSpacing(12)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Back button (X) to exit selection mode
        self.back_btn = QPushButton("✕")
        self.back_btn.setToolTip("Exit selection mode")
        self.back_btn.setStyleSheet(self._get_button_style())
        self.back_btn.clicked.connect(self.exitRequested.emit)
        self.layout.addWidget(self.back_btn)

        # Selection counter label
        self.selection_counter = QLabel("0 selected")
        self.layout.addWidget(self.selection_counter)

        # Spacer to push action buttons to the right
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.layout.addItem(spacer)

        # Create containers for dynamic buttons with center alignment
        self.action_buttons_layout = QHBoxLayout()
        self.action_buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addLayout(self.action_buttons_layout)

    def applyStyles(self):
        self.setStyleSheet("""
                  SelectionActionBar {
                      background-color: #905BA9;
                      border: none;
                  }
                  QLabel {
                      color: white;
                      font-size: 18px;
                      font-weight: bold;
                      margin: 0 16px;
                      background-color: transparent;
                  }
              """)

    def _get_button_style(self):
        """Get consistent button styling"""
        return """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 24px;
                padding: 8px;
                margin: 2px;
                font-size: 22px;
                color: white;
                min-width: 48px;
                min-height: 48px;
                max-width: 48px;
                max-height: 48px;
                font-family: "Segoe UI Symbol", "Arial Unicode MS", sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """

    def update_selection_count(self, count):
        """Update the selection counter and action buttons"""
        self.selected_count = count
        text = f"{count} selected" if count != 1 else "1 selected"
        self.selection_counter.setText(text)
        self._update_action_buttons()

    def _update_action_buttons(self):
        """Update action buttons based on selection count"""
        # Clear existing buttons
        self._clear_action_buttons()

        if self.selected_count == 1:
            # Single selection: Show info, edit, delete
            info_btn = QPushButton("ℹ️")
            info_btn.setToolTip("Show details")
            info_btn.setStyleSheet(self._get_button_style())
            info_btn.clicked.connect(self.showDetailsRequested.emit)
            self.action_buttons_layout.addWidget(info_btn)

            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Edit item")
            edit_btn.setStyleSheet(self._get_button_style())
            edit_btn.clicked.connect(self.editItemRequested.emit)
            self.action_buttons_layout.addWidget(edit_btn)

            delete_btn = QPushButton("🗑")
            delete_btn.setToolTip("Delete item")
            delete_btn.setStyleSheet(self._get_button_style())
            delete_btn.clicked.connect(self.deleteRequested.emit)
            self.action_buttons_layout.addWidget(delete_btn)

        elif self.selected_count > 1:
            # Multiple selection: Only delete button (clean and simple)
            delete_btn = QPushButton("🗑")
            delete_btn.setToolTip("Delete selected items")
            delete_btn.setStyleSheet(self._get_button_style())
            delete_btn.clicked.connect(self.deleteRequested.emit)
            self.action_buttons_layout.addWidget(delete_btn)

    def _clear_action_buttons(self):
        """Remove all action buttons from the layout"""
        while self.action_buttons_layout.count():
            child = self.action_buttons_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def show_action_bar(self, parent_widget):
        """Show the action bar at the top of the parent widget"""
        self.setParent(parent_widget)
        self.parent_widget = parent_widget  # Store reference to parent

        # Install event filter to catch parent resize events
        parent_widget.installEventFilter(self)

        self.resize(parent_widget.width(), 72)
        self.move(0, 0)
        self.setWindowFlags(Qt.WindowType.Widget)
        self.raise_()
        self.show()

    def hide_action_bar(self):
        """Hide the action bar"""
        # Remove event filter when hiding
        if hasattr(self, 'parent_widget') and self.parent_widget:
            self.parent_widget.removeEventFilter(self)
        self.hide()

    def resize_to_parent(self, parent_width):
        """Resize the action bar to match parent width"""
        self.resize(parent_width, 72)

    def paintEvent(self, event):
        """Custom paint event to ensure background color is painted"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#905BA9"))
        super().paintEvent(event)

    def resizeEvent(self, event):
        """Handle resize events to maintain proper positioning"""
        super().resizeEvent(event)
        # Always stay at the top of the parent
        self.move(0, 0)

    def eventFilter(self, obj, event):
        """Filter events to catch parent widget resize events"""
        if obj == self.parent_widget and event.type() == QEvent.Type.Resize:
            # Parent widget was resized, update our width
            self.resize(self.parent_widget.width(), 72)
            return False  # Continue processing the event
        return super().eventFilter(obj, event)

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton

    class WTestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Selection Action Bar Test")
            self.setGeometry(100, 100, 800, 600)

            self.central_widget = QWidget()
            self.setCentralWidget(self.central_widget)
            self.layout = QVBoxLayout(self.central_widget)

            self.test_button = QPushButton("Select Items")
            self.test_button.clicked.connect(self.enter_selection_mode)
            self.layout.addWidget(self.test_button)

            self.action_bar = SelectionActionBar()
            self.action_bar.exitRequested.connect(self.exit_selection_mode)
            self.action_bar.showDetailsRequested.connect(lambda: print("Show details"))
            self.action_bar.editItemRequested.connect(lambda: print("Edit item"))
            self.action_bar.deleteRequested.connect(lambda: print("Delete items"))

        def enter_selection_mode(self):
            self.action_bar.update_selection_count(1)  # Simulate selecting one item
            self.action_bar.show_action_bar(self.central_widget)

        def exit_selection_mode(self):
            self.action_bar.hide_action_bar()

    app = QApplication(sys.argv)
    window = WTestWindow()
    window.show()
    sys.exit(app.exec())
from PyQt6.QtCore import QPropertyAnimation, QRect, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from deprecated.pl_gui.customWidgets.Drawer import Drawer

class FilterPanel(Drawer,QWidget):
    # Signals to communicate with parent
    filtersChanged = pyqtSignal(str, str, str)  # id_filter, area_filter, filename_filter
    filtersCleared = pyqtSignal()
    closeRequested = pyqtSignal()

    def __init__(self, parent=None, width=220):
        super().__init__(parent)
        self.panel_width = width
        self.is_visible = False
        self.animation = None

        self.setup_ui()
        self.setup_styles()
        self.connect_signals()

        # Initially hide the panel off-screen
        if parent:
            # Set initial geometry with parent's current height
            self.setGeometry(parent.width(), 0, self.panel_width, parent.height())
            # Make sure the panel spans the full height
            self.setFixedWidth(self.panel_width)
            self.setMinimumHeight(parent.height())
        self.hide()

    def setup_ui(self):
        """Setup the user interface"""
        self.setFixedWidth(self.panel_width)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 15, 12, 15)
        layout.setSpacing(8)

        # Title
        self.title_label = QLabel("Filters", self)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #905BA9; margin-bottom: 5px;")
        layout.addWidget(self.title_label)

        # Filter by ID
        self.id_label = QLabel("ID:", self)
        self.id_input = QLineEdit(self)
        self.id_input.setPlaceholderText("Enter ID...")
        layout.addWidget(self.id_label)
        layout.addWidget(self.id_input)

        # Filter by Area
        self.area_label = QLabel("Area:", self)
        self.area_input = QLineEdit(self)
        self.area_input.setPlaceholderText("Enter area...")
        layout.addWidget(self.area_label)
        layout.addWidget(self.area_input)

        # Filter by filename
        self.filename_label = QLabel("Filename:", self)
        self.filename_input = QLineEdit(self)
        self.filename_input.setPlaceholderText("Enter filename...")
        layout.addWidget(self.filename_label)
        layout.addWidget(self.filename_input)

        # Add some spacing
        layout.addSpacing(10)

        # Buttons in horizontal layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        # Clear filters button
        self.clear_btn = QPushButton("Clear", self)
        button_layout.addWidget(self.clear_btn)

        # Close button
        self.close_btn = QPushButton("Close", self)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        # Add stretch to push everything to the top
        layout.addStretch()

    def setup_styles(self):
        """Setup the styling for the panel"""
        self.setStyleSheet("""
            QWidget {
                background: #f8f8f8; 
                border-left: 2px solid #905BA9;
            }
            QLabel {
                color: #333;
                font-weight: bold;
                font-size: 11px;
                margin: 0px;
                padding: 0px;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #905BA9;
                border-radius: 3px;
                padding: 4px;
                font-size: 11px;
                min-height: 18px;
                max-height: 18px;
            }
            QPushButton {
                background-color: #905BA9;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
                min-height: 24px;
                max-height: 24px;
            }
            QPushButton:hover {
                background-color: #7a4791;
            }
        """)

    def connect_signals(self):
        """Connect internal signals"""
        self.id_input.textChanged.connect(self.on_filters_changed)
        self.area_input.textChanged.connect(self.on_filters_changed)
        self.filename_input.textChanged.connect(self.on_filters_changed)
        self.clear_btn.clicked.connect(self.clear_filters)
        self.close_btn.clicked.connect(self.close_panel)

    def on_filters_changed(self):
        """Emit signal when any filter changes"""
        id_filter = self.id_input.text().strip()
        area_filter = self.area_input.text().strip()
        filename_filter = self.filename_input.text().strip()
        self.filtersChanged.emit(id_filter, area_filter, filename_filter)

    def clear_filters(self):
        """Clear all filter inputs"""
        self.id_input.clear()
        self.area_input.clear()
        self.filename_input.clear()
        self.filtersCleared.emit()

    def close_panel(self):
        """Request to close the panel"""
        self.closeRequested.emit()

    def show_panel(self):
        """Show the panel with animation"""
        if not self.parent():
            return

        # Update height to match parent before showing
        parent_height = self.parent().height()
        self.setFixedHeight(parent_height)
        self.setGeometry(self.parent().width(), 0, self.panel_width, parent_height)

        self.show()
        self.animate_panel(show=True)

    def hide_panel(self):
        """Hide the panel with animation"""
        if not self.parent():
            return

        self.animate_panel(show=False)

    def animate_panel(self, show=True):
        """Animate the panel sliding in/out"""
        if not self.parent():
            return

        parent_width = self.parent().width()
        parent_height = self.parent().height()

        start_x = parent_width if show else parent_width - self.panel_width
        end_x = parent_width - self.panel_width if show else parent_width

        self.is_visible = show
        self.setGeometry(start_x, 0, self.panel_width, parent_height)

        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(QRect(start_x, 0, self.panel_width, parent_height))
        self.animation.setEndValue(QRect(end_x, 0, self.panel_width, parent_height))

        if not show:
            self.animation.finished.connect(self.hide)

        self.animation.start()

    def update_position(self):
        """Update panel position when parent is resized"""
        if not self.parent():
            return

        parent_width = self.parent().width()
        parent_height = self.parent().height()

        # Always update height to match parent
        self.setFixedHeight(parent_height)

        if self.is_visible:
            # Panel is visible, position it properly
            self.setGeometry(
                parent_width - self.panel_width,
                0,
                self.panel_width,
                parent_height
            )
        else:
            # Panel is hidden, keep it off-screen
            self.setGeometry(
                parent_width,
                0,
                self.panel_width,
                parent_height
            )

    def get_filter_values(self):
        """Get current filter values"""
        return {
            'id': self.id_input.text().strip(),
            'area': self.area_input.text().strip(),
            'filename': self.filename_input.text().strip()
        }

    def set_filter_values(self, id_filter='', area_filter='', filename_filter=''):
        """Set filter values programmatically"""
        self.id_input.setText(id_filter)
        self.area_input.setText(area_filter)
        self.filename_input.setText(filename_filter)
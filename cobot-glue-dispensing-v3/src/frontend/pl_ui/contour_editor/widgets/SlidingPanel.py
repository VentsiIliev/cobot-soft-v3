"""
Sliding panel widget that slides in and out from the right side.
Contains a floating toggle button to show/hide the panel.
"""
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFrame


class SlidingPanel(QWidget):
    """A panel that slides in from the right side with a floating toggle button"""

    def __init__(self, content_widget, parent=None):
        super().__init__(parent)
        self.content_widget = content_widget
        self.is_visible = True  # Start visible by default
        self.panel_width = 400  # Width of the sliding panel
        self.button_width = 35

        # Set initial width for the entire widget (panel + button)
        self.setMinimumWidth(self.panel_width + self.button_width)
        self.setMaximumWidth(self.panel_width + self.button_width)

        self.setup_ui()
        self.setup_animation()

    def setup_ui(self):
        """Setup the UI components"""
        # No layout manager - use absolute positioning
        self.setStyleSheet("background-color: transparent;")

        # Panel container (the part that slides)
        self.panel_container = QFrame(self)
        self.panel_container.setFixedWidth(self.panel_width)
        self.panel_container.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-left: 1px solid #cccccc;
            }
        """)

        # Panel layout
        panel_layout = QVBoxLayout(self.panel_container)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        # Add content widget to panel
        if self.content_widget:
            panel_layout.addWidget(self.content_widget)

        # Toggle button (floating on the left edge of the panel)
        self.toggle_button = QPushButton("◀", self)  # Left arrow when visible
        self.toggle_button.setFixedSize(35, 100)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #6750A4;
                color: white;
                border: none;
                border-radius: 5px 0px 0px 5px;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7860B4;
            }
            QPushButton:pressed {
                background-color: #5640A4;
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_panel)
        self.toggle_button.show()
        self.toggle_button.raise_()  # Ensure button is on top

    def setup_animation(self):
        """Setup slide animation"""
        self.animation = QPropertyAnimation(self.panel_container, b"pos")
        self.animation.setDuration(300)  # 300ms animation
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def toggle_panel(self):
        """Toggle the panel visibility with slide animation"""
        if self.is_visible:
            self.hide_panel()
        else:
            self.show_panel()

    def show_panel(self):
        """Slide panel in from the right"""
        if self.is_visible:
            return

        self.is_visible = True
        self.toggle_button.setText("◀")  # Change to left arrow

        # Expand widget to full size (panel + button)
        self.setMinimumWidth(self.panel_width + self.button_width)
        self.setMaximumWidth(self.panel_width + self.button_width)

        # Move toggle button immediately
        button_x = 0
        button_y = (self.height() - self.toggle_button.height()) // 2
        self.toggle_button.move(button_x, button_y)

        # Animate panel from off-screen to visible
        start_pos = self.panel_container.pos()  # Current position (off-screen)
        end_pos = QPoint(self.button_width, 0)  # Visible position

        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        self.animation.start()

    def hide_panel(self):
        """Slide panel out to the right"""
        if not self.is_visible:
            return

        self.is_visible = False
        self.toggle_button.setText("▶")  # Change to right arrow

        # Shrink widget to button width only
        self.setMinimumWidth(self.button_width)
        self.setMaximumWidth(self.button_width)

        # Move toggle button to the edge
        button_x = 0  # Now at left edge since widget is button-width only
        button_y = (self.height() - self.toggle_button.height()) // 2
        self.toggle_button.move(button_x, button_y)

        # Animate panel sliding out
        start_pos = self.panel_container.pos()
        end_pos = QPoint(self.button_width, 0)  # Move panel off-screen (just past button)

        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        self.animation.start()

    def resizeEvent(self, event):
        """Handle resize events to reposition components"""
        super().resizeEvent(event)

        # Ensure panel container height matches parent
        self.panel_container.setFixedHeight(self.height())

        # Position components based on visibility
        if self.is_visible:
            # Panel visible - positioned after the button
            self.panel_container.move(self.button_width, 0)
            button_x = 0
        else:
            # Panel hidden - positioned off-screen (to the right of button)
            self.panel_container.move(self.button_width, 0)
            button_x = 0

        button_y = (self.height() - self.toggle_button.height()) // 2
        self.toggle_button.move(button_x, button_y)

    def set_visible(self, visible):
        """Programmatically set panel visibility without animation"""
        self.is_visible = visible
        if visible:
            self.panel_container.move(self.width() - self.panel_width, 0)
            self.toggle_button.setText("◀")
        else:
            self.panel_container.move(self.width(), 0)
            self.toggle_button.setText("▶")
        self.update()

    def replace_content_widget(self, new_content_widget):
        """Replace the inner widget of the sliding panel dynamically."""
        import traceback
        print("replace_content_widget called: new=%s" %
              (type(new_content_widget).__name__ if new_content_widget else None))

        if not hasattr(self.panel_container, "layout") or self.panel_container.layout() is None:
            print("Panel container has no layout; creating QVBoxLayout")
            panel_layout = QVBoxLayout(self.panel_container)
            panel_layout.setContentsMargins(0, 0, 0, 0)
            panel_layout.setSpacing(0)
        else:
            panel_layout = self.panel_container.layout()
            print("Using existing panel layout:", panel_layout)

        # Remove the old widget
        if self.content_widget:
            print("Removing old content widget:", type(self.content_widget).__name__)
            try:
                panel_layout.removeWidget(self.content_widget)
            except Exception:
                print("Error removing old widget from layout")
                traceback.print_exc()
            # Detach the widget from the layout/parent but do NOT delete it.
            # The calling code (the MainApplicationFrame) keeps references to commonly reused widgets
            # like PointManagerWidget and expects them to remain valid after being swapped out.
            # Calling deleteLater() here caused the referenced widget to be destroyed, leading to
            # "wrapped C/C++ object of type QListWidget has been deleted" when the app later
            # tried to access it. To avoid that, only remove the widget from the layout and
            # unset its parent so it can be re-added later. Hide it so it's not visible.
            try:
                self.content_widget.hide()
                self.content_widget.setParent(None)
            except Exception:
                print("Error detaching old content widget")
                traceback.print_exc()
        else:
            print("No existing content widget to remove")

        # Add the new one
        self.content_widget = new_content_widget
        if self.content_widget:
            panel_layout.addWidget(self.content_widget)
            self.content_widget.show()  # Make sure it's visible again
            print("Added new content widget:", type(self.content_widget).__name__)
        else:
            print("New content widget is None; nothing added")

        # Force Qt to relayout and repaint
        print("Updating geometry and repainting panel_container")
        self.panel_container.updateGeometry()
        self.panel_container.adjustSize()
        self.panel_container.repaint()
        print("replace_content_widget completed")

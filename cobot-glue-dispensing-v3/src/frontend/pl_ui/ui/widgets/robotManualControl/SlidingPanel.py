from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtWidgets import QFrame


class SlidingPanel(QFrame):
    """Sliding panel that can slide in/out from the right"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(400)  # Fixed width for the sliding panel
        self.is_visible = False

        # Set initial position (hidden to the right)
        self.hide_position = 400  # Width of the panel
        self.show_position = 0

        # Animation
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(250)  # Slightly faster, more professional feel
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuart)  # Smoother easing

        self.setStyleSheet("""
            SlidingPanel {
                background-color: #FFFFFF;
                border-left: 1px solid #E5E5E5;
                border-radius: 0px;
                padding: 0px;
            }
        """)

    def slideIn(self):
        """Slide the panel in from the right"""
        if not self.is_visible:
            self.show()
            self.is_visible = True

            # Get parent size to calculate correct positions
            parent_rect = self.parent().rect()
            start_x = parent_rect.width()
            end_x = parent_rect.width() - self.width()

            # Set current position to start from right edge
            current_y = self.pos().y()
            self.move(start_x, current_y)

            # Animate to final position
            self.animation.setStartValue(QPoint(start_x, current_y))
            self.animation.setEndValue(QPoint(end_x, current_y))
            self.animation.start()

    def slideOut(self):
        """Slide the panel out to the right"""
        if self.is_visible:
            parent_rect = self.parent().rect()
            start_pos = self.pos()
            end_x = parent_rect.width()

            self.animation.setStartValue(start_pos)
            self.animation.setEndValue(QPoint(end_x, start_pos.y()))

            # Disconnect any previous connections to avoid multiple calls
            self.animation.finished.disconnect()
            self.animation.finished.connect(self._onSlideOutFinished)
            self.animation.start()
            self.is_visible = False

    def _onSlideOutFinished(self):
        """Handle slide out animation completion"""
        self.hide()
        # Disconnect to prevent memory leaks
        self.animation.finished.disconnect()

    def toggle(self):
        """Toggle the panel visibility"""
        if self.is_visible:
            self.slideOut()
        else:
            self.slideIn()

    def setContent(self, widget):
        """Set the content widget for the panel"""
        # If there's existing content, remove it
        if self.layout() is not None:
            # Clear existing layout
            while self.layout().count():
                child = self.layout().takeAt(0)
                if child.widget():
                    child.widget().setParent(None)

        # Create layout if it doesn't exist
        if self.layout() is None:
            from PyQt6.QtWidgets import QVBoxLayout
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            self.setLayout(layout)

        # Add the widget
        self.layout().addWidget(widget)

    def resizeEvent(self, event):
        """Handle resize events to maintain proper positioning"""
        super().resizeEvent(event)
        if self.parent() and self.is_visible:
            # Adjust position when parent is resized
            parent_rect = self.parent().rect()
            correct_x = parent_rect.width() - self.width()
            if self.pos().x() != correct_x:
                self.move(correct_x, self.pos().y())

    def isAnimating(self):
        """Check if the panel is currently animating"""
        return self.animation.state() == QPropertyAnimation.State.Running
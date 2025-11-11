from PyQt6.QtCore import QObject


class BaseMode(QObject):
    """Abstract base class for editor modes."""

    name = "base"

    def enter(self, editor):
        """Called when the mode is activated."""
        pass

    def exit(self, editor):
        """Called when the mode is deactivated."""
        pass

    def mousePress(self, editor, event): pass
    def mouseMove(self, editor, event): pass
    def mouseRelease(self, editor, event): pass
    def wheel(self, editor, event): pass
    def keyPress(self, editor, event): pass

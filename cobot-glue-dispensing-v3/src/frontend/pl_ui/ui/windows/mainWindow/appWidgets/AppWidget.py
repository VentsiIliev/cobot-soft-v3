from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSizePolicy


class AppWidget(QWidget):
    """Base widget for individual applications"""

    app_closed = pyqtSignal()  # Signal emitted when app wants to close

    def __init__(self, app_name, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.setup_ui()

    def setup_ui(self):
        """Setup the basic app UI with a back button"""
        layout = QVBoxLayout(self)
        # App content area
        content = QLabel(
            f"This is the {self.app_name} application.\n\nClick the Back button or press ESC to return to the main menu.")
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # content.setStyleSheet("""
        #     QLabel {
        #         background-color: white;
        #         border: 2px solid #e2e8f0;
        #         border-radius: 10px;
        #         padding: 40px;
        #         font-size: 16px;
        #         color: #4a5568;
        #     }
        # """)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout.addWidget(content)

    def close_app(self):
        """Close this app and return to main view"""
        self.app_closed.emit()

    def clean_up(self):
        pass

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = AppWidget("TestApp")
    widget.show()
    sys.exit(app.exec())
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtGui import QFont

class EmptyPlaceholder(QWidget):
    """Empty placeholder widget to maintain grid structure"""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(120)
        self.setMaximumWidth(500)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("""
            QWidget {
                border: 1px dashed #ccc;
                border-radius: 10px;
                background-color: transparent;
            }
        """)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
            self.setStyleSheet("""
                QWidget {
                    border: 2px dashed #0078d7;
                    border-radius: 10px;
                    background-color: #f0f8ff;
                }
            """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QWidget {
                border: 1px dashed #ccc;
                border-radius: 10px;
                background-color: transparent;
            }
        """)

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # Don't handle the drop here - let the parent CardContainer handle it
        # But we need to reset our styling first
        self.setStyleSheet("""
            QWidget {
                border: 1px dashed #ccc;
                border-radius: 10px;
                background-color: transparent;
            }
        """)
        # Don't call event.ignore() - let it propagate to parent
        super().dropEvent(event)
import sys
import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtWidgets import QApplication, QTabWidget, QWidget, QVBoxLayout, QLabel, QSizePolicy

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
BACKGROUND = os.path.join(RESOURCE_DIR, "pl_ui_icons", "Background_&_Logo.png")


class BackgroundTabPage(QWidget):
    def __init__(self):
        super().__init__()
        self.background = QPixmap(BACKGROUND)
        if self.background.isNull():
            print("Error: Tab background image not loaded correctly!")

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background.isNull():
            painter.drawPixmap(self.rect(), self.background)
        super().paintEvent(event)




    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background.isNull():
            painter.drawPixmap(self.rect(), self.background)
        super().paintEvent(event)


class CustomTabWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("QTabBar::tab { height: 40px; width: 120px; }")


from PyQt6.QtCore import Qt, QMimeData, QTimer, pyqtSignal
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout, QHBoxLayout, QLabel, QWidget


class DashboardCard(QFrame):
    long_press_detected = pyqtSignal(int)  # Signal emitted with card index on long press

    def __init__(self, title: str, content_widgets: list, remove_callback=None, container=None, card_index=None):
        super().__init__()
        self.setObjectName(title)
        self.container = container
        self.remove_callback = remove_callback
        self.card_index = card_index

        self.is_minimized = False
        self.content_widgets = content_widgets
        self.original_min_height = 80

        # Long press detection
        self.long_press_timer = QTimer()
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self._on_long_press)
        self.long_press_duration = 1000  # 1 second

        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                padding: 10px;
            }
        """)
        # self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setMaximumWidth(500)
        self.setMinimumHeight(self.original_min_height)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # --- Title bar layout ---
        self.top_layout = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setMaximumHeight(40)
        self.title_label.setStyleSheet("font-weight: bold;")

        self.top_layout.addWidget(self.title_label)
        self.top_layout.addStretch()

        self.layout.addLayout(self.top_layout)

        # --- Add content widgets without extra frames ---
        for w in self.content_widgets:
            # Create a transparent container to prevent automatic frame wrapping
            container_widget = QWidget()
            container_widget.setStyleSheet("QWidget { border: none; background: transparent; }")
            container_layout = QVBoxLayout(container_widget)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            container_layout.addWidget(w)
            self.layout.addWidget(container_widget)

    def hideLabel(self) -> None:
        self.title_label.setVisible(False)

    def on_close(self) -> None:
        if self.remove_callback:
            for widget in self.content_widgets:
                widget.close()

            self.remove_callback(self)

    def set_selected(self, selected: bool) -> None:
        if selected:
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #0078d7;
                    border-radius: 10px;
                    background-color: #d0e7ff;
                    padding: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #ccc;
                    border-radius: 10px;
                    background-color: #f9f9f9;
                    padding: 10px;
                }
            """)

    def mouseDoubleClickEvent(self, event) -> None:
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.long_press_timer.start(self.long_press_duration)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self.long_press_timer.stop()
        super().mouseReleaseEvent(event)

    def _on_long_press(self) -> None:
        """Called when long press is detected"""
        if self.card_index is not None:
            self.long_press_detected.emit(self.card_index)



    # def mousePressEvent(self, event) -> None:
    #     if not self.dragEnabled:
    #         # Dragging disabled — ignore drag start
    #         return super().mousePressEvent(event)
    #
    #     if event.button() == Qt.MouseButton.LeftButton:
    #         drag = QDrag(self)
    #         mime_data = QMimeData()
    #         mime_data.setText(self.objectName())
    #         drag.setMimeData(mime_data)
    #
    #         pixmap = self.grab()
    #         drag.setPixmap(pixmap)
    #         drag.setHotSpot(event.position().toPoint())
    #
    #         drag.exec(Qt.DropAction.MoveAction)

    # def dragEnterEvent(self, event) -> None:
    #     event.ignore()
    #
    # def dragMoveEvent(self, event) -> None:
    #     event.ignore()
    #
    # def dropEvent(self, event) -> None:
    #     event.ignore()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QComboBox
    import sys

    app = QApplication(sys.argv)

    # Test with combo box and label
    combo = QComboBox()
    combo.addItems(["Type A", "Type B", "Type C"])

    label = QLabel("Test Content")

    card = DashboardCard("Test Card", [combo, label])
    card.show()

    sys.exit(app.exec())

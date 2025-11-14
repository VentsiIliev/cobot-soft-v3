from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect, QFrame, QWidget, QApplication
)
from frontend.pl_ui.ui.widgets.MaterialButton import MaterialButton
from frontend.pl_ui.utils.styles.globalStyles import FONT

from enum import Enum

class DialogType(Enum):
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"
    ERROR = "error"
    FEEDBACK = "feedback"

class CustomFeedbackDialog(QDialog):
    """Unified dialog for warnings, info, success, errors, and feedback."""

    STYLE_MAP = {
        DialogType.WARNING: {
            "icon": "⚠",
            "icon_bg": "#fef2f2",
            "icon_color": "#dc2626",
            "border": "#fecaca",
        },
        DialogType.INFO: {
            "icon": "ℹ",
            "icon_bg": "#eff6ff",
            "icon_color": "#2563eb",
            "border": "#bfdbfe",
        },
        DialogType.SUCCESS: {
            "icon": "✔",
            "icon_bg": "#f0fdf4",
            "icon_color": "#16a34a",
            "border": "#bbf7d0",
        },
        DialogType.ERROR: {
            "icon": "✖",
            "icon_bg": "#fef2f2",
            "icon_color": "#dc2626",
            "border": "#fecaca",
        },
        DialogType.FEEDBACK: {
            "icon": "💬",
            "icon_bg": "#fdf4ff",
            "icon_color": "#9333ea",
            "border": "#e9d5ff",
        },
    }

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        title: str = "Message",
        message: str = "",
        info_text: str = "",
        dialog_type: DialogType = DialogType.INFO
,  # one of: warning, info, success, error, feedback
        ok_text: str = "OK",
        cancel_text: Optional[str] = None,
    ) -> None:
        super().__init__(parent)
        self.result_value: Optional[str] = None
        self.dialog_type = dialog_type
        self.ok_text = ok_text
        self.cancel_text = cancel_text
        self.setup_dialog(title, message, info_text)

    def setup_dialog(self, title: str, message: str, info_text: str) -> None:
        """Setup the dialog layout and styling"""
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(420, 300)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Container ---
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 25))
        container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(24, 20, 24, 20)
        container_layout.setSpacing(16)

        # --- Header ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        style = self.STYLE_MAP.get(self.dialog_type, self.STYLE_MAP[self.dialog_type])

        icon_label = QLabel(style["icon"])
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                color: {style["icon_color"]};
                background-color: {style["icon_bg"]};
                border: 1px solid {style["border"]};
                border-radius: 20px;
                padding: 8px;
                min-width: 20px;
                max-width: 20px;
                min-height: 20px;
                max-height: 20px;
            }}
        """)
        header_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_font = QFont(FONT, 17)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1e293b; background: transparent; border: none;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        container_layout.addLayout(header_layout)

        # --- Message ---
        message_label = QLabel(message)
        message_label.setFont(QFont(FONT, 13))
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                color: #475569;
                background: transparent;
                border: none;
                line-height: 1.5;
                padding-left: 44px;
            }
        """)
        container_layout.addWidget(message_label)

        if info_text:
            info_label = QLabel(info_text)
            info_label.setFont(QFont(FONT, 12))
            info_label.setStyleSheet("""
                QLabel {
                    color: #64748b;
                    background: transparent;
                    border: none;
                    padding-left: 44px;
                    margin-top: 4px;
                }
            """)
            info_label.setWordWrap(True)
            container_layout.addWidget(info_label)

        container_layout.addStretch()

        # --- Separator ---
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #f1f5f9; border: none;")
        container_layout.addWidget(line)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.setContentsMargins(0, 16, 0, 0)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        if self.cancel_text:
            self.cancel_button = MaterialButton(self.cancel_text)
            self.cancel_button.setFixedSize(100, 36)
            self.cancel_button.clicked.connect(self.reject_dialog)
            button_layout.addWidget(self.cancel_button)

        ok_button = MaterialButton(self.ok_text)
        ok_button.setFixedSize(100, 36)
        ok_button.clicked.connect(self.accept_dialog)
        button_layout.addWidget(ok_button)

        container_layout.addLayout(button_layout)

        main_layout.addWidget(container)
        self.setLayout(main_layout)

        # Center on parent
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

    # --- Behavior ---
    def accept_dialog(self):
        self.result_value = "OK"
        self.accept()

    def reject_dialog(self):
        self.result_value = "Cancel"
        self.reject()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.accept_dialog()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject_dialog()
        else:
            super().keyPressEvent(event)


# ----------------------------
# TEST SECTION
# ----------------------------
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    examples = [
        (DialogType.WARNING, "Delete Workpiece", "Are you sure you want to delete this workpiece?", "This action cannot be undone."),
        (DialogType.INFO, "Information", "Your changes have been saved successfully.", ""),
        (DialogType.SUCCESS, "Upload Complete", "The file was uploaded successfully.", ""),
        (DialogType.ERROR, "Connection Failed", "Unable to reach the server.", "Check your internet connection and try again."),
        (DialogType.FEEDBACK, "Feedback", "Thanks for your submission!", "We’ll review your input shortly."),
    ]

    for dialog_type, title, msg, info in examples:
        dialog = CustomFeedbackDialog(
            title=title,
            message=msg,
            info_text=info,
            dialog_type=dialog_type,
            ok_text="OK",
            cancel_text="Cancel" if dialog_type == DialogType.WARNING else None,
        )
        result = dialog.exec()
        print(f"[{dialog_type}] Result:", "Accepted" if result == QDialog.DialogCode.Accepted else "Rejected")

    sys.exit(app.exec())
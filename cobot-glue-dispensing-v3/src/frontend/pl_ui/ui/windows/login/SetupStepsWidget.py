from typing import Any, Callable, Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget

from src.frontend.pl_ui.localization import TranslationKeys, TranslatableWidget
from src.frontend.pl_ui.utils.IconLoader import MACHINE_BUTTONS_IMAGE
from src.frontend.pl_ui.ui.widgets.MaterialButton import MaterialButton
from src.frontend.pl_ui.utils.styles.globalStyles import FONT
class SetupStepsWidget(TranslatableWidget):
    """Initial setup steps widget."""

    def __init__(
        self,
        controller: Any,  # could be narrowed with a Protocol if needed
        parent=None
    ) -> None:
        super().__init__(parent, auto_retranslate=False)
        self.controller: Any = controller

        # Fonts
        self.font: QFont = QFont(FONT, 16, QFont.Weight.Bold)
        self.font_small: QFont = QFont(FONT, 14)

        # Widgets (assigned in setup_ui)
        self.image_label: Optional[QLabel] = None
        self.instructions: Optional[QLabel] = None
        self.confirm_blue_button: Optional[MaterialButton] = None

        self.setStyleSheet("background-color: white;")
        self.setup_ui()
        
        # Initialize translations after UI is created
        self.init_translations()

    def setup_ui(self) -> None:
        """Initialize the UI layout and widgets."""
        outer_layout: QVBoxLayout = QVBoxLayout()
        outer_layout.setContentsMargins(20, 20, 20, 20)

        # Top layout with language selector
        top_layout: QHBoxLayout = QHBoxLayout()
        top_layout.addStretch()
        outer_layout.addLayout(top_layout)

        # Spacer to center vertically
        outer_layout.addStretch()

        # Center content - image
        self.image_label = QLabel()
        self.image_label.setPixmap(
            QPixmap(MACHINE_BUTTONS_IMAGE).scaled(
                400,
                400,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Text label under the image (text set in retranslate())
        self.instructions = QLabel()
        self.instructions.setFont(self.font_small)
        self.instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(self.instructions, alignment=Qt.AlignmentFlag.AlignCenter)

        # Spacer below
        outer_layout.addStretch()

        # Bottom buttons layout
        bottom_buttons_layout: QHBoxLayout = QHBoxLayout()
        bottom_buttons_layout.setContentsMargins(0, 0, 0, 20)

        # Next button (text set in retranslate())
        # self.confirm_blue_button = QPushButton()
        self.confirm_blue_button = MaterialButton(
            self.tr(TranslationKeys.Navigation.NEXT)
        )
        self.confirm_blue_button.setFixedSize(200, 60)
        self.confirm_blue_button.clicked.connect(self.user_confirmed_blue_button)

        bottom_buttons_layout.addWidget(
            self.confirm_blue_button, alignment=Qt.AlignmentFlag.AlignRight
        )

        outer_layout.addLayout(bottom_buttons_layout)
        self.setLayout(outer_layout)

    def user_confirmed_blue_button(self) -> None:
        """Handle confirmation of blue button press."""
        from src.frontend.pl_ui.ui.windows.login.LoginWindow import LoginWindow

        parent: Optional[QWidget] = self.parentWidget()
        while parent and not isinstance(parent, LoginWindow):
            parent = parent.parentWidget()

        if parent and hasattr(parent, "right_stack") and hasattr(parent, "tabs_widget"):
            parent.right_stack.setCurrentWidget(parent.tabs_widget)

    def check_physical_button(self) -> None:
        """Check for physical button press (polling every 500ms)."""
        if self.controller.is_blue_button_pressed():
            if self.instructions:
                self.instructions.setText(self.tr(TranslationKeys.Setup.SETUP_FIRST_STEP))
            if hasattr(self, "home_button") and self.home_button:  # if defined elsewhere
                self.home_button.setVisible(True)
        else:
            QTimer.singleShot(500, self.check_physical_button)

    def retranslate(self) -> None:
        """Update all text labels for language changes - called automatically"""
        if self.instructions:
            self.instructions.setText(self.tr(TranslationKeys.Setup.SETUP_FIRST_STEP))
        if self.confirm_blue_button:
            self.confirm_blue_button.setText(self.tr(TranslationKeys.Navigation.NEXT))

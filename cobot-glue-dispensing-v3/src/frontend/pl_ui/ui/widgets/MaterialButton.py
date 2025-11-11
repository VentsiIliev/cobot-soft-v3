from PyQt6.QtWidgets import (QApplication, QWizard, QWizardPage, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QCheckBox, QRadioButton,
                             QButtonGroup, QTextEdit, QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QColor
import sys


# MaterialButton class
class MaterialButton(QPushButton):
    def __init__(self, text, color="#6750A4", font_size=12):
        super().__init__(text)
        self.color = color
        self.font_size = font_size
        self.setMinimumHeight(40)
        self.setMaximumHeight(100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_style()

    def apply_style(self):
        lighter = QColor(self.color).lighter(110).name()
        darker = QColor(self.color).darker(110).name()
        self.setStyleSheet(f"""
            QPushButton {{
                background: {self.color};
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                padding: 4px 12px;
                font-size: {self.font_size}px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {lighter}; }}
            QPushButton:pressed {{ background: {darker}; }}
            QPushButton:disabled {{
                background: #E8DEF8;
                color: #79747E;
            }}
        """)


class WizardStep(QWizardPage):
    """Base class for wizard steps with image and text support"""

    def __init__(self, title, subtitle, description, image_path=None):
        super().__init__()
        self.setTitle(title)
        self.setSubTitle(subtitle)

        layout = QVBoxLayout()

        # Image placeholder
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(200)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #e0e0e0;
                border: 2px dashed #999;
                border-radius: 8px;
            }
        """)

        if image_path:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(400, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("📷 Image Placeholder")
            font = QFont()
            font.setPointSize(14)
            self.image_label.setFont(font)

        layout.addWidget(self.image_label)

        # Description text
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("QLabel { margin: 15px 0; line-height: 1.5; }")
        layout.addWidget(description_label)

        # Content area for custom widgets
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)

        layout.addStretch()
        self.setLayout(layout)


class WelcomeStep(WizardStep):
    """Welcome page - Step 1"""

    def __init__(self):
        super().__init__(
            title="Welcome",
            subtitle="Welcome to the Setup Wizard",
            description="This wizard will guide you through the setup process. Click Next to continue.",
            image_path=None  # Replace with actual image path: "images/welcome.png"
        )


class UserInfoStep(WizardStep):
    """User information page - Step 2"""

    def __init__(self):
        super().__init__(
            title="User Information",
            subtitle="Please provide your information",
            description="Enter your details below to personalize your experience.",
            image_path=None  # Replace with: "images/user_info.png"
        )

        # Add custom fields
        name_label = QLabel("Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name")
        self.registerField("name*", self.name_input)  # Required field

        email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.registerField("email*", self.email_input)

        self.content_layout.addWidget(name_label)
        self.content_layout.addWidget(self.name_input)
        self.content_layout.addWidget(email_label)
        self.content_layout.addWidget(self.email_input)


class PreferencesStep(WizardStep):
    """Preferences page - Step 3"""

    def __init__(self):
        super().__init__(
            title="Preferences",
            subtitle="Configure your preferences",
            description="Choose your preferred settings.",
            image_path=None  # Replace with: "images/preferences.png"
        )

        # Theme selection
        theme_label = QLabel("Select Theme:")
        theme_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.content_layout.addWidget(theme_label)

        self.theme_group = QButtonGroup(self)

        self.light_radio = QRadioButton("Light Theme")
        self.dark_radio = QRadioButton("Dark Theme")
        self.light_radio.setChecked(True)

        self.theme_group.addButton(self.light_radio, 1)
        self.theme_group.addButton(self.dark_radio, 2)

        self.content_layout.addWidget(self.light_radio)
        self.content_layout.addWidget(self.dark_radio)

        # Additional options
        options_label = QLabel("Additional Options:")
        options_label.setStyleSheet("font-weight: bold; margin-top: 15px;")
        self.content_layout.addWidget(options_label)

        self.notifications_check = QCheckBox("Enable notifications")
        self.notifications_check.setChecked(True)
        self.auto_update_check = QCheckBox("Enable automatic updates")

        self.content_layout.addWidget(self.notifications_check)
        self.content_layout.addWidget(self.auto_update_check)


class SummaryStep(WizardStep):
    """Summary page - Step 4"""

    def __init__(self):
        super().__init__(
            title="Summary",
            subtitle="Review your settings",
            description="Please review your settings before completing the setup.",
            image_path=None  # Replace with: "images/summary.png"
        )

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        self.content_layout.addWidget(self.summary_text)

    def initializePage(self):
        """Update summary when page is shown"""
        name = self.field("name")
        email = self.field("email")

        summary = f"""
<b>Name:</b> {name}<br>
<b>Email:</b> {email}<br>
<b>Theme:</b> {"Light" if self.wizard().page(2).light_radio.isChecked() else "Dark"}<br>
<b>Notifications:</b> {"Enabled" if self.wizard().page(2).notifications_check.isChecked() else "Disabled"}<br>
<b>Auto-updates:</b> {"Enabled" if self.wizard().page(2).auto_update_check.isChecked() else "Disabled"}
        """
        self.summary_text.setHtml(summary)


class SetupWizard(QWizard):
    """Main wizard class"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Setup Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(600, 500)

        # Add steps here - Easy to add/remove!
        self.addPage(WelcomeStep())  # Step 1
        self.addPage(UserInfoStep())  # Step 2
        self.addPage(PreferencesStep())  # Step 3
        self.addPage(SummaryStep())  # Step 4

        # To add a new step, simply create a new class inheriting from WizardStep
        # and add it here with: self.addPage(YourNewStep())

        # To remove a step, just comment out or delete the corresponding addPage() line

        self.button(QWizard.WizardButton.FinishButton).clicked.connect(self.on_finish)

        # Customize button appearance
        self.customize_buttons()

    def on_finish(self):
        """Handle wizard completion"""
        print("Setup completed!")
        print(f"Name: {self.field('name')}")
        print(f"Email: {self.field('email')}")

    def customize_buttons(self):
        """Customize the appearance of wizard buttons using MaterialButton styling"""

        # Get references to the buttons
        back_button = self.button(QWizard.WizardButton.BackButton)
        next_button = self.button(QWizard.WizardButton.NextButton)
        cancel_button = self.button(QWizard.WizardButton.CancelButton)
        finish_button = self.button(QWizard.WizardButton.FinishButton)

        # Apply MaterialButton styling to each button
        self.apply_material_style(back_button, color="#2196F3")  # Blue for Back
        self.apply_material_style(next_button, color="#6750A4")  # Purple for Next
        self.apply_material_style(finish_button, color="#4CAF50")  # Green for Finish
        self.apply_material_style(cancel_button, color="#f44336")  # Red for Cancel

        # Optional: Change button text
        # back_button.setText("← Previous")
        # next_button.setText("Continue →")
        # cancel_button.setText("Exit")
        # finish_button.setText("Complete Setup")

    def apply_material_style(self, button, color="#6750A4", font_size=12):
        """Apply MaterialButton style to a wizard button"""
        button.setMinimumHeight(40)
        button.setCursor(Qt.CursorShape.PointingHandCursor)

        lighter = QColor(color).lighter(110).name()
        darker = QColor(color).darker(110).name()

        button.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                padding: 8px 20px;
                font-size: {font_size}px;
                font-weight: 500;
                min-width: 80px;
            }}
            QPushButton:hover {{ background: {lighter}; }}
            QPushButton:pressed {{ background: {darker}; }}
            QPushButton:disabled {{
                background: #E8DEF8;
                color: #79747E;
            }}
        """)


def main():
    app = QApplication(sys.argv)
    wizard = SetupWizard()
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
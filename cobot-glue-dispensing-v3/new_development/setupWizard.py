from PyQt6.QtWidgets import (QApplication, QWizard, QWizardPage, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QCheckBox, QRadioButton,
                             QButtonGroup, QTextEdit, QPushButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QColor, QIcon
import sys
from pl_ui.ui.widgets.MaterialButton import MaterialButton


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
        description_label.setStyleSheet("QLabel { margin: 15px 0; line-height: 1.5; font-size: 16px; }")
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
            title="Glue Change Guide",
            subtitle="Welcome to the Glue Change Wizard",
            description="This wizard will guide you through the process of changing the glue container. Click Next to continue.",
            image_path=None  # Replace with actual image path: "images/welcome.png"
        )


class OpenDrawerStep(WizardStep):
    """Open drawer - Step 2"""

    def __init__(self):
        super().__init__(
            title="Step 1: Open Drawer",
            subtitle="Open the glue container drawer",
            description="Locate and carefully open the drawer containing the glue container.",
            image_path=None  # Replace with: "images/open_drawer.png"
        )


class DisconnectHoseStep(WizardStep):
    """Disconnect hose - Step 3"""

    def __init__(self):
        super().__init__(
            title="Step 2: Disconnect Hose",
            subtitle="Disconnect the hose from the glue container",
            description="Carefully disconnect the hose from the current glue container. Make sure to avoid any spills.",
            image_path=None  # Replace with: "images/disconnect_hose.png"
        )


class PlaceNewContainerStep(WizardStep):
    """Place new container - Step 4"""

    def __init__(self):
        super().__init__(
            title="Step 3: Place New Glue Container",
            subtitle="Place the new glue container in the drawer",
            description="Remove the old glue container and place the new one in its position.",
            image_path=None  # Replace with: "images/place_container.png"
        )


class ConnectHoseStep(WizardStep):
    """Connect hose - Step 5"""

    def __init__(self):
        super().__init__(
            title="Step 4: Connect Hose",
            subtitle="Connect the hose to the new container",
            description="Securely connect the hose to the new glue container. Ensure the connection is tight.",
            image_path=None  # Replace with: "images/connect_hose.png"
        )


class CloseDrawerStep(WizardStep):
    """Close drawer - Step 6"""

    def __init__(self):
        super().__init__(
            title="Step 5: Close Drawer",
            subtitle="Close the glue container drawer",
            description="Carefully close the drawer. Make sure everything is secured properly.",
            image_path=None  # Replace with: "images/close_drawer.png"
        )


class SelectGlueTypeStep(WizardStep):
    """Select glue type - Step 7"""

    def __init__(self):
        super().__init__(
            title="Step 6: Select Glue Type",
            subtitle="Select the type of the new glue",
            description="Choose the type of glue you have installed from the options below.",
            image_path=None  # Replace with: "images/glue_type.png"
        )

        # Glue type selection
        glue_label = QLabel("Select Glue Type:")
        glue_label.setStyleSheet("font-weight: bold; margin-top: 10px; font-size: 16px;")
        self.content_layout.addWidget(glue_label)

        self.glue_group = QButtonGroup(self)

        self.glue_type1_radio = QRadioButton("Type A")
        self.glue_type2_radio = QRadioButton("Type B")
        self.glue_type3_radio = QRadioButton("Type C")
        self.glue_type4_radio = QRadioButton("Type D")
        self.glue_type1_radio.setStyleSheet("font-size: 14px;")
        self.glue_type2_radio.setStyleSheet("font-size: 14px;")
        self.glue_type3_radio.setStyleSheet("font-size: 14px;")
        self.glue_type4_radio.setStyleSheet("font-size: 14px;")
        self.glue_type1_radio.setChecked(True)

        self.glue_group.addButton(self.glue_type1_radio, 1)
        self.glue_group.addButton(self.glue_type2_radio, 2)
        self.glue_group.addButton(self.glue_type3_radio, 3)
        self.glue_group.addButton(self.glue_type4_radio, 4)

        self.content_layout.addWidget(self.glue_type1_radio)
        self.content_layout.addWidget(self.glue_type2_radio)
        self.content_layout.addWidget(self.glue_type3_radio)
        self.content_layout.addWidget(self.glue_type4_radio)


class SummaryStep(WizardStep):
    """Summary page - Step 8"""

    def __init__(self):
        super().__init__(
            title="Summary",
            subtitle="Glue change completed",
            description="Review the completed steps and the selected glue type.",
            image_path=None  # Replace with: "images/summary.png"
        )

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        self.summary_text.setStyleSheet("font-size: 14px;")
        self.content_layout.addWidget(self.summary_text)

    def initializePage(self):
        """Update summary when page is shown"""
        glue_page = self.wizard().page(6)
        glue_type = "Glue Type A"
        if glue_page.glue_type2_radio.isChecked():
            glue_type = "Glue Type B"
        elif glue_page.glue_type3_radio.isChecked():
            glue_type = "Glue Type C"

        summary = f"""
<b>Glue Change Steps Completed:</b><br>
✓ Drawer opened<br>
✓ Hose disconnected from old container<br>
✓ New glue container placed<br>
✓ Hose connected to new container<br>
✓ Drawer closed<br><br>
<b>Selected Glue Type:</b> {glue_type}
        """
        self.summary_text.setHtml(summary)


class SetupWizard(QWizard):
    """Main wizard class"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Glue Change Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(600, 500)

        # Set window icon
        self.setWindowIcon(QIcon(r"D:\GitHub\cobot-soft-v2\cobot-soft-glue-dispencing-v2\pl_ui\resources\logo.ico"))

        # Set logo
        logo_pixmap = QPixmap(r"D:\GitHub\cobot-soft-v2\cobot-soft-glue-dispencing-v2\pl_ui\resources\logo.ico")
        self.setPixmap(QWizard.WizardPixmap.LogoPixmap, logo_pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        # Add steps here - Easy to add/remove!
        self.addPage(WelcomeStep())  # Step 1
        self.addPage(OpenDrawerStep())  # Step 2
        self.addPage(DisconnectHoseStep())  # Step 3
        self.addPage(PlaceNewContainerStep())  # Step 4
        self.addPage(ConnectHoseStep())  # Step 5
        self.addPage(CloseDrawerStep())  # Step 6
        self.addPage(SelectGlueTypeStep())  # Step 7
        self.addPage(SummaryStep())  # Step 8

        # To add a new step, simply create a new class inheriting from WizardStep
        # and add it here with: self.addPage(YourNewStep())

        # To remove a step, just comment out or delete the corresponding addPage() line

        self.button(QWizard.WizardButton.FinishButton).clicked.connect(self.on_finish)

        # Customize button appearance
        self.customize_buttons()

    def on_finish(self):
        """Handle wizard completion"""
        selected_type = self.get_selected_glue_type()
        print("Glue change completed!")
        print(f"Selected Glue Type: {selected_type}")

    def get_selected_glue_type(self):
        """Get the selected glue type from the wizard"""
        glue_page = self.page(6)
        if glue_page.glue_type1_radio.isChecked():
            return "Type A"
        elif glue_page.glue_type2_radio.isChecked():
            return "Type B"
        elif glue_page.glue_type3_radio.isChecked():
            return "Type C"
        elif hasattr(glue_page, 'glue_type4_radio') and glue_page.glue_type4_radio.isChecked():
            return "Type D"
        return "Type A"  # Default

    def customize_buttons(self):
        """Replace wizard buttons with MaterialButton instances"""

        # Get the original button positions and text
        back_btn = self.button(QWizard.WizardButton.BackButton)
        next_btn = self.button(QWizard.WizardButton.NextButton)
        cancel_btn = self.button(QWizard.WizardButton.CancelButton)
        finish_btn = self.button(QWizard.WizardButton.FinishButton)

        # Create MaterialButton instances with default styling
        material_back = MaterialButton(back_btn.text())
        material_next = MaterialButton(next_btn.text())
        material_cancel = MaterialButton(cancel_btn.text())
        material_finish = MaterialButton(finish_btn.text())

        # Replace the default buttons with MaterialButtons
        self.setButton(QWizard.WizardButton.BackButton, material_back)
        self.setButton(QWizard.WizardButton.NextButton, material_next)
        self.setButton(QWizard.WizardButton.CancelButton, material_cancel)
        self.setButton(QWizard.WizardButton.FinishButton, material_finish)

        # Optional: Change button text
        # material_back.setText("← Previous")
        # material_next.setText("Continue →")
        # material_cancel.setText("Exit")
        # material_finish.setText("Complete Setup")


def main():
    app = QApplication(sys.argv)
    wizard = SetupWizard()
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
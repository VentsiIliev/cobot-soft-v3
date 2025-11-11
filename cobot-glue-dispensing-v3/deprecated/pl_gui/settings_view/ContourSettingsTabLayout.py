from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QCheckBox, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt
from deprecated.pl_gui.customWidgets.PlSlider import PlSlider  # Assuming PlSlider is available from previous code
from API.shared.settings.conreateSettings.enums.CameraSettingKey import CameraSettingKey
from .BaseSettingsTabLayout import BaseSettingsTabLayout

class ContourSettingsTabLayout(BaseSettingsTabLayout,QVBoxLayout):

    """Handles layout and contents of the Contour Settings tab."""

    def __init__(self, parent_widget):
        BaseSettingsTabLayout.__init__(self, parent_widget)
        QVBoxLayout.__init__(self)
        # self.className = self.__class__.__name__
        # self.sliders = []
        # self.callback = None

        # Add Contour settings layout
        self.addContourSettings()

    def addContourSettings(self):
        """Creates sliders for Threshold and Epsilon and checkboxes for Contour Detection and Draw Contours."""

        # Create vertical layouts for sliders and checkboxes
        self.sliders_layout = QVBoxLayout()
        self.checkboxes_layout = QVBoxLayout()

        # Add sliders to the sliders layout
        self.addContourSliders()

        # Add checkboxes to the checkboxes layout
        self.addContourCheckboxes()

        # Combine sliders and checkboxes layout into a horizontal layout
        self.horizontal_layout = QHBoxLayout()
        self.horizontal_layout.addLayout(self.sliders_layout)

        # Add a fixed-width horizontal spacer between sliders and checkboxes
        spacer = QSpacerItem(50, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.horizontal_layout.addItem(spacer)

        # Add the checkboxes layout after the spacer
        self.horizontal_layout.addLayout(self.checkboxes_layout)

        # Set the alignment of the items to the top within their layouts
        self.horizontal_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Add combined layout to the main layout
        self.addLayout(self.horizontal_layout)


    def addContourSliders(self):
        """Creates sliders for Threshold and Epsilon with proper labels and spacing."""

        # Threshold Slider Layout
        self.threshold_layout = QHBoxLayout()
        self.threshold_slider = PlSlider(label_text=CameraSettingKey.THRESHOLD.value)
        self.threshold_slider.slider.setRange(0, 100)
        self.threshold_slider.slider.setValue(50)  # Default value for threshold slider
        self.threshold_layout.addWidget(self.threshold_slider)
        self.sliders_layout.addLayout(self.threshold_layout)
        self.sliders.append(self.threshold_slider)

        # Epsilon Slider Layout
        self.epsilon = QHBoxLayout()
        self.epsilon_slider = PlSlider(label_text=CameraSettingKey.EPSILON.value)
        self.epsilon_slider.slider.setRange(0, 100)
        self.epsilon_slider.slider.setValue(50)  # Default value for spsilon slider
        self.epsilon.addWidget(self.epsilon_slider)
        self.sliders_layout.addLayout(self.epsilon)
        self.sliders.append(self.epsilon_slider)

        # Set alignment of sliders layout to top and make them responsive
        self.sliders_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Ensure sliders expand with window size by using QSizePolicy
        self.threshold_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.epsilon_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    # def onSliderMove(self, key, value):
    #     if self.callback is None:
    #         return
    #
    #     self.callback(key, value, self.className)
    #
    #
    # def connectSlidersCallback(self,callback):
    #     self.callback = callback
    #     for slider in self.sliders:
    #         slider.updateValueCallback = self.onSliderMove

    def addContourCheckboxes(self):
        """Creates checkboxes for Contour Detection and Draw Contours."""

        # Contour Detection Checkbox Layout
        self.contour_detection_checkbox = QCheckBox("Contour Detection")
        self.contour_detection_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 16px;
                font-weight: bold;
                color: black;
            }
            QCheckBox:checked {
                color: #800080;  /* Purple color */
            }
        """)
        self.checkboxes_layout.addWidget(self.contour_detection_checkbox)

        # Draw Contours Checkbox Layout
        self.draw_contours_checkbox = QCheckBox("Draw Contours")
        self.draw_contours_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 16px;
                font-weight: bold;
                color: black;
            }
            QCheckBox:checked {
                color: #800080;  /* Purple color */
            }
        """)
        self.checkboxes_layout.addWidget(self.draw_contours_checkbox)

        # Set spacing between checkboxes
        self.checkboxes_layout.setSpacing(15)  # Adjust this number for space between checkboxes

        # Set alignment of checkboxes layout to top
        self.checkboxes_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Ensure checkboxes expand with window size by using QSizePolicy
        self.contour_detection_checkbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.draw_contours_checkbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def updateValues(self,contourSettings):
        self.threshold_slider.slider.setValue(contourSettings.get_threshold())
        self.epsilon_slider.slider.setValue(contourSettings.get_epsilon())

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Contour Settings Tab Layout")

    # Create and add Contour Settings tab layout
    contour_settings_tab_layout = ContourSettingsTabLayout(window)

    window.setLayout(contour_settings_tab_layout)
    window.show()

    sys.exit(app.exec())

from PyQt6.QtWidgets import QWidget

from deprecated.pl_gui.Endpoints import CALIBRATE, GO_TO_CALIBRATION_POS, RAW_MODE_ON, CALIBRATE_CAMERA, \
    CAPTURE_CALIBRATION_IMAGE, JOG_ROBOT, CALIBRATE_ROBOT, TEST_CALIBRATION, SAVE_WORK_AREA_POINTS
from deprecated.pl_gui.main_application.appWidgets.AppWidget import AppWidget
from deprecated.pl_gui.main_application.helpers.Endpoints import UPDATE_CAMERA_FEED, HOME_ROBOT, SAVE_ROBOT_CALIBRATION_POINT


class ServiceCalibrationAppWidget(AppWidget):
    """Specialized widget for User Management application"""

    def __init__(self, parent=None, controller=None):
        self.parent= parent
        self.controller = controller
        super().__init__("ServiceCalibrationAppWidget", parent)
        print("ServiceCalibrationAppWidget initialized with parent:", self.parent)

    def setup_ui(self):
        """Setup the user management specific UI"""
        super().setup_ui()  # Get the basic layout with back button
        self.setStyleSheet("""
                           QWidget {
                               background-color: #f8f9fa;
                               font-family: 'Segoe UI', Arial, sans-serif;
                               color: #000000;  /* Force black text */
                           }

                       """)
        try:
            from deprecated.pl_gui.settings_view.CalibrationSettingsTab import CalibrationServiceTabLayout

            def updateCameraFeedCallback():
                frame = self.controller.handle(UPDATE_CAMERA_FEED)
                self.content_layout.update_camera_feed(frame)

            self.content_widget = QWidget(self.parent)
            self.content_layout = CalibrationServiceTabLayout()
            self.content_layout.update_camera_feed_signal.connect(lambda: updateCameraFeedCallback())
            self.content_layout.move_to_pickup_requested.connect(lambda: self.controller.handle(HOME_ROBOT))
            self.content_layout.jogRequested.connect(lambda endpoint,axis, dir_str, step_size: self.controller.handle(JOG_ROBOT,axis, dir_str, step_size))
            self.content_layout.compute_homography_requested.connect(lambda: self.controller.handle(CALIBRATE_ROBOT))
            self.content_layout.save_point_requested.connect(lambda: self.controller.handle(SAVE_ROBOT_CALIBRATION_POINT))

            def onMoveToCalibrationPos():
                self.controller.handle(RAW_MODE_ON)
                self.controller.handle(GO_TO_CALIBRATION_POS)

            self.content_layout.move_to_calibration_requested.connect(lambda: onMoveToCalibrationPos())
            self.content_layout.calibrate_camera_requested.connect(lambda: self.controller.handle(CALIBRATE_CAMERA))
            self.content_layout.capture_image_requested.connect(lambda: self.controller.handle(CAPTURE_CALIBRATION_IMAGE))
            self.content_layout.auto_calibrate_requested.connect(lambda: self.controller.handle(CALIBRATE))
            self.content_layout.test_calibration_requested.connect(lambda: self.controller.handle(TEST_CALIBRATION))
            self.content_layout.save_work_area_requested.connect(lambda points: self.controller.handle(SAVE_WORK_AREA_POINTS,points))

            # self.content_layout.start_calibration_requested.connect(lambda: self.controller.handle(CALIBRATE))

            self.content_widget.setLayout(self.content_layout)
            print("CALIBRATION WIDGET TYPE:", type(self.content_widget))
            # broker = MessageBroker()
            # broker.subscribe("Language", content_widget.updateLanguage)

            # Replace the last widget in the layout (the placeholder) with the real widget
            layout = self.layout()
            old_content = layout.itemAt(layout.count() - 1).widget()
            layout.removeWidget(old_content)
            old_content.deleteLater()

            layout.addWidget(self.content_widget)
        except ImportError:
            # Keep the placeholder if the UserManagementWidget is not available
            print("Service Calibration not available, using placeholder")

import os

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QApplication, QFrame
from deprecated.pl_gui.ButtonConfig import ButtonConfig
from deprecated.pl_gui.Sidebar import Sidebar
from deprecated.pl_gui.ManualControlWidget import ManualControlWidget
from deprecated.pl_gui.Endpoints import *
from PyQt6.QtCore import QPoint, QPropertyAnimation,pyqtSignal
from deprecated.pl_gui.SessionInfoWidget import SessionInfoWidget
from deprecated.pl_gui.main_application.controller.ButtonKey import ButtonKey
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),"..", "resources")
RUN_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "RUN_BUTTON.png")

RUN_BUTTON_PRESSED_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PRESSED_RUN_BUTTON.png")
STOP_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "STOP_BUTTON.png")
STOP_BUTTON_PRESSED_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PRESSED_STOP_BUTTON.png")
CREATE_WORKPIECE_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "CREATE_WORKPIECE_BUTTON_SQUARE.png")
CREATE_WORKPIECE_PRESSED_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PRESSED_CREATE_WORKPIECE_BUTTON_SQUARE.png")
DXF_BUTTON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "DXF_BUTTON.png")
# CALIBRATION_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "CALIBRATION_BUTTON_SQUARE.png")
# CALIBRATION__PRESSED_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PRESSED_CALIBRATION_BUTTON_SQUARE.png")
# ROBOT_SETTINGS_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "ROBOT_SETTINGS_BUTTON_SQUARE.png")
# ROBOT_SETTINGS_PRESSED_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PRESSSED_ROBOT_SETTINGS_BUTTON_SQUARE.png")
HOME_ROBOT_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "HOME_MACHINE_BUTTON.png")
STATIC_IMAGE_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "BACKGROUND_&_Logo.png")
ACCOUNT_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "ACCOUNT_BUTTON_SQUARE.png")
GALLERY_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "LIBRARY_BUTTON_SQARE.png")


class MainContent(QFrame):
    logout_requested = pyqtSignal()
    def __init__(self, screenWidth=1280, controller=None, parent=None):
        super().__init__()
        self.screenWidth = screenWidth
        self.parent = parent
        self.controller = controller
        self.setStyleSheet("background:transparent;")
        self.setContentsMargins(0, 0, 0, 0)

        # Main Layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(1)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.drawer = SessionInfoWidget(self,self.onLogout)
        self.drawer.logout_requested.connect(self.logout_requested.emit)
        self.drawer.setFixedWidth(300)
        self.drawer.setVisible(False)

        # Sidebar
        self.side_menu = self.create_side_menu()
        self.createWpButtonEnableToggle(False)
        self.startButtonEnableToggle(False)
        self.main_layout.addWidget(self.side_menu)

        # Stacked widget for dynamic content
        self.stacked_widget = QStackedWidget()
        self.content_area = QWidget()

        from deprecated.pl_gui.dashboard.NewDashboardWidget import GlueDashboardWidget
        self.testWidget = GlueDashboardWidget(updateCameraFeedCallback = self.updateCameraFeed,parent = self)

        self.content_layout = QHBoxLayout()

        # Content area and layout
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.content_layout.addWidget(self.testWidget)
        self.content_area.setLayout(self.content_layout)

        # Add content area to stacked widget
        self.stacked_widget.addWidget(self.content_area)
        self.main_layout.addWidget(self.stacked_widget)

        self.createWorkpieceForm = None
        self.manualMoveContent = None
    def onLogout(self):
        if self.parent is None:
            return
        self.parent.logout()
        self.drawer.setVisible(False)



    def updateCameraFeed(self):
        # if not hasattr(self, "_last_camera_feed_time"):
        #     self._last_camera_feed_time = time.time()
        #     self._camera_feed_call_count = 0
        # self._camera_feed_call_count += 1
        # now = time.time()
        # elapsed = now - self._last_camera_feed_time
        # calls_per_second = self._camera_feed_call_count / elapsed if elapsed > 0 else 0
        # print(f"updateCameraFeed called {self._camera_feed_call_count} times, {calls_per_second} per second")
        return self.controller.handle(UPDATE_CAMERA_FEED)

    def onToggleCameraViewSize(self):
        is_expanded = self.cameraFeed.current_resolution == self.cameraFeed.resolution_small

        # Hide glue meters when camera is expanded
        self.glueMeters.setVisible(is_expanded)


    def create_side_menu(self):
        """Creates and returns the side menu widget."""
        upperButtonsConfig = [
            ButtonConfig(RUN_BUTTON_ICON_PATH, RUN_BUTTON_PRESSED_ICON_PATH, ButtonKey.START.value, self.onStartButton),
            ButtonConfig(STOP_BUTTON_ICON_PATH, STOP_BUTTON_PRESSED_ICON_PATH, ButtonKey.SETTINGS.value, self.onStopButton),
            ButtonConfig(CREATE_WORKPIECE_BUTTON_ICON_PATH, CREATE_WORKPIECE_PRESSED_BUTTON_ICON_PATH, ButtonKey.CREATE_WORKPIECE.value, self.onCreateWorkpiece),
            # ButtonConfig(CALIBRATION_BUTTON_ICON_PATH, CALIBRATION__PRESSED_BUTTON_ICON_PATH, "calibrate", self.onCalibrate),
            # ButtonConfig(ROBOT_SETTINGS_BUTTON_ICON_PATH, ROBOT_SETTINGS_PRESSED_BUTTON_ICON_PATH, "manualMove", self.onManualMoveButton),
            ButtonConfig(HOME_ROBOT_BUTTON_ICON_PATH, HOME_ROBOT_BUTTON_ICON_PATH, ButtonKey.HOME_ROBOT.value, self.onHomeRobot),
            ButtonConfig(DXF_BUTTON_PATH, DXF_BUTTON_PATH, ButtonKey.DFX.value, self.dfxUpload),
            ButtonConfig(GALLERY_BUTTON_ICON_PATH,GALLERY_BUTTON_ICON_PATH,ButtonKey.GALLERY.value,self.onGallery),
            # ButtonConfig(RUN_BUTTON_ICON_PATH, RUN_BUTTON_PRESSED_ICON_PATH, "DFX", self.calibPickup),
            # ButtonConfig(RUN_BUTTON_ICON_PATH, RUN_BUTTON_PRESSED_ICON_PATH, "Belt", self.sendMoveBeltReq),
            ButtonConfig(RUN_BUTTON_ICON_PATH, RUN_BUTTON_PRESSED_ICON_PATH, ButtonKey.TEST_CREATE_WP.value, self.on_test_create_workpiece),
        ]

        lowerButtonsConfig = [ButtonConfig(ACCOUNT_BUTTON_ICON_PATH, ACCOUNT_BUTTON_ICON_PATH,ButtonKey.ACCOUNT.value, self.openAccountPage)]

        side_menu = Sidebar(self.screenWidth, upperButtonsConfig,lowerButtonsConfig)
        side_menu.setContentsMargins(0, 0, 0, 0)
        return side_menu

    # Button Handlers
    def onStartButton(self):
        self.controller.handle(START)

    def onStopButton(self):
        self.controller.handle(STOP)

    # def onCalibrate(self):
    #     result, message = self.controller.handle(CALIBRATE)
    #     if result:
    #         self.onManualMoveButton()
    #         self.manualMoveContent.savePointButton.show()
    #         self.manualMoveContent.onSaveCallback = lambda endpoint : self.controller.handle(endpoint)

    def onHomeRobot(self):
        self.controller.handle(HOME_ROBOT)
        self.createWpButtonEnableToggle(True)
        self.startButtonEnableToggle(True)

    def startButtonEnableToggle(self, state):
        self.side_menu.buttonsDict[ButtonKey.START.value].setEnabled(state)

    def createWpButtonEnableToggle(self,state):
        self.side_menu.buttonsDict[ButtonKey.CREATE_WORKPIECE.value].setEnabled(state)

    def openAccountPage(self):
        self.drawer.toggle()
        # if hasattr(self, 'drawer') and self.drawer.isVisible():
        #     self.drawer.slide_out()
        # else:
        #     self.drawer.update_info()
        #     self.drawer.slide_in()

    def onManualMoveButton(self):
        DRAWER_WIDTH = 600
        if self.manualMoveContent is None:
            if self.createWorkpieceForm:
                self.createWorkpieceForm.close()
                self.createWorkpieceForm = None

            self.manualMoveContent = ManualControlWidget(self, callback = self.manualMoveCallback, jogCallback=self.controller.handle)
            self.manualMoveContent.setParent(self)  # make it top-level in this widget
            self.manualMoveContent.setGeometry(self.width(), 0, DRAWER_WIDTH, self.height())  # start off-screen right
            self.manualMoveContent.raise_()
            self.manualMoveContent.show()

            self.drawer_anim = QPropertyAnimation(self.manualMoveContent, b"pos")
            self.drawer_anim.setDuration(300)
            self.drawer_anim.setStartValue(QPoint(self.width(), 0))
            self.drawer_anim.setEndValue(QPoint(self.width() - DRAWER_WIDTH, 0))  # Slide in
            self.drawer_anim.start()

        else:
            # Animate out and delete after
            self.drawer_anim = QPropertyAnimation(self.manualMoveContent, b"pos")
            self.drawer_anim.setDuration(300)
            self.drawer_anim.setStartValue(self.manualMoveContent.pos())
            self.drawer_anim.setEndValue(QPoint(self.width(), 0))
            self.drawer_anim.finished.connect(self.manualMoveContent.deleteLater)
            self.drawer_anim.start()
            self.manualMoveContent = None

    def on_test_create_workpiece(self):
        print("Test Create Workpiece Button Clicked")
        # self.parent.show_contour_editor()
        # self.parent.contourEditor.set_image(frame)
        # self.parent.contourEditor.init_contours([contours])
        # self.parent.contourEditor.createWorkpieceForm.onSubmitCallBack = self.onCreateWorkpieceSubmit

    def onGallery(self):
        self.parent.onGalleryButton()

    def onCreateWorkpiece(self):
        from deprecated.pl_gui.dashboard.WorkpieceOptionsWidget import WorkpieceOptionsWidget
        dialog = WorkpieceOptionsWidget(self)

        def onCamera():
            print("Camera option selected")
            self.controller.handle(CREATE_WORKPIECE_TOPIC, self.handleCreateWorkpieceSuccess,
                                   self.handleCreateWorkpieceFailure)

        def onDxfUpload():
            print("DXF upload option selected")
            self.dfxUpload()

        # Connect signals to your methods
        dialog.camera_selected.connect(onCamera)
        dialog.dxf_selected.connect(onDxfUpload)

        dialog.exec()
        # show widget with 2 choices: camera or dxf upload



    def handleCreateWorkpieceSuccess(self, frame, contours, data):
        print("originalcnt received: ", contours)
        self.parent.show_contour_editor()
        self.parent.contourEditor.set_image(frame)
        contours_by_layer = {
            "External": [contours] if len(contours) > 0 else [],
            "Contour": [],
            "Fill": []
        }

        print("Loading contours into editor: ", contours_by_layer)
        print("EXTERNAL CONTOURS: ", contours_by_layer["External"])
        self.parent.contourEditor.init_contours(contours_by_layer)
        self.parent.contourEditor.createWorkpieceForm.onSubmitCallBack = self.onCreateWorkpieceSubmit

    def handleCreateWorkpieceFailure(self, req, msg):
        from deprecated.pl_gui.FeedbackProvider import FeedbackProvider
        FeedbackProvider.showMessage(msg)


    def manualMoveCallback(self):
        self.manualMoveContent = None

    def onCreateWorkpieceSubmit(self, data):
        wp_contours_data = self.parent.contourEditor.contourEditor.manager.to_wp_data()

        print("WP Contours Data: ", wp_contours_data)
        print("WP form data: ",data)

        sprayPatternsDict = {
            "Contour": [],
            "Fill": []
        }

        sprayPatternsDict['Contour'] = wp_contours_data.get('Contour')
        sprayPatternsDict['Fill'] = wp_contours_data.get('Fill')

        from API.shared.workpiece.Workpiece import WorkpieceField

        data[WorkpieceField.SPRAY_PATTERN.value] = sprayPatternsDict
        data[WorkpieceField.CONTOUR.value] = wp_contours_data.get('External')
        print("EXTERNAL CONTOURS AFTER WP FORM: ", data[WorkpieceField.CONTOUR.value])

        self.side_menu.uncheck_all_buttons()
        self.testWidget.camera_feed.resume_feed()

        self.controller.handle(SAVE_WORKPIECE,data)
        self.testWidget.camera_feed.resume_feed()
        self.parent.show_home()



    def dfxUpload(self):
        self.parent.showDxfBrowser()


    def resizeEvent(self, event):
        """Resize content and side menu dynamically."""
        super().resizeEvent(event)
        new_width = self.width()

        # Adjust icon sizes of the sidebar buttons
        icon_size = int(new_width * 0.06)  # 5% of the new window width
        for button in self.side_menu.buttons:
            button.setIconSize(QSize(icon_size, icon_size))
            # Ensure the drawer is always positioned and sized correctly
        self.drawer.resize_to_parent_height()


    def calibPickup(self):
        self.controller.calibPickupArea()

    def sendMoveBeltReq(self):
        self.controller.moveBelt()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainContent(1280, app)
    window.show()
    sys.exit(app.exec())

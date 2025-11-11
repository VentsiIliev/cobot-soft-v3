import os

from PyQt6.QtCore import QSize
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget
)

from API.MessageBroker import MessageBroker
from API.shared.user.Session import SessionManager
from API.shared.user.User import Role
from GlueDispensingApplication.tools.GlueNozzleService import GlueNozzleService
from pl_ui.contour_editor.ContourEditor import MainApplicationFrame
from pl_ui.controller.ButtonKey import ButtonKey
from pl_ui.ui.windows.gallery.GalleryContent import GalleryContent
from pl_ui.ui.windows.settings.SettingsContent import SettingsContent
from .ButtonConfig import ButtonConfig
from .Endpoints import *
from .Header import Header
from .Sidebar import Sidebar
from pl_ui.controller.UserPermissionManager import UserPermissionManager

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
DASHBOARD_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "DASHBOARD_BUTTON_SQUARE.png")
SETTINGS_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "SETTINGS_BUTTON.png")
SETTINGS_PRESSED_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PRESSED_SETTINGS_BUTTON.png")
# GALLERY_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "LIBRARY_BUTTON_SQARE.png")
RUN_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "RUN_BUTTON.png")
RUN_PRESSED_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PRESSED_RUN_BUTTON.png")
LOGIN_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "LOGIN_BUTTON_SQUARE.png")
LOGIN_PRESSED_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PRESSED_RUN_BUTTON.png")
HELP_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "HELP_BUTTON_SQUARE.png")
HELP_PRESSED_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PRESSED_HELP_BUTTON_SQUARE.png")
LOGOUT_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "LOGOUT_BUTTON_SQUARE.png")
ACCOUNT_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "ACCOUNT_BUTTON_SQUARE.png")
HOME_ROBOT_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "HOME_MACHINE_BUTTON.png")
CALIBRATION__PRESSED_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PRESSED_CALIBRATION_BUTTON_SQUARE.png")
CALIBRATION_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "CALIBRATION_BUTTON_SQUARE.png")
ROBOT_SETTINGS_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "ROBOT_SETTINGS_BUTTON_SQUARE.png")
ROBOT_SETTINGS_PRESSED_BUTTON_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "PRESSSED_ROBOT_SETTINGS_BUTTON_SQUARE.png")
USER_MANAGEMENT_ICON_PATH = os.path.join(RESOURCE_DIR, "pl_ui_icons", "user_management.png")
class MainWindow(QMainWindow):
    def __init__(self, dashboardWidget=None, controller=None):
        print("MainWindow init started")
        self.controller = controller
        super().__init__()
        self.glueNozzleService = GlueNozzleService.get_instance()
        self.glueNozzleService._startCommandProcessor()
        self.keyPressEvent = self.on_key_press

        if dashboardWidget is None:
            print("Dash is none")
            self.main_content = QWidget()
        else:
            self.main_content = dashboardWidget
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background-color: white")  # A light gray background instead of transparent
        # self.setStyleSheet("background-color: white;")  # A light gray background instead of transparent

        # Get screen size
        screen_size = QApplication.primaryScreen().size()

        self.screen_width = screen_size.width()
        self.screen_height = screen_size.height()

        # self.drawer = SessionDrawer(self,onLogOutCallback = self.logout)
        # self.drawer.setVisible(False)

        # Main container widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layouts
        self.main_layout = QVBoxLayout(self.central_widget)
        # Set spacing for the main layout
        self.main_layout.setSpacing(1)  # Set spacing to 10 pixels
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # Set margins to 0 pixels
        self.content_layout = QHBoxLayout()  # Contains sidebar and main content

        # Header Section
        self.header = Header(self.screen_width, self.screen_height, self.toggle_menu,self.show_home)

        # self.galleryContent = GalleryContent(thumbnails=thumbnails)
        # self.galleryContent = GalleryContent()
        # broker = MessageBroker()
        # broker.subscribe("Language",self.galleryContent.updateLanguage)
        self.contourEditor = MainApplicationFrame(parent=self)

        # Sidebar Section
        dashboardButtonConfig = ButtonConfig(
            DASHBOARD_BUTTON_ICON_PATH,
            DASHBOARD_BUTTON_ICON_PATH,
            ButtonKey.DASHBOARD.value,
            self.show_home
        )
        settingsButtonConfig = ButtonConfig(
            SETTINGS_BUTTON_ICON_PATH,
            SETTINGS_PRESSED_BUTTON_ICON_PATH,
            ButtonKey.SETTINGS.value,
            self.show_settings)

        # galleryButtonConfig = ButtonConfig(
        #     GALLERY_BUTTON_ICON_PATH,
        #     GALLERY_BUTTON_ICON_PATH,
        #     "Gallery",
        #     self.onGalleryButton)

        helpButtonConfig = ButtonConfig(
            HELP_BUTTON_ICON_PATH,
            HELP_PRESSED_BUTTON_ICON_PATH,
            ButtonKey.HELP.value,
            self.show_help)

        # logOutButtonConfig = ButtonConfig(
        #     LOGOUT_BUTTON_ICON_PATH,
        #     LOGOUT_BUTTON_ICON_PATH,
        #     "Logout",
        #     self.logout)

        userManagementButtonConfig = ButtonConfig(
            USER_MANAGEMENT_ICON_PATH,
            USER_MANAGEMENT_ICON_PATH,
            ButtonKey.USER_MANAGEMENT.value,
            self.showUserManagementWidget)


        manualMoveButtonConfig = ButtonConfig(
            ROBOT_SETTINGS_BUTTON_ICON_PATH,
            ROBOT_SETTINGS_PRESSED_BUTTON_ICON_PATH,
            ButtonKey.MANUAL_MOVE.value,
            self.main_content.onManualMoveButton)

        calibButtonConfig = ButtonConfig(
            CALIBRATION_BUTTON_ICON_PATH,
            CALIBRATION__PRESSED_BUTTON_ICON_PATH,
            ButtonKey.CALIBRATE.value,
            self.onCalibrate)

        homeRobotButtonConfig = ButtonConfig(
            HOME_ROBOT_BUTTON_ICON_PATH,
            HOME_ROBOT_BUTTON_ICON_PATH,
            ButtonKey.HOME_ROBOT.value,
            self.onHomeRobot)

        serviceButtonConfig = ButtonConfig(
            HOME_ROBOT_BUTTON_ICON_PATH,
            HOME_ROBOT_BUTTON_ICON_PATH,
            ButtonKey.SERVICE.value,
            self.onTestRun)

        self.sidebar = Sidebar(self.screen_width,
                               [dashboardButtonConfig, settingsButtonConfig,homeRobotButtonConfig,calibButtonConfig,manualMoveButtonConfig,userManagementButtonConfig,serviceButtonConfig],
                               [helpButtonConfig])
        # self.sidebar.setFixedWidth(200)
        self.sidebar.setFixedWidth(int(self.screen_width * 0.10))
        self.sidebar.heightOffset = self.header.height()  # Adjust height offset for sidebar
        self.sidebar.resize_to_parent_height()
        print("Sidebar height offset:", self.sidebar.heightOffset)
        self.sidebar.setContentsMargins(0, 0, 0, 0)
        # self.sidebar.setFixedHeight(self.screen_height)


        self.sidebar.setVisible(False)  # Make sidebar hidden by default

        self.sidebar.setStyleSheet("QWidget { background-color: white; }")

        # Create the QStackedWidget for content switching
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: white;")  # Set background color
        # Create content widgets and add them to the stacked widget
        # self.main_content = MainContent(self.screen_width)

        self.settings_content = SettingsContent(updateSettingsCallback = self.updateSettingsCallback)
        self.stacked_widget.addWidget(self.main_content)
        self.stacked_widget.addWidget(self.settings_content)
        # self.stacked_widget.addWidget(self.galleryContent)
        self.stacked_widget.addWidget(self.contourEditor)

        # Add only the stacked widget to the content layout so it fills the space
        self.content_layout.addWidget(self.stacked_widget, 1)

        # Set sidebar as a child of central widget (not added to layout)
        self.sidebar.setParent(self)
        # self.sidebar.move(-self.sidebar.width(), self.header.height())  # Start offscreen left, below header
        self.sidebar.setVisible(False)
        self.sidebar.raise_()

        # Add header and content layout to main layout
        self.main_layout.addWidget(self.header)
        # add horizontal separator

        self.main_layout.addLayout(self.content_layout)

    def onTestRun(self):
        self.controller.handle(TEST_RUN)

    def showUserManagementWidget(self):
        from API.shared.user.UserDashboard import UserManagementWidget
        from API.MessageBroker import MessageBroker

        # Navigate up to project root, then down to API/shared/user/users.csv
        base_dir = os.path.dirname(os.path.abspath(__file__))  # pl_gui/
        project_root = os.path.abspath(os.path.join(base_dir, ".."))  # move up one level
        csv_file_path = os.path.join(project_root, "API", "shared", "user", "users.csv")

        widget = UserManagementWidget(csv_file_path=csv_file_path)
        broker = MessageBroker()
        broker.subscribe("Language",widget.update_language)
        self.stacked_widget.addWidget(widget)
        self.stacked_widget.setCurrentWidget(widget)
        self.sidebar.setVisible(False)


    def onCalibrate(self):
        result, message = self.controller.handle(CALIBRATE)
        if result:
            self.main_content.onManualMoveButton()
            self.main_content.manualMoveContent.savePointButton.show()
            self.main_content.manualMoveContent.onSaveCallback = lambda endpoint : self.controller.handle(endpoint)

    def onHomeRobot(self):
        self.controller.handle(HOME_ROBOT)

    def updateSettingsCallback(self,key,value,className):
        # self.controller.updateSettings(key,value,className)
        print("Update Settings Callback called with key:", key, "value:", value, "className:", className)
        self.controller.handle(UPDATE_SETTINGS,key,value,className)

    def show_contour_editor(self):
        self.stacked_widget.setCurrentWidget(self.contourEditor)

    def on_key_press(self, event):
        # temp code to test glue nozzle
        if event.key() == Qt.Key.Key_O:
            self.glueNozzleService.addCommandToQueue(self.glueNozzleService.startGlueDotsDispensing)
        elif event.key() == Qt.Key.Key_P:
            self.glueNozzleService.addCommandToQueue(self.glueNozzleService.stopGlueDispensing)
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_F1:
            self.showNormal()

    def toggle_menu(self):
        self.sidebar.toggle()


    def onGalleryButton(self):
        """Display Gallery Content"""
        workpieces = self.controller.handle(WORPIECE_GET_ALL)

        def onApply(selectedWorkpieces):
            if len(selectedWorkpieces) == 0:
                return
            workpieces = self.controller.handle(WORPIECE_GET_ALL)
            selected = selectedWorkpieces[0]

            selectedWp = None
            for wp in workpieces:
                if str(wp.workpieceId) == str(selected):
                    selectedWp = wp
                    break
            print("Selected Workpiece:", selectedWp.sprayPattern)
            self.controller.handleExecuteFromGallery(selectedWp)


        self.galleryContent = GalleryContent(workpieces = workpieces,onApplyCallback=onApply)
        self.stacked_widget.addWidget(self.galleryContent)
        broker = MessageBroker()
        broker.subscribe("Language", self.galleryContent.updateLanguage)
        self.stacked_widget.setCurrentWidget(self.galleryContent)

    def onDxfBrowserSubmit(self, file_name, thumbnail):
        if not file_name:
            return

        from API.shared.dxf.DxfParser import DXFPathExtractor
        from deprecated.pl_gui.settings.Paths import DXF_DIRECTORY
        from deprecated.pl_gui.contour_editor.utils import qpixmap_to_cv, create_light_gray_pixmap

        file_name = file_name  # Assume single select for now
        extractor = DXFPathExtractor(os.path.join(DXF_DIRECTORY, file_name))

        # Use the new method with centering
        wp_contour, spray, fill = extractor.get_opencv_contours()
        print("Extracted Contours:", spray)

        scale_x = 1280 / 900  # 1.422
        scale_y = 720 / 600  # 1.2

        from API.shared.dxf.utils import scale_contours

        wp_contour = scale_contours(wp_contour, scale_x, scale_y)
        spray = scale_contours(spray, scale_x, scale_y)
        fill = scale_contours(fill, scale_x, scale_y)

        print("Extracted Contours after scale:", spray)

        # SHOW AND SETUP CONTOUR EDITOR

        self.show_contour_editor()
        # Create the image
        image = create_light_gray_pixmap()
        image = qpixmap_to_cv(image)

        # Set up the contour editor
        self.contourEditor.set_image(image)

        # Prepare dictionary for initContour (layer -> contours)
        contours_by_layer = {
            "External": [wp_contour] if wp_contour is not None and len(wp_contour) > 0 else [],
            "Contour": spray if len(spray) > 0 else [],
            "Fill": fill if len(fill) > 0 else []
        }

        # Initialize contours in the editor
        self.contourEditor.init_contours(contours_by_layer)

        # Set up the callback with proper error checking
        from PyQt6.QtCore import QTimer
        def set_callback():
            if hasattr(self.contourEditor, 'createWorkpieceForm') and self.contourEditor.createWorkpieceForm:
                self.contourEditor.createWorkpieceForm.onSubmitCallBack = self.onCreateWorkpieceSubmitDxf
                print("DXF callback set successfully")
            else:
                print("Warning: createWorkpieceForm not found")

        QTimer.singleShot(100, set_callback)

    def onCreateWorkpieceSubmitDxf(self, data):
        """Handle DXF workpiece form submission - mirrors camera workflow"""
        print("onCreateWorkpieceSubmitDxf called with data:", data)

        wp_contours_data = self.contourEditor.contourEditor.manager.to_wp_data()

        print("WP Contours Data: ", wp_contours_data)
        print("WP form data: ", data)

        sprayPatternsDict = {
            "Contour": [],
            "Fill": []
        }

        sprayPatternsDict['Contour'] = wp_contours_data.get('Contour', [])
        sprayPatternsDict['Fill'] = wp_contours_data.get('Fill', [])

        from API.shared.workpiece.Workpiece import WorkpieceField

        data[WorkpieceField.SPRAY_PATTERN.value] = sprayPatternsDict
        data[WorkpieceField.CONTOUR.value] = wp_contours_data.get('External', [])
        data[WorkpieceField.CONTOUR_AREA.value] = 0 # PLACEHOLDER NEED TO CALCULATE AREA
        # Navigate back to main content like camera workflow
        self.show_home()

        # Save the workpiece using DXF endpoint
        print("Saving DXF workpiece with data:", data)
        self.controller.handle(SAVE_WORKPIECE, data)
        print("DXF workpiece saved successfully")

    def showDxfBrowser(self):
        """Show DXF file browser"""
        from deprecated.pl_gui.gallery.DxfThumbnailLoader import DXFThumbnailLoader
        from deprecated.pl_gui.gallery.GalleryContent import GalleryContent
        from deprecated.pl_gui.settings.Paths import DXF_DIRECTORY

        loader = DXFThumbnailLoader(DXF_DIRECTORY)
        thumbnails = loader.run()
        self.dxfBrowser = GalleryContent(thumbnails=thumbnails, onApplyCallback=self.onDxfBrowserSubmit)
        self.stacked_widget.addWidget(self.dxfBrowser)  # Add the widget to the stack
        self.stacked_widget.setCurrentWidget(self.dxfBrowser)

    def show_home(self):
        """Show Main Content (Replace QWidget with MainContent)"""

        if isinstance(self.stacked_widget.currentWidget(), MainApplicationFrame):
            self.stacked_widget.removeWidget(self.contourEditor)
            self.contourEditor = MainApplicationFrame(parent=self)
            # Add the new instance to the stacked widget
            self.stacked_widget.addWidget(self.contourEditor)

        if isinstance(self.main_content, QWidget):  # Check if it’s the initial QWidget
            # from pl_gui.dashboard.DashboardContent import MainContent  # Import only when needed
            # self.main_content = MainContent(screenWidth=self.screen_width, controller=self.controller,
            #                                 parent=self)  # Replace with MainContent
            self.onLogEvent()
            self.stacked_widget.addWidget(self.main_content)  # Add new widget to stacked widget
            self.stacked_widget.setCurrentWidget(self.main_content)  # Set it to current widget
        else:
            self.stacked_widget.setCurrentWidget(self.main_content)  # Already MainContent, just switch


        currentUser = SessionManager.get_current_user()
        if currentUser.role != Role.OPERATOR:
            self.toggle_menu()

    def show_settings(self):
        """Show Settings Content with Tabs"""
        self.stacked_widget.setCurrentWidget(self.settings_content)
        cameraSettings, robotSettings, glueSettings = self.controller.handle(GET_SETTINGS)
        self.settings_content.updateCameraSettings(cameraSettings)
        self.settings_content.updateRobotSettings(robotSettings)
        self.settings_content.updateContourSettings(cameraSettings)
        self.settings_content.updateGlueSettings(glueSettings)
        self.toggle_menu()

    def show_help(self):
        """Display Help Content"""
        self.stacked_widget.setCurrentWidget(self.main_content)
        self.settings_content.setVisible(False)
        self.controller.handle(HELP)

    def show_login(self):
        """Display Login Content"""
        self.controller.handle(LOGIN)

    def resizeEvent(self, event):
        """Adjust icon sizes and layout on window resize"""
        new_width = self.width()
        new_height = self.height()  # Fix: get current window height

        icon_size = int(new_width * 0.06)  # 5% of new window width
        # Update sidebar offset and height after header is laid out
        self.sidebar.heightOffset = self.header.height()
        self.sidebar.resize_to_parent_height()

        # Resize sidebar buttons by accessing them by index
        self.sidebar.buttons[0].setIconSize(QSize(icon_size, icon_size))  # Home button
        self.sidebar.buttons[1].setIconSize(QSize(icon_size, icon_size))  # Settings button
        self.sidebar.buttons[2].setIconSize(QSize(icon_size, icon_size))  # Home Robot
        self.sidebar.buttons[3].setIconSize(QSize(icon_size, icon_size))  # INFO
        self.sidebar.buttons[4].setIconSize(QSize(icon_size, icon_size))
        self.sidebar.buttons[5].setIconSize(QSize(icon_size, icon_size))
        self.sidebar.buttons[6].setIconSize(QSize(icon_size, icon_size))

        # Resize menu button's icon size
        self.header.menu_button.setIconSize(QSize(icon_size, icon_size))

        if hasattr(self, 'drawer') and self.drawer.isVisible():
            self.drawer.move(0, self.height() - self.drawer.height())

        super().resizeEvent(event)

    def logout(self):
        from deprecated.pl_gui.LoginWindow import LoginWindow

        print("Logging out...")
        # Clear the current session
        SessionManager.logout()
        self.main_content.drawer.setVisible(False)
        # Disable current window while login is shown
        self.setEnabled(False)

        # Show login window fullscreen (non-blocking)
        login = LoginWindow(self.controller,onLogEventCallback=self.onLogEvent,header=self.header)
        login.showFullScreen()

        # Block here until login window returns
        if login.exec():
            print("Logged in successfully")
            self.setEnabled(True)  # Re-enable after successful login
        else:
            print("Login failed or cancelled")
            return  # You could also call self.close() or sys.exit() if needed

        self.onLogEvent()

    # def openAccountPage(self):
    #     if hasattr(self, 'drawer') and self.drawer.isVisible():
    #         self.drawer.slide_out()
    #     else:
    #         self.drawer.update_info()
    #         self.drawer.slide_in()

    def onLogEvent(self):
        user = SessionManager.get_current_user()
        role = user.role

        visible_buttons = UserPermissionManager.get_visible_buttons(role)
        print(f"[DEBUG] Logged in as: {role.name}")
        # print(f"[DEBUG] Allowed buttons: {UserPermissionManager.get_visible_buttons(role)}")

        for btn in self.sidebar.buttons:
            # print(f"[DEBUG] Checking button: {btn.button_key}")
            label = btn.button_key
            btn.setVisible(label in visible_buttons)

        for btn in self.main_content.side_menu.buttons:
            # print(f"[DEBUG] Checking main content button: {btn.button_key}")
            label = btn.button_key
            btn.setVisible(label in visible_buttons)

        # Optional: Handle other role-specific UI logic
        if role == Role.OPERATOR:
            self.header.hideMenuButton()
            self.header.showDashboardButton()
            self.header.hideLanguageSelector()
            self.main_content.createWpButtonEnableToggle(False)
            self.main_content.startButtonEnableToggle(False)
        elif role == Role.ADMIN:
            self.header.showMenuButton()
            self.header.hideDashboardButton()
            self.header.showLanguageSelector()


# Run the application
# app = QApplication(sys.argv)

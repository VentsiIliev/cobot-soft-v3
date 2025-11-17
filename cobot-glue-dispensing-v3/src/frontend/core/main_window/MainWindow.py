import os

from PyQt6.QtCore import QTimer
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QStackedWidget, QFrame)
from PyQt6.QtWidgets import (QVBoxLayout, QApplication)
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QMessageBox

from frontend.contour_editor.utils.utils import create_light_gray_pixmap, qpixmap_to_cv
from frontend.core.shared.base_widgets.AppWidget import AppWidget
from frontend.core.utils.localization import TranslationKeys, TranslatableWidget
from modules.shared.core.user.Session import SessionManager

from modules.shared.v1.endpoints import operations_endpoints, robot_endpoints,workpiece_endpoints
from frontend.widgets.Header import Header
from frontend.legacy_ui.windows.folders_page.FoldersPage import FoldersPage, FolderConfig
from frontend.legacy_ui.windows.login.LoginWindow import LoginWindow
from frontend.core.main_window.WidgetFactory import WidgetType
from frontend.core.main_window.PluginWidgetFactory import PluginWidgetFactory
from frontend.legacy_ui.windows.mainWindow.managers.CreateWorkpieceManager import CreateWorkpieceManager
from frontend.core.utils.DxfThumbnailLoader import DXFThumbnailLoader
from frontend.core.utils.IconLoader import (DASHBOARD_ICON, CREATE_WORKPIECE_ICON, GALLERY_ICON,
                                                 SETTINGS_ICON, CALIBRATION_ICON, USER_MANAGEMENT_ICON,
                                                 GLUE_WEIGHT_CELL_ICON)
from frontend.core.services.authorizationService import AuthorizationService , Permission
from frontend.core.utils.FilePaths import DXF_DIRECTORY
from modules.shared.core.dxf.DxfParser import DXFPathExtractor
from modules.shared.core.dxf.utils import scale_contours




class MainWindow(TranslatableWidget):
    """Demo application showing the Android folder widget with QStackedWidget for app management"""
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    pause_requested = pyqtSignal()

    def __init__(self, controller):
        super().__init__(auto_retranslate=False)
        self.controller = controller
        self.current_running_app = None  # Track currently running app
        self.current_app_folder = None  # Track which folder has the running app
        self.stacked_widget = None  # The main stacked widget
        self.folders_page = None  # The folders page widget
        self.auth_service = AuthorizationService()
        self.pending_camera_operations = False  # Track if camera operations are in progress
        
        # Initialize plugin-based widget factory
        self.plugin_widget_factory = PluginWidgetFactory(controller, self)
        
        # Keep legacy factory for fallback during transition
        self.legacy_widget_factory = None

        self.setup_ui()

    def on_folder_opened(self, opened_folder):
        """Handle when a folder is opened - gray out other folders"""
        # This is now handled by the FoldersPage, but we keep it for compatibility
        pass

    def on_folder_closed(self):
        """Handle when a folder is closed - restore all folders"""
        print("MainWindow: Folder closed - restoring all folders")
        # Reset the current app state
        self.current_running_app = None
        self.current_app_folder = None

    def on_app_selected(self, app_name):
        """Handle when an app is selected from any folder"""
        print(f"Currently running app: {self.current_running_app}")
        print(f"MainWindow: App selected - {app_name}")

        # Find which folder emitted this signal by looking at the folders page
        sender_folder = None
        for folder in self.folders_page.get_folders():
            if folder == self.sender():
                sender_folder = folder
                break

        # Store the running app info
        self.current_running_app = app_name
        self.current_app_folder = sender_folder
        # Show the appropriate app
        self.show_app(app_name)

    def on_back_button_pressed(self):
        """Handle when the back button is pressed in the sidebar"""
        print("MainWindow: Back button signal received - closing app and returning to main")
        self.close_current_app()


    def on_clean(self):
        print("Clean requested from on_clean")
        self.controller.handleCleanNozzle()

    def create_app(self, app_name):
        """Create app widget using plugin system with legacy fallback"""
        print(f"MainWindow: Creating app widget for '{app_name}'")
        
        # Try plugin-based widget factory first
        app_widget = self.plugin_widget_factory.create_widget(app_name)
        
        if app_widget:
            print(f"MainWindow: Successfully created plugin widget for '{app_name}'")
            
            # Connect widget-specific signals (plugin-agnostic)
            self._connect_widget_signals(app_widget, app_name)
            
            # Handle special setup cases
            self._setup_special_widgets(app_widget, app_name)
        else:
            print(f"MainWindow: No plugin widget found for '{app_name}', using fallback")
            app_widget = AppWidget(app_name=f"Placeholder ({app_name})")

        return app_widget
    
    def _connect_widget_signals(self, app_widget, app_name):
        """Connect signals for specific widget types (plugin-agnostic)"""
        try:
            # Create Workpiece signals
            if hasattr(app_widget, 'create_workpiece_camera_selected'):
                app_widget.create_workpiece_camera_selected.connect(self.create_workpiece_via_camera_selected)
                app_widget.create_workpiece_dxf_selected.connect(self.create_workpiece_via_dxf_selected)
            
            # Dashboard signals
            if hasattr(app_widget, 'start_requested'):
                app_widget.start_requested.connect(lambda: self.controller.handle(operations_endpoints.START))
                app_widget.pause_requested.connect(lambda: self.controller.handle(operations_endpoints.PAUSE))
                app_widget.stop_requested.connect(lambda: self.controller.handle(operations_endpoints.STOP))
                app_widget.clean_requested.connect(self.on_clean)
                app_widget.reset_errors_requested.connect(lambda: self.controller.handle(robot_endpoints.ROBOT_RESET_ERRORS))
                app_widget.start_demo_requested.connect(lambda: self.controller.handle(operations_endpoints.RUN_DEMO))
                app_widget.stop_demo_requested.connect(lambda: self.controller.handle(operations_endpoints.STOP_DEMO))
                app_widget.LOGOUT_REQUEST.connect(self.onLogout)
            
            # Gallery signals
            if hasattr(app_widget, 'edit_requested'):
                def on_edit_request(workpiece_id):
                    result, workpiece = self.controller.getWorkpieceById(workpiece_id)
                    self.contour_editor = self.show_app(WidgetType.CONTOUR_EDITOR.value)
                    self.contour_editor.load_workpiece(workpiece)
                    create_wp_manager = CreateWorkpieceManager(self.contour_editor, self.controller)
                    self.contour_editor.set_create_workpiece_for_on_submit_callback(create_wp_manager.via_camera_on_create_workpiece_submit)
                app_widget.edit_requested.connect(lambda workpieceId: on_edit_request(workpieceId))
                
        except Exception as e:
            print(f"Error connecting widget signals for {app_name}: {e}")
    
    def _setup_special_widgets(self, app_widget, app_name):
        """Handle special widget setup requirements"""
        try:
            # DXF Browser special setup
            if app_name == WidgetType.DXF_BROWSER.value:
                print("MainWindow: Setting up DXF Browser with thumbnails")
                loader = DXFThumbnailLoader(DXF_DIRECTORY)
                thumbnails = loader.run()
                
                # Configure the widget with thumbnails if it supports it
                if hasattr(app_widget, 'set_thumbnails'):
                    app_widget.set_thumbnails(thumbnails)
                elif hasattr(app_widget, 'thumbnails'):
                    app_widget.thumbnails = thumbnails
                    
                # Set callback if supported
                if hasattr(app_widget, 'set_apply_callback'):
                    app_widget.set_apply_callback(self.onDxfBrowserSubmit)
                    
        except Exception as e:
            print(f"Error setting up special widget {app_name}: {e}")

    def show_app(self, app_name):
        """Show the specified app in the stacked widget"""
        app_widget = self.create_app(app_name)
        if not app_widget:
            print(f"MainWindow: App '{app_name}' could not be created.")
            return None

        # Connect the app's close signal
        app_widget.app_closed.connect(self.close_current_app)
        # Add the app widget to the stacked widget (index 1)
        if self.stacked_widget.count() > 1:
            # Remove existing app widget
            old_app = self.stacked_widget.widget(1)
            old_app.clean_up()  # Call cleanup if needed
            print(f"MainWindow: Closing old app widget - {old_app}")
            self.stacked_widget.removeWidget(old_app)
            old_app.deleteLater()

        self.stacked_widget.addWidget(app_widget)
        # Switch to the app view (index 1)
        self.stacked_widget.setCurrentIndex(1)
        print(f"App '{app_name}' is now running. Press ESC to close or click the back button.")
        return app_widget

    def close_current_app(self):
        print(f"MainWindow: Current running app before closing: {self.current_running_app}")
        """Close the currently running app and restore the folder interface"""
        if self.current_running_app:
            print(f"MainWindow: Closing app - {self.current_running_app}")

            # check if current app is dashboard
            if self.current_running_app == WidgetType.DASHBOARD.value:
                print("MainWindow: Closing Dashboard App Widget and cleaning up")
                self.stacked_widget.widget(1).clean_up()
            else:
                print(f"MainWindow: Closing App Widget - {self.current_running_app}")

            # Switch back to the folder view (index 0)
            self.stacked_widget.setCurrentIndex(0)

            # Remove the app widget
            if self.stacked_widget.count() > 1:
                app_widget = self.stacked_widget.widget(1)
                self.stacked_widget.removeWidget(app_widget)
                app_widget.deleteLater()

            # Close the app in the folder if needed
            if self.current_app_folder:
                self.current_app_folder.close_app()

            # Clear the running app info
            self.current_running_app = None
            self.current_app_folder = None


    def setup_ui(self):
        self.setWindowTitle("Android-Style App Folder Demo with QStackedWidget")
        # Set reasonable window size instead of maximized
        self.resize(1200, 800)  # Reasonable default size
        # Center the window on screen
        self.center_on_screen()
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(248, 250, 252, 1),
                    stop:1 rgba(241, 245, 249, 1));
            }
        """)

        # Create main layout for the window
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # --- Machine indicator toolbar at the very top ---
        screen_width = QApplication.primaryScreen().size().width()
        screen_height = QApplication.primaryScreen().size().height()
        self.header = Header(screen_width,
                             screen_height,
                             toggle_menu_callback=None,
                             dashboard_button_callback=None)
        self.header.menu_button.setVisible(False)
        self.header.dashboardButton.setVisible(False)
        self.header.power_toggle_button.setVisible(False)
        self.header.user_account_clicked.connect(self.show_session_info_widget)

        machine_toolbar_frame = QFrame()
        machine_toolbar_frame.setFrameShape(QFrame.Shape.StyledPanel)
        machine_toolbar_frame.setStyleSheet("background-color: #FFFBFE; border: 1px solid #E7E0EC;")
        machine_toolbar_layout = QVBoxLayout(machine_toolbar_frame)
        machine_toolbar_layout.setContentsMargins(5, 5, 5, 5)
        machine_toolbar_layout.addWidget(self.header)

        main_layout.addWidget(machine_toolbar_frame)

        # Create the stacked widget
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Create and add the folders page (index 0)
        self.create_folders_page()

        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Initialize translations after UI is created
        self.init_translations()
        self.retranslate()

    def create_folders_page(self):
        """Create and configure the folders page"""


        def translate_fn(translation_key):
            return self.tr(translation_key)

        folder_config_list = [
            FolderConfig(
                ID=1,
                name=self.tr(TranslationKeys.Navigation.WORK),
                apps=[[WidgetType.DASHBOARD, DASHBOARD_ICON],
                      [WidgetType.CREATE_WORKPIECE_OPTIONS, CREATE_WORKPIECE_ICON],
                      [WidgetType.GALLERY, GALLERY_ICON]],
                translate_fn=lambda _: translate_fn(TranslationKeys.Navigation.WORK)
            ),
            FolderConfig(
                ID=2,
                name=self.tr(TranslationKeys.Navigation.SERVICE),
                apps=[[WidgetType.SETTINGS, SETTINGS_ICON],
                      [WidgetType.CALIBRATION, CALIBRATION_ICON],
                      [WidgetType.GLUE_WEIGHT_CELL,GLUE_WEIGHT_CELL_ICON]],
                      # [WidgetType.SERVICE, SETTINGS_ICON]],
                translate_fn=lambda _: translate_fn(TranslationKeys.Navigation.SERVICE)
            ),
            FolderConfig(
                ID=3,
                name=self.tr(TranslationKeys.Navigation.ADMINISTRATION),
                apps=[[WidgetType.USER_MANAGEMENT, USER_MANAGEMENT_ICON]],
                translate_fn=lambda _: translate_fn(TranslationKeys.Navigation.ADMINISTRATION)
            ),
            # FolderConfig(
            #     ID=4,
            #     name=self.tr(TranslationKeys.Navigation.STATISTICS),
            #     apps=[[WidgetType.ANALYTICS, PLACEHOLDER_ICON],
            #           [WidgetType.REPORTS, PLACEHOLDER_ICON],
            #           [WidgetType.METRICS, PLACEHOLDER_ICON]],
            #     translate_fn=lambda _: translate_fn(TranslationKeys.Navigation.STATISTICS)
            # )
        ]

        if self.folders_page:
            self.stacked_widget.removeWidget(self.folders_page)
            self.folders_page.deleteLater()

        self.folders_page = FoldersPage(folder_config_list=folder_config_list, main_window=self)

        # Connect signals from the folders page
        self.folders_page.folder_opened.connect(self.on_folder_opened)
        self.folders_page.folder_closed.connect(self.on_folder_closed)
        self.folders_page.app_selected.connect(self.on_app_selected)
        self.folders_page.close_current_app_requested.connect(self.close_current_app)

        # Add the folders page to the stacked widget (index 0)
        self.stacked_widget.addWidget(self.folders_page)

    def retranslate(self):
        """Handle language change events - called automatically"""
        # Update existing folder titles instead of recreating everything
        if hasattr(self, 'folders_page') and self.folders_page:
            # Get all folder widgets and update their titles
            for folder_widget in self.folders_page.get_folder_widgets():
                if hasattr(folder_widget, 'update_title_label'):
                    folder_widget.update_title_label()

    def center_on_screen(self):
        """Center the window on the screen"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())

    def resizeEvent(self, event):
        """Handle window resize to maintain proper layout"""
        super().resizeEvent(event)
        # The responsive folders will handle their own sizing

    def sizeHint(self):
        """Provide a reasonable size hint for the window"""
        # Calculate size based on folder grid (3x2) plus margins
        folder_size = 350  # Approximate folder width
        spacing = 30
        margins = 80  # Total margins (40 on each side)

        width = (folder_size * 3) + (spacing * 2) + margins
        height = (folder_size * 2) + spacing + margins

        return self.size() if hasattr(self, '_initialized') else self.size()

    def keyPressEvent(self, event):
        """Handle key press events"""
        # ESC key to close current app (for demo purposes)
        if event.key() == Qt.Key.Key_Escape and self.current_running_app:
            self.close_current_app()
        super().keyPressEvent(event)

    def create_workpiece_via_camera_selected(self):
        """Handle camera selection for workpiece creation"""
        print("Create Workpiece via Camera selected")
        result,message = self.controller.handle(workpiece_endpoints.WORKPIECE_CREATE_STEP_1)
        if not result:
            # show warning message box
            QMessageBox.warning(self, "Camera Error", f"Failed to start camera:\n{message}")
            print(f"Failed to start camera for workpiece creation: {message}")
            return
        else:
            print(f"Result of create workpiece step 1 req: {result}, message: {message}")


        self.contour_editor = self.show_app(WidgetType.CONTOUR_EDITOR.value)

    def create_workpiece_via_dxf_selected(self):
        """Handle DXF selection for workpiece creation"""
        self.show_app(WidgetType.DXF_BROWSER.value)

    def onLogEvent(self):
        user = SessionManager.get_current_user()
        if not user:
            raise ValueError("No user logged in")

        try:
            self.session_info_drawer.update_info()
        except Exception:
            pass

        # Permissions → Folder IDs mapping
        permission_to_folder_id = {
            Permission.VIEW_WORK_FOLDER: 1,
            Permission.VIEW_SERVICE_FOLDER: 2,
            Permission.VIEW_ADMIN_FOLDER: 3,
            Permission.VIEW_STATS_FOLDER: 4,
        }

        # Enable/disable folders based on authorization
        for permission, folder_id in permission_to_folder_id.items():
            if self.auth_service.can_view(user, permission):
                print(f"Enabling {permission.name} for {user.role.name}")
                self.folders_page.enable_folder_by_id(folder_id)
            else:
                print(f"Disabling {permission.name} for {user.role.name}")
                self.folders_page.disable_folder_by_id(folder_id)

        print(f"User '{user.firstName}' with role '{user.role}' logged in.")
        from modules.shared.MessageBroker import MessageBroker
        broker=MessageBroker()
        broker.publish("vison-auto-brightness","start")
        print("Log event triggered in ApplicationDemo")

    def lock(self):
        """Lock the GUI to prevent interaction"""
        self.setEnabled(False)
        print("GUI locked")

    def unlock(self):
        """Unlock the GUI to allow interaction"""
        self.setEnabled(True)
        print("GUI unlocked")

    def onDxfBrowserSubmit(self, file_name, thumbnail):
        if not file_name:
            return
        print("DXF_DIRECTORY:", DXF_DIRECTORY)
        print(f"DXF file selected: {file_name}")

        file_name = file_name  # Assume single select for now
        extractor = DXFPathExtractor(os.path.join(DXF_DIRECTORY, file_name))

        wp_contour, spray, fill = extractor.get_opencv_contours()
        print("Extracted Contours:", spray)

        # Calibration data: convert DXF coordinates (mm) to pixels
        pixels_per_mm = 0.987
        mm_per_pixel = 1 / pixels_per_mm  # ≈ 1.015

        # Scale factors to convert from mm to pixels
        scale_x = pixels_per_mm  # 0.985 pixels per mm
        scale_y = pixels_per_mm  # 0.985 pixels per mm

        # scale_x, scale_y = 1,1 # TODO placeholder until we have real scale from DXF

        print(f"Computed mm to pixel scale: scale_x={scale_x}, scale_y={scale_y}")

        wp_contour = scale_contours(wp_contour, scale_x, scale_y)
        spray = scale_contours(spray, scale_x, scale_y)
        fill = scale_contours(fill, scale_x, scale_y)

        print("Extracted Contours after scale:", spray)

        # SHOW AND SETUP CONTOUR EDITOR
        self.contour_editor = self.show_app(WidgetType.CONTOUR_EDITOR.value)

        # Create the image
        image = create_light_gray_pixmap()
        image = qpixmap_to_cv(image)

        # Set up the contour editor
        self.contour_editor.set_image(image)

        # Prepare dictionary for initContour (layer -> contours)
        contours_by_layer = {
            "Workpiece": [wp_contour] if wp_contour is not None and len(wp_contour) > 0 else [],
            "Contour": spray if len(spray) > 0 else [],
            "Fill": fill if len(fill) > 0 else []
        }

        # Initialize contours in the editor
        self.contour_editor.init_contours(contours_by_layer)

        # Set up the callback with proper error checking
        def set_callback():
            self.contour_editor.set_create_workpiece_for_on_submit_callback(self.onCreateWorkpieceSubmitDxf)
            print("DXF callback set successfully")

        QTimer.singleShot(100, set_callback)

    def onCreateWorkpieceSubmitDxf(self, data):
        """Handle DXF workpiece form submission - mirrors camera workflow"""
        print("onCreateWorkpieceSubmitDxf called with data:", data)

        wp_contours_data = self.contour_editor.to_wp_data()

        print("WP Contours Data: ", wp_contours_data)
        print("WP form data: ", data)

        sprayPatternsDict = {
            "Contour": [],
            "Fill": []
        }

        sprayPatternsDict['Contour'] = wp_contours_data.get('Contour', [])
        sprayPatternsDict['Fill'] = wp_contours_data.get('Fill', [])

        from modules.shared.core.workpiece.Workpiece import WorkpieceField

        data[WorkpieceField.SPRAY_PATTERN.value] = sprayPatternsDict
        data[WorkpieceField.CONTOUR.value] = wp_contours_data.get('Workpiece', [])
        data[WorkpieceField.CONTOUR_AREA.value] = 0  # PLACEHOLDER NEED TO CALCULATE AREA

        # Save the workpiece using DXF endpoint
        print("Saving DXF workpiece with data:", data)
        self.controller.handle(workpiece_endpoints.WORKPIECE_SAVE, data)
        print("DXF workpiece saved successfully")

    def onLogout(self):
        """Handle logout action"""
        print("Logout action triggered")
        # Perform logout logic here
        # For example, clear session data, redirect to login screen, etc.
        SessionManager.logout()
        print("User logged out successfully")
        # Show login window fullscreen (non-blocking)
        login = LoginWindow(self.controller, onLogEventCallback=self.onLogEvent, header=self.header)
        login.showFullScreen()
        self.setEnabled(False)
        # Block here until login window returns
        if login.exec():
            print("Logged in successfully")
            self.setEnabled(True)  # Re-enable after successful login
            self.onLogEvent()
        else:
            print("Login failed or cancelled")
            return  # You could also call self.close() or sys.exit() if needed

        self.onLogEvent()
        # Optionally, you can close the application or redirect to a login screen

    def show_session_info_widget(self):
        """Toggle the session info drawer with proper state management"""
        # Create drawer on first use
        if not hasattr(self, 'session_info_drawer') or self.session_info_drawer is None:
            from frontend.widgets.SessionInfoWidget import SessionInfoWidget
            self.session_info_drawer = SessionInfoWidget(self, onLogoutCallback=self.onLogout)
            self.session_info_drawer.setFixedWidth(300)
            self.session_info_drawer.heightOffset = self.header.height()  # Account for header height

        # Update session info and resize to current parent height
        self.session_info_drawer.update_info()
        self.session_info_drawer.resize_to_parent_height()

        # Toggle the drawer
        self.session_info_drawer.toggle()

    def setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts for the application"""
        # TCP Offset Dialog shortcut - Ctrl+T
        self.tcp_offset_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        self.tcp_offset_shortcut.activated.connect(self.show_tcp_offset_dialog)
        
        # Alternative shortcut - Ctrl+Shift+T for even faster access
        self.tcp_offset_shortcut_alt = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        self.tcp_offset_shortcut_alt.activated.connect(self.show_tcp_offset_dialog)
        
        print("🔧 TCP Offset keyboard shortcuts setup: Ctrl+T or Ctrl+Shift+T")

    def show_tcp_offset_dialog(self):
        """Show the TCP offset configuration dialog"""
        try:
            from frontend.dialogs.TcpOffsetDialog import show_tcp_offset_dialog
            
            # Show the dialog with this window as parent
            dialog = show_tcp_offset_dialog(self)
            
            # Connect the signal to handle updates
            dialog.tcp_offsets_updated.connect(self.on_tcp_offsets_updated)
            
            print("📍 TCP Offset dialog opened")
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to open TCP Offset dialog:\n{str(e)}"
            )
            print(f"Error opening TCP offset dialog: {e}")

    def on_tcp_offsets_updated(self, tcp_x, tcp_y):
        """Handle TCP offsets being updated"""
        print(f"📍 TCP Offsets updated: X={tcp_x:.3f}mm, Y={tcp_y:.3f}mm")
        
        # Send update request to robot controller if available
        try:
            self.controller.handle(robot_endpoints.ROBOT_UPDATE_CONFIG)
            print("🤖 Robot configuration update request sent")
        except Exception as e:
            print(f"Warning: Could not send robot config update: {e}")
    
    def cleanup(self):
        """Cleanup resources when main window is closed"""
        try:
            print("MainWindow: Cleaning up plugin system...")
            if hasattr(self, 'plugin_widget_factory'):
                self.plugin_widget_factory.cleanup()
            print("MainWindow: Cleanup complete")
        except Exception as e:
            print(f"Error during MainWindow cleanup: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.cleanup()
        super().closeEvent(event)


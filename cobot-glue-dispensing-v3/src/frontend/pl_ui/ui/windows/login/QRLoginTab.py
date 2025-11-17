from typing import Any, Callable, Optional

from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout

from modules.shared.v1 import Constants
from frontend.pl_ui.localization import TranslationKeys, TranslatableWidget
from frontend.pl_ui.ui.widgets.CameraFeed import CameraFeed,CameraFeedConfig
from frontend.pl_ui.ui.widgets.MaterialButton import MaterialButton
from frontend.pl_ui.utils.IconLoader import LOGIN_QR_BUTTON
from modules.shared.v1.endpoints import camera_endpoints,auth_endpoints


class QRLoginTab(TranslatableWidget):
    """QR code login tab"""

    # Emits (user_id: str, password: str) when a QR login succeeds
    login_requested = pyqtSignal(str, str)

    def __init__(
        self,
        controller: Any,  # could be narrowed if you define an interface/protocol
        on_login_callback: Optional[Callable[[str, str], None]],
        parent=None
    ) -> None:
        super().__init__(parent, auto_retranslate=False)
        self.controller: Any = controller
        self.on_login_callback: Optional[Callable[[str, str], None]] = on_login_callback
        self.font_small: QFont = QFont("Arial", 14)
        self.qr_label: Optional[QLabel] = None
        self.camera_feed: Optional[CameraFeed] = None
        self.qr_button: Optional[QPushButton] = None
        
        # QR detection timer for automatic scanning
        self.qr_timer: QTimer = QTimer()
        self.qr_timer.timeout.connect(self.check_for_qr_code)
        self.qr_scanning_active: bool = False
        
        self.setup_ui()
        
        # Initialize translations after UI is created
        self.init_translations()
        
        # Start automatic QR scanning
        self.start_automatic_qr_scanning()

    def setup_ui(self) -> None:
        """Initialize UI layout and widgets."""
        # Stop contour detection when initializing QR tab
        self.controller.handle(camera_endpoints.STOP_CONTOUR_DETECTION)

        layout: QVBoxLayout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Create label without text - text will be set in retranslate()
        self.qr_label = QLabel()
        self.qr_label.setFont(self.font_small)
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.qr_label)

        layout.addStretch(1)

        # Add CameraFeed widget
        camera_feed_config = CameraFeedConfig(
            updateFrequency=30,
            screen_size=(640,360),
            resolution_small=(640,360),
            resolution_large=(640,360),
            current_resolution=(640,360)
        )
        self.camera_feed = CameraFeed(
            cameraFeedConfig=camera_feed_config,
            updateCallback=self.get_camera_frame,
            toggleCallback=None
        )
        layout.addWidget(self.camera_feed, alignment=Qt.AlignmentFlag.AlignCenter)

        # add stretch to push elements to top
        layout.addStretch(1)

        # Login button - hidden since we use automatic scanning
        # Keeping for backward compatibility but hiding it
        self.qr_button = MaterialButton(text=self.tr(TranslationKeys.Auth.LOGIN))
        self.qr_button.clicked.connect(self.handle_qr_code)
        self.qr_button.setVisible(False)  # Hide the button - automatic scanning handles login
        layout.addWidget(self.qr_button)

        self.setLayout(layout)

    def get_camera_frame(self) -> Any:
        """Get camera frame for the camera feed."""
        return self.controller.handle(camera_endpoints.UPDATE_CAMERA_FEED)

    def handle_qr_code(self) -> None:
        """Handle QR code scanning and login."""
        self.controller.handle(camera_endpoints.START_CONTOUR_DETECTION)

        response: Any = self.controller.handle(auth_endpoints.QR_LOGIN)
        if response is None:
            raise ValueError("No response from QR login endpoint")

        if response.status == Constants.RESPONSE_STATUS_SUCCESS:
            user_data: dict[str, str] = response.data
            user_id: str = user_data.get("id", "")
            password: str = user_data.get("password", "")
            # self.login_requested.emit(user_id, password)
            self.on_login_callback(user_id, password)  # deprecated in favor of signal
        else:
            print("Failed to retrieve QR code data:", response)

    def start_automatic_qr_scanning(self) -> None:
        """Start automatic QR code detection."""
        if not self.qr_scanning_active:
            print("Starting automatic QR scanning...")
            self.controller.handle(camera_endpoints.START_CONTOUR_DETECTION)
            self.qr_scanning_active = True
            # Check for QR codes every 2 seconds
            self.qr_timer.start(2000)
            
            # Update label to show automatic scanning status
            if self.qr_label:
                self.qr_label.setText(self.tr(TranslationKeys.Auth.SCAN_QR_TO_LOGIN))

    def check_for_qr_code(self) -> None:
        """Automatically check for QR codes and login if found."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] ===== check_for_qr_code CALLED =====")
        print(f"[{timestamp}] qr_scanning_active: {self.qr_scanning_active}")
        print(f"[{timestamp}] qr_timer.isActive(): {self.qr_timer.isActive()}")
        
        # First check: if scanning is no longer active, exit immediately
        if not self.qr_scanning_active:
            print(f"[{timestamp}] QR scanning not active - exiting check_for_qr_code")
            return
            
        # Second check: if timer is not active, exit immediately  
        if not self.qr_timer.isActive():
            print(f"[{timestamp}] QR timer not active - exiting check_for_qr_code")
            self.qr_scanning_active = False
            return
            
        try:
            # Only proceed if we're still supposed to be scanning
            if not self.qr_scanning_active:
                print(f"[{timestamp}] QR scanning became inactive during method - returning")
                return
                
            print(f"[{timestamp}] Calling controller.handle(QR_LOGIN)...")
            response: Any = self.controller.handle(auth_endpoints.QR_LOGIN)
            if response is None:
                print(f"[{timestamp}] QR_LOGIN response is None")
                return

            print(f"[{timestamp}] QR_LOGIN response status: {response.status}")
            if response.status == Constants.RESPONSE_STATUS_SUCCESS:
                # QR code detected and login successful
                print(f"[{timestamp}] QR code detected - logging in automatically!")
                
                # IMMEDIATELY stop all scanning activities
                self._emergency_stop_scanning()
                
                # Process login
                user_data: dict[str, str] = response.data
                user_id: str = user_data.get("id", "")
                password: str = user_data.get("password", "")
                
                if self.on_login_callback:
                    print(f"[{timestamp}] Calling login callback...")
                    self.on_login_callback(user_id, password)
                
                # Return immediately to prevent any further processing
                print(f"[{timestamp}] Login successful - returning from check_for_qr_code")
                return
                    
            # If no QR code detected, continue scanning (response status != success)
            # But only if we're still supposed to be scanning
            if not self.qr_scanning_active:
                print(f"[{timestamp}] QR scanning became inactive - returning")
                return
            
            print(f"[{timestamp}] No QR code found - continuing scanning")
            
        except Exception as e:
            print(f"[{timestamp}] Error during automatic QR scanning: {e}")
            # On error, stop scanning to prevent endless errors
            self._emergency_stop_scanning()
    
    def _emergency_stop_scanning(self) -> None:
        """Emergency stop for all scanning activities."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] ===== EMERGENCY STOP: Stopping all QR scanning activities immediately =====")
        
        # Stop timer with force
        if hasattr(self, 'qr_timer'):
            was_active = self.qr_timer.isActive()
            self.qr_timer.stop()
            print(f"[{timestamp}] QR timer force stopped (was_active: {was_active}, is_active_now: {self.qr_timer.isActive()})")
        
        # Set scanning flag to false
        old_flag = self.qr_scanning_active
        self.qr_scanning_active = False
        print(f"[{timestamp}] QR scanning flag set to False (was: {old_flag}, now: {self.qr_scanning_active})")
        
        # Stop contour detection completely
        try:
            self.controller.handle(camera_endpoints.STOP_CONTOUR_DETECTION)
            print(f"[{timestamp}] Contour detection stopped during emergency stop")
        except Exception as e:
            print(f"[{timestamp}] Error stopping contour detection: {e}")
        
        # Disconnect timer signal to prevent any delayed calls
        try:
            self.qr_timer.timeout.disconnect()
            self.qr_timer.timeout.connect(self.check_for_qr_code)
            print(f"[{timestamp}] Timer signal disconnected and reconnected after emergency stop")
        except Exception as e:
            print(f"[{timestamp}] Error handling timer signals: {e}")
            
        print(f"[{timestamp}] ===== EMERGENCY STOP COMPLETED =====")

    def stop_automatic_qr_scanning(self) -> None:
        """Stop automatic QR code detection."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] stop_automatic_qr_scanning called")
        if self.qr_scanning_active:
            print(f"[{timestamp}] Stopping automatic QR scanning...")
            self.qr_timer.stop()
            self.qr_scanning_active = False
            self.controller.handle(camera_endpoints.STOP_CONTOUR_DETECTION)
            print(f"[{timestamp}] QR scanning stopped successfully")
        else:
            print(f"[{timestamp}] QR scanning was already inactive")
    
    def force_stop_scanning(self) -> None:
        """Force stop scanning - called when login succeeds through any method."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] ===== FORCE STOP SCANNING CALLED =====")
        print(f"[{timestamp}] Current state - scanning_active: {self.qr_scanning_active}, timer_active: {self.qr_timer.isActive()}")
        
        # Use emergency stop to ensure everything is cleaned up
        self._emergency_stop_scanning()
        
        print(f"[{timestamp}] ===== FORCE STOP SCANNING COMPLETED =====")
    
    def closeEvent(self, event) -> None:
        """Handle widget close event - ensure timer is stopped."""
        print("QR Login Tab closing - cleaning up...")
        self.cleanup()
        super().closeEvent(event)
    
    def cleanup(self) -> None:
        """Clean up resources when widget is destroyed."""
        print("QR Login Tab cleanup - stopping all scanning activities...")
        if hasattr(self, 'qr_timer') and self.qr_timer.isActive():
            self.qr_timer.stop()
            print("QR timer stopped during cleanup")
        
        if hasattr(self, 'qr_scanning_active'):
            self.qr_scanning_active = False
        
        # Stop contour detection
        if hasattr(self, 'controller'):
            self.controller.handle(camera_endpoints.STOP_CONTOUR_DETECTION)
            print("Contour detection stopped during cleanup")
    
    def __del__(self) -> None:
        """Destructor - ensure cleanup when object is destroyed."""
        try:
            self.cleanup()
        except Exception as e:
            print(f"Error during QR login cleanup: {e}")

    def retranslate(self) -> None:
        """Update all text labels for language changes - called automatically"""
        if self.qr_label:
            self.qr_label.setText(self.tr(TranslationKeys.Auth.SCAN_QR_TO_LOGIN))

        if self.qr_button:
            self.qr_button.setText(self.tr(TranslationKeys.Auth.LOGIN))

    def resize_elements(self, window_width: int, window_height: int) -> None:
        """Handle responsive design for button sizing."""
        button_width: int = max(160, min(int(window_width * 0.3), 300))
        button_height: int = max(70, min(int(window_height * 0.15), 120))
        icon_size: QSize = QSize(
            max(60, min(int(window_width * 0.12), 100)),
            max(60, min(int(window_width * 0.12), 100))
        )

        # if self.qr_button:
        #     self.qr_button.setFixedSize(button_width, button_height)
        #     self.qr_button.setIconSize(icon_size)

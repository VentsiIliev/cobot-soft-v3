from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QShortcut, QKeySequence

from frontend.pl_ui.contour_editor import constants


class SettingsManager:
    def __init__(self, editor):
        self.editor = editor
        
        # Load and apply initial settings
        self.load_initial_settings()
        
        # Setup settings-related UI
        self.setup_settings_shortcuts()
        
        # Initialize cached constants
        self.setup_cached_constants()
    
    def load_initial_settings(self):
        """Load user settings from JSON and apply to constants"""
        from pl_ui.contour_editor.ConstantsManager import ConstantsManager
        settings = ConstantsManager.load_settings()
        ConstantsManager.apply_settings(settings)
    
    def setup_settings_shortcuts(self):
        """Setup keyboard shortcuts for settings"""
        # Settings dialog shortcut (Ctrl+S)
        self.settings_shortcut = QShortcut(QKeySequence("Ctrl+S"), self.editor)
        self.settings_shortcut.activated.connect(self.open_settings_dialog)
    
    def setup_cached_constants(self):
        """Initialize cached constants from the constants module"""
        self.handle_radius = constants.POINT_HANDLE_RADIUS
        self.handle_color = constants.POINT_HANDLE_COLOR
        self.handle_selected_color = constants.POINT_HANDLE_SELECTED_COLOR
        self.min_point_display_scale = constants.POINT_MIN_DISPLAY_SCALE
        self.cluster_distance_px = constants.CLUSTER_DISTANCE_PX
    
    def open_settings_dialog(self):
        """Open the constants settings dialog (Ctrl+S)"""
        from pl_ui.contour_editor.widgets.ConstantsSettingsDialog import ConstantsSettingsDialog

        dialog = ConstantsSettingsDialog(self.editor)
        result = dialog.show()

        if result == dialog.DialogCode.Accepted:
            print("Settings dialog closed with OK")
            # Note: Settings are already applied and reloaded by the dialog's apply_changes method
    
    def reload_constants(self):
        """Reload constants that are cached as instance variables"""
        # Reload the constants module to get updated values
        from pl_ui.contour_editor import constants

        # Update cached instance variables
        self.handle_radius = constants.POINT_HANDLE_RADIUS
        self.handle_color = constants.POINT_HANDLE_COLOR
        self.handle_selected_color = constants.POINT_HANDLE_SELECTED_COLOR
        self.min_point_display_scale = constants.POINT_MIN_DISPLAY_SCALE
        self.cluster_distance_px = constants.CLUSTER_DISTANCE_PX

        # Update editor's cached values
        self.editor.handle_radius = self.handle_radius
        self.editor.handle_color = self.handle_color
        self.editor.handle_selected_color = self.handle_selected_color
        self.editor.min_point_display_scale = self.min_point_display_scale
        self.editor.cluster_distance_px = self.cluster_distance_px

        # Update timer intervals
        if hasattr(self.editor, 'drag_timer'):
            self.editor.drag_timer.setInterval(constants.DRAG_UPDATE_INTERVAL_MS)
        if hasattr(self.editor.overlay_manager, 'point_info_timer'):
            self.editor.overlay_manager.point_info_timer.setInterval(constants.POINT_INFO_HOLD_DURATION_MS)

        print("Reloaded cached constants in editor")

        # Trigger a repaint to show the changes
        self.editor.update()
    
    def show_global_settings(self):
        """Show global settings dialog"""
        from pl_ui.contour_editor.widgets.GlobalSettingsDialog import GlobalSettingsDialog
        from PyQt6.QtWidgets import QApplication
        
        if hasattr(self.editor, 'point_manager_widget') and self.editor.point_manager_widget:
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()  # QRect(x, y, width, height)
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            dialog = GlobalSettingsDialog(self.editor.point_manager_widget, parent=self.editor)
            dialog.setMinimumWidth(screen_width)
            dialog.setMinimumHeight(int(screen_height / 2))
            dialog.setMaximumHeight(int(screen_height / 2))
            # Position at top-left of the screen (x=0, y=0)
            # dialog.move(0, 0)
            dialog.adjustSize()
            dialog.show()
        else:
            print("Point manager widget not found")
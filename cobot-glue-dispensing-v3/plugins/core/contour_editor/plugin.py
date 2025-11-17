"""
Contour Editor Plugin Implementation

Main plugin class for the workpiece contour editing system.
"""

import os
from typing import Optional
from PyQt6.QtWidgets import QWidget

# Import plugin base classes
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from plugins.base.plugin_interface import IPlugin, PluginMetadata, PluginCategory, PluginPermission

# Import the contour editor widget
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../src'))
from plugins.core.contour_editor.ui.ContourEditorAppWidget import ContourEditorAppWidget


class ContourEditorPlugin(IPlugin):
    """
    Contour Editor plugin for advanced workpiece design and editing.
    
    Provides comprehensive contour editing capabilities including:
    - Interactive contour drawing and editing
    - Camera integration for workpiece capture
    - Bezier curve tools for smooth path creation
    - Workpiece save/load functionality
    """
    
    def __init__(self):
        super().__init__()
        self._widget_instance = None
    
    @property
    def metadata(self) -> PluginMetadata:
        """Plugin metadata and information"""
        return PluginMetadata(
            name="ContourEditor",
            version="1.0.0",
            author="PL Team",
            description="Advanced contour editing interface for workpiece design and modification",
            category=PluginCategory.CORE,
            dependencies=[],
            permissions=[
                PluginPermission.FILE_SYSTEM,
                PluginPermission.CAMERA_ACCESS
            ],
            auto_load=True,
            min_app_version="1.0.0"
        )
    
    @property
    def icon_path(self) -> str:
        """Path to plugin icon"""
        return os.path.join(os.path.dirname(__file__), "icons", "contour_editor.png")
    
    def initialize(self, controller_service) -> bool:
        """
        Initialize the contour editor plugin.
        
        Args:
            controller_service: Main controller service for backend operations
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.controller_service = controller_service
            self._mark_initialized(True)
            return True
        except Exception as e:
            print(f"Contour Editor plugin initialization failed: {e}")
            self._mark_initialized(False)
            return False
    
    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        Create the contour editor widget.
        
        Args:
            parent: Parent widget for the contour editor interface
            
        Returns:
            QWidget representing the contour editor interface
        """
        if not self._is_initialized:
            raise RuntimeError("Plugin not initialized")
        
        # Create widget instance if it doesn't exist
        if not self._widget_instance:
            self._widget_instance = ContourEditorAppWidget(
                parent=parent,
                controller=self.controller_service.controller  # For backward compatibility
            )
        
        return self._widget_instance
    
    def cleanup(self) -> None:
        """Cleanup plugin resources"""
        try:
            if self._widget_instance:
                # Clean up widget if it has a cleanup method
                if hasattr(self._widget_instance, 'clean_up'):
                    self._widget_instance.clean_up()
                self._widget_instance = None
            
            self.controller_service = None
            self._mark_initialized(False)
            
        except Exception as e:
            print(f"Error during contour editor plugin cleanup: {e}")
    
    def can_load(self) -> bool:
        """Check if plugin can be loaded"""
        try:
            # Check if the contour editor dependencies are available
            from frontend.contour_editor.ContourEditor import MainApplicationFrame
            return True
        except ImportError as e:
            print(f"Contour Editor plugin cannot load: missing dependency {e}")
            return False
    
    def get_status(self) -> dict:
        """Get plugin status"""
        status = super().get_status()
        status.update({
            "widget_created": self._widget_instance is not None,
            "controller_service_available": self.controller_service is not None,
            "contour_editor_available": self.can_load()
        })
        return status
    
    def get_capabilities(self) -> list:
        """Get plugin capabilities"""
        return [
            "contour_drawing",
            "bezier_editing", 
            "camera_capture",
            "workpiece_management",
            "path_optimization",
            "interactive_editing"
        ]
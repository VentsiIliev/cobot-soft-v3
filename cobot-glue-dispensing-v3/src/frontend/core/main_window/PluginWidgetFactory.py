"""
Plugin-Based Widget Factory

Replaces the hard-coded WidgetFactory with a dynamic plugin-based system.
"""

import os
import sys
import logging
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QWidget

from plugins.core.gallery.ui.GalleryAppWidget import GalleryAppWidget

# Add plugin path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from plugins.base.plugin_manager import PluginManager
from frontend.core.services.ControllerService import ControllerService
from frontend.core.shared.base_widgets.AppWidget import AppWidget
from frontend.core.main_window.WidgetFactory import WidgetType

class PluginWidgetFactory:
    """
    Plugin-based widget factory that replaces the hard-coded approach.
    
    Dynamically discovers and loads plugins to create app widgets,
    enabling a modular and extensible architecture.
    """
    
    def __init__(self, controller, main_window):
        """
        Initialize the plugin-based widget factory.
        
        Args:
            controller: Main application controller
            main_window: Reference to the main window
        """
        self.controller = controller
        self.main_window = main_window
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Create controller service for plugins
        self.controller_service = ControllerService(controller)
        
        # Initialize plugin manager
        self.plugin_manager = PluginManager(self.controller_service)
        
        # Cache for plugin widgets
        self._widget_cache: Dict[str, QWidget] = {}
        
        # Initialize plugin system
        self._setup_plugin_system()
    
    def _setup_plugin_system(self):
        """Setup and initialize the plugin system"""
        try:
            # Configure plugin directories
            base_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'plugins')
            self.logger.info(f"Plugin base directory: {base_dir}")
            
            self.plugin_manager.add_plugin_directory(os.path.join(base_dir, 'core'))
            self.plugin_manager.add_plugin_directory(os.path.join(base_dir, 'features'))
            self.plugin_manager.add_plugin_directory(os.path.join(base_dir, 'extensions'))
            
            # Set up event callbacks
            self.plugin_manager.set_event_callbacks(
                on_loaded=self._on_plugin_loaded,
                on_failed=self._on_plugin_failed
            )
            
            # Load all plugins
            results = self.plugin_manager.discover_and_load_all()
            
            self.logger.info(f"Plugin system initialized. Loaded: {len([r for r in results.values() if r])} plugins")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize plugin system: {e}", exc_info=True)
    
    def _on_plugin_loaded(self, plugin_name: str, plugin):
        """Callback when a plugin is successfully loaded"""
        self.logger.info(f"Plugin loaded: {plugin_name}")
    
    def _on_plugin_failed(self, plugin_name: str, error: Exception):
        """Callback when a plugin fails to load"""
        self.logger.error(f"Plugin failed to load: {plugin_name} - {error}")
    
    def create_widget(self, widget_type, *args, **kwargs) -> Optional[QWidget]:
        """
        Create a widget using the plugin system.
        
        Args:
            widget_type: Type of widget to create (can be WidgetType enum or string)
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Widget instance or None if not found
        """
        try:
            # Convert widget type to string if it's an enum
            if hasattr(widget_type, 'value'):
                app_name = widget_type.value
            else:
                app_name = str(widget_type)
            
            self.logger.info(f"Creating widget for: {app_name}")
            
            # Try to create widget from plugin first
            plugin_widget = self._create_plugin_widget(app_name, *args, **kwargs)
            if plugin_widget:
                print(f"Created plugin widget for: {app_name}")
                return plugin_widget
            
            # Fallback to legacy widget creation for widgets not yet migrated
            legacy_widget = self._create_legacy_widget(app_name, *args, **kwargs)
            if legacy_widget:
                print(f"Created legacy widget for: {app_name}")
                return legacy_widget
            
            # Ultimate fallback to default widget
            self.logger.warning(f"No plugin or legacy widget found for: {app_name}")
            return AppWidget(app_name=f"Default Widget ({app_name})")
            
        except Exception as e:
            self.logger.error(f"Error creating widget for {widget_type}: {e}", exc_info=True)
            return AppWidget(app_name="Error Widget")
    
    def _create_plugin_widget(self, app_name: str, *args, **kwargs) -> Optional[QWidget]:
        """
        Create widget from plugin system.
        
        Args:
            app_name: Name of the app/plugin
            *args: Additional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Plugin widget or None if not found
        """
        try:
            # Map WidgetType enum values to plugin names
            plugin_name_map = {
                WidgetType.SETTINGS.value: 'Settings',
                WidgetType.DASHBOARD.value: 'Dashboard',
                WidgetType.GALLERY.value: 'Gallery',
                WidgetType.CALIBRATION.value: 'Calibration',
                WidgetType.USER_MANAGEMENT.value: 'User Management',
                WidgetType.CONTOUR_EDITOR.value: 'ContourEditor',
                WidgetType.CREATE_WORKPIECE_OPTIONS.value: 'CreateWorkpiece',
                WidgetType.GLUE_WEIGHT_CELL.value: 'Glue Weight Cell Settings',
                WidgetType.DXF_BROWSER.value: 'DxfBrowser'
            }
            
            plugin_name = plugin_name_map.get(app_name.lower(), app_name)

            # Debug logging
            self.logger.info(f"Looking for plugin: {plugin_name} (from app_name: {app_name})")
            loaded_plugins = self.plugin_manager.get_loaded_plugin_names()
            self.logger.info(f"Available plugins: {loaded_plugins}")
            
            # Get plugin from manager
            plugin = self.plugin_manager.get_plugin(plugin_name)
            if not plugin:
                self.logger.debug(f"No plugin found for: {plugin_name}")
                return None
            
            # Create widget from plugin
            widget = plugin.create_widget(parent=self.main_window)
            self.logger.info(f"Created plugin widget: {plugin_name}")
            
            return widget
            
        except Exception as e:
            self.logger.error(f"Error creating plugin widget for {app_name}: {e}")
            return None
    
    def _create_legacy_widget(self, app_name: str, *args, **kwargs) -> Optional[QWidget]:
        """
        Create widget using legacy factory methods for widgets not yet migrated.
        
        Args:
            app_name: Name of the app
            *args: Additional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Legacy widget or None if not supported
        """
        try:
            # Legacy widget creation for non-migrated widgets using WidgetType enum
            legacy_methods = {

                WidgetType.CREATE_WORKPIECE_OPTIONS.value: self._create_legacy_create_workpiece,
                WidgetType.DXF_BROWSER.value: self._create_legacy_dxf_browser
            }
            
            method = legacy_methods.get(app_name.lower())
            if method:
                widget = method(*args, **kwargs)
                self.logger.info(f"Created legacy widget: {app_name}")
                return widget
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating legacy widget for {app_name}: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    # Legacy widget creation methods (gradually remove as plugins are created)


    def _create_legacy_create_workpiece(self, *args, **kwargs):
        """Create legacy create workpiece widget"""
        from frontend.legacy_ui.app_widgets.CreateWorkpieceOptionsAppWidget import CreateWorkpieceOptionsAppWidget
        return CreateWorkpieceOptionsAppWidget(controller=self.controller)

    
    def _create_legacy_dxf_browser(self, *args, **kwargs):
        """Create legacy DXF browser widget"""
        return GalleryAppWidget(*args, **kwargs)

    def get_available_apps(self) -> Dict[str, Dict[str, Any]]:
        """
        Get list of available apps/plugins.
        
        Returns:
            Dictionary mapping app names to their information
        """
        apps = {}
        
        # Get loaded plugins
        for plugin_name in self.plugin_manager.get_loaded_plugin_names():
            plugin = self.plugin_manager.get_plugin(plugin_name)
            if plugin:
                apps[plugin_name.lower()] = {
                    'name': plugin.metadata.name,
                    'description': plugin.metadata.description,
                    'icon_path': plugin.icon_path,
                    'category': plugin.metadata.category.value,
                    'version': plugin.metadata.version
                }
        
        # Add legacy apps that haven't been migrated yet using WidgetType enum
        legacy_apps = {
            WidgetType.DASHBOARD.value: {'name': 'Dashboard', 'description': 'Main dashboard', 'category': 'core'},

            WidgetType.CONTOUR_EDITOR.value: {'name': 'Contour Editor', 'description': 'Contour editing', 'category': 'feature'},
            WidgetType.CREATE_WORKPIECE_OPTIONS.value: {'name': 'Create Workpiece', 'description': 'Create workpiece', 'category': 'feature'},
            WidgetType.DXF_BROWSER.value: {'name': 'DXF Browser', 'description': 'DXF file browser', 'category': 'tool'}
        }
        
        for app_name, info in legacy_apps.items():
            if app_name not in apps:  # Only add if not already loaded as plugin
                apps[app_name] = info
        
        return apps
    
    def cleanup(self):
        """Cleanup the plugin system"""
        try:
            self.plugin_manager.cleanup_all()
            self._widget_cache.clear()
            self.logger.info("Plugin widget factory cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_plugin_system_status(self) -> Dict[str, Any]:
        """Get plugin system status for debugging"""
        return self.plugin_manager.get_system_status()
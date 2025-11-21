"""
Application Context Manager

This module provides a global context for the current running application,
allowing base services to access application-specific core settings.
"""

import threading
from typing import Optional
from backend.system.utils.ApplicationStorageResolver import get_application_storage_resolver


class ApplicationContext:
    """
    Global context manager for the current running application.
    
    This class provides a thread-safe way to set and get the current
    application name, allowing base services to access core settings
    from the correct application storage location.
    """
    
    _instance: Optional['ApplicationContext'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        """Initialize the application context."""
        self._current_app_name: Optional[str] = None
        self._app_lock = threading.Lock()
        self._storage_resolver = get_application_storage_resolver()
    
    def set_current_application(self, app_name: str) -> None:
        """
        Set the current running application.
        
        Args:
            app_name: Name of the current application (e.g., 'glue_dispensing_application')
        """
        with self._app_lock:
            self._current_app_name = app_name
            print(f"ApplicationContext: Current application set to '{app_name}'")
    
    def get_current_application(self) -> Optional[str]:
        """
        Get the current running application name.
        
        Returns:
            str or None: The current application name, or None if not set
        """
        with self._app_lock:
            return self._current_app_name
    
    def get_core_settings_path(self, settings_filename: str, create_if_missing: bool = False) -> Optional[str]:
        """
        Get the path to a core settings file in the current application's storage.
        
        Core settings are settings that all applications need (camera_settings.json, robot_config.json).
        
        Args:
            settings_filename: Name of the settings file (e.g., 'camera_settings.json')
            create_if_missing: Whether to create directories if they don't exist
            
        Returns:
            str or None: Full path to the core settings file, or None if no application is set
        """
        current_app = self.get_current_application()
        if current_app is None:
            print(f"ApplicationContext: No current application set, cannot get core settings path for '{settings_filename}'")
            return None
        
        # Extract settings type from filename (remove .json extension)
        settings_type = settings_filename.replace('.json', '')
        
        settings_path = self._storage_resolver.get_settings_path(
            current_app, settings_type, create_if_missing
        )
        
        return settings_path
    
    def is_application_set(self) -> bool:
        """
        Check if a current application has been set.
        
        Returns:
            bool: True if an application is set, False otherwise
        """
        return self.get_current_application() is not None


class ApplicationContextSingleton:
    """Singleton wrapper for ApplicationContext."""
    
    _instance: Optional[ApplicationContext] = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> ApplicationContext:
        """
        Get the singleton ApplicationContext instance.
        
        Returns:
            ApplicationContext: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = ApplicationContext()
        return cls._instance


# Convenience functions
def set_current_application(app_name: str) -> None:
    """
    Set the current running application.
    
    Args:
        app_name: Name of the current application
    """
    context = ApplicationContextSingleton.get_instance()
    context.set_current_application(app_name)


def get_current_application() -> Optional[str]:
    """
    Get the current running application name.
    
    Returns:
        str or None: The current application name
    """
    context = ApplicationContextSingleton.get_instance()
    return context.get_current_application()


def get_core_settings_path(settings_filename: str, create_if_missing: bool = False) -> Optional[str]:
    """
    Get the path to a core settings file in the current application's storage.
    
    Args:
        settings_filename: Name of the settings file (e.g., 'camera_settings.json')
        create_if_missing: Whether to create directories if they don't exist
        
    Returns:
        str or None: Full path to the core settings file
    """
    context = ApplicationContextSingleton.get_instance()
    return context.get_core_settings_path(settings_filename, create_if_missing)


def is_application_context_set() -> bool:
    """
    Check if a current application has been set.
    
    Returns:
        bool: True if an application is set, False otherwise
    """
    context = ApplicationContextSingleton.get_instance()
    return context.is_application_set()


if __name__ == "__main__":
    # Test the application context
    print("=== ApplicationContext Test ===")
    
    # Test setting application
    set_current_application("glue_dispensing_application")
    print(f"Current application: {get_current_application()}")
    
    # Test getting core settings paths
    camera_path = get_core_settings_path("camera_settings.json")
    robot_path = get_core_settings_path("robot_config.json")
    
    print(f"Camera settings path: {camera_path}")
    print(f"Robot config path: {robot_path}")
    
    # Test context check
    print(f"Is context set: {is_application_context_set()}")
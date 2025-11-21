"""
Application Storage Resolver

This module provides application-specific storage path resolution,
allowing each application to have its own isolated storage structure
while maintaining consistency across the system.
"""

import os
from pathlib import Path
from typing import Optional, List
from backend.system.utils.PathResolver import PathResolver, PathType


class ApplicationStorageResolver:
    """
    Resolver for application-specific storage paths.
    
    This class provides a clean interface for getting storage paths
    for different applications, ensuring each app has its own isolated
    storage space.
    """
    
    def __init__(self):
        """Initialize the application storage resolver."""
        self.path_resolver = PathResolver()
        self._project_root = self.path_resolver.get_path(PathType.PROJECT_ROOT)
    
    def get_app_root_path(self, app_name: str, create_if_missing: bool = False) -> str:
        """
        Get the root storage path for an application.
        
        Args:
            app_name: Name of the application (e.g., 'glue_dispensing_application')
            create_if_missing: Whether to create the directory if it doesn't exist
            
        Returns:
            str: Path to application root directory
        """
        app_path = self._project_root / "src" / "applications" / app_name
        
        if create_if_missing and not app_path.exists():
            app_path.mkdir(parents=True, exist_ok=True)
            
        return str(app_path)
    
    def get_storage_root_path(self, app_name: str, create_if_missing: bool = False) -> str:
        """
        Get the storage root path for an application.
        
        Args:
            app_name: Name of the application
            create_if_missing: Whether to create the directory if it doesn't exist
            
        Returns:
            str: Path to application storage root directory
        """
        storage_path = self._project_root / "src" / "applications" / app_name / "storage"
        
        if create_if_missing and not storage_path.exists():
            storage_path.mkdir(parents=True, exist_ok=True)
            
        return str(storage_path)
    
    def get_settings_path(self, app_name: str, settings_type: str, create_if_missing: bool = False) -> str:
        """
        Get the path to a specific settings file for an application.
        
        Args:
            app_name: Name of the application
            settings_type: Type of settings (e.g., 'glue_settings', 'spray_settings')
            create_if_missing: Whether to create the directory if it doesn't exist
            
        Returns:
            str: Full path to the settings file
        """
        settings_dir = self._project_root / "src" / "applications" / app_name / "storage" / "settings"
        
        if create_if_missing and not settings_dir.exists():
            settings_dir.mkdir(parents=True, exist_ok=True)
            
        settings_file = settings_dir / f"{settings_type}.json"
        return str(settings_file)
    
    def get_settings_directory_path(self, app_name: str, create_if_missing: bool = False) -> str:
        """
        Get the settings directory path for an application.
        
        Args:
            app_name: Name of the application
            create_if_missing: Whether to create the directory if it doesn't exist
            
        Returns:
            str: Path to application settings directory
        """
        settings_dir = self._project_root / "src" / "applications" / app_name / "storage" / "settings"
        
        if create_if_missing and not settings_dir.exists():
            settings_dir.mkdir(parents=True, exist_ok=True)
            
        return str(settings_dir)
    
    def get_templates_path(self, app_name: str, create_if_missing: bool = False) -> str:
        """
        Get the templates directory path for an application.
        
        Args:
            app_name: Name of the application
            create_if_missing: Whether to create the directory if it doesn't exist
            
        Returns:
            str: Path to application templates directory
        """
        templates_dir = self._project_root / "src" / "applications" / app_name / "storage" / "templates"
        
        if create_if_missing and not templates_dir.exists():
            templates_dir.mkdir(parents=True, exist_ok=True)
            
        return str(templates_dir)
    
    def get_cache_path(self, app_name: str, create_if_missing: bool = False) -> str:
        """
        Get the cache directory path for an application.
        
        Args:
            app_name: Name of the application
            create_if_missing: Whether to create the directory if it doesn't exist
            
        Returns:
            str: Path to application cache directory
        """
        cache_dir = self._project_root / "src" / "applications" / app_name / "storage" / "cache"
        
        if create_if_missing and not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
            
        return str(cache_dir)
    
    def get_data_path(self, app_name: str, data_type: str, create_if_missing: bool = False) -> str:
        """
        Get the path to a specific data directory for an application.
        
        Args:
            app_name: Name of the application
            data_type: Type of data (e.g., 'workpieces', 'profiles', 'logs')
            create_if_missing: Whether to create the directory if it doesn't exist
            
        Returns:
            str: Path to application data directory
        """
        data_dir = self._project_root / "src" / "applications" / app_name / "storage" / "data" / data_type
        
        if create_if_missing and not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
            
        return str(data_dir)
    
    def get_logs_path(self, app_name: str, create_if_missing: bool = False) -> str:
        """
        Get the logs directory path for an application.
        
        Args:
            app_name: Name of the application
            create_if_missing: Whether to create the directory if it doesn't exist
            
        Returns:
            str: Path to application logs directory
        """
        logs_dir = self._project_root / "src" / "applications" / app_name / "storage" / "logs"
        
        if create_if_missing and not logs_dir.exists():
            logs_dir.mkdir(parents=True, exist_ok=True)
            
        return str(logs_dir)
    
    def list_application_directories(self) -> List[str]:
        """
        List all application directories that exist.
        
        Returns:
            List[str]: List of application directory names
        """
        apps_root = self._project_root / "src" / "applications"
        
        if not apps_root.exists():
            return []
        
        app_dirs = []
        for item in apps_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                app_dirs.append(item.name)
        
        return sorted(app_dirs)
    
    def application_exists(self, app_name: str) -> bool:
        """
        Check if an application directory exists.
        
        Args:
            app_name: Name of the application to check
            
        Returns:
            bool: True if application directory exists, False otherwise
        """
        app_path = self._project_root / "src" / "applications" / app_name
        return app_path.exists() and app_path.is_dir()
    
    def create_application_structure(self, app_name: str) -> bool:
        """
        Create the complete directory structure for an application.
        
        Args:
            app_name: Name of the application
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create all standard directories
            self.get_storage_root_path(app_name, create_if_missing=True)
            self.get_settings_directory_path(app_name, create_if_missing=True)
            self.get_templates_path(app_name, create_if_missing=True)
            self.get_cache_path(app_name, create_if_missing=True)
            self.get_logs_path(app_name, create_if_missing=True)
            
            # Create common data directories
            self.get_data_path(app_name, "workpieces", create_if_missing=True)
            self.get_data_path(app_name, "profiles", create_if_missing=True)
            
            return True
        except Exception as e:
            print(f"Error creating application structure for {app_name}: {e}")
            return False


# === CONVENIENCE FUNCTIONS ===

_resolver_instance: Optional[ApplicationStorageResolver] = None


def get_application_storage_resolver() -> ApplicationStorageResolver:
    """
    Get the singleton ApplicationStorageResolver instance.
    
    Returns:
        ApplicationStorageResolver: The resolver instance
    """
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = ApplicationStorageResolver()
    return _resolver_instance


def get_app_settings_path(app_name: str, settings_type: str, create_if_missing: bool = False) -> str:
    """
    Convenience function to get application settings file path.
    
    Args:
        app_name: Name of the application
        settings_type: Type of settings
        create_if_missing: Whether to create directories if they don't exist
        
    Returns:
        str: Full path to the settings file
    """
    resolver = get_application_storage_resolver()
    return resolver.get_settings_path(app_name, settings_type, create_if_missing)


def get_app_templates_path(app_name: str, create_if_missing: bool = False) -> str:
    """
    Convenience function to get application templates directory path.
    
    Args:
        app_name: Name of the application
        create_if_missing: Whether to create directory if it doesn't exist
        
    Returns:
        str: Path to templates directory
    """
    resolver = get_application_storage_resolver()
    return resolver.get_templates_path(app_name, create_if_missing)


def get_app_data_path(app_name: str, data_type: str, create_if_missing: bool = False) -> str:
    """
    Convenience function to get application data directory path.
    
    Args:
        app_name: Name of the application
        data_type: Type of data
        create_if_missing: Whether to create directory if it doesn't exist
        
    Returns:
        str: Path to data directory
    """
    resolver = get_application_storage_resolver()
    return resolver.get_data_path(app_name, data_type, create_if_missing)


if __name__ == "__main__":
    # Test the application storage resolver
    resolver = ApplicationStorageResolver()
    
    print("=== ApplicationStorageResolver Test ===")
    
    # Test glue dispensing application paths
    app_name = "glue_dispensing_application"
    print(f"App Root: {resolver.get_app_root_path(app_name)}")
    print(f"Storage Root: {resolver.get_storage_root_path(app_name)}")
    print(f"Settings Path: {resolver.get_settings_path(app_name, 'glue_settings')}")
    print(f"Templates Path: {resolver.get_templates_path(app_name)}")
    print(f"Cache Path: {resolver.get_cache_path(app_name)}")
    print(f"Workpieces Data: {resolver.get_data_path(app_name, 'workpieces')}")
    print(f"Logs Path: {resolver.get_logs_path(app_name)}")
    
    # Test convenience functions
    print(f"\nConvenience function test:")
    print(f"Settings: {get_app_settings_path(app_name, 'spray_settings')}")
    print(f"Templates: {get_app_templates_path(app_name)}")
    
    # List applications
    print(f"\nApplications found: {resolver.list_application_directories()}")
"""
Centralized Path Resolver

This module provides a centralized way to resolve file and directory paths
throughout the application, eliminating scattered path logic and making
the codebase more maintainable.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional, Union


class PathType(Enum):
    """
    Enumeration of all standardized path types in the application.
    """
    # === ROOT DIRECTORIES ===
    PROJECT_ROOT = "project_root"
    BACKEND_ROOT = "backend_root"
    FRONTEND_ROOT = "frontend_root"
    MODULES_ROOT = "modules_root"
    
    # === STORAGE DIRECTORIES ===
    STORAGE_ROOT = "storage"
    SETTINGS_STORAGE = "settings_storage"
    LOGS_STORAGE = "logs_storage"
    STATISTICS_STORAGE = "statistics_storage"
    
    # === APPLICATION-SPECIFIC STORAGE ===
    GLUE_APPLICATION_STORAGE = "glue_app_storage"
    WORKPIECE_STORAGE = "workpiece_storage"
    
    # === VISION SYSTEM PATHS ===
    VISION_SYSTEM_ROOT = "vision_system"
    CALIBRATION_ROOT = "calibration"
    CAMERA_CALIBRATION_ROOT = "camera_calibration"
    CALIBRATION_RESULTS = "calibration_results"

    # === UI ASSETS ===
    UI_ASSETS = "ui_assets"
    UI_ICONS = "ui_icons"
    UI_IMAGES = "ui_images"


class PathResolver:
    """
    Centralized path resolver for the entire application.
    
    This class provides a single source of truth for all file paths,
    making the application more maintainable and reducing path-related errors.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the path resolver with base paths."""
        if not PathResolver._initialized:
            self._project_root = self._find_project_root()
            self._path_cache = {}
            self._init_base_paths()
            PathResolver._initialized = True
    
    def _find_project_root(self) -> Path:
        """
        Find the project root directory by looking for characteristic files/directories.
        
        Returns:
            Path: The project root directory
        """
        current_path = Path(__file__).resolve()
        
        # Look for project markers (src/, modules/, requirements.txt)
        for parent in current_path.parents:
            if (
                (parent / "src").exists() and 
                (parent / "modules").exists() and
                (parent / "requirements.txt").exists()
            ):
                return parent
        
        # Fallback: assume we're in src/backend/system/utils/ and go up 4 levels
        return current_path.parent.parent.parent.parent
    
    def _init_base_paths(self):
        """Initialize all base path mappings."""
        root = self._project_root
        
        # === ROOT DIRECTORIES ===
        self._base_paths = {
            PathType.PROJECT_ROOT: root,
            PathType.BACKEND_ROOT: root / "src" / "backend",
            PathType.FRONTEND_ROOT: root / "src" / "frontend",
            PathType.MODULES_ROOT: root / "modules",
            
            # === STORAGE DIRECTORIES ===
            PathType.STORAGE_ROOT: root / "src" / "backend" / "system" / "storage",
            PathType.SETTINGS_STORAGE: root / "src" / "backend" / "system" / "storage" / "settings",
            PathType.LOGS_STORAGE: root / "src" / "backend" / "system" / "storage" / "logs",
            PathType.STATISTICS_STORAGE: root / "src" / "backend" / "system" / "storage",
            
            # === APPLICATION-SPECIFIC STORAGE ===
            PathType.GLUE_APPLICATION_STORAGE: root / "src" / "backend" / "robot_application" / "glue_dispensing_application" / "storage",
            PathType.WORKPIECE_STORAGE: root / "src" / "backend" / "system"  / "storage" / "workpieces",
            
            # === VISION SYSTEM PATHS ===
            PathType.VISION_SYSTEM_ROOT: root / "modules" / "VisionSystem",
            PathType.CALIBRATION_ROOT: root / "modules" / "VisionSystem" / "calibration",
            PathType.CAMERA_CALIBRATION_ROOT: root / "modules" / "VisionSystem" / "calibration" / "cameraCalibration",
            PathType.CALIBRATION_RESULTS: root / "modules" / "VisionSystem" / "calibration" / "cameraCalibration" / "storage" / "calibration_result",
            
            # === UI ASSETS ===
            PathType.UI_ASSETS: root / "src" / "frontend" / "pl_ui" / "assets",
            PathType.UI_ICONS: root / "src" / "frontend" / "pl_ui" / "assets" / "icons",
            PathType.UI_IMAGES: root / "src" / "frontend" / "pl_ui" / "assets" / "images",
        }
    
    def get_path(self, path_type: PathType, *args, create_if_missing: bool = False) -> Path:
        """
        Get a resolved path for the given path type.
        
        Args:
            path_type: The type of path to resolve
            *args: Additional path components to append
            create_if_missing: Whether to create the directory if it doesn't exist
            
        Returns:
            Path: The resolved path
        """
        if path_type not in self._base_paths:
            raise ValueError(f"Unknown path type: {path_type}")
        
        # Build cache key
        cache_key = (path_type, args, create_if_missing)
        
        # Check cache first
        if cache_key in self._path_cache:
            return self._path_cache[cache_key]
        
        # Resolve the path
        base_path = self._base_paths[path_type]
        full_path = base_path
        
        # Append additional components
        for component in args:
            full_path = full_path / component
        
        # Create directory if requested
        if create_if_missing and not full_path.exists():
            if full_path.suffix:  # This is a file path
                full_path.parent.mkdir(parents=True, exist_ok=True)
            else:  # This is a directory path
                full_path.mkdir(parents=True, exist_ok=True)
        
        # Cache the result
        self._path_cache[cache_key] = full_path
        
        return full_path
    
    def get_path_str(self, path_type: PathType, *args, create_if_missing: bool = False) -> str:
        """
        Get a resolved path as a string.
        
        Args:
            path_type: The type of path to resolve
            *args: Additional path components to append
            create_if_missing: Whether to create the directory if it doesn't exist
            
        Returns:
            str: The resolved path as a string
        """
        return str(self.get_path(path_type, *args, create_if_missing=create_if_missing))
    
    def ensure_directory_exists(self, path_type: PathType, *args) -> Path:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            path_type: The type of path to resolve
            *args: Additional path components to append
            
        Returns:
            Path: The ensured directory path
        """
        return self.get_path(path_type, *args, create_if_missing=True)
    
    def clear_cache(self):
        """Clear the path cache (useful for testing)."""
        self._path_cache.clear()


# === CONVENIENCE FUNCTIONS ===

def get_path(path_type: PathType, *args, create_if_missing: bool = False) -> Path:
    """
    Convenience function to get a path without creating a PathResolver instance.
    
    Args:
        path_type: The type of path to resolve
        *args: Additional path components to append
        create_if_missing: Whether to create the directory if it doesn't exist
        
    Returns:
        Path: The resolved path
    """
    resolver = PathResolver()
    return resolver.get_path(path_type, *args, create_if_missing=create_if_missing)


def get_path_str(path_type: PathType, *args, create_if_missing: bool = False) -> str:
    """
    Convenience function to get a path as a string.
    
    Args:
        path_type: The type of path to resolve
        *args: Additional path components to append
        create_if_missing: Whether to create the directory if it doesn't exist
        
    Returns:
        str: The resolved path as a string
    """
    resolver = PathResolver()
    return resolver.get_path_str(path_type, *args, create_if_missing=create_if_missing)


# === SPECIFIC PATH FUNCTIONS ===

def get_settings_file_path(filename: str, create_if_missing: bool = False) -> str:
    """
    Get the path to a settings file.
    
    Args:
        filename: The settings filename (e.g., 'camera_settings.json')
        create_if_missing: Whether to create the directory if it doesn't exist
        
    Returns:
        str: The full path to the settings file
    """
    return get_path_str(PathType.SETTINGS_STORAGE, filename, create_if_missing=create_if_missing)


def get_glue_settings_file_path(create_if_missing: bool = False) -> str:
    """
    Get the path to the glue settings file.
    
    Args:
        create_if_missing: Whether to create the directory if it doesn't exist
        
    Returns:
        str: The full path to the glue settings file
    """
    return get_path_str(PathType.SETTINGS_STORAGE, "glue_settings.json", create_if_missing=create_if_missing)


def get_robot_config_file_path(create_if_missing: bool = False) -> str:
    """
    Get the path to the robot config file.
    
    Args:
        create_if_missing: Whether to create the directory if it doesn't exist
        
    Returns:
        str: The full path to the robot config file
    """
    return get_path_str(PathType.SETTINGS_STORAGE, "robot_config.json", create_if_missing=create_if_missing)


def get_workpiece_storage_path(create_if_missing: bool = False) -> str:
    """
    Get the path to the workpiece storage directory.
    
    Args:
        create_if_missing: Whether to create the directory if it doesn't exist
        
    Returns:
        str: The full path to the workpiece storage directory
    """
    return get_path_str(PathType.WORKPIECE_STORAGE, create_if_missing=create_if_missing)


def get_calibration_result_path(filename: str, create_if_missing: bool = False) -> str:
    """
    Get the path to a calibration result file.
    
    Args:
        filename: The calibration filename (e.g., 'camera_calibration.npz')
        create_if_missing: Whether to create the directory if it doesn't exist
        
    Returns:
        str: The full path to the calibration file
    """
    return get_path_str(PathType.CALIBRATION_RESULTS, filename, create_if_missing=create_if_missing)


def get_statistics_file_path(create_if_missing: bool = False) -> str:
    """
    Get the path to the statistics file.
    
    Args:
        create_if_missing: Whether to create the directory if it doesn't exist
        
    Returns:
        str: The full path to the statistics file
    """
    return get_path_str(PathType.STATISTICS_STORAGE, "statistics.json", create_if_missing=create_if_missing)


def get_log_file_path(filename: str, create_if_missing: bool = False) -> str:
    """
    Get the path to a log file.
    
    Args:
        filename: The log filename (e.g., 'session.txt')
        create_if_missing: Whether to create the directory if it doesn't exist
        
    Returns:
        str: The full path to the log file
    """
    return get_path_str(PathType.LOGS_STORAGE, filename, create_if_missing=create_if_missing)


# === LEGACY COMPATIBILITY ===

def get_legacy_paths():
    """
    Get a dictionary of commonly used legacy paths for backward compatibility.
    
    Returns:
        dict: Dictionary mapping legacy path names to resolved paths
    """
    resolver = PathResolver()
    
    return {
        # Settings paths
        'CAMERA_SETTINGS_PATH': get_settings_file_path('camera_settings.json'),

        'GLUE_CELLS_CONFIG_PATH': get_settings_file_path('glue_cells_config.json'),
        'GLUE_SETTINGS_PATH': get_glue_settings_file_path(),
        'ROBOT_CONFIG_PATH': get_robot_config_file_path(),
        
        # Storage paths
        'WORKPIECE_STORAGE_PATH': get_workpiece_storage_path(),
        'STATISTICS_PATH': get_statistics_file_path(),
        
        # Calibration paths
        'CAMERA_CALIBRATION_PATH': get_calibration_result_path('camera_calibration.npz'),
        'PERSPECTIVE_MATRIX_PATH': get_calibration_result_path('perspectiveTransform.npy'),
        'CAMERA_TO_ROBOT_MATRIX_PATH': get_calibration_result_path('cameraToRobotMatrix_robot_tcp.npy'),
        'PICKUP_AREA_POINTS_PATH': get_calibration_result_path('pickupAreaPoints.npy'),
        'SPRAY_AREA_POINTS_PATH': get_calibration_result_path('sprayAreaPoints.npy'),
        'WORK_AREA_POINTS_PATH': get_calibration_result_path('workAreaPoints.npy'),
        
        # Log paths
        'SESSION_LOG_PATH': get_log_file_path('session.txt'),
    }


if __name__ == "__main__":
    # Test the path resolver
    resolver = PathResolver()
    
    print("=== PathResolver Test ===")
    print(f"Project Root: {resolver.get_path(PathType.PROJECT_ROOT)}")
    print(f"Settings Storage: {resolver.get_path(PathType.SETTINGS_STORAGE)}")
    print(f"Glue Settings File: {get_glue_settings_file_path()}")
    print(f"Workpiece Storage: {get_workpiece_storage_path()}")
    print(f"Camera Calibration: {get_calibration_result_path('camera_calibration.npz')}")
    
    print("\n=== Legacy Paths ===")
    legacy_paths = get_legacy_paths()
    for name, path in legacy_paths.items():
        print(f"{name}: {path}")
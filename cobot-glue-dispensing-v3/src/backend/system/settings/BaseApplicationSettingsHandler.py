"""
Base Application Settings Handler

This module provides a standardized base class for all application-specific
settings handlers, ensuring consistent behavior across different applications
while eliminating parameter passing bugs and providing unified persistence.
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple

from backend.system.utils.ApplicationStorageResolver import get_application_storage_resolver
from core.application.interfaces.application_settings_interface import ApplicationSettingsHandler


class BaseApplicationSettingsHandler(ApplicationSettingsHandler, ABC):
    """
    Base class for all application-specific settings handlers.
    
    This class provides:
    - Standardized file persistence using ApplicationStorageResolver
    - Consistent error handling and logging
    - Automatic directory creation
    - Transaction-like save operations
    - Unified validation flow
    """
    
    def __init__(self, app_name: str, settings_type: str):
        """
        Initialize the base settings handler.
        
        Args:
            app_name: Name of the application (e.g., 'glue_dispensing_application')
            settings_type: Type of settings (e.g., 'glue_settings', 'spray_settings')
        """
        self.app_name = app_name
        self.settings_type = settings_type
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{app_name}")
        
        # Get storage resolver and paths
        self.storage_resolver = get_application_storage_resolver()
        self.settings_file_path = self.storage_resolver.get_settings_path(
            app_name, settings_type, create_if_missing=True
        )
        
        # Initialize settings object
        self._settings_object = None
        self._load_settings()
    
    @abstractmethod
    def create_default_settings(self):
        """
        Create and return a default settings object.
        
        This method must be implemented by each application-specific handler
        to provide their default settings structure.
        
        Returns:
            The default settings object for this application
        """
        pass
    
    @abstractmethod
    def validate_settings_data(self, settings_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate settings data specific to this application.
        
        Args:
            settings_data: Dictionary containing settings to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def update_settings_object(self, settings_data: Dict[str, Any]) -> None:
        """
        Update the internal settings object with new data.
        
        Args:
            settings_data: Dictionary containing new settings values
        """
        pass
    
    @abstractmethod
    def get_settings_dict(self) -> Dict[str, Any]:
        """
        Get the current settings as a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Current settings as dictionary
        """
        pass
    
    def handle_get_settings(self) -> Dict[str, Any]:
        """
        Handle GET request for application settings.
        
        Returns:
            Dict[str, Any]: Current settings data
        """
        try:
            return self.get_settings_dict()
        except Exception as e:
            self.logger.error(f"Error getting {self.settings_type} settings: {e}")
            # Return default settings on error
            return self.create_default_settings().to_dict() if hasattr(self.create_default_settings(), 'to_dict') else {}
    
    def handle_set_settings(self, settings: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Handle SET request for application settings.
        
        Args:
            settings: New settings data
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Skip API header if present
            settings_data = self._clean_settings_data(settings)
            
            # Validate settings
            is_valid, validation_message = self.validate_settings_data(settings_data)
            if not is_valid:
                return False, f"Validation failed: {validation_message}"
            
            # Create backup of current settings for rollback
            original_settings = self.get_settings_dict()
            
            try:
                # Update settings object
                self.update_settings_object(settings_data)
                
                # Save to file
                success, save_message = self._save_settings()
                if not success:
                    # Rollback on save failure
                    self.update_settings_object(original_settings)
                    return False, f"Failed to save settings: {save_message}"
                
                self.logger.info(f"{self.settings_type} settings updated successfully")
                return True, f"{self.settings_type.replace('_', ' ').title()} settings saved successfully"
                
            except Exception as update_error:
                # Rollback on update failure
                self.update_settings_object(original_settings)
                raise update_error
            
        except Exception as e:
            self.logger.error(f"Error setting {self.settings_type} settings: {e}")
            return False, f"Error updating settings: {str(e)}"
    
    def get_settings_type(self) -> str:
        """
        Get the settings type this handler manages.
        
        Returns:
            str: Settings type identifier
        """
        return self.settings_type
    
    def get_settings_object(self):
        """
        Get the internal settings object.
        
        Returns:
            The current settings object
        """
        return self._settings_object
    
    def reload_settings(self) -> bool:
        """
        Reload settings from file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._load_settings()
            return True
        except Exception as e:
            self.logger.error(f"Error reloading {self.settings_type} settings: {e}")
            return False
    
    def _load_settings(self) -> None:
        """Load settings from JSON file."""
        try:
            if os.path.exists(self.settings_file_path):
                with open(self.settings_file_path, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                
                # Create default settings object
                self._settings_object = self.create_default_settings()
                
                # Update with loaded data
                self.update_settings_object(settings_data)
                
                self.logger.debug(f"Loaded {self.settings_type} settings from {self.settings_file_path}")
            else:
                self.logger.info(f"{self.settings_type} settings file not found. Creating defaults.")
                self._settings_object = self.create_default_settings()
                self._save_settings()  # Create file with defaults

        except Exception as e:
            self.logger.error(f"Error loading {self.settings_type} settings: {e}")
            self.logger.info(f"Using default {self.settings_type} settings")
            self._settings_object = self.create_default_settings()
    
    def _save_settings(self) -> Tuple[bool, str]:
        """
        Save current settings to JSON file.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.settings_file_path), exist_ok=True)
            
            # Get settings data for saving
            settings_data = self.get_settings_dict()
            
            # Write to file with atomic operation
            temp_file = f"{self.settings_file_path}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4, ensure_ascii=False)
            
            # Atomic move
            os.replace(temp_file, self.settings_file_path)
            
            self.logger.info(f"{self.settings_type} settings saved to {self.settings_file_path}")
            return True, "Settings saved successfully"
            
        except Exception as e:
            self.logger.error(f"Error saving {self.settings_type} settings: {e}")
            return False, str(e)
    
    def _clean_settings_data(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean settings data by removing API-specific fields.
        
        Args:
            settings: Raw settings data from API
            
        Returns:
            Dict[str, Any]: Cleaned settings data
        """
        cleaned = {}
        for key, value in settings.items():
            # Skip API headers and other metadata
            if key not in ['header']:
                cleaned[key] = value
        return cleaned


class StandardizedSettingsError(Exception):
    """Custom exception for settings-related errors."""
    pass


class SettingsValidationError(StandardizedSettingsError):
    """Exception raised when settings validation fails."""
    pass


class SettingsPersistenceError(StandardizedSettingsError):
    """Exception raised when settings persistence fails."""
    pass
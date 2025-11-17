"""
Application Settings Interface

This module defines the interface that all robot applications must implement
for their application-specific settings. This allows the core settings system
to remain application-agnostic while supporting extensibility.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class ApplicationSettingsInterface(ABC):
    """
    Interface that all application-specific settings must implement.
    
    This allows applications to define their own settings while maintaining
    compatibility with the core settings system.
    """
    
    @abstractmethod
    def get_settings_type_name(self) -> str:
        """
        Get the unique name for this settings type.
        
        Returns:
            str: Settings type identifier (e.g., "glue", "paint", "welding")
        """
        pass
    
    @abstractmethod
    def get_default_values(self) -> Dict[str, Any]:
        """
        Get default settings values for this application.
        
        Returns:
            Dict[str, Any]: Default settings dictionary
        """
        pass
    
    @abstractmethod
    def validate_settings(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate settings data for this application.
        
        Args:
            settings: Settings dictionary to validate
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def update_from_dict(self, settings: Dict[str, Any]) -> None:
        """
        Update settings from a dictionary.
        
        Args:
            settings: Settings data to apply
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to dictionary format.
        
        Returns:
            Dict[str, Any]: Settings as dictionary
        """
        pass
    
    @abstractmethod
    def get_supported_endpoints(self) -> List[str]:
        """
        Get list of API endpoints this settings type supports.
        
        Returns:
            List[str]: List of endpoint paths
        """
        pass


class ApplicationSettingsHandler(ABC):
    """
    Interface for handling application-specific settings requests.
    
    Applications can implement this to handle their own settings
    operations (get, set, validate, etc.)
    """
    
    @abstractmethod
    def handle_get_settings(self) -> Dict[str, Any]:
        """
        Handle GET request for application settings.
        
        Returns:
            Dict[str, Any]: Current settings data
        """
        pass
    
    @abstractmethod
    def handle_set_settings(self, settings: Dict[str, Any]) -> tuple[bool, str]:
        """
        Handle SET request for application settings.
        
        Args:
            settings: New settings data
            
        Returns:
            tuple[bool, str]: (success, message)
        """
        pass
    
    @abstractmethod
    def get_settings_type(self) -> str:
        """
        Get the settings type this handler manages.
        
        Returns:
            str: Settings type identifier
        """
        pass


class ApplicationSettingsRegistry:
    """
    Registry for managing application-specific settings types.
    
    This allows the core settings system to discover and route
    to application-specific settings handlers.
    """
    
    def __init__(self):
        self._settings_types: Dict[str, ApplicationSettingsInterface] = {}
        self._handlers: Dict[str, ApplicationSettingsHandler] = {}
    
    def register_settings_type(self, settings: ApplicationSettingsInterface) -> None:
        """
        Register an application settings type.
        
        Args:
            settings: Application settings implementation
        """
        settings_type = settings.get_settings_type_name()
        self._settings_types[settings_type] = settings
        
    def register_handler(self, handler: ApplicationSettingsHandler) -> None:
        """
        Register an application settings handler.
        
        Args:
            handler: Application settings handler
        """
        settings_type = handler.get_settings_type()
        self._handlers[settings_type] = handler
    
    def get_settings_type(self, type_name: str) -> ApplicationSettingsInterface:
        """
        Get settings implementation by type name.
        
        Args:
            type_name: Settings type identifier
            
        Returns:
            ApplicationSettingsInterface: Settings implementation
            
        Raises:
            KeyError: If settings type not found
        """
        if type_name not in self._settings_types:
            raise KeyError(f"Settings type '{type_name}' not registered")
        return self._settings_types[type_name]
    
    def get_handler(self, type_name: str) -> ApplicationSettingsHandler:
        """
        Get settings handler by type name.
        
        Args:
            type_name: Settings type identifier
            
        Returns:
            ApplicationSettingsHandler: Settings handler
            
        Raises:
            KeyError: If handler not found
        """
        if type_name not in self._handlers:
            raise KeyError(f"Settings handler for '{type_name}' not registered")
        return self._handlers[type_name]
    
    def get_registered_types(self) -> List[str]:
        """
        Get list of all registered settings types.
        
        Returns:
            List[str]: List of settings type names
        """
        return list(self._settings_types.keys())
    
    def is_type_registered(self, type_name: str) -> bool:
        """
        Check if a settings type is registered.
        
        Args:
            type_name: Settings type identifier
            
        Returns:
            bool: True if registered, False otherwise
        """
        return type_name in self._settings_types
    
    def get_all_endpoints(self) -> Dict[str, str]:
        """
        Get all supported endpoints mapped to their settings type.
        
        Returns:
            Dict[str, str]: Mapping of endpoint -> settings_type
        """
        endpoint_mapping = {}
        for type_name, settings in self._settings_types.items():
            for endpoint in settings.get_supported_endpoints():
                endpoint_mapping[endpoint] = type_name
        return endpoint_mapping


# Global registry instance
settings_registry = ApplicationSettingsRegistry()
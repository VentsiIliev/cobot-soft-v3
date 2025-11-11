"""
Enhanced BaseContext with dependency injection and callback support.

This module provides the enhanced context system for state machines with
thread-safe data access, service container integration, and callback registry.
"""

import threading
from typing import Dict, Any, Optional, Callable, Type, TypeVar
from abc import ABC

from ..ServiceInterfaces import ServiceContainer

T = TypeVar('T')


class BaseContext:
    """Enhanced context with dependency injection and callback support"""

    def __init__(self, service_container: Optional[ServiceContainer] = None):
        """
        Initialize BaseContext with optional service container.
        
        Args:
            service_container: Optional ServiceContainer for dependency injection
        """
        self.data: Dict[str, Any] = {}
        self.error_message: str = ""
        self.operation_result: Any = None
        self.metadata: Dict[str, Any] = {}
        self.services = service_container or ServiceContainer()

        # Thread safety
        self._data_lock = threading.RLock()

        # Callback registry for external hooks (e.g. execute_operation, process_event)
        self._callbacks: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._callbacks_lock = threading.RLock()

    def set_data(self, key: str, value: Any) -> None:
        """
        Thread-safe data setting.
        
        Args:
            key: Data key
            value: Data value
        """
        with self._data_lock:
            self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Thread-safe data getting.
        
        Args:
            key: Data key
            default: Default value if key not found
            
        Returns:
            Data value or default
        """
        with self._data_lock:
            return self.data.get(key, default)

    def update_data(self, updates: Dict[str, Any]) -> None:
        """
        Thread-safe bulk data update.
        
        Args:
            updates: Dictionary of key-value pairs to update
        """
        with self._data_lock:
            self.data.update(updates)

    def clear_data(self) -> None:
        """Thread-safe data clearing."""
        with self._data_lock:
            self.data.clear()

    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service from the container.
        
        Args:
            service_type: Type of service to retrieve
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service is not registered
        """
        return self.services.get_service(service_type)

    def has_service(self, service_type: Type[T]) -> bool:
        """
        Check if service is available.
        
        Args:
            service_type: Type of service to check
            
        Returns:
            True if service is available, False otherwise
        """
        return self.services.has_service(service_type)

    # --- Callback registry API ---

    def register_callback(self, name: str, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """
        Register a named callback. Overwrites existing callback with same name.
        
        Args:
            name: Callback name
            callback: Callback function
        """
        with self._callbacks_lock:
            self._callbacks[name] = callback

    def unregister_callback(self, name: str) -> None:
        """
        Unregister a previously registered callback (no-op if missing).
        
        Args:
            name: Callback name to remove
        """
        with self._callbacks_lock:
            self._callbacks.pop(name, None)

    def execute_callback(self, name: str, params: Dict[str, Any]) -> Any:
        """
        Execute a registered callback with provided params.
        
        Args:
            name: Callback name
            params: Parameters to pass to callback
            
        Returns:
            Callback result or None if no callback is registered
            
        Raises:
            Exception: Any exception raised by the callback
        """
        with self._callbacks_lock:
            cb = self._callbacks.get(name)

        if cb is None:
            return None

        return cb(params)

    def has_callback(self, name: str) -> bool:
        """
        Check if callback is registered.
        
        Args:
            name: Callback name
            
        Returns:
            True if callback exists, False otherwise
        """
        with self._callbacks_lock:
            return name in self._callbacks

    def list_callbacks(self) -> list[str]:
        """
        Get list of registered callback names.
        
        Returns:
            List of callback names
        """
        with self._callbacks_lock:
            return list(self._callbacks.keys())

    def copy_data(self) -> Dict[str, Any]:
        """
        Get a thread-safe copy of current data.
        
        Returns:
            Copy of current data dictionary
        """
        with self._data_lock:
            return dict(self.data)

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    def __repr__(self) -> str:
        """String representation for debugging."""
        with self._data_lock:
            data_keys = list(self.data.keys())
        with self._callbacks_lock:
            callback_names = list(self._callbacks.keys())
        
        return (f"BaseContext(data_keys={data_keys}, "
                f"callbacks={callback_names}, "
                f"services={len(self.services._services) + len(self.services._singletons)})")
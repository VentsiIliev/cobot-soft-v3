"""
Enhanced service container with lifecycle management and advanced features.

This module provides an advanced dependency injection container with support for
different service lifetimes, metadata, initialization/disposal hooks, and scoped services.
"""

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeVar, Type, Callable, Optional, Any, Dict, List
import inspect
import weakref

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime management options."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceRegistration:
    """Service registration information."""
    service_type: Type
    implementation: Any
    lifetime: ServiceLifetime
    factory: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[Type] = field(default_factory=list)


class ServiceScope:
    """Represents a service scope for scoped lifetime management."""
    
    def __init__(self, name: str):
        """
        Initialize service scope.
        
        Args:
            name: Scope name
        """
        self.name = name
        self._instances: Dict[Type, Any] = {}
        self._disposal_handlers: List[Callable[[Any], None]] = []
        self._lock = threading.RLock()

    def get_instance(self, service_type: Type[T]) -> Optional[T]:
        """
        Get scoped instance if it exists.
        
        Args:
            service_type: Service type
            
        Returns:
            Service instance or None
        """
        with self._lock:
            return self._instances.get(service_type)

    def set_instance(self, service_type: Type[T], instance: T) -> None:
        """
        Set scoped instance.
        
        Args:
            service_type: Service type
            instance: Service instance
        """
        with self._lock:
            self._instances[service_type] = instance

    def add_disposal_handler(self, handler: Callable[[Any], None]) -> None:
        """
        Add disposal handler for this scope.
        
        Args:
            handler: Disposal handler function
        """
        with self._lock:
            self._disposal_handlers.append(handler)

    def dispose(self) -> None:
        """Dispose all services in this scope."""
        with self._lock:
            # Call disposal handlers
            for instance in self._instances.values():
                for handler in self._disposal_handlers:
                    try:
                        handler(instance)
                    except Exception as e:
                        # Log error but continue disposal
                        print(f"Error during service disposal: {e}")
            
            # Clear instances
            self._instances.clear()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic disposal."""
        self.dispose()


class IServiceInitializer(ABC):
    """Interface for services that need initialization."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the service."""
        pass


class IServiceDisposable(ABC):
    """Interface for services that need disposal."""
    
    @abstractmethod
    def dispose(self) -> None:
        """Dispose the service."""
        pass


class EnhancedServiceContainer:
    """Enhanced DI container with lifecycle management and metadata."""

    def __init__(self):
        """Initialize enhanced service container."""
        self._registrations: Dict[Type, ServiceRegistration] = {}
        self._singleton_instances: Dict[Type, Any] = {}
        self._scopes: Dict[str, ServiceScope] = {}
        self._service_metadata: Dict[Type, Dict[str, Any]] = {}
        self._initialization_hooks: List[Callable[[Any], None]] = []
        self._disposal_hooks: List[Callable[[Any], None]] = []
        self._lock = threading.RLock()
        
        # Weak references to track all created instances for cleanup
        self._created_instances: weakref.WeakSet = weakref.WeakSet()

    def register_service(self, 
                        service_type: Type[T], 
                        implementation: T = None,
                        factory: Callable[[], T] = None,
                        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
                        metadata: Dict[str, Any] = None,
                        dependencies: List[Type] = None) -> 'EnhancedServiceContainer':
        """
        Enhanced service registration with lifecycle and metadata.
        
        Args:
            service_type: Type of service
            implementation: Service implementation instance
            factory: Factory function to create service
            lifetime: Service lifetime
            metadata: Service metadata
            dependencies: Service dependencies
            
        Returns:
            Self for chaining
            
        Raises:
            ValueError: If neither implementation nor factory is provided
        """
        if implementation is None and factory is None:
            raise ValueError("Either implementation or factory must be provided")

        registration = ServiceRegistration(
            service_type=service_type,
            implementation=implementation,
            lifetime=lifetime,
            factory=factory,
            metadata=metadata or {},
            dependencies=dependencies or []
        )

        with self._lock:
            self._registrations[service_type] = registration
            self._service_metadata[service_type] = metadata or {}

        return self

    def register_singleton(self, service_type: Type[T], instance: T, 
                          metadata: Dict[str, Any] = None) -> 'EnhancedServiceContainer':
        """
        Register singleton service.
        
        Args:
            service_type: Service type
            instance: Service instance
            metadata: Service metadata
            
        Returns:
            Self for chaining
        """
        return self.register_service(
            service_type=service_type,
            implementation=instance,
            lifetime=ServiceLifetime.SINGLETON,
            metadata=metadata
        )

    def register_transient(self, service_type: Type[T], factory: Callable[[], T],
                          metadata: Dict[str, Any] = None,
                          dependencies: List[Type] = None) -> 'EnhancedServiceContainer':
        """
        Register transient service.
        
        Args:
            service_type: Service type
            factory: Factory function
            metadata: Service metadata
            dependencies: Service dependencies
            
        Returns:
            Self for chaining
        """
        return self.register_service(
            service_type=service_type,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT,
            metadata=metadata,
            dependencies=dependencies
        )

    def register_scoped(self, service_type: Type[T], factory: Callable[[], T],
                       metadata: Dict[str, Any] = None,
                       dependencies: List[Type] = None) -> 'EnhancedServiceContainer':
        """
        Register scoped service.
        
        Args:
            service_type: Service type
            factory: Factory function
            metadata: Service metadata
            dependencies: Service dependencies
            
        Returns:
            Self for chaining
        """
        return self.register_service(
            service_type=service_type,
            factory=factory,
            lifetime=ServiceLifetime.SCOPED,
            metadata=metadata,
            dependencies=dependencies
        )

    def get_service(self, service_type: Type[T], scope: str = "default") -> T:
        """
        Get service with scope support.
        
        Args:
            service_type: Service type
            scope: Scope name for scoped services
            
        Returns:
            Service instance
            
        Raises:
            ValueError: If service is not registered
        """
        with self._lock:
            if service_type not in self._registrations:
                raise ValueError(f"Service {service_type.__name__} not registered")

            registration = self._registrations[service_type]

            if registration.lifetime == ServiceLifetime.SINGLETON:
                return self._get_singleton(registration)
            elif registration.lifetime == ServiceLifetime.TRANSIENT:
                return self._create_instance(registration)
            elif registration.lifetime == ServiceLifetime.SCOPED:
                return self._get_scoped(registration, scope)

    def get_services_by_metadata(self, key: str, value: Any) -> List[Any]:
        """
        Query services by metadata.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            List of services matching the metadata
        """
        results = []
        with self._lock:
            for service_type, metadata in self._service_metadata.items():
                if metadata.get(key) == value:
                    try:
                        service_instance = self.get_service(service_type)
                        results.append(service_instance)
                    except ValueError:
                        # Service not registered properly, skip
                        continue
        return results

    def has_service(self, service_type: Type[T]) -> bool:
        """
        Check if service is registered.
        
        Args:
            service_type: Service type
            
        Returns:
            True if service is registered
        """
        with self._lock:
            return service_type in self._registrations

    def create_scope(self, name: str) -> ServiceScope:
        """
        Create a new service scope.
        
        Args:
            name: Scope name
            
        Returns:
            New service scope
        """
        with self._lock:
            scope = ServiceScope(name)
            self._scopes[name] = scope
            return scope

    def get_scope(self, name: str) -> Optional[ServiceScope]:
        """
        Get existing scope.
        
        Args:
            name: Scope name
            
        Returns:
            Scope or None if not found
        """
        with self._lock:
            return self._scopes.get(name)

    def dispose_scope(self, scope: str) -> None:
        """
        Dispose all scoped services in a scope.
        
        Args:
            scope: Scope name
        """
        with self._lock:
            if scope in self._scopes:
                self._scopes[scope].dispose()
                del self._scopes[scope]

    def add_initialization_hook(self, hook: Callable[[Any], None]) -> None:
        """
        Add service initialization hook.
        
        Args:
            hook: Initialization hook function
        """
        with self._lock:
            self._initialization_hooks.append(hook)

    def add_disposal_hook(self, hook: Callable[[Any], None]) -> None:
        """
        Add service disposal hook.
        
        Args:
            hook: Disposal hook function
        """
        with self._lock:
            self._disposal_hooks.append(hook)

    def get_service_info(self, service_type: Type[T]) -> Optional[Dict[str, Any]]:
        """
        Get service registration information.
        
        Args:
            service_type: Service type
            
        Returns:
            Service information dictionary or None
        """
        with self._lock:
            if service_type not in self._registrations:
                return None
            
            registration = self._registrations[service_type]
            return {
                'service_type': service_type.__name__,
                'lifetime': registration.lifetime.value,
                'metadata': registration.metadata,
                'dependencies': [dep.__name__ for dep in registration.dependencies],
                'has_factory': registration.factory is not None,
                'has_implementation': registration.implementation is not None
            }

    def list_services(self) -> List[Dict[str, Any]]:
        """
        List all registered services.
        
        Returns:
            List of service information dictionaries
        """
        with self._lock:
            return [self.get_service_info(service_type) 
                   for service_type in self._registrations.keys()]

    def validate_dependencies(self) -> List[str]:
        """
        Validate all service dependencies.
        
        Returns:
            List of validation errors
        """
        errors = []
        with self._lock:
            for service_type, registration in self._registrations.items():
                for dependency in registration.dependencies:
                    if dependency not in self._registrations:
                        errors.append(
                            f"Service {service_type.__name__} depends on "
                            f"unregistered service {dependency.__name__}"
                        )
        return errors

    def dispose_all(self) -> None:
        """Dispose all services and clear container."""
        with self._lock:
            # Dispose all scopes
            for scope in list(self._scopes.values()):
                scope.dispose()
            self._scopes.clear()
            
            # Dispose singletons
            for instance in self._singleton_instances.values():
                self._dispose_instance(instance)
            self._singleton_instances.clear()
            
            # Clear registrations
            self._registrations.clear()
            self._service_metadata.clear()

    def _get_singleton(self, registration: ServiceRegistration) -> Any:
        """Get or create singleton instance."""
        service_type = registration.service_type
        
        if service_type in self._singleton_instances:
            return self._singleton_instances[service_type]
        
        instance = self._create_instance(registration)
        self._singleton_instances[service_type] = instance
        return instance

    def _get_scoped(self, registration: ServiceRegistration, scope_name: str) -> Any:
        """Get or create scoped instance."""
        service_type = registration.service_type
        
        # Ensure scope exists
        if scope_name not in self._scopes:
            self._scopes[scope_name] = ServiceScope(scope_name)
        
        scope = self._scopes[scope_name]
        instance = scope.get_instance(service_type)
        
        if instance is None:
            instance = self._create_instance(registration)
            scope.set_instance(service_type, instance)
            
            # Add disposal hooks to scope
            for hook in self._disposal_hooks:
                scope.add_disposal_handler(hook)
        
        return instance

    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """Create new service instance."""
        if registration.factory:
            instance = registration.factory()
        elif registration.implementation:
            instance = registration.implementation
        else:
            raise ValueError(f"No factory or implementation for {registration.service_type.__name__}")
        
        # Track instance
        self._created_instances.add(instance)
        
        # Initialize if needed
        if isinstance(instance, IServiceInitializer):
            instance.initialize()
        
        # Call initialization hooks
        for hook in self._initialization_hooks:
            try:
                hook(instance)
            except Exception as e:
                print(f"Initialization hook failed: {e}")
        
        return instance

    def _dispose_instance(self, instance: Any) -> None:
        """Dispose service instance."""
        # Call disposal hooks
        for hook in self._disposal_hooks:
            try:
                hook(instance)
            except Exception as e:
                print(f"Disposal hook failed: {e}")
        
        # Dispose if implements interface
        if isinstance(instance, IServiceDisposable):
            try:
                instance.dispose()
            except Exception as e:
                print(f"Service disposal failed: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic disposal."""
        self.dispose_all()

    def __repr__(self) -> str:
        """String representation for debugging."""
        with self._lock:
            service_count = len(self._registrations)
            singleton_count = len(self._singleton_instances)
            scope_count = len(self._scopes)
            
        return (f"EnhancedServiceContainer(services={service_count}, "
                f"singletons={singleton_count}, scopes={scope_count})")
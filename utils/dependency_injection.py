"""
Lightweight Dependency Injection Framework
==========================================

A minimalist dependency injection container designed for the financial analysis system
to reduce coupling between modules, enable better testing, and improve modularity.

Key Features:
- Constructor injection for clean dependencies
- Service lifecycle management (singleton, transient)
- Circular dependency detection
- Type-safe dependency resolution
- Minimal overhead and simple API

Usage Example:
>>> container = DIContainer()
>>> container.register(DatabaseConfig, lambda: DatabaseConfig("localhost", 5432))
>>> container.register(DataManager, DataManager, [DatabaseConfig])
>>> data_manager = container.resolve(DataManager)
"""

import logging
import threading
from typing import Dict, Any, Callable, Type, List, Optional, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime management options"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"


@dataclass
class ServiceDescriptor:
    """Describes a service registration"""
    service_type: Type
    implementation: Optional[Type] = None
    factory: Optional[Callable] = None
    dependencies: List[Type] = None
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    instance: Any = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class DependencyInjectionError(Exception):
    """Base exception for dependency injection errors"""
    pass


class CircularDependencyError(DependencyInjectionError):
    """Raised when circular dependencies are detected"""
    pass


class ServiceNotRegisteredError(DependencyInjectionError):
    """Raised when trying to resolve an unregistered service"""
    pass


class DIContainer:
    """
    Lightweight dependency injection container
    
    Features:
    - Service registration with lifetime management
    - Automatic dependency resolution
    - Circular dependency detection
    - Thread-safe operations
    """

    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._resolution_stack: List[Type] = []
        self._lock = threading.Lock()
        logger.debug("DIContainer initialized")

    def register(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        dependencies: Optional[List[Type]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    ) -> 'DIContainer':
        """
        Register a service in the container
        
        Args:
            service_type: The service interface/type to register
            implementation: Concrete implementation class (if different from service_type)
            factory: Factory function to create instances
            dependencies: List of dependency types required by the service
            lifetime: Service lifetime (SINGLETON or TRANSIENT)
            
        Returns:
            Self for method chaining
        """
        with self._lock:
            if implementation is None and factory is None:
                implementation = service_type

            descriptor = ServiceDescriptor(
                service_type=service_type,
                implementation=implementation,
                factory=factory,
                dependencies=dependencies or [],
                lifetime=lifetime
            )

            self._services[service_type] = descriptor
            logger.debug(f"Registered service: {service_type.__name__} with lifetime {lifetime.value}")
            
        return self

    def register_instance(self, service_type: Type[T], instance: T) -> 'DIContainer':
        """
        Register a pre-created instance as a singleton
        
        Args:
            service_type: The service type
            instance: Pre-created instance
            
        Returns:
            Self for method chaining
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                service_type=service_type,
                lifetime=ServiceLifetime.SINGLETON,
                instance=instance
            )
            self._services[service_type] = descriptor
            logger.debug(f"Registered instance: {service_type.__name__}")
            
        return self

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service instance
        
        Args:
            service_type: The service type to resolve
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotRegisteredError: If service is not registered
            CircularDependencyError: If circular dependency detected
        """
        with self._lock:
            return self._resolve_internal(service_type)

    def _resolve_internal(self, service_type: Type[T]) -> T:
        """Internal resolution method (not thread-safe, assumes lock held)"""
        
        # Check for circular dependencies
        if service_type in self._resolution_stack:
            cycle = " -> ".join([t.__name__ for t in self._resolution_stack + [service_type]])
            raise CircularDependencyError(f"Circular dependency detected: {cycle}")

        # Check if service is registered
        if service_type not in self._services:
            raise ServiceNotRegisteredError(f"Service {service_type.__name__} is not registered")

        descriptor = self._services[service_type]

        # Return existing singleton instance if available
        if descriptor.lifetime == ServiceLifetime.SINGLETON and descriptor.instance is not None:
            logger.debug(f"Returning cached singleton: {service_type.__name__}")
            return descriptor.instance

        # Add to resolution stack for circular dependency detection
        self._resolution_stack.append(service_type)

        try:
            # Create instance
            if descriptor.factory:
                logger.debug(f"Creating instance using factory: {service_type.__name__}")
                instance = descriptor.factory()
            else:
                # Resolve dependencies
                dependency_instances = []
                for dep_type in descriptor.dependencies:
                    logger.debug(f"Resolving dependency {dep_type.__name__} for {service_type.__name__}")
                    dependency_instances.append(self._resolve_internal(dep_type))

                # Create instance with dependencies
                logger.debug(f"Creating instance with dependencies: {service_type.__name__}")
                instance = descriptor.implementation(*dependency_instances)

            # Store singleton instance
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                descriptor.instance = instance
                logger.debug(f"Cached singleton instance: {service_type.__name__}")

            return instance

        finally:
            # Remove from resolution stack
            self._resolution_stack.pop()

    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered"""
        with self._lock:
            return service_type in self._services

    def get_registration_info(self, service_type: Type) -> Optional[Dict[str, Any]]:
        """Get registration information for a service"""
        with self._lock:
            if service_type not in self._services:
                return None
                
            descriptor = self._services[service_type]
            return {
                "service_type": descriptor.service_type.__name__,
                "implementation": descriptor.implementation.__name__ if descriptor.implementation else None,
                "has_factory": descriptor.factory is not None,
                "dependencies": [dep.__name__ for dep in descriptor.dependencies],
                "lifetime": descriptor.lifetime.value,
                "has_instance": descriptor.instance is not None
            }

    def get_all_registrations(self) -> Dict[str, Dict[str, Any]]:
        """Get all service registrations"""
        with self._lock:
            return {
                service_type.__name__: self.get_registration_info(service_type)
                for service_type in self._services.keys()
            }

    def clear(self) -> None:
        """Clear all service registrations"""
        with self._lock:
            self._services.clear()
            self._resolution_stack.clear()
            logger.debug("DIContainer cleared")

    def validate_dependencies(self) -> Dict[str, List[str]]:
        """
        Validate all registered dependencies
        
        Returns:
            Dict mapping service names to lists of validation errors
        """
        errors = defaultdict(list)
        
        with self._lock:
            for service_type, descriptor in self._services.items():
                service_name = service_type.__name__
                
                # Check if all dependencies are registered
                for dep_type in descriptor.dependencies:
                    if dep_type not in self._services:
                        errors[service_name].append(f"Dependency {dep_type.__name__} is not registered")
                
                # Try to detect circular dependencies
                try:
                    self._check_circular_dependency(service_type, set())
                except CircularDependencyError as e:
                    errors[service_name].append(str(e))
        
        return dict(errors)

    def _check_circular_dependency(self, service_type: Type, visited: set) -> None:
        """Recursively check for circular dependencies"""
        if service_type in visited:
            raise CircularDependencyError(f"Circular dependency involving {service_type.__name__}")
        
        if service_type not in self._services:
            return
            
        visited.add(service_type)
        descriptor = self._services[service_type]
        
        for dep_type in descriptor.dependencies:
            self._check_circular_dependency(dep_type, visited.copy())


# Global container instance for convenience
_global_container: Optional[DIContainer] = None
_container_lock = threading.Lock()


def get_global_container() -> DIContainer:
    """Get or create the global DI container"""
    global _global_container
    
    if _global_container is None:
        with _container_lock:
            if _global_container is None:
                _global_container = DIContainer()
                logger.debug("Global DIContainer created")
    
    return _global_container


def register_service(
    service_type: Type[T],
    implementation: Optional[Type[T]] = None,
    factory: Optional[Callable[[], T]] = None,
    dependencies: Optional[List[Type]] = None,
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
) -> None:
    """Register a service in the global container"""
    get_global_container().register(service_type, implementation, factory, dependencies, lifetime)


def register_instance(service_type: Type[T], instance: T) -> None:
    """Register an instance in the global container"""
    get_global_container().register_instance(service_type, instance)


def resolve_service(service_type: Type[T]) -> T:
    """Resolve a service from the global container"""
    return get_global_container().resolve(service_type)


def clear_global_container() -> None:
    """Clear the global container"""
    global _global_container
    if _global_container:
        _global_container.clear()


class DIContextManager:
    """Context manager for dependency injection setup"""
    
    def __init__(self, container: Optional[DIContainer] = None):
        self.container = container or DIContainer()
        self._original_global = None
        
    def __enter__(self) -> DIContainer:
        global _global_container
        self._original_global = _global_container
        _global_container = self.container
        return self.container
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _global_container
        _global_container = self._original_global


# Decorator for automatic dependency injection
def inject(*dependency_types: Type):
    """
    Decorator to automatically inject dependencies into a function/method
    
    Args:
        *dependency_types: Types to inject as function arguments
        
    Usage:
        @inject(DatabaseConfig, ApiClient)
        def process_data(db_config: DatabaseConfig, api_client: ApiClient, user_param: str):
            # db_config and api_client are automatically injected
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            container = get_global_container()
            injected_args = []
            
            for dep_type in dependency_types:
                injected_args.append(container.resolve(dep_type))
            
            return func(*(injected_args + list(args)), **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator
"""
Dependency Injection Framework
==============================

A lightweight dependency injection container for managing service dependencies
and object lifecycles in the financial analysis application.

This framework provides:
- Service registration and resolution
- Multiple service lifetimes (Singleton, Transient, Scoped)
- Circular dependency detection
- Thread-safe operations
- Global container management
"""

import threading
import inspect
from typing import Any, Dict, Type, Callable, Optional, TypeVar, Generic
from enum import Enum
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime enumeration"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class DependencyInjectionError(Exception):
    """Base exception for dependency injection errors"""
    pass


class CircularDependencyError(DependencyInjectionError):
    """Exception raised when circular dependencies are detected"""
    pass


class ServiceNotRegisteredError(DependencyInjectionError):
    """Exception raised when attempting to resolve an unregistered service"""
    pass


class ServiceRegistration:
    """Service registration information"""

    def __init__(
        self,
        service_type: Type,
        implementation: Any,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.instance = None


class DIContainer:
    """
    Dependency injection container for service registration and resolution
    """

    def __init__(self):
        self._services: Dict[Type, ServiceRegistration] = {}
        self._lock = threading.RLock()
        self._resolution_stack = set()

    def register(
        self,
        service_type: Type[T],
        implementation: Any = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ) -> 'DIContainer':
        """
        Register a service with the container

        Args:
            service_type: The service type/interface
            implementation: The implementation (class or instance)
            lifetime: Service lifetime

        Returns:
            Self for method chaining
        """
        with self._lock:
            if implementation is None:
                implementation = service_type

            registration = ServiceRegistration(service_type, implementation, lifetime)
            self._services[service_type] = registration

            logger.debug(f"Registered service {service_type.__name__} with lifetime {lifetime.value}")
            return self

    def register_singleton(self, service_type: Type[T], implementation: Any = None) -> 'DIContainer':
        """Register a singleton service"""
        return self.register(service_type, implementation, ServiceLifetime.SINGLETON)

    def register_transient(self, service_type: Type[T], implementation: Any = None) -> 'DIContainer':
        """Register a transient service"""
        return self.register(service_type, implementation, ServiceLifetime.TRANSIENT)

    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service from the container

        Args:
            service_type: The service type to resolve

        Returns:
            Service instance

        Raises:
            ServiceNotRegisteredError: If service is not registered
            CircularDependencyError: If circular dependency detected
        """
        with self._lock:
            # Check for circular dependencies
            if service_type in self._resolution_stack:
                raise CircularDependencyError(f"Circular dependency detected for {service_type.__name__}")

            if service_type not in self._services:
                raise ServiceNotRegisteredError(f"Service {service_type.__name__} is not registered")

            registration = self._services[service_type]

            # Return existing singleton instance
            if registration.lifetime == ServiceLifetime.SINGLETON and registration.instance is not None:
                return registration.instance

            # Add to resolution stack
            self._resolution_stack.add(service_type)

            try:
                instance = self._create_instance(registration)

                # Store singleton instance
                if registration.lifetime == ServiceLifetime.SINGLETON:
                    registration.instance = instance

                return instance

            finally:
                # Remove from resolution stack
                self._resolution_stack.discard(service_type)

    def _create_instance(self, registration: ServiceRegistration) -> Any:
        """Create an instance of the registered service"""
        implementation = registration.implementation

        # If implementation is already an instance, return it
        if not inspect.isclass(implementation):
            return implementation

        # Get constructor parameters
        sig = inspect.signature(implementation.__init__)
        params = {}

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # Try to resolve parameter from container
            param_type = param.annotation
            if param_type != inspect.Parameter.empty:
                try:
                    params[param_name] = self.resolve(param_type)
                except ServiceNotRegisteredError:
                    # Use default value if available
                    if param.default != inspect.Parameter.empty:
                        params[param_name] = param.default
                    else:
                        # For unresolvable parameters without defaults, pass None
                        params[param_name] = None

        return implementation(**params)

    def clear(self):
        """Clear all registered services"""
        with self._lock:
            self._services.clear()
            self._resolution_stack.clear()
            logger.debug("Container cleared")


# Global container instance
_global_container = DIContainer()
_container_lock = threading.RLock()


def get_global_container() -> DIContainer:
    """Get the global DI container"""
    return _global_container


def register_service(
    service_type: Type[T],
    implementation: Any = None,
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
) -> DIContainer:
    """Register a service with the global container"""
    return _global_container.register(service_type, implementation, lifetime)


def resolve_service(service_type: Type[T]) -> T:
    """Resolve a service from the global container"""
    return _global_container.resolve(service_type)


def clear_global_container():
    """Clear the global container"""
    with _container_lock:
        _global_container.clear()


class DIContextManager:
    """Context manager for dependency injection scopes"""

    def __init__(self, container: DIContainer = None):
        self.container = container or get_global_container()
        self._original_services = {}

    def __enter__(self):
        # Store original services for restoration
        self._original_services = self.container._services.copy()
        return self.container

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original services
        self.container._services = self._original_services


def inject(service_type: Type[T]) -> T:
    """
    Decorator for injecting dependencies into function parameters

    Usage:
        @inject
        def my_function(service: SomeService):
            return service.do_something()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind_partial(*args, **kwargs)

            # Inject missing parameters
            for param_name, param in sig.parameters.items():
                if param_name not in bound_args.arguments:
                    param_type = param.annotation
                    if param_type != inspect.Parameter.empty:
                        try:
                            injected_value = resolve_service(param_type)
                            bound_args.arguments[param_name] = injected_value
                        except ServiceNotRegisteredError:
                            # Use default if available
                            if param.default != inspect.Parameter.empty:
                                bound_args.arguments[param_name] = param.default

            return func(**bound_args.arguments)
        return wrapper
    return decorator
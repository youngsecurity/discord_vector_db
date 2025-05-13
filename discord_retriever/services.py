"""
Service provider for dependency injection in Discord Message Vector DB.

This module provides a centralized registry for service dependencies,
making it easier to manage, test, and extend the application.
"""

from typing import Any, Dict, Optional, Type, TypeVar, cast, get_type_hints, Generic
from typing import Protocol, runtime_checkable

# Type variable for generic type safety
T = TypeVar('T')
C = TypeVar('C')


class ServiceProvider:
    """
    Central registry for service dependencies.
    
    This class implements a simple service locator pattern for dependency
    injection, allowing components to access shared dependencies.
    """
    
    # Class variable to store service implementations
    _services: Dict[Type[Any], Any] = {}
    
    @classmethod
    def register(cls, interface: Type[Any], implementation: Any) -> None:
        """
        Register a service implementation.
        
        Args:
            interface: The protocol or interface type
            implementation: The concrete implementation
            
        Raises:
            TypeError: If the implementation does not satisfy the interface
        """
        # Runtime check for protocol compatibility
        if hasattr(interface, "__runtime_checkable__") and not isinstance(implementation, interface):
            raise TypeError(f"Implementation {implementation.__class__.__name__} does not satisfy {interface.__name__}")
        
        cls._services[interface] = implementation
    
    @classmethod
    def get(cls, interface: Type[Any]) -> Any:
        """
        Get a service implementation.
        
        Args:
            interface: The protocol or interface type
            
        Returns:
            The registered implementation
            
        Raises:
            ValueError: If no implementation is registered for the interface
        """
        if interface not in cls._services:
            raise ValueError(f"No implementation registered for {interface.__name__}")
        
        return cls._services[interface]
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered services (primarily for testing)."""
        cls._services.clear()
        
    @classmethod
    def has_implementation(cls, interface: Type[Any]) -> bool:
        """
        Check if an implementation is registered for an interface.
        
        Args:
            interface: The protocol or interface type
            
        Returns:
            True if an implementation is registered, False otherwise
        """
        return interface in cls._services


def inject(cls: Type[C]) -> Type[C]:
    """
    Class decorator for automatic dependency injection.
    
    This decorator automatically injects dependencies from the ServiceProvider
    into a class based on type annotations.
    
    Args:
        cls: The class to inject dependencies into
        
    Returns:
        The modified class with dependency injection
        
    Example:
        @inject
        class MyClass:
            vector_db: VectorDatabase
            model: EmbeddingModel
            
            def __init__(self, other_param: str):
                self.other_param = other_param
    """
    original_init = cls.__init__
    
    # Get type hints for the class
    hints = get_type_hints(cls)
    
    def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
        # Call the original __init__ method
        original_init(self, *args, **kwargs)
        
        # Inject dependencies from ServiceProvider
        for attr_name, attr_type in hints.items():
            # Skip attributes that are already set or don't exist
            if hasattr(self, attr_name) and getattr(self, attr_name) is not None:
                continue
            
            # Skip special attributes and methods
            if attr_name.startswith('__') and attr_name.endswith('__'):
                continue
            
            # Check if we have an implementation for this type
            if ServiceProvider.has_implementation(attr_type):
                setattr(self, attr_name, ServiceProvider.get(attr_type))
    
    cls.__init__ = __init__  # type: ignore
    return cls

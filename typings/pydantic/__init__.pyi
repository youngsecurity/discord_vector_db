from typing import Any, Dict, List, Optional, Type, TypeVar, Union, overload, Callable
from typing_extensions import TypedDict, Literal, Protocol
from pathlib import Path
from datetime import datetime

T = TypeVar('T')

class ConfigDictOptions(TypedDict, total=False):
    """Type hint for Pydantic ConfigDict options."""
    env_prefix: str
    env_nested_delimiter: str
    populate_by_name: bool
    str_strip_whitespace: bool
    str_to_lower: bool
    str_to_upper: bool
    arbitrary_types_allowed: bool
    extra: str
    frozen: bool
    use_enum_values: bool
    validate_assignment: bool
    json_schema_extra: Dict[str, Any]

# Support multiple overloads for ConfigDict to handle different combinations of parameters
@overload
def ConfigDict() -> Dict[str, Any]: ...
@overload
def ConfigDict(*, env_prefix: str) -> Dict[str, Any]: ...
@overload
def ConfigDict(*, env_nested_delimiter: str) -> Dict[str, Any]: ...
@overload
def ConfigDict(*, env_prefix: str, env_nested_delimiter: str) -> Dict[str, Any]: ...

class ValidationInfo:
    """Validation info for field validators."""
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]]
    
    def __init__(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> None: ...

class BaseModel:
    """Stub for Pydantic BaseModel with V2 features."""
    model_config: Dict[str, Any]
    
    def __init__(self, **data: Any) -> None: ...
    
    # Make Config class very flexible to avoid type conflicts
    class Config: ...

# Common field type for annotations
def Field(
    default: Any = ...,
    *,
    default_factory: Optional[Callable[[], Any]] = None,
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    exclude: Optional[Union[bool, Callable[[Any], bool]]] = None,
    include: Optional[Union[bool, Callable[[Any], bool]]] = None,
    **extra: Any
) -> Any: ...

# Validator functions
def field_validator(
    *fields: str, 
    mode: str = ..., 
    check_fields: bool = ...,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...

# Root validator
def model_validator(
    mode: str = ...,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...

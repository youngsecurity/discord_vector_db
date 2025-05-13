"""
Type stubs for the typer library.

These stubs use modern Python 3.10+ typing notation.
"""

import enum
from typing import Callable, Sequence, TypeVar, ClassVar, TypeAlias

# Define specific type aliases to avoid Any usage
# Using object as a more typesafe alternative to Any

# More specific type alternatives
StrAny: TypeAlias = dict[str, object]  # For string-keyed dictionaries of any values
AnyCallable: TypeAlias = Callable[..., object]  # For functions with any signature
AnyValue: TypeAlias = object  # For truly unknown values

# Type variables
T = TypeVar("T")
F = TypeVar("F", bound=AnyCallable)
CommandFunctionType = TypeVar("CommandFunctionType", bound=AnyCallable)

class Context:
    """Context for a command with info about the command line app."""
    obj: AnyValue
    info_name: str | None
    invoked_subcommand: str | None
    parent: "Context" | None
    params: dict[str, AnyValue]
    command: "Command"
    
class CallbackParam:
    """Base class for Argument and Option."""
    name: str
    type: AnyValue
    default: AnyValue
    callback: AnyCallable | None
    help: str | None
    hidden: bool

class Command:
    """A command in a CLI app."""
    name: str
    callback: AnyCallable
    help: str | None
    hidden: bool
    context_settings: dict[str, AnyValue]
    params: list[CallbackParam]

class Typer:
    """The main class to create a CLI application."""
    info: ClassVar[dict[str, AnyValue]]
    
    def __init__(
        self,
        *,
        name: str | None = None,
        help: str | None = None,
        add_completion: bool = True,
        no_args_is_help: bool = False,
        invoke_without_command: bool = False,
        callback: AnyCallable | None = None,
        rich_markup_mode: str = "rich",
        context_settings: dict[str, AnyValue] | None = None,
        pretty_exceptions_enable: bool = True,
        pretty_exceptions_show_locals: bool = False,
        pretty_exceptions_short: bool = False,
    ) -> None: ...
    
    def callback(
        self, 
        name: str | None = None,
        *,
        help: str | None = None,
        rich_help_panel: str | None = None,
    ) -> Callable[[F], F]: ...
    
    def command(
        self,
        name: str | None = None,
        *,
        help: str | None = None,
        rich_help_panel: str | None = None,
        context_settings: dict[str, AnyValue] | None = None,
        hidden: bool = False,
    ) -> Callable[[CommandFunctionType], CommandFunctionType]: ...
    
    def add_typer(
        self,
        typer_instance: "Typer",
        *,
        name: str | None = None,
        help: str | None = None,
        rich_help_panel: str | None = None,
        context_settings: dict[str, AnyValue] | None = None,
        hidden: bool = False,
    ) -> None: ...
    
    def __call__(
        self,
        *,
        prog_name: str | None = None,
        standalone_mode: bool = True,
        **kwargs: AnyValue,
    ) -> AnyValue: ...

class ParamTypes(enum.Enum):
    """Enum for param types."""
    STRING = "string"
    INT = "integer"
    FLOAT = "number"
    BOOL = "boolean"
    UUID = "string"
    DATETIME = "string"
    PATH = "string"
    CHOICE = "choice"

class OptionClass(CallbackParam):
    """Represents a command line option."""
    pass

# The actual Option function that typer makes available
def Option(  # type: ignore
    default: AnyValue = None,
    *,
    param_decls: Sequence[str] | None = None,
    callback: AnyCallable | None = None,
    metavar: str | None = None,
    expose_value: bool = True,
    is_eager: bool = False,
    envvar: str | list[str] | None = None,
    shell_complete: AnyCallable | None = None,
    autocompletion: AnyCallable | None = None,
    show_default: bool = True,
    show_choices: bool = True,
    show_envvar: bool = False,
    help: str | None = None,
    hidden: bool = False,
    case_sensitive: bool = True,
    min: int | float | None = None,
    max: int | float | None = None,
    clamp: bool = False,
    formats: list[str] | None = None,
    mode: str | None = None,
    exists: bool = False,
    file_okay: bool = True,
    dir_okay: bool = True,
    writable: bool = False,
    readable: bool = True,
    resolve_path: bool = False,
    allow_dash: bool = False,
    path_type: type[object] | None = None,
    rich_help_panel: str | None = None,
) -> object: ...

class ArgumentClass(CallbackParam):
    """Represents a command line argument."""
    pass

# The actual Argument function that typer makes available
def Argument(  # type: ignore
    default: AnyValue = None,
    *,
    param_decls: Sequence[str] | None = None,
    callback: AnyCallable | None = None,
    metavar: str | None = None,
    expose_value: bool = True,
    is_eager: bool = False,
    envvar: str | list[str] | None = None,
    shell_complete: AnyCallable | None = None,
    autocompletion: AnyCallable | None = None,
    show_default: bool = True,
    show_choices: bool = True,
    show_envvar: bool = False,
    help: str | None = None,
    hidden: bool = False,
    case_sensitive: bool = True,
    min: int | float | None = None,
    max: int | float | None = None,
    clamp: bool = False,
    formats: list[str] | None = None,
    mode: str | None = None,
    exists: bool = False,
    file_okay: bool = True,
    dir_okay: bool = True,
    writable: bool = False,
    readable: bool = True,
    resolve_path: bool = False,
    allow_dash: bool = False,
    path_type: type[object] | None = None,
    rich_help_panel: str | None = None,
) -> object: ...

def run(
    function: AnyCallable | None = None,
    *,
    name: str | None = None,
    help: str | None = None,
    add_completion: bool = True,
    no_args_is_help: bool = False,
    invoke_without_command: bool = False,
    catch_exceptions: bool = True,
    pretty_exceptions_enable: bool = True,
    pretty_exceptions_show_locals: bool = False,
    pretty_exceptions_short: bool = False,
    **kwargs: AnyValue,
) -> AnyValue: ...

def secho(
    message: str | None = None,
    file: AnyValue = None,
    nl: bool = True,
    err: bool = False,
    color: bool | None = None,
    **styles: AnyValue,
) -> None: ...

def echo(
    message: str | None = None,
    file: AnyValue = None,
    nl: bool = True,
    err: bool = False,
    color: bool | None = None,
) -> None: ...

def prompt(
    text: str,
    default: str | None = None,
    hide_input: bool = False,
    confirmation_prompt: bool = False,
    type: AnyValue | None = None,
    value_proc: AnyCallable | None = None,
    prompt_suffix: str = ": ",
    show_default: bool = True,
    err: bool = False,
) -> AnyValue: ...

def confirm(
    text: str,
    default: bool = False,
    abort: bool = False,
    prompt_suffix: str = ": ",
    show_default: bool = True,
    err: bool = False,
) -> bool: ...

__all__ = [
    "Argument",
    "CallbackParam",
    "Command",
    "Context",
    "Option",
    "ParamTypes",
    "Typer",
    "confirm",
    "echo",
    "prompt",
    "run",
    "secho",
]

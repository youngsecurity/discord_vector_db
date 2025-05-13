"""
Type stubs for rich.console module.

These stubs use modern Python 3.10+ typing notation.
"""

from typing import Any, Callable, Dict, List, Sequence, Protocol, TypeVar, Iterator, Type, ClassVar, overload

class ConsoleOptions:
    """Console options for rendering."""
    max_width: int
    min_width: int
    encoding: str
    is_terminal: bool

class RenderResult:
    """Result of rendering."""
    ...

class RenderableType(Protocol):
    """A renderable object."""
    def __rich_console__(self, console: "Console", options: ConsoleOptions) -> Iterator[Any]: ...

T = TypeVar("T")

class Console:
    """Rich console for pretty printing."""
    
    options_class: ClassVar[Type[ConsoleOptions]]
    
    def __init__(
        self,
        *,
        file: Any | None = None,
        width: int | None = None,
        height: int | None = None,
        color_system: str | None = None,
        force_terminal: bool | None = None,
        force_jupyter: bool | None = None,
        force_interactive: bool | None = None,
        soft_wrap: bool | None = None,
        tab_size: int = 8,
        record: bool = False,
        markup: bool = True,
        emoji: bool = True,
        highlight: bool = True,
        log_time: bool = True,
        log_path: bool = True,
        log_time_format: str | None = None,
        highlight_background_color: str | None = None,
    ) -> None: ...
    
    def print(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: str | Dict[str, Any] | None = None,
        justify: str | None = None,
        overflow: str | None = None,
        crop: bool = True,
        markup: bool | None = None,
        emoji: bool | None = None,
        highlight: bool | None = None,
        width: int | None = None,
        height: int | None = None,
        no_wrap: bool | None = None,
        soft_wrap: bool | None = None,
    ) -> None: ...
    
    def log(
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        style: str | Dict[str, Any] | None = None,
        justify: str | None = None,
        overflow: str | None = None,
        crop: bool = True,
        markup: bool | None = None,
        emoji: bool | None = None,
        highlight: bool | None = None,
        width: int | None = None,
        height: int | None = None,
        no_wrap: bool | None = None,
        soft_wrap: bool | None = None,
        level: str | None = None,
    ) -> None: ...
    
    def input(
        self,
        prompt: str = "",
        *,
        password: bool = False,
        stream: Any | None = None,
        markup: bool | None = None,
        emoji: bool | None = None,
        highlight: bool | None = None,
    ) -> str: ...
    
    @overload
    def status(
        self,
        status: str,
        *,
        spinner: str = "dots",
        spinner_style: str = "status.spinner",
        speed: float = 1.0,
        refresh_per_second: float = 12.5,
    ) -> Any: ...
    
    @overload
    def status(
        self,
        status: str,
        *,
        console: "Console" | None = None,
        spinner: str = "dots",
        spinner_style: str = "status.spinner",
        speed: float = 1.0,
        refresh_per_second: float = 12.5,
    ) -> Any: ...

class Group:
    """A renderable that groups other renderables together."""
    
    def __init__(self, *renderables: Any, fit: bool = True) -> None: ...
    
    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult: ...

__all__ = [
    "Console",
    "ConsoleOptions",
    "Group",
    "RenderResult",
    "RenderableType",
]

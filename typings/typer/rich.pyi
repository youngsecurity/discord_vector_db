"""
Type stubs for rich components used with typer.

These stubs use modern Python 3.10+ typing notation.
"""

from typing import Callable, Sequence, Protocol, runtime_checkable, TextIO
from rich.progress import ProgressColumn

class ConsoleOptions:
    """Console options for rendering."""
    max_width: int
    min_width: int
    encoding: str
    is_terminal: bool

class RenderResult:
    """Result of rendering."""
    ...

@runtime_checkable
class RenderableType(Protocol):
    """A renderable object."""
    def __rich_console__(self, console: "Console", options: ConsoleOptions) -> RenderResult: ...

class Console:
    """Rich console for pretty printing."""
    
    def __init__(
        self,
        *,
        file: TextIO | None = None,
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
        *objects: RenderableType | str | object,
        sep: str = " ",
        end: str = "\n",
        style: str | dict[str, object] | None = None,
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

class RichHandler:
    """Rich handler for logging."""
    
    def __init__(
        self,
        *,
        level: int | str = 20,
        console: Console | None = None,
        show_time: bool = True,
        show_level: bool = True,
        show_path: bool = True,
        enable_link_path: bool = True,
        rich_tracebacks: bool = False,
        tracebacks_width: int | None = None,
        tracebacks_extra_lines: int = 3,
        tracebacks_theme: str | None = None,
        tracebacks_word_wrap: bool = True,
        tracebacks_show_locals: bool = False,
        tracebacks_suppress: Sequence[str | type[BaseException]] = (),
        locals_max_length: int = 10,
        locals_max_string: int = 80,
        markup: bool = False,
        keywords: list[str] | None = None,
        omit_repeated_times: bool = True,
        level_styles: dict[str, str] | None = None,
        highlighter: RenderableType | None = None,
        log_time_format: str | None = None,
    ) -> None: ...

class Progress:
    """Progress bar context manager."""
    
    def __init__(
        self,
        *columns: str | ProgressColumn,
        console: Console | None = None,
        auto_refresh: bool = True,
        refresh_per_second: float = 10,
        speed_estimate_period: float = 30.0,
        transient: bool = False,
        redirect_stdout: bool = True,
        redirect_stderr: bool = True,
        get_time: Callable[[], float] | None = None,
        disable: bool = False,
        expand: bool = False,
    ) -> None: ...
    
    def __enter__(self) -> "Progress": ...
    
    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object | None) -> None: ...
    
    def add_task(
        self,
        description: str,
        *,
        start: bool = True,
        total: float | None = 100.0,
        completed: float = 0,
        visible: bool = True,
        **fields: object,
    ) -> int: ...
    
    def update(
        self,
        task_id: int,
        *,
        description: str | None = None,
        total: float | None = None,
        completed: float | None = None,
        advance: float | None = None,
        visible: bool | None = None,
        refresh: bool = False,
        **fields: object,
    ) -> None: ...

class SpinnerColumn:
    """Column with a spinner animation."""
    
    def __init__(
        self,
        spinner_name: str = "dots",
        style: str | None = None,
        speed: float = 1.0,
        finished_text: str = "✓",
    ) -> None: ...

class TextColumn:
    """Column containing text."""
    
    def __init__(
        self,
        text_format: str,
        style: str | None = None,
        justify: str | None = None,
        no_wrap: bool = False,
        width: int | None = None,
    ) -> None: ...

class Table:
    """Rich table for tabular data."""
    
    def __init__(
        self,
        *,
        title: str | None = None,
        caption: str | None = None,
        width: int | None = None,
        min_width: int | None = None,
        box: object | None = None,
        safe_box: bool = True,
        padding: int | tuple[int, int] = (0, 1),
        collapse_padding: bool = False,
        pad_edge: bool = True,
        expand: bool = False,
        show_header: bool = True,
        show_footer: bool = False,
        show_edge: bool = True,
        show_lines: bool = False,
        leading: int = 1,
        style: str | None = None,
        row_styles: list[str] | None = None,
        header_style: str | None = None,
        footer_style: str | None = None,
        border_style: str | None = None,
        title_style: str | None = None,
        caption_style: str | None = None,
        title_justify: str | None = "center",
        caption_justify: str | None = "center",
        highlight: bool = False,
    ) -> None: ...
    
    def add_column(
        self,
        header: str = "",
        footer: str = "",
        *,
        header_style: str | None = None,
        footer_style: str | None = None,
        style: str | None = None,
        justify: str | None = None,
        vertical: str | None = None,
        width: int | None = None,
        min_width: int | None = None,
        max_width: int | None = None,
        ratio: int | None = None,
        no_wrap: bool = False,
    ) -> None: ...
    
    def add_row(
        self,
        *renderables: RenderableType | str | object,
        style: str | None = None,
        end_section: bool = False,
    ) -> None: ...

__all__ = [
    "Console",
    "ConsoleOptions",
    "Progress",
    "RenderResult",
    "RenderableType",
    "RichHandler",
    "SpinnerColumn",
    "Table",
    "TextColumn",
]

"""
Type stubs for rich.table module.

These stubs use modern Python 3.10+ typing notation.
"""

from typing import Any, Callable, Dict, List, Sequence, Tuple
import sys

from rich.console import Console, ConsoleOptions, RenderableType

class Column:
    """Represents a column in a table."""
    header: str
    footer: str
    header_style: str | None
    footer_style: str | None
    style: str | None
    justify: str | None
    vertical: str | None
    width: int | None
    min_width: int | None
    max_width: int | None
    ratio: int | None
    no_wrap: bool
    overflow: str | None

class Table:
    """Rich table for tabular data."""
    
    def __init__(
        self,
        *,
        title: str | None = None,
        caption: str | None = None,
        width: int | None = None,
        min_width: int | None = None,
        box: Any | None = None,
        safe_box: bool = True,
        padding: int | Tuple[int, int] = (0, 1),
        collapse_padding: bool = False,
        pad_edge: bool = True,
        expand: bool = False,
        show_header: bool = True,
        show_footer: bool = False,
        show_edge: bool = True,
        show_lines: bool = False,
        leading: int = 1,
        style: str | None = None,
        row_styles: List[str] | None = None,
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
        overflow: str | None = None,
    ) -> None: ...
    
    def add_row(
        self,
        *renderables: Any,
        style: str | None = None,
        end_section: bool = False,
    ) -> None: ...
    
    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> Any: ...
    
    @property
    def columns(self) -> List[Column]: ...
    
    @property
    def row_count(self) -> int: ...
    
    def row(self, index: int) -> List[Any]: ...
    
    def rows(self) -> List[List[Any]]: ...
    
    def render(self) -> Any: ...

__all__ = ["Column", "Table"]

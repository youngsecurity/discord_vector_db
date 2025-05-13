"""
Type stubs for rich.logging module.

These stubs use modern Python 3.10+ typing notation.
"""

from logging import Handler, LogRecord
from typing import Sequence, override

from rich.console import Console

class RichHandler(Handler):
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
        highlighter: object | None = None,
        log_time_format: str | None = None,
    ) -> None: ...
    
    @override
    def emit(self, record: LogRecord) -> None: ...

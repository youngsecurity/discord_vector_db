"""
Type stubs for rich.progress module.

These stubs use modern Python 3.10+ typing notation.
"""

from typing import Any, Callable, Dict, List, Sequence, Protocol, Set, TypeVar, Generic, Iterable
import time
from datetime import timedelta

from rich.console import Console, RenderableType

class Task:
    """Information about a progress task."""
    id: int
    description: str
    total: float
    completed: float
    visible: bool
    fields: Dict[str, Any]

class TaskID(int):
    """A task ID (wrapper around int)."""
    pass

T = TypeVar("T")

class ProgressColumn:
    """Base class for a column in a progress display."""
    def render(self, task: Task) -> RenderableType: ...

class TextColumn(ProgressColumn):
    """A column containing text."""
    
    def __init__(
        self,
        text_format: str,
        style: str | None = None,
        justify: str | None = None,
        no_wrap: bool = False,
        width: int | None = None,
        table_column: Any | None = None,
    ) -> None: ...
    
    def render(self, task: Task) -> RenderableType: ...

class BarColumn(ProgressColumn):
    """A column with a progress bar."""
    
    def __init__(
        self,
        bar_width: int | None = None,
        style: str | None = None,
        complete_style: str | None = None,
        finished_style: str | None = None,
        pulse_style: str | None = None,
        table_column: Any | None = None,
    ) -> None: ...
    
    def render(self, task: Task) -> RenderableType: ...

class SpinnerColumn(ProgressColumn):
    """A column with a spinner animation."""
    
    def __init__(
        self,
        spinner_name: str = "dots",
        style: str | None = None,
        speed: float = 1.0,
        finished_text: str = "✓",
        table_column: Any | None = None,
    ) -> None: ...
    
    def render(self, task: Task) -> RenderableType: ...

class TimeElapsedColumn(ProgressColumn):
    """A column showing time elapsed."""
    
    def __init__(
        self,
        style: str | None = None,
        elapsed_style: str | None = None,
        table_column: Any | None = None,
    ) -> None: ...
    
    def render(self, task: Task) -> RenderableType: ...

class TimeRemainingColumn(ProgressColumn):
    """A column showing time remaining."""
    
    def __init__(
        self,
        style: str | None = None,
        compact: bool = False,
        elapsed_when_finished: bool = True,
        table_column: Any | None = None,
    ) -> None: ...
    
    def render(self, task: Task) -> RenderableType: ...

class FileSizeColumn(ProgressColumn):
    """A column showing file size."""
    
    def __init__(
        self,
        style: str | None = None,
        table_column: Any | None = None,
    ) -> None: ...
    
    def render(self, task: Task) -> RenderableType: ...

class TotalFileSizeColumn(ProgressColumn):
    """A column showing total file size."""
    
    def __init__(
        self,
        style: str | None = None,
        table_column: Any | None = None,
    ) -> None: ...
    
    def render(self, task: Task) -> RenderableType: ...

class DownloadColumn(ProgressColumn):
    """A column showing download speed."""
    
    def __init__(
        self,
        style: str | None = None,
        table_column: Any | None = None,
    ) -> None: ...
    
    def render(self, task: Task) -> RenderableType: ...

class TransferSpeedColumn(ProgressColumn):
    """A column showing transfer speed."""
    
    def __init__(
        self,
        style: str | None = None,
        table_column: Any | None = None,
    ) -> None: ...
    
    def render(self, task: Task) -> RenderableType: ...

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
    
    def start(self) -> None: ...
    
    def stop(self) -> None: ...
    
    def __enter__(self) -> "Progress": ...
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...
    
    def track(
        self,
        sequence: Iterable[T],
        description: str = "Working...",
        total: float | None = None,
        auto_refresh: bool = True,
        console: Console | None = None,
        transient: bool | None = None,
        get_time: Callable[[], float] | None = None,
        refresh_per_second: float | None = None,
        **fields: Any,
    ) -> Iterable[T]: ...
    
    def add_task(
        self,
        description: str,
        *,
        start: bool = True,
        total: float | None = 100.0,
        completed: float = 0,
        visible: bool = True,
        **fields: Any,
    ) -> TaskID: ...
    
    def update(
        self,
        task_id: TaskID,
        *,
        description: str | None = None,
        total: float | None = None,
        completed: float | None = None,
        advance: float | None = None,
        visible: bool | None = None,
        refresh: bool = False,
        **fields: Any,
    ) -> None: ...
    
    def remove_task(self, task_id: TaskID) -> None: ...
    
    def refresh(self) -> None: ...

def track(
    sequence: Iterable[T],
    description: str = "Working...",
    total: float | None = None,
    auto_refresh: bool = True,
    console: Console | None = None,
    transient: bool = False,
    get_time: Callable[[], float] | None = None,
    refresh_per_second: float = 10,
    **fields: Any,
) -> Iterable[T]: ...

__all__ = [
    "BarColumn",
    "DownloadColumn",
    "FileSizeColumn",
    "Progress",
    "ProgressColumn",
    "SpinnerColumn",
    "Task",
    "TaskID",
    "TextColumn",
    "TimeElapsedColumn",
    "TimeRemainingColumn",
    "TotalFileSizeColumn",
    "TransferSpeedColumn",
    "track",
]

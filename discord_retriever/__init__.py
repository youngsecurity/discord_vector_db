"""
Discord Message Vector DB package.

This package provides tools for retrieving Discord messages and storing them in a vector database.
"""

from .models import (
    MessageSource,
    DiscordMessage,
    CheckpointData,
    ProgressTracker,
    CircuitBreaker,
)
from .fetcher import DiscordMessageFetcher, parse_messages
from .processor import VectorDBProcessor, process_for_vector_db
from .privacy import PrivacyFilter, RedactionPattern
from .security import SecureStorage

__version__ = "0.1.0"
__all__ = [
    "MessageSource",
    "DiscordMessage",
    "CheckpointData",
    "ProgressTracker",
    "CircuitBreaker",
    "DiscordMessageFetcher",
    "parse_messages",
    "VectorDBProcessor",
    "process_for_vector_db",
    "PrivacyFilter",
    "RedactionPattern",
    "SecureStorage",
]

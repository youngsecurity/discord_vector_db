"""
Custom exceptions for the Discord Message Vector DB project.

This module defines specific exception types for different components
of the system, improving error handling and providing more actionable
error messages.
"""

from typing import Optional, List


class DiscordRetrievalError(Exception):
    """Base exception for Discord message retrieval errors."""
    pass


class CircuitBreakerOpenError(DiscordRetrievalError):
    """Raised when circuit breaker is open due to repeated failures."""
    def __init__(self, message: str = "Circuit breaker is open due to repeated failures"):
        super().__init__(message)


class RateLimitExceededError(DiscordRetrievalError):
    """Raised when Discord API rate limit is exceeded."""
    def __init__(self, message: str = "Discord API rate limit exceeded", retry_after: Optional[float] = None):
        self.retry_after = retry_after
        super().__init__(f"{message}{f' (retry after {retry_after} seconds)' if retry_after else ''}")


class APIConnectionError(DiscordRetrievalError):
    """Raised when connection to Discord API fails."""
    pass


class DiscordAPIError(DiscordRetrievalError):
    """Raised when Discord API returns an error response."""
    def __init__(self, status_code: int, message: str = "Discord API error"):
        self.status_code = status_code
        super().__init__(f"{message}: HTTP {status_code}")


class MessageProcessingError(Exception):
    """Base exception for message processing errors."""
    pass


class EmbeddingGenerationError(MessageProcessingError):
    """Raised when message embedding generation fails."""
    pass


class VectorDatabaseError(MessageProcessingError):
    """Raised when vector database operations fail."""
    pass


class CollectionNotFoundError(VectorDatabaseError):
    """Raised when a vector database collection cannot be found."""
    def __init__(self, collection_name: str):
        super().__init__(f"Collection not found: {collection_name}")
        self.collection_name = collection_name


class PrivacyError(Exception):
    """Base exception for privacy-related errors."""
    pass


class PIIDetectionError(PrivacyError):
    """Raised when PII detection fails."""
    pass


class OptOutListError(PrivacyError):
    """Raised when there's an error handling the opt-out list."""
    pass


class SecurityError(Exception):
    """Base exception for security-related errors."""
    pass


class EncryptionError(SecurityError):
    """Raised when encryption or decryption fails."""
    pass


class KeyFileError(SecurityError):
    """Raised when there's an error with the encryption key file."""
    pass


class ConfigurationError(Exception):
    """Raised when there's an error in the configuration."""
    
    def __init__(self, message: str, validation_errors: Optional[List[str]] = None):
        self.validation_errors = validation_errors or []
        error_details = ""
        if validation_errors:
            error_details = "\n- " + "\n- ".join(validation_errors)
        super().__init__(f"{message}{error_details}")


class CheckpointError(Exception):
    """Raised when there's an error with checkpoint operations."""
    pass

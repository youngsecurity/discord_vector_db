"""
API contracts for the Discord Message Vector DB project.

This module defines formal interfaces for the project's components using Protocol classes,
making dependencies explicit and improving type safety.
"""

from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Sequence, Union, runtime_checkable


@runtime_checkable
class MessageFetcher(Protocol):
    """Protocol defining the message fetcher interface."""
    
    def fetch_all(self) -> int:
        """
        Fetch all messages from the Discord channel.
        
        This method handles pagination, checkpointing, and error recovery
        to fetch all messages from the specified channel.
        
        Returns:
            Total number of messages fetched
            
        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            RateLimitExceededError: If Discord rate limit is exceeded
            APIConnectionError: If connection to Discord API fails
            DiscordAPIError: If Discord API returns an error response
        """
        ...
    
    @property
    def channel_id(self) -> str:
        """Get the channel ID."""
        ...
    
    @property
    def checkpoint_file(self) -> Path:
        """Get the checkpoint file path."""
        ...


@runtime_checkable
class MessageProcessor(Protocol):
    """Protocol defining message processor interface."""
    
    def process_all(self) -> int:
        """
        Process all message batches and add them to the vector database.
        
        Returns:
            Total number of messages processed
        
        Raises:
            FileNotFoundError: If messages directory doesn't exist
            EmbeddingGenerationError: If embedding generation fails
            VectorDatabaseError: If vector database operations fail
        """
        ...
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector database for messages similar to the query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of search results with content, metadata, and similarity score
            
        Raises:
            VectorDatabaseError: If vector database operations fail
            EmbeddingGenerationError: If embedding generation fails
        """
        ...
    
    @property
    def collection_name(self) -> str:
        """Get the collection name."""
        ...


@runtime_checkable
class PrivacyProcessor(Protocol):
    """Protocol defining privacy processor interface."""
    
    def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a message, applying privacy filters.
        
        Args:
            message: The Discord message to process
            
        Returns:
            Processed message, or None if it should be excluded
            
        Raises:
            PIIDetectionError: If PII detection fails
            OptOutListError: If there's an error handling the opt-out list
        """
        ...
    
    def add_opt_out_user(self, user_id: str) -> None:
        """
        Add a user to the opt-out list.
        
        Args:
            user_id: The user ID to add
            
        Raises:
            OptOutListError: If there's an error updating the opt-out list
        """
        ...
    
    def add_redaction_pattern(self, pattern_type: str, regex: str, replacement: str) -> None:
        """
        Add a new redaction pattern.
        
        Args:
            pattern_type: Type of PII to detect
            regex: Regular expression pattern
            replacement: Text to use as replacement
            
        Raises:
            PIIDetectionError: If the regex pattern is invalid
        """
        ...


@runtime_checkable
class SecureStorage(Protocol):
    """Protocol defining secure storage interface."""
    
    def save_data(self, filename: str, data: Dict[str, Any]) -> Path:
        """
        Save data to a file, optionally encrypting it.
        
        Args:
            filename: Name of the file to save
            data: Data to save (must be JSON serializable)
            
        Returns:
            Path to the saved file
            
        Raises:
            EncryptionError: If encryption fails
            KeyFileError: If there's an error with the encryption key
            OSError: If there's an error writing to the file
        """
        ...
    
    def load_data(self, filename: str) -> Dict[str, Any]:
        """
        Load data from a file, decrypting if necessary.
        
        Args:
            filename: Name of the file to load
            
        Returns:
            Loaded data
            
        Raises:
            FileNotFoundError: If the file does not exist
            EncryptionError: If decryption fails
            KeyFileError: If there's an error with the encryption key
            ValueError: If the file cannot be parsed
        """
        ...
    
    def secure_delete(self, filename: str) -> None:
        """
        Securely delete a file by overwriting it before deletion.
        
        Args:
            filename: Name of the file to delete
            
        Raises:
            FileNotFoundError: If the file does not exist
            OSError: If there's an error deleting the file
        """
        ...
    
    @property
    def encryption_enabled(self) -> bool:
        """Check if encryption is enabled."""
        ...


@runtime_checkable
class VectorDatabase(Protocol):
    """Protocol defining vector database interface."""
    
    def add(self, ids: List[str], embeddings: List[List[float]], 
            documents: List[str], metadatas: List[Dict[str, Any]]) -> None:
        """
        Add items to the vector database.
        
        Args:
            ids: List of unique IDs
            embeddings: List of embedding vectors
            documents: List of document contents
            metadatas: List of metadata dictionaries
            
        Raises:
            VectorDatabaseError: If the operation fails
        """
        ...
    
    def query(self, query_embeddings: List[List[float]], n_results: int,
              include: List[str]) -> Dict[str, Any]:
        """
        Query the vector database.
        
        Args:
            query_embeddings: List of query embedding vectors
            n_results: Number of results to return
            include: What to include in results (e.g., "documents", "metadatas")
            
        Returns:
            Query results
            
        Raises:
            VectorDatabaseError: If the query fails
        """
        ...
    
    def count(self) -> int:
        """
        Get the number of items in the collection.
        
        Returns:
            Number of items
            
        Raises:
            VectorDatabaseError: If the operation fails
        """
        ...


@runtime_checkable
class EmbeddingModel(Protocol):
    """Protocol defining embedding model interface."""
    
    def encode(self, texts: List[str]) -> Any:
        """
        Encode texts into embedding vectors.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            Embedding vectors
            
        Raises:
            EmbeddingGenerationError: If encoding fails
        """
        ...

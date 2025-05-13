"""
Vector database processor for Discord messages.

This module handles converting Discord messages to vector embeddings and
storing them in a vector database for semantic search.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .models import DiscordMessage, ProgressTracker

# Configure logging
logger = logging.getLogger(__name__)


class VectorDBProcessor:
    """
    Process Discord messages and add them to a vector database.
    
    This class handles loading messages from JSON files, generating embeddings,
    and storing them in a vector database for semantic search.
    """
    
    def __init__(
        self,
        messages_directory: Union[str, Path],
        collection_name: str,
        embedding_model: str = "all-MiniLM-L6-v2",
        batch_size: int = 100,
        chroma_client: Optional[Any] = None,
        model: Optional[Any] = None,
    ):
        """
        Initialize the vector database processor.
        
        Args:
            messages_directory: Directory containing message batch files
            collection_name: Name of the vector database collection
            embedding_model: Name of the sentence transformer model to use
            batch_size: Number of messages to process at once
            chroma_client: Optional pre-configured ChromaDB client (for testing)
            model: Optional pre-configured embedding model (for testing)
        """
        self.messages_directory = Path(messages_directory)
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.batch_size = batch_size
        
        # Progress tracking
        self.progress = ProgressTracker()
        
        # Lazy-loaded components or injected dependencies
        self._chroma_client = chroma_client
        self._collection = None
        self._model = model
    
    @property
    def chroma_client(self):
        """Get or create the ChromaDB client."""
        if self._chroma_client is None:
            try:
                import chromadb
                self._chroma_client = chromadb.Client()
                logger.info("Initialized ChromaDB client")
            except ImportError:
                logger.error("chromadb is not installed. Please install it with: pip install chromadb")
                raise
        return self._chroma_client
    
    @property
    def collection(self):
        """Get or create the ChromaDB collection."""
        if self._collection is None:
            try:
                # Try to get existing collection
                self._collection = self.chroma_client.get_or_create_collection(name=self.collection_name)
                logger.info(f"Using collection: {self.collection_name}")
            except Exception as e:
                logger.error(f"Error accessing collection: {e}")
                raise
        return self._collection
    
    @property
    def model(self):
        """Get or create the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.embedding_model)
                logger.info(f"Loaded embedding model: {self.embedding_model}")
            except ImportError:
                logger.error("sentence-transformers is not installed. Please install it with: pip install sentence-transformers")
                raise
        return self._model
        
    # For testing purposes only
    def test_setup(self, mock_collection: Optional[Any] = None, mock_model: Optional[Any] = None):
        """
        Set up test doubles for unit testing.
        
        This method should ONLY be used in tests.
        
        Args:
            mock_collection: Mock collection to use
            mock_model: Mock model to use
        """
        if mock_collection is not None:
            self._collection = mock_collection
        if mock_model is not None:
            self._model = mock_model
    
    def _load_messages_batch(self, batch_file: Path) -> List[Dict[str, Any]]:
        """
        Load messages from a batch file.
        
        Args:
            batch_file: Path to the batch file
            
        Returns:
            List of message dictionaries
        """
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Error loading {batch_file}: {e}")
            return []
    
    def _process_batch(self, messages: List[Dict[str, Any]]) -> None:
        """
        Process a batch of messages and add to vector database.
        
        Args:
            messages: List of message dictionaries
        """
        if not messages:
            return
            
        # Extract message content and metadata
        ids = []
        texts = []
        metadatas = []
        
        for msg in messages:
            # Skip empty messages
            if not msg.get("content"):
                continue
                
            # Create Discord message object
            discord_msg = DiscordMessage.from_dict(msg)
            
            ids.append(discord_msg.id)
            texts.append(discord_msg.content)
            
            # Extract metadata
            metadatas.append({
                "author": discord_msg.author,
                "timestamp": discord_msg.timestamp.isoformat(),
                "channel_id": discord_msg.channel_id,
                "has_attachments": len(discord_msg.attachments) > 0,
                "has_reactions": len(discord_msg.reactions) > 0,
                "has_mentions": len(discord_msg.mentions) > 0,
            })
        
        if not ids:
            logger.warning("No valid messages to process in batch")
            return
            
        # Generate embeddings
        embeddings = self.model.encode(texts)
        
        # Add to vector database
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas
        )
        
        # Update progress
        self.progress.update(len(ids))
        logger.info(f"Added {len(ids)} messages to vector database. Total: {self.progress.processed_items}")
    
    def process_all(self) -> int:
        """
        Process all message batches and add them to the vector database.
        
        Returns:
            Total number of messages processed
        """
        logger.info(f"Starting vector database processing from {self.messages_directory}")
        
        # Find all batch files
        batch_files = sorted(self.messages_directory.glob("messages_batch_*.json"))
        logger.info(f"Found {len(batch_files)} batch files to process")
        
        # Set total for progress tracking
        self.progress.total_items = len(batch_files) * self.batch_size  # Estimate
        
        try:
            for batch_file in batch_files:
                logger.info(f"Processing {batch_file}")
                
                # Load messages from file
                messages = self._load_messages_batch(batch_file)
                
                # Process in smaller sub-batches to avoid memory issues
                for i in range(0, len(messages), self.batch_size):
                    sub_batch = messages[i:i+self.batch_size]
                    self._process_batch(sub_batch)
                
                logger.info(f"Completed processing {batch_file}")
                
        except KeyboardInterrupt:
            logger.info("Process interrupted by user.")
        except Exception as e:
            logger.exception(f"Error processing messages: {e}")
        
        # Get actual count from collection
        total_count = self.collection.count()
        logger.info(f"Vector database populated with {total_count} messages")
        return total_count
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector database for messages similar to the query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of search results
        """
        logger.info(f"Searching for: {query}")
        
        # Generate query embedding
        query_embedding = self.model.encode(query).tolist()
        
        # Search vector database
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results["documents"][0])):
            formatted_results.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity": 1.0 - results["distances"][0][i]  # Convert distance to similarity
            })
            
        return formatted_results


# Convenience function
def process_for_vector_db(
    messages_directory: Union[str, Path],
    collection_name: str,
    embedding_model: str = "all-MiniLM-L6-v2",
    batch_size: int = 100
) -> Any:
    """
    Process Discord messages and add them to a vector database.
    
    Args:
        messages_directory: Directory containing message batch files
        collection_name: Name of the vector database collection
        embedding_model: Name of the sentence transformer model to use
        batch_size: Number of messages to process at once
        
    Returns:
        ChromaDB collection
    """
    processor = VectorDBProcessor(
        messages_directory=messages_directory,
        collection_name=collection_name,
        embedding_model=embedding_model,
        batch_size=batch_size
    )
    
    processor.process_all()
    return processor.collection

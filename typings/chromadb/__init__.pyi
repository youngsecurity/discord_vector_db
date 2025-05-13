"""Type stubs for chromadb module."""

from typing import Any, Dict, List, Optional, Union

class Client:
    """Client for ChromaDB vector database."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the ChromaDB client."""
        ...
    
    def get_or_create_collection(self, name: str, **kwargs: Any) -> "Collection":
        """Get or create a collection with the given name."""
        ...


class Collection:
    """Collection in ChromaDB vector database."""
    
    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        documents: Optional[List[str]] = None,
        **kwargs: Any
    ) -> None:
        """Add items to the collection."""
        ...
    
    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 10,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Query the collection by vector similarity."""
        ...
    
    def count(self) -> int:
        """Get the number of items in the collection."""
        ...

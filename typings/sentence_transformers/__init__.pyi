"""Type stubs for sentence_transformers module."""

from typing import Any, List, Optional, Union, overload

class SentenceTransformer:
    """Sentence Transformer model for creating sentence embeddings."""
    
    def __init__(self, model_name_or_path: str, **kwargs: Any) -> None:
        """
        Initialize the model with a name or path.
        
        Args:
            model_name_or_path: The name or path of the model to load
        """
        ...
    
    def encode(
        self,
        sentences: Union[str, List[str]],
        batch_size: int = 32,
        show_progress_bar: bool = False,
        convert_to_numpy: bool = True,
        **kwargs: Any
    ) -> Any:
        """
        Encode sentences to embeddings.
        
        Args:
            sentences: The sentences to encode
            batch_size: Batch size for encoding
            show_progress_bar: Whether to show a progress bar
            convert_to_numpy: Convert the output to a numpy array
            
        Returns:
            Embeddings for the sentences
        """
        ...
    
    def tolist(self) -> List[List[float]]:
        """Convert embeddings to a Python list."""
        ...

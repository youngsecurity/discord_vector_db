"""
Unit tests for the discord_retriever.processor module.

This module tests the vector database processor functionality, which converts
Discord messages to vector embeddings and stores them in a database.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, cast

import pytest
from pytest_mock import MockFixture

from discord_retriever.processor import VectorDBProcessor


class TestVectorDBProcessor:
    """Tests for the VectorDBProcessor class."""

    def test_initialization(self, temp_message_directory: Path) -> None:
        """Test initialization with various parameters."""
        # Basic initialization
        processor = VectorDBProcessor(
            messages_directory=temp_message_directory,
            collection_name="test_collection",
        )
        
        assert processor.messages_directory == temp_message_directory
        assert processor.collection_name == "test_collection"
        assert processor.embedding_model == "all-MiniLM-L6-v2"
        assert processor.batch_size == 100
        
        # Custom parameters
        processor = VectorDBProcessor(
            messages_directory=temp_message_directory,
            collection_name="test_collection",
            embedding_model="custom-model",
            batch_size=50,
        )
        
        assert processor.embedding_model == "custom-model"
        assert processor.batch_size == 50

    def test_lazy_loading(
        self, temp_message_directory: Path, mock_chroma_client: Any, mock_sentence_transformer: Any
    ) -> None:
        """Test lazy loading of components."""
        processor = VectorDBProcessor(
            messages_directory=temp_message_directory,
            collection_name="test_collection",
        )
        
        # Properties should be None initially
        assert processor._chroma_client is None
        assert processor._collection is None
        assert processor._model is None
        
        # Access properties to trigger lazy loading
        _ = processor.chroma_client
        _ = processor.collection
        _ = processor.model
        
        # Properties should now be set
        assert processor._chroma_client is not None
        assert processor._collection is not None
        assert processor._model is not None

    def test_load_messages_batch(self, tmp_path: Path) -> None:
        """Test loading messages from a batch file."""
        # Create a test batch file
        messages = [
            {
                "id": "1",
                "content": "Test message 1",
                "author": "user1",
                "timestamp": "2025-01-01T12:00:00",
                "channel_id": "123",
            },
            {
                "id": "2",
                "content": "Test message 2",
                "author": "user2",
                "timestamp": "2025-01-01T12:01:00",
                "channel_id": "123",
            },
        ]
        
        batch_file = tmp_path / "test_batch.json"
        with open(batch_file, "w", encoding="utf-8") as f:
            json.dump(messages, f)
        
        # Initialize processor
        processor = VectorDBProcessor(
            messages_directory=tmp_path,
            collection_name="test_collection",
        )
        
        # Load batch
        loaded_messages = processor._load_messages_batch(batch_file)
        
        # Verify contents
        assert len(loaded_messages) == 2
        assert loaded_messages[0]["id"] == "1"
        assert loaded_messages[0]["content"] == "Test message 1"
        assert loaded_messages[1]["id"] == "2"
        assert loaded_messages[1]["content"] == "Test message 2"

    def test_load_messages_batch_invalid_json(self, tmp_path: Path) -> None:
        """Test loading an invalid JSON file."""
        # Create an invalid JSON file
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, "w", encoding="utf-8") as f:
            f.write("This is not valid JSON")
        
        # Initialize processor
        processor = VectorDBProcessor(
            messages_directory=tmp_path,
            collection_name="test_collection",
        )
        
        # Load batch - should return empty list for invalid JSON
        loaded_messages = processor._load_messages_batch(invalid_file)
        assert len(loaded_messages) == 0

    def test_process_batch(
        self,
        tmp_path: Path,
        mock_chroma_client: Any,
        mock_sentence_transformer: Any,
        sample_message_batch: List[Dict[str, Any]],
    ) -> None:
        """Test processing a batch of messages."""
        # Initialize processor
        processor = VectorDBProcessor(
            messages_directory=tmp_path,
            collection_name="test_collection",
        )
        
        # Process batch
        processor._process_batch(sample_message_batch)
        
        # Verify model was called to generate embeddings
        assert mock_sentence_transformer.encode.called
        
        # Verify messages were added to collection
        collection = processor.collection
        assert collection.add.called
        
        # Verify progress was updated
        assert processor.progress.processed_items > 0

    def test_process_batch_empty(
        self,
        tmp_path: Path,
        mock_chroma_client: Any,
        mock_sentence_transformer: Any,
    ) -> None:
        """Test processing an empty batch."""
        # Initialize processor
        processor = VectorDBProcessor(
            messages_directory=tmp_path,
            collection_name="test_collection",
        )
        
        # Initial progress count
        initial_count = processor.progress.processed_items
        
        # Process empty batch
        processor._process_batch([])
        
        # Verify model was not called
        assert not mock_sentence_transformer.encode.called
        
        # Verify collection was not updated
        assert not processor.collection.add.called
        
        # Verify progress was not updated
        assert processor.progress.processed_items == initial_count

    def test_process_batch_skips_empty_content(
        self,
        tmp_path: Path,
        mock_chroma_client: Any,
        mock_sentence_transformer: Any,
    ) -> None:
        """Test that empty content messages are skipped during processing."""
        # Create test batch with some empty messages
        messages = [
            {"id": "1", "content": "Test message", "author": "user1", "timestamp": "2025-01-01T12:00:00"},
            {"id": "2", "content": "", "author": "user2", "timestamp": "2025-01-01T12:01:00"},
            {"id": "3", "content": None, "author": "user3", "timestamp": "2025-01-01T12:02:00"},
        ]
        
        # Initialize processor
        processor = VectorDBProcessor(
            messages_directory=tmp_path,
            collection_name="test_collection",
        )
        
        # Process batch
        processor._process_batch(messages)
        
        # Verify only non-empty messages were processed
        # Check this by verifying the encode method was called with only one string
        mock_sentence_transformer.encode.assert_called_once()
        args, _ = mock_sentence_transformer.encode.call_args
        assert len(args[0]) == 1
        assert args[0][0] == "Test message"

    def test_process_all(
        self,
        temp_message_directory: Path,
        mock_chroma_client: Any,
        mock_sentence_transformer: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test processing all message batches."""
        # Initialize processor
        processor = VectorDBProcessor(
            messages_directory=temp_message_directory,
            collection_name="test_collection",
        )
        
        # Mock the _process_batch method to track calls
        original_process_batch = processor._process_batch
        process_batch_calls = []
        
        def mock_process_batch(messages: List[Dict[str, Any]]) -> None:
            process_batch_calls.append(len(messages))
            original_process_batch(messages)
        
        monkeypatch.setattr(processor, "_process_batch", mock_process_batch)
        
        # Mock collection count method
        processor.collection.count.return_value = 15
        
        # Process all batches
        total = processor.process_all()
        
        # Verify results
        assert total == 15  # From mocked collection count
        assert len(process_batch_calls) == 3  # 3 batch files from fixture
        assert all(call == 5 for call in process_batch_calls)  # 5 messages per batch

    def test_search(
        self,
        temp_message_directory: Path,
        mock_chroma_client: Any,
        mock_sentence_transformer: Any,
    ) -> None:
        """Test searching for messages."""
        # Initialize processor
        processor = VectorDBProcessor(
            messages_directory=temp_message_directory,
            collection_name="test_collection",
        )
        
        # Set up mock query response
        processor.collection.query.return_value = {
            "ids": [["id1", "id2", "id3"]],
            "documents": [["Message 1", "Message 2", "Message 3"]],
            "metadatas": [[
                {"author": "user1", "timestamp": "2025-01-01T12:00:00", "channel_id": "123"},
                {"author": "user2", "timestamp": "2025-01-01T12:01:00", "channel_id": "123"},
                {"author": "user3", "timestamp": "2025-01-01T12:02:00", "channel_id": "123"},
            ]],
            "distances": [[0.1, 0.2, 0.3]],
        }
        
        # Perform search
        results = processor.search("test query", n_results=3)
        
        # Verify results
        assert len(results) == 3
        assert results[0]["content"] == "Message 1"
        assert results[0]["metadata"]["author"] == "user1"
        assert results[0]["similarity"] == 0.9  # 1.0 - 0.1
        
        assert results[1]["content"] == "Message 2"
        assert results[1]["metadata"]["author"] == "user2"
        assert results[1]["similarity"] == 0.8  # 1.0 - 0.2
        
        assert results[2]["content"] == "Message 3"
        assert results[2]["metadata"]["author"] == "user3"
        assert results[2]["similarity"] == 0.7  # 1.0 - 0.3

    def test_search_custom_results_count(
        self,
        temp_message_directory: Path,
        mock_chroma_client: Any,
        mock_sentence_transformer: Any,
    ) -> None:
        """Test searching with a custom result count."""
        # Initialize processor
        processor = VectorDBProcessor(
            messages_directory=temp_message_directory,
            collection_name="test_collection",
        )
        
        # Perform search with custom result count
        _ = processor.search("test query", n_results=10)
        
        # Verify n_results parameter was passed correctly
        processor.collection.query.assert_called_once()
        _, kwargs = processor.collection.query.call_args
        assert kwargs["n_results"] == 10

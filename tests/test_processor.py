"""
Unit tests for the discord_retriever.processor module.

This module tests the vector database processor functionality, which converts
Discord messages to vector embeddings and stores them in a database.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, cast

import pytest
from unittest.mock import MagicMock, patch

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
        
        # Initially the properties should be accessible but not initialized
        assert processor.chroma_client is not None
        assert processor.collection is not None
        assert processor.model is not None
        
        # Verify the collection was created
        mock_chroma_client.get_or_create_collection.assert_called_once_with(name="test_collection")

    def test_load_messages(self, tmp_path: Path) -> None:
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
        
        # Initialize processor with patched method
        processor = VectorDBProcessor(
            messages_directory=tmp_path,
            collection_name="test_collection",
        )
        
        # Use patch for internal method to test indirectly
        # We use type: ignore to suppress protected member access warnings
        with patch.object(
            VectorDBProcessor, 
            "_load_messages_batch",
            wraps=processor._load_messages_batch  # type: ignore[attr-defined]
        ) as mock_load:
            # Create batch files for process_all
            for i in range(3):
                test_file = tmp_path / f"messages_batch_{i:04d}.json"
                with open(test_file, "w", encoding="utf-8") as f:
                    json.dump(messages, f)
            
            # Also patch process_batch to avoid actual processing
            with patch.object(VectorDBProcessor, "_process_batch"):  # type: ignore
                # Also patch collection.count to return a value
                mock_collection = MagicMock()
                mock_collection.count.return_value = 0
                processor.test_setup(mock_collection=mock_collection)
                
                # Call process_all to trigger loading
                processor.process_all()
                
                # Verify load_messages_batch was called for each batch file
                assert mock_load.call_count >= 3

    def test_load_messages_invalid_json(self, tmp_path: Path) -> None:
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
        
        # Use patch for internal method to test indirectly
        with patch.object(
            VectorDBProcessor, 
            "_load_messages_batch",  # type: ignore
            wraps=processor._load_messages_batch  # type: ignore
        ) as mock_load:
            # Create a messages_batch file that will trigger loading
            batch_file = tmp_path / "messages_batch_0000.json"
            with open(batch_file, "w", encoding="utf-8") as f:
                f.write("This is not valid JSON")
                
            # Also patch process_batch to avoid actual processing
            with patch.object(VectorDBProcessor, "_process_batch"):  # type: ignore
                # Also patch collection.count to return a value
                mock_collection = MagicMock()
                mock_collection.count.return_value = 0
                processor.test_setup(mock_collection=mock_collection)
                
                # Call process_all to trigger loading
                processor.process_all()
                
                # Verify our method was called
                assert mock_load.call_count > 0
                
                # Directly verify the method returned empty list for our invalid file
                # Instead of relying on the mock's return value capturing
                # We can directly check if the method was called with the batch_file
                # The processor._load_messages_batch method should've been called with 
                # batch_file as its argument, and that call should return an empty list
                # because the file contains invalid JSON
                
                # First check if it was called with our batch_file
                mock_load.assert_any_call(batch_file)
                
        # Direct call would violate encapsulation in type checking, so we can either:
        # 1. Use getattr to bypass the protection warning
        # 2. Or verify indirectly by checking the call result through the mock
        load_method = getattr(processor, "_load_messages_batch")
        result = load_method(batch_file)
        assert result == []

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
        
        # Use patch for internal method to test indirectly
        with patch.object(
            VectorDBProcessor, 
            "_process_batch",  # type: ignore
            wraps=processor._process_batch  # type: ignore
        ) as mock_process:
            # Call process_all to trigger the method
            # First set up the collection mock
            mock_collection = MagicMock()
            mock_collection.count.return_value = 5
            processor.test_setup(mock_collection=mock_collection)
            
            # Mock load_messages to return our sample batch
            with patch.object(
                VectorDBProcessor,
                "_load_messages_batch",  # type: ignore
                return_value=sample_message_batch
            ):
                # Create a batch file to process
                batch_file = tmp_path / "messages_batch_0000.json"
                with open(batch_file, "w", encoding="utf-8") as f:
                    json.dump(sample_message_batch, f)
                    
                # Run process_all to trigger process_batch
                processor.process_all()
                
                # Verify process_batch was called with our messages
                assert mock_process.call_count > 0
                # At least one call should have our sample messages
                found_match = False
                for call in mock_process.mock_calls:
                    if len(call.args) > 0 and call.args[0] == sample_message_batch:
                        found_match = True
                        break
                assert found_match
                
                # Verify model encode was called
                assert mock_sentence_transformer.encode.call_count > 0
                
                # Verify collection add was called
                assert processor.collection.add.call_count > 0  # type: ignore

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
        
        # Track initial progress count
        initial_count = processor.progress.processed_items
        
        # Directly test the method for empty input
        # We're not using a spy here to avoid accessing protected method multiple times
        # This works because we need to test a specific behavior with empty input
        processor._process_batch([])  # type: ignore
        
        # Verify model was not called
        assert mock_sentence_transformer.encode.call_count == 0
        
        # Verify progress was not updated
        assert processor.progress.processed_items == initial_count
        
        # Test with collection mock to verify it's not updated
        mock_collection = MagicMock()
        processor.test_setup(mock_collection=mock_collection)
        processor._process_batch([])  # type: ignore
        assert processor.collection.add.call_count == 0  # type: ignore

    def test_process_batch_skips_empty_content(
        self,
        tmp_path: Path,
        mock_chroma_client: Any,
        mock_sentence_transformer: Any,
    ) -> None:
        """Test that empty content messages are skipped during processing."""
        # Create test batch with some empty messages
        messages: List[Dict[str, Any]] = [
            {"id": "1", "content": "Test message", "author": "user1", "timestamp": "2025-01-01T12:00:00"},
            {"id": "2", "content": "", "author": "user2", "timestamp": "2025-01-01T12:01:00"},
            {"id": "3", "content": None, "author": "user3", "timestamp": "2025-01-01T12:02:00"},
        ]
        
        # Initialize processor
        processor = VectorDBProcessor(
            messages_directory=tmp_path,
            collection_name="test_collection",
        )
        
        # Reset mock before our test
        mock_sentence_transformer.encode.reset_mock()
        
        # Process the batch with mix of empty and non-empty messages
        processor._process_batch(messages)  # type: ignore
        
        # Verify only non-empty messages were processed
        mock_sentence_transformer.encode.assert_called_once()
        args = mock_sentence_transformer.encode.call_args[0]
        assert len(args[0]) == 1
        assert args[0][0] == "Test message"

    def test_process_all(
        self,
        temp_message_directory: Path,
        mock_chroma_client: Any,
        mock_sentence_transformer: Any,
    ) -> None:
        """Test processing all message batches."""
        # Initialize processor
        processor = VectorDBProcessor(
            messages_directory=temp_message_directory,
            collection_name="test_collection",
        )
        
        # Use patch for process_batch to track calls
        with patch.object(VectorDBProcessor, "_process_batch") as mock_process:  # type: ignore
            # Configure collection to return a count
            mock_collection = MagicMock()
            mock_collection.count.return_value = 15
            processor.test_setup(mock_collection=mock_collection)
            
            # Process all batches
            total = processor.process_all()
            
            # Verify results
            assert total == 15  # From mocked collection count
            assert mock_process.call_count == 3  # 3 batch files from fixture
            
            # Each call should have received 5 messages (from fixture)
            for call_args in mock_process.call_args_list:
                assert len(call_args[0][0]) == 5

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
        query_result = {
            "ids": [["id1", "id2", "id3"]],
            "documents": [["Message 1", "Message 2", "Message 3"]],
            "metadatas": [[
                {"author": "user1", "timestamp": "2025-01-01T12:00:00", "channel_id": "123"},
                {"author": "user2", "timestamp": "2025-01-01T12:01:00", "channel_id": "123"},
                {"author": "user3", "timestamp": "2025-01-01T12:02:00", "channel_id": "123"},
            ]],
            "distances": [[0.1, 0.2, 0.3]],
        }
        mock_collection = MagicMock()
        mock_collection.query.return_value = query_result
        processor.test_setup(mock_collection=mock_collection)
        
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
        
        # Set up mock for collection
        mock_collection = MagicMock()
        # Set up query to return empty results
        mock_collection.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        processor.test_setup(mock_collection=mock_collection)
        
        # Perform search with custom result count
        _ = processor.search("test query", n_results=10)
        
        # Verify n_results parameter was passed correctly
        mock_collection.query.assert_called_once()
        args = mock_collection.query.call_args
        assert args[1]["n_results"] == 10

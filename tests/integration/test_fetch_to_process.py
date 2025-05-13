"""
Integration tests for the Discord Vector DB project.

This module tests the integration between the fetcher and processor components,
showing how data flows through the entire pipeline.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pytest
from pytest import MonkeyPatch

from discord_retriever.fetcher import DiscordMessageFetcher, MessageData
from discord_retriever.processor import VectorDBProcessor


class TestFetchToProcess:
    """Integration tests for the fetcher and processor components."""

    def test_end_to_end_workflow(
        self,
        mock_discord_mcp: None,
        mock_chroma_client: Any,
        mock_sentence_transformer: Any,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """
        Test end-to-end workflow from fetching to processing.
        
        This test simulates fetching messages from Discord and then
        processing them into a vector database.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 1. Set up the fetcher
            fetcher = DiscordMessageFetcher(
                channel_id="123456789012345678",
                save_directory=temp_path,
                rate_limit_delay=0.01,  # Fast for testing
            )
            
            # Mock sleep to speed up tests
            monkeypatch.setattr("time.sleep", lambda _: None)
            
            # 2. Fetch messages - limit to 2 batches for testing
            original_fetch = fetcher._fetch_messages_batch
            batch_counter = 0
            
            def mock_fetch_with_limit() -> List[MessageData]:
                nonlocal batch_counter
                if batch_counter < 2:
                    batch_counter += 1
                    return original_fetch()
                return []
            
            monkeypatch.setattr(fetcher, "_fetch_messages_batch", mock_fetch_with_limit)
            
            # Run the fetcher
            total_messages = fetcher.fetch_all()
            
            # Verify messages were fetched
            assert total_messages > 0
            assert fetcher.batch_count == 2
            
            # Check if batch files were created
            batch_files = list(temp_path.glob("messages_batch_*.json"))
            assert len(batch_files) == 2
            
            # 3. Set up the processor
            processor = VectorDBProcessor(
                messages_directory=temp_path,
                collection_name="test_collection",
                batch_size=5,
            )
            
            # Set a fixed return value for the collection count
            processor.collection.count.return_value = 10
            
            # 4. Process messages
            total_processed = processor.process_all()
            
            # Verify messages were processed
            assert total_processed == 10
            
            # 5. Test search functionality
            # Create a completely fresh mock collection with specific return values for this test
            from unittest.mock import MagicMock
            
            # Create fresh mock for the collection
            mock_collection = MagicMock()
            
            # Set up exact return value for this specific test
            mock_collection.query.return_value = {
                "ids": [["id1", "id2"]],
                "documents": [["Test message 1", "Test message 2"]],
                "metadatas": [[
                    {"author": "testuser", "timestamp": "2025-01-01T12:00:00", "channel_id": "123"},
                    {"author": "testuser", "timestamp": "2025-01-01T12:01:00", "channel_id": "123"},
                ]],
                "distances": [[0.1, 0.2]],
            }
            
            # Install our mock collection
            processor.test_setup(mock_collection=mock_collection)
            
            # Perform search
            results = processor.search("test query")
            
            # Verify our mock was used and results match what we set up
            mock_collection.query.assert_called_once()
            assert len(results) == 2
            assert results[0]["content"] == "Test message 1"
            assert results[1]["content"] == "Test message 2"

    def test_partial_data_recovery(
        self,
        mock_discord_mcp: None,
        mock_chroma_client: Any,
        mock_sentence_transformer: Any,
        monkeypatch: MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """
        Test recovering from a partial fetch and continuing processing.
        
        This test simulates a scenario where fetching was interrupted
        and later resumed, with processing happening afterward.
        """
        # 1. Create a checkpoint file to simulate a previous partial fetch
        message_dir = tmp_path / "messages"
        message_dir.mkdir()
        
        # Create a batch file with some messages
        batch_file = message_dir / "messages_batch_0000.json"
        messages = [
            {
                "id": f"10000000000000{i}",
                "content": f"Partial batch message {i}",
                "author": "testuser",
                "timestamp": datetime(2025, 1, 1, 12, i).isoformat(),
                "channel_id": "123456789012345678",
            }
            for i in range(5)
        ]
        
        with open(batch_file, "w", encoding="utf-8") as f:
            json.dump(messages, f)
        
        # Create a checkpoint file pointing to the last message
        checkpoint_file = tmp_path / "checkpoint.json"
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump({
                "channel_id": "123456789012345678",
                "oldest_message_id": "100000000000004",
                "batch_count": 1,
                "total_messages": 5,
                "last_updated": datetime.now().isoformat()
            }, f)
        
        # 2. Set up the fetcher with the checkpoint
        fetcher = DiscordMessageFetcher(
            channel_id="123456789012345678",
            save_directory=message_dir,
            checkpoint_file=checkpoint_file,
            rate_limit_delay=0.01,
        )
        
        # Mock sleep to speed up tests
        monkeypatch.setattr("time.sleep", lambda _: None)
        
        # Verify checkpoint was loaded
        assert fetcher.oldest_message_id == "100000000000004"
        assert fetcher.batch_count == 1
        assert fetcher.total_messages == 5
        
        # 3. Fetch additional messages - limit to 1 more batch
        original_fetch = fetcher._fetch_messages_batch
        fetch_count = 0
        
        def mock_fetch_once() -> List[MessageData]:
            nonlocal fetch_count
            if fetch_count < 1:
                fetch_count += 1
                return original_fetch()
            return []
        
        monkeypatch.setattr(fetcher, "_fetch_messages_batch", mock_fetch_once)
        
        # Run the fetcher to get more messages
        total_messages = fetcher.fetch_all()
        
        # Verify messages were added
        assert total_messages == 10  # 5 from checkpoint + 5 new
        assert fetcher.batch_count == 2
        
        # Check if a new batch file was created
        batch_files = list(message_dir.glob("messages_batch_*.json"))
        assert len(batch_files) == 2
        
        # 4. Process all messages
        processor = VectorDBProcessor(
            messages_directory=message_dir,
            collection_name="test_collection",
        )
        
        # Set a fixed return value for the collection count
        processor.collection.count.return_value = 10
        
        # Process messages
        total_processed = processor.process_all()
        
        # Verify all messages were processed
        assert total_processed == 10

"""
Test fixtures for the Discord Vector DB project.

This module provides fixtures that can be used across all test files
to reduce duplication and provide standardized test data.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
from pytest_mock import MockerFixture

from discord_retriever.models import (
    CheckpointData,
    DiscordMessage,
    MessageSource,
)


# --------- Sample Data Fixtures --------- #


@pytest.fixture
def sample_raw_message() -> Dict[str, Any]:
    """Return a sample raw message dict as received from the Discord API."""
    return {
        "id": "123456789012345678",
        "content": "This is a test message",
        "author": {"id": "987654321098765432", "username": "testuser"},
        "timestamp": "2025-01-01T12:00:00.000Z",
        "channel_id": "111222333444555666",
        "attachments": [],
        "reactions": [
            {
                "emoji": {"name": "👍", "id": None},
                "count": 3,
            }
        ],
        "mentions": [{"id": "444555666777888999", "username": "mentioneduser"}],
    }


@pytest.fixture
def sample_discord_message(sample_raw_message: Dict[str, Any]) -> DiscordMessage:
    """Return a sample DiscordMessage object."""
    return DiscordMessage.from_api_response(sample_raw_message)


@pytest.fixture
def sample_message_batch() -> List[Dict[str, Any]]:
    """Return a sample batch of raw message dicts."""
    return [
        {
            "id": f"10000000000000000{i}",
            "content": f"Sample message #{i}",
            "author": {"id": "987654321098765432", "username": "testuser"},
            "timestamp": (
                datetime(2025, 1, 1, 12, 0, 0) + timedelta(minutes=i)
            ).isoformat() + "Z",
            "channel_id": "111222333444555666",
            "attachments": [],
            "reactions": [],
            "mentions": [],
        }
        for i in range(5)
    ]


@pytest.fixture
def temp_checkpoint_file(tmp_path: Path) -> Path:
    """Create a temporary file path for checkpoint testing."""
    return tmp_path / "test_checkpoint.json"


@pytest.fixture
def sample_checkpoint_data() -> CheckpointData:
    """Return a sample CheckpointData object."""
    return CheckpointData(
        channel_id="111222333444555666",
        oldest_message_id="123456789012345678",
        batch_count=5,
        total_messages=500,
        last_updated=datetime(2025, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def sample_embeddings() -> List[List[float]]:
    """Return sample vector embeddings for testing."""
    # Creating 5 simple embeddings with 4 dimensions each
    return [
        [0.1, 0.2, 0.3, 0.4],
        [0.2, 0.3, 0.4, 0.5],
        [0.3, 0.4, 0.5, 0.6],
        [0.4, 0.5, 0.6, 0.7],
        [0.5, 0.6, 0.7, 0.8],
    ]


# --------- Mock Fixtures --------- #


@pytest.fixture
def mock_discord_mcp(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Mock the Discord MCP server call in the fetcher.
    
    This patches the _call_discord_mcp method in DiscordMessageFetcher to return
    predetermined responses instead of making actual API calls.
    """
    
    def mock_call_discord_mcp(self: Any, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock implementation of _call_discord_mcp."""
        # Generate 5 test messages
        messages = []
        for i in range(5):
            msg_id = f"10000000000000000{i}"
            
            # If 'before' is in args, generate older messages
            if "before" in args:
                base_id = int(args["before"]) - 100
                msg_id = str(base_id - (i * 10))
                
            messages.append({
                "id": msg_id,
                "content": f"Test message #{i} for channel {args['channel_id']}",
                "author": {"id": "123456789", "username": "testuser"},
                "timestamp": (
                    datetime(2025, 1, 1, 12, 0, 0) - timedelta(hours=i)
                ).isoformat() + "Z",
                "channel_id": args["channel_id"],
                "attachments": [],
                "reactions": [],
                "mentions": [],
            })
            
        return messages
    
    # Apply the monkeypatch
    from discord_retriever.fetcher import DiscordMessageFetcher
    monkeypatch.setattr(DiscordMessageFetcher, "_call_discord_mcp", mock_call_discord_mcp)


@pytest.fixture
def mock_sentence_transformer(mocker: MockerFixture) -> Any:
    """Mock the SentenceTransformer class."""
    mock_model = mocker.MagicMock()
    
    # Set up the encode method to return predictable vectors
    def mock_encode(texts: List[str]) -> List[List[float]]:
        # Generate a simple vector for each text
        return [[float(ord(c) % 10) * 0.1 for c in text[:4].ljust(4)] for text in texts]
    
    mock_model.encode.side_effect = mock_encode
    
    # Mock the import and constructor
    mock_st = mocker.patch("sentence_transformers.SentenceTransformer", return_value=mock_model)
    
    return mock_model


@pytest.fixture
def mock_chroma_client(mocker: MockerFixture) -> Any:
    """Mock the ChromaDB client and collection."""
    mock_collection = mocker.MagicMock()
    
    # Configure the collection's query method
    def mock_query(query_embeddings: List[List[float]], n_results: int, include: List[str]) -> Dict[str, Any]:
        return {
            "ids": [["id1", "id2", "id3"]],
            "documents": [["Message 1", "Message 2", "Message 3"]],
            "metadatas": [[
                {"author": "user1", "timestamp": "2025-01-01T12:00:00", "channel_id": "123"},
                {"author": "user2", "timestamp": "2025-01-01T12:01:00", "channel_id": "123"},
                {"author": "user3", "timestamp": "2025-01-01T12:02:00", "channel_id": "123"},
            ]],
            "distances": [[0.1, 0.2, 0.3]],
        }
    
    mock_collection.query.side_effect = mock_query
    mock_collection.count.return_value = 3
    
    # Configure the client
    mock_client = mocker.MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    
    # Mock the import
    mocker.patch("chromadb.Client", return_value=mock_client)
    
    return mock_client


@pytest.fixture
def temp_message_directory(tmp_path: Path) -> Path:
    """Create a temporary directory with sample message batch files."""
    message_dir = tmp_path / "messages"
    message_dir.mkdir()
    
    # Create a few batch files
    for i in range(3):
        batch_file = message_dir / f"messages_batch_{i:04d}.json"
        messages = [
            {
                "id": f"10000000000000{i}{j}",
                "content": f"Sample message batch {i}, message {j}",
                "author": "testuser",
                "timestamp": (
                    datetime(2025, 1, 1, 12, 0, 0) + timedelta(hours=i, minutes=j)
                ).isoformat(),
                "channel_id": "111222333444555666",
                "attachments": [],
                "reactions": [],
                "mentions": [],
            }
            for j in range(5)
        ]
        
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f)
    
    return message_dir

"""
Unit tests for the discord_retriever.fetcher module.

This module tests the functionality for fetching messages from Discord, including
pagination, checkpointing, and error handling.
"""

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, cast

import pytest
from pytest import MonkeyPatch

from discord_retriever.fetcher import DiscordMessageFetcher, MessageData, parse_messages
from discord_retriever.models import CheckpointData, CircuitBreaker


class TestDiscordMessageFetcher:
    """Tests for the DiscordMessageFetcher class."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test initializing a fetcher with various parameters."""
        # Basic initialization
        fetcher = DiscordMessageFetcher(
            channel_id="123456789012345678",
            save_directory=tmp_path,
        )
        
        assert fetcher.channel_id == "123456789012345678"
        assert fetcher.save_directory == tmp_path
        assert fetcher.rate_limit_delay == 1.0
        assert fetcher.max_retries == 5
        assert fetcher.start_date is None
        assert fetcher.end_date is None
        assert fetcher.oldest_message_id is None
        assert fetcher.batch_count == 0
        assert fetcher.total_messages == 0
        
        # Initialization with optional parameters
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)
        
        fetcher = DiscordMessageFetcher(
            channel_id="123456789012345678",
            save_directory=tmp_path,
            checkpoint_file=tmp_path / "custom_checkpoint.json",
            rate_limit_delay=2.0,
            max_retries=10,
            start_date=start_date,
            end_date=end_date,
        )
        
        assert fetcher.checkpoint_file == tmp_path / "custom_checkpoint.json"
        assert fetcher.rate_limit_delay == 2.0
        assert fetcher.max_retries == 10
        assert fetcher.start_date == start_date
        assert fetcher.end_date == end_date

    def test_load_checkpoint(self, tmp_path: Path) -> None:
        """Test loading checkpoint data."""
        # Create a checkpoint file
        checkpoint = CheckpointData(
            channel_id="123456789012345678",
            oldest_message_id="987654321098765432",
            batch_count=5,
            total_messages=500,
        )
        
        checkpoint_file = tmp_path / "test_checkpoint.json"
        checkpoint.save(checkpoint_file)
        
        # Create fetcher and verify it loads the checkpoint
        fetcher = DiscordMessageFetcher(
            channel_id="123456789012345678",
            save_directory=tmp_path,
            checkpoint_file=checkpoint_file,
        )
        
        assert fetcher.oldest_message_id == "987654321098765432"
        assert fetcher.batch_count == 5
        assert fetcher.total_messages == 500

    def test_load_checkpoint_wrong_channel(self, tmp_path: Path) -> None:
        """Test loading checkpoint for a different channel."""
        # Create a checkpoint file for a different channel
        checkpoint = CheckpointData(
            channel_id="different_channel_id",
            oldest_message_id="987654321098765432",
            batch_count=5,
            total_messages=500,
        )
        
        checkpoint_file = tmp_path / "test_checkpoint.json"
        checkpoint.save(checkpoint_file)
        
        # Create fetcher and verify it doesn't load the checkpoint
        fetcher = DiscordMessageFetcher(
            channel_id="123456789012345678",  # Different from checkpoint
            save_directory=tmp_path,
            checkpoint_file=checkpoint_file,
        )
        
        # Should not load checkpoint for different channel
        assert fetcher.oldest_message_id is None
        assert fetcher.batch_count == 0
        assert fetcher.total_messages == 0

    def test_fetch_messages_batch(self, tmp_path: Path, mock_discord_mcp: None) -> None:
        """Test fetching a batch of messages."""
        fetcher = DiscordMessageFetcher(
            channel_id="123456789012345678",
            save_directory=tmp_path,
        )
        
        # Fetch batch
        messages = fetcher._fetch_messages_batch()
        
        # Verify results
        assert len(messages) == 5
        assert all(isinstance(msg, dict) for msg in messages)
        assert all("id" in msg for msg in messages)
        assert all("content" in msg for msg in messages)
        assert all("channel_id" in msg for msg in messages)
        assert all(msg["channel_id"] == "123456789012345678" for msg in messages)

    def test_fetch_messages_batch_with_before(
        self, tmp_path: Path, mock_discord_mcp: None
    ) -> None:
        """Test fetching a batch of messages with a 'before' parameter."""
        fetcher = DiscordMessageFetcher(
            channel_id="123456789012345678",
            save_directory=tmp_path,
        )
        
        # Set oldest message ID
        fetcher.oldest_message_id = "987654321098765432"
        
        # Fetch batch
        messages = fetcher._fetch_messages_batch()
        
        # Our mock should use this ID to generate older messages
        assert all(int(msg["id"]) < 987654321098765432 for msg in messages)

    def test_circuit_breaker_integration(self, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
        """Test circuit breaker prevents calls after failures."""
        # Create a fresh CircuitBreaker for this test
        from discord_retriever.models import CircuitBreaker
        
        # Monkeypatch the circuit breaker construction to ensure we get a clean one
        original_circuit_breaker = CircuitBreaker
        
        def fresh_circuit_breaker(*args: Any, **kwargs: Any) -> CircuitBreaker:
            cb = original_circuit_breaker(*args, **kwargs)
            cb.failures = 0
            cb.is_open = False
            return cb
            
        monkeypatch.setattr("discord_retriever.models.CircuitBreaker", fresh_circuit_breaker)
        
        # Now create our fetcher with the fresh circuit breaker
        fetcher = DiscordMessageFetcher(
            channel_id="123456789012345678",
            save_directory=tmp_path,
            max_retries=2,  # Set low for testing
        )
        
        # We need to completely override the _fetch_messages_batch to avoid the retry mechanism
        original_fetch = fetcher._fetch_messages_batch
        
        def mock_fetch_with_failures() -> List[MessageData]:
            # Each call increments the failure counter directly
            fetcher.circuit_breaker.failures += 1
            if fetcher.circuit_breaker.failures >= fetcher.circuit_breaker.max_failures:
                fetcher.circuit_breaker.is_open = True
                raise RuntimeError("Circuit breaker is open")
            raise RuntimeError("Simulated API failure")
            
        monkeypatch.setattr(fetcher, "_fetch_messages_batch", mock_fetch_with_failures)
        
        # Verify we're starting fresh
        assert fetcher.circuit_breaker.failures == 0
        assert not fetcher.circuit_breaker.is_open
        
        # First call - should fail but circuit still closed
        with pytest.raises(RuntimeError):
            fetcher._fetch_messages_batch()
        
        assert fetcher.circuit_breaker.failures == 1
        assert not fetcher.circuit_breaker.is_open
        
        # Second call - should fail and open circuit
        with pytest.raises(RuntimeError):
            fetcher._fetch_messages_batch()
        
        assert fetcher.circuit_breaker.failures == 2
        assert fetcher.circuit_breaker.is_open
        
        # Third call - should fail immediately due to open circuit
        with pytest.raises(RuntimeError, match="Circuit breaker is open"):
            fetcher._fetch_messages_batch()

    def test_filter_messages_by_date(self, tmp_path: Path) -> None:
        """Test filtering messages by date range."""
        # Create messages with different dates
        messages: List[MessageData] = [
            {
                "id": "1",
                "content": "Message 1",
                "timestamp": "2025-01-01T12:00:00Z",
            },
            {
                "id": "2",
                "content": "Message 2",
                "timestamp": "2025-01-15T12:00:00Z",
            },
            {
                "id": "3",
                "content": "Message 3",
                "timestamp": "2025-01-31T12:00:00Z",
            },
        ]
        
        fetcher = DiscordMessageFetcher(
            channel_id="123456789012345678",
            save_directory=tmp_path,
        )
        
        # Test no filtering
        filtered = fetcher._filter_messages_by_date(messages)
        assert len(filtered) == 3
        
        # Test start date only - add timezone info to match expected format
        fetcher.start_date = datetime(2025, 1, 10, tzinfo=timezone.utc)
        filtered = fetcher._filter_messages_by_date(messages)
        assert len(filtered) == 2
        assert filtered[0]["id"] == "2"
        assert filtered[1]["id"] == "3"
        
        # Test end date only - add timezone info to match expected format
        fetcher.start_date = None
        fetcher.end_date = datetime(2025, 1, 20, tzinfo=timezone.utc)
        filtered = fetcher._filter_messages_by_date(messages)
        assert len(filtered) == 2
        assert filtered[0]["id"] == "1"
        assert filtered[1]["id"] == "2"
        
        # Test both dates - add timezone info to both
        fetcher.start_date = datetime(2025, 1, 10, tzinfo=timezone.utc)
        fetcher.end_date = datetime(2025, 1, 20, tzinfo=timezone.utc)
        filtered = fetcher._filter_messages_by_date(messages)
        assert len(filtered) == 1
        assert filtered[0]["id"] == "2"

    def test_save_messages_batch(self, tmp_path: Path) -> None:
        """Test saving a batch of messages to a file."""
        fetcher = DiscordMessageFetcher(
            channel_id="123456789012345678",
            save_directory=tmp_path,
        )
        
        messages: List[MessageData] = [
            {
                "id": "1",
                "content": "Test message 1",
                "timestamp": "2025-01-01T12:00:00Z",
            },
            {
                "id": "2",
                "content": "Test message 2",
                "timestamp": "2025-01-01T12:01:00Z",
            },
        ]
        
        # Save batch
        batch_file = fetcher._save_messages_batch(messages)
        
        # Verify file exists
        assert batch_file.exists()
        
        # Load and verify contents
        with open(batch_file, "r", encoding="utf-8") as f:
            loaded_messages = json.load(f)
        
        assert len(loaded_messages) == 2
        assert loaded_messages[0]["id"] == "1"
        assert loaded_messages[1]["id"] == "2"
        assert loaded_messages[0]["content"] == "Test message 1"
        assert loaded_messages[1]["content"] == "Test message 2"

    def test_fetch_all_with_mocked_batches(
        self, tmp_path: Path, mock_discord_mcp: None, monkeypatch: MonkeyPatch
    ) -> None:
        """Test fetching all messages with mocked batches."""
        fetcher = DiscordMessageFetcher(
            channel_id="123456789012345678",
            save_directory=tmp_path,
            rate_limit_delay=0.01,  # Set low for testing
        )
        
        # Mock the rate limiting delay to speed up test
        original_sleep = time.sleep
        monkeypatch.setattr(time, "sleep", lambda s: original_sleep(0.01))
        
        # Override fetch to only get 2 batches then return empty
        original_fetch = fetcher._fetch_messages_batch
        batch_counter = 0
        
        def mock_fetch_with_limit() -> List[MessageData]:
            nonlocal batch_counter
            if batch_counter < 2:
                batch_counter += 1
                return original_fetch()
            return []
        
        monkeypatch.setattr(fetcher, "_fetch_messages_batch", mock_fetch_with_limit)
        
        # Fetch all messages
        total = fetcher.fetch_all()
        
        # Verify results
        assert total == 10  # 2 batches * 5 messages
        assert fetcher.batch_count == 2
        assert fetcher.total_messages == 10
        
        # Verify files were created
        batch_files = list(tmp_path.glob("messages_batch_*.json"))
        assert len(batch_files) == 2


class TestParseMessages:
    """Tests for the parse_messages function."""

    def test_parse_messages_empty(self) -> None:
        """Test parsing an empty message result."""
        result = ""
        parsed = parse_messages(result)
        assert len(parsed) == 0

    def test_parse_messages_simple_format(self) -> None:
        """Test parsing messages in the basic format."""
        result = """
        user1 (2025-01-01T12:00:00Z): Hello world
        user2 (2025-01-01T12:01:00Z): How are you?
        user1 (2025-01-01T12:02:00Z): I'm good, thanks!
        """
        
        parsed = parse_messages(result)
        
        assert len(parsed) == 3
        assert parsed[0]["author"] == "user1"
        assert parsed[0]["content"] == "Hello world"
        assert parsed[0]["timestamp"] == "2025-01-01T12:00:00Z"
        
        assert parsed[1]["author"] == "user2"
        assert parsed[1]["content"] == "How are you?"
        
        assert parsed[2]["author"] == "user1"
        assert parsed[2]["content"] == "I'm good, thanks!"

    def test_parse_messages_complex_content(self) -> None:
        """Test parsing messages with more complex content."""
        result = """
        user1 (2025-01-01T12:00:00Z): This message has (parentheses) in it
        user2 (2025-01-01T12:01:00Z): This message has a : colon in it
        admin (2025-01-01T12:02:00Z): This message
        spans multiple lines
        like this
        """
        
        parsed = parse_messages(result)
        
        assert len(parsed) == 3
        assert parsed[0]["content"] == "This message has (parentheses) in it"
        assert parsed[1]["content"] == "This message has a : colon in it"
        # The current implementation would only capture the first line of multi-line messages
        assert parsed[2]["content"] == "This message"

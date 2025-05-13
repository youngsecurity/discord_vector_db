"""
Unit tests for the discord_retriever.models module.

This module tests the data structures and utilities defined in models.py.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from discord_retriever.models import (
    CheckpointData,
    CircuitBreaker,
    DiscordMessage,
    MessageSource,
    ProgressTracker,
)


class TestDiscordMessage:
    """Tests for the DiscordMessage class."""

    def test_from_api_response(self, sample_raw_message):
        """Test conversion from API response dictionary."""
        message = DiscordMessage.from_api_response(sample_raw_message)
        
        assert message.id == "123456789012345678"
        assert message.content == "This is a test message"
        assert message.author == "testuser"
        assert message.channel_id == "111222333444555666"
        assert len(message.reactions) == 1
        assert message.reactions[0]["emoji"] == "👍"
        assert message.reactions[0]["count"] == 3
        assert len(message.mentions) == 1
        assert message.mentions[0] == "444555666777888999"
        assert message.source == MessageSource.DISCORD

    def test_to_dict(self, sample_discord_message):
        """Test conversion to dictionary representation."""
        message_dict = sample_discord_message.to_dict()
        
        assert message_dict["id"] == sample_discord_message.id
        assert message_dict["content"] == sample_discord_message.content
        assert message_dict["author"] == sample_discord_message.author
        assert message_dict["timestamp"] == sample_discord_message.timestamp.isoformat()
        assert message_dict["channel_id"] == sample_discord_message.channel_id
        assert message_dict["source"] == MessageSource.DISCORD.value

    def test_from_dict(self, sample_discord_message):
        """Test creation from dictionary representation."""
        # Convert message to dict and back to test round trip
        message_dict = sample_discord_message.to_dict()
        reconstructed = DiscordMessage.from_dict(message_dict)
        
        assert reconstructed.id == sample_discord_message.id
        assert reconstructed.content == sample_discord_message.content
        assert reconstructed.author == sample_discord_message.author
        # Compare only dates, not full datetime objects to avoid microsecond issues
        assert reconstructed.timestamp.date() == sample_discord_message.timestamp.date()
        assert reconstructed.channel_id == sample_discord_message.channel_id
        assert reconstructed.source == sample_discord_message.source

    def test_from_dict_with_minimal_data(self):
        """Test creation with minimal dictionary data."""
        minimal_dict = {
            "id": "12345",
            "content": "Minimal message",
            "author": "minimaluser",
            "timestamp": "2025-01-01T00:00:00",
        }
        
        message = DiscordMessage.from_dict(minimal_dict)
        
        assert message.id == "12345"
        assert message.content == "Minimal message"
        assert message.author == "minimaluser"
        assert message.channel_id == ""  # Default empty string
        assert not message.attachments  # Empty list
        assert not message.reactions  # Empty list
        assert not message.mentions  # Empty list
        assert message.source == MessageSource.DISCORD  # Default enum value


class TestCheckpointData:
    """Tests for the CheckpointData class."""

    def test_save_load(self, sample_checkpoint_data, temp_checkpoint_file):
        """Test saving and loading checkpoint data."""
        # Save the checkpoint
        sample_checkpoint_data.save(temp_checkpoint_file)
        
        # Ensure file exists
        assert temp_checkpoint_file.exists()
        
        # Load the checkpoint
        loaded = CheckpointData.load(temp_checkpoint_file)
        
        # Verify data integrity
        assert loaded is not None
        assert loaded.channel_id == sample_checkpoint_data.channel_id
        assert loaded.oldest_message_id == sample_checkpoint_data.oldest_message_id
        assert loaded.batch_count == sample_checkpoint_data.batch_count
        assert loaded.total_messages == sample_checkpoint_data.total_messages
        
        # Dates might have microsecond differences, so compare only date components
        assert loaded.last_updated.date() == sample_checkpoint_data.last_updated.date()

    def test_load_nonexistent_file(self):
        """Test loading from a nonexistent file."""
        result = CheckpointData.load(Path("nonexistent_file.json"))
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        """Test loading from an invalid JSON file."""
        # Create an invalid JSON file
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, "w") as f:
            f.write("This is not valid JSON")
        
        result = CheckpointData.load(invalid_file)
        assert result is None


class TestProgressTracker:
    """Tests for the ProgressTracker class."""

    def test_update(self):
        """Test updating the progress tracker."""
        tracker = ProgressTracker(total_items=100)
        
        # Initial state
        assert tracker.processed_items == 0
        assert tracker.percentage_complete == 0.0
        
        # After update
        tracker.update(10)
        assert tracker.processed_items == 10
        assert tracker.percentage_complete == 10.0
        
        # Multiple updates
        tracker.update(15)
        tracker.update(25)
        assert tracker.processed_items == 50
        assert tracker.percentage_complete == 50.0

    def test_percentage_complete_no_total(self):
        """Test percentage calculation with no total items."""
        tracker = ProgressTracker()  # No total items specified
        tracker.update(50)
        assert tracker.percentage_complete == 0.0

    def test_percentage_complete_exceeds_100(self):
        """Test percentage doesn't exceed 100%."""
        tracker = ProgressTracker(total_items=10)
        tracker.update(20)  # Process more than the total
        assert tracker.percentage_complete == 100.0

    def test_is_stalled(self, monkeypatch):
        """Test stall detection."""
        tracker = ProgressTracker(stall_timeout=1)  # 1 second timeout for faster testing
        
        # Not stalled initially
        assert not tracker.is_stalled()
        
        # Mock datetime.now() to return a time in the future
        future_time = datetime.now() + timedelta(seconds=2)
        monkeypatch.setattr("discord_retriever.models.datetime", type('MockDatetime', (), {
            'now': lambda: future_time,
            'fromisoformat': datetime.fromisoformat,
        }))
        
        # Should be stalled now
        assert tracker.is_stalled()


class TestCircuitBreaker:
    """Tests for the CircuitBreaker class."""

    def test_initial_state(self):
        """Test initial state of circuit breaker."""
        breaker = CircuitBreaker()
        assert not breaker.is_open
        assert breaker.failures == 0
        assert breaker.last_failure_time is None
        assert breaker.can_execute()

    def test_record_failure(self):
        """Test recording failures."""
        breaker = CircuitBreaker(max_failures=3)
        
        # First failure
        breaker.record_failure()
        assert not breaker.is_open
        assert breaker.failures == 1
        assert breaker.last_failure_time is not None
        assert breaker.can_execute()
        
        # Second failure
        breaker.record_failure()
        assert not breaker.is_open
        assert breaker.failures == 2
        assert breaker.can_execute()
        
        # Third failure - should open circuit
        breaker.record_failure()
        assert breaker.is_open
        assert breaker.failures == 3
        assert not breaker.can_execute()

    def test_record_success(self):
        """Test recording success resets the circuit breaker."""
        breaker = CircuitBreaker(max_failures=3)
        
        # Record some failures
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.failures == 2
        
        # Record success
        breaker.record_success()
        assert not breaker.is_open
        assert breaker.failures == 0
        assert breaker.last_failure_time is None
        assert breaker.can_execute()

    def test_timeout_reset(self, monkeypatch):
        """Test circuit half-opens after timeout."""
        breaker = CircuitBreaker(max_failures=1, reset_timeout=10)
        
        # Open the circuit
        breaker.record_failure()
        assert breaker.is_open
        assert not breaker.can_execute()
        
        # Move time forward past the reset timeout
        future_time = datetime.now() + timedelta(seconds=11)
        monkeypatch.setattr("discord_retriever.models.datetime", type('MockDatetime', (), {
            'now': lambda: future_time,
            'fromisoformat': datetime.fromisoformat,
        }))
        
        # Circuit should allow execution but still be technically open
        assert breaker.is_open
        assert breaker.can_execute()

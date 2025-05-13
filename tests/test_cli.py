"""
Unit tests for the discord_retriever.cli module.

This module tests the command-line interface functionality.
"""

import tempfile
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockFixture
from typer.testing import CliRunner

from discord_retriever.cli import app


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CLI runner for testing."""
    return CliRunner()


class TestCLICommands:
    """Tests for the CLI commands."""

    def test_version_command(self, cli_runner: CliRunner) -> None:
        """Test the version command."""
        result = cli_runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "discord-retriever version" in result.stdout

    def test_fetch_command(
        self, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch, mock_discord_mcp: None
    ) -> None:
        """Test the fetch command."""
        # Mock the DiscordMessageFetcher
        mock_fetch_called = False
        fetch_args = {}

        def mock_fetch_init(self: Any, **kwargs: Any) -> None:
            nonlocal fetch_args
            fetch_args = kwargs
            # Set required attributes
            self.channel_id = kwargs.get("channel_id", "")
            self.save_directory = kwargs.get("save_directory", Path())
            self.checkpoint_file = None
            self.rate_limit_delay = 1.0
            self.max_retries = 5
            self.start_date = kwargs.get("start_date", None)
            self.end_date = kwargs.get("end_date", None)
            self.oldest_message_id = None
            self.batch_count = 0
            self.total_messages = 0
            # Mock the circuit breaker and progress tracker
            from discord_retriever.models import CircuitBreaker, ProgressTracker
            self.circuit_breaker = CircuitBreaker()
            self.progress = ProgressTracker()

        def mock_fetch_all(self: Any) -> int:
            nonlocal mock_fetch_called
            mock_fetch_called = True
            return 10  # Return a dummy count

        # Apply the mocks
        from discord_retriever.fetcher import DiscordMessageFetcher
        monkeypatch.setattr(DiscordMessageFetcher, "__init__", mock_fetch_init)
        monkeypatch.setattr(DiscordMessageFetcher, "fetch_all", mock_fetch_all)

        # Run the command with minimal arguments
        with tempfile.TemporaryDirectory() as temp_dir:
            result = cli_runner.invoke(
                app, ["fetch", "--channel-id", "123456789012345678", "--output", temp_dir]
            )

            # Verify the result
            assert result.exit_code == 0
            assert mock_fetch_called
            assert fetch_args["channel_id"] == "123456789012345678"
            assert fetch_args["save_directory"] == Path(temp_dir)

    def test_process_command(
        self, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch, mock_sentence_transformer: Any, mock_chroma_client: Any
    ) -> None:
        """Test the process command."""
        # Mock the VectorDBProcessor
        mock_process_called = False
        process_args = {}

        def mock_process_init(self: Any, **kwargs: Any) -> None:
            nonlocal process_args
            process_args = kwargs
            # Set required attributes
            self.messages_directory = kwargs.get("messages_directory", Path())
            self.collection_name = kwargs.get("collection_name", "")
            self.embedding_model = kwargs.get("embedding_model", "")
            self.batch_size = kwargs.get("batch_size", 100)
            # Mock lazy loaded properties
            self._chroma_client = None
            self._collection = None
            self._model = None
            # Mock progress tracker
            from discord_retriever.models import ProgressTracker
            self.progress = ProgressTracker()

        def mock_process_all(self: Any) -> int:
            nonlocal mock_process_called
            mock_process_called = True
            return 10  # Return a dummy count

        # Apply the mocks
        from discord_retriever.processor import VectorDBProcessor
        monkeypatch.setattr(VectorDBProcessor, "__init__", mock_process_init)
        monkeypatch.setattr(VectorDBProcessor, "process_all", mock_process_all)

        # Run the command with minimal arguments
        with tempfile.TemporaryDirectory() as temp_dir:
            result = cli_runner.invoke(
                app, ["process", "--input", temp_dir, "--collection", "test_collection"]
            )

            # Verify the result
            assert result.exit_code == 0
            assert mock_process_called
            assert process_args["messages_directory"] == Path(temp_dir)
            assert process_args["collection_name"] == "test_collection"

    def test_search_command(
        self, cli_runner: CliRunner, monkeypatch: pytest.MonkeyPatch, mock_sentence_transformer: Any, mock_chroma_client: Any
    ) -> None:
        """Test the search command."""
        # Mock the VectorDBProcessor.search method
        mock_search_called = False
        search_args = {}
        search_results = [
            {
                "content": "Test message 1",
                "metadata": {
                    "author": "testuser",
                    "timestamp": "2025-01-01T12:00:00",
                    "channel_id": "123",
                },
                "similarity": 0.9,
            },
            {
                "content": "Test message 2",
                "metadata": {
                    "author": "testuser",
                    "timestamp": "2025-01-01T12:01:00",
                    "channel_id": "123",
                },
                "similarity": 0.8,
            },
        ]

        def mock_processor_init(self: Any, **kwargs: Any) -> None:
            # Set required attributes
            self.messages_directory = kwargs.get("messages_directory", Path())
            self.collection_name = kwargs.get("collection_name", "")
            self.embedding_model = kwargs.get("embedding_model", "")
            self.batch_size = kwargs.get("batch_size", 100)
            # Mock lazy loaded properties
            self._chroma_client = None
            self._collection = None
            self._model = None
            # Mock progress tracker
            from discord_retriever.models import ProgressTracker
            self.progress = ProgressTracker()

        def mock_search(self: Any, query: str, n_results: int = 5) -> list:
            nonlocal mock_search_called, search_args
            mock_search_called = True
            search_args = {"query": query, "n_results": n_results}
            return search_results

        # Apply the mocks
        from discord_retriever.processor import VectorDBProcessor
        monkeypatch.setattr(VectorDBProcessor, "__init__", mock_processor_init)
        monkeypatch.setattr(VectorDBProcessor, "search", mock_search)

        # Run the command
        result = cli_runner.invoke(
            app, ["search", "--collection", "test_collection", "test query"]
        )

        # Verify the result
        assert result.exit_code == 0
        assert mock_search_called
        assert search_args["query"] == "test query"
        assert search_args["n_results"] == 5
        # Verify output contains search results
        assert "Test message 1" in result.stdout
        assert "Test message 2" in result.stdout
        assert "Similarity: 90%" in result.stdout
        assert "Similarity: 80%" in result.stdout

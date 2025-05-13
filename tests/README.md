# Discord Vector DB Tests

This directory contains tests for the Discord Vector DB project. It uses pytest as the test runner and includes unit tests, integration tests, and fixtures.

## Test Structure

The test directory is organized as follows:

```python
tests/
├── __init__.py                      # Makes tests a Python package
├── conftest.py                      # Shared fixtures and test configuration
├── test_models.py                   # Unit tests for data models
├── test_fetcher.py                  # Unit tests for the message fetcher
├── test_processor.py                # Unit tests for the vector DB processor
├── test_cli.py                      # Tests for CLI functionality
├── integration/                     # Integration tests directory
│   ├── __init__.py
│   └── test_fetch_to_process.py     # Tests the fetcher and processor together
└── fixtures/                        # Test data fixtures
    ├── __init__.py
    ├── sample_messages.json         # Sample Discord messages for testing
    └── sample_embeddings.json       # Sample vector embeddings for testing
```

## Running Tests

To run all tests:

```bash
pytest
```

To run specific test modules:

```bash
pytest tests/test_models.py
pytest tests/integration/
```

To run tests with specific markers:

```bash
pytest -m unit
pytest -m integration
```

## Test Categories

Tests are categorized using markers:

- `unit`: Tests for individual components
- `integration`: Tests that check multiple components working together
- `slow`: Tests that take a long time to run
- `wip`: Work in progress tests

To see all available markers:

```bash
pytest --markers
```

## Test Configuration

The test configuration is defined in `pytest.ini`, which includes:

- Minimum pytest version
- Test discovery patterns
- Filter warnings
- Test markers
- Logging level

## Fixtures

Common test fixtures are defined in `conftest.py` and include:

1. **Sample Data Fixtures**:
   - `sample_raw_message`: A raw Discord message dictionary
   - `sample_discord_message`: A DiscordMessage object
   - `sample_message_batch`: A batch of raw message dictionaries
   - `sample_checkpoint_data`: A CheckpointData object
   - `sample_embeddings`: Vector embeddings for testing

2. **Mock Fixtures**:
   - `mock_discord_mcp`: Mocks the Discord MCP server
   - `mock_sentence_transformer`: Mocks the embedding model
   - `mock_chroma_client`: Mocks the ChromaDB client and collection
   - `temp_message_directory`: Creates temporary directory with message batch files

## Writing New Tests

When adding new tests:

1. For unit tests, add a new test file or extend an existing one
2. For integration tests, add to the `integration` directory
3. Add new fixtures to `conftest.py` if they will be used across multiple test files
4. Follow the naming convention: `test_*.py` for files, `Test*` for classes, and `test_*` for functions
5. Use type annotations to ensure code quality
6. Document the purpose of each test class and function

## Mocking Strategy

The tests use several mocking strategies:

1. **Discord MCP Server**: Mocked to return predetermined message batches
2. **Sentence Transformer**: Mocked to return simple vector embeddings
3. **ChromaDB**: Mocked to simulate database operations
4. **Filesystem**: Uses temporary directories/files for testing

## CI Integration

The tests are designed to run in a CI environment and should:

1. Be isolated and not rely on external services
2. Use mocks for external dependencies
3. Be deterministic and reproducible
4. Have clear error messages

## Requirements

To run the tests, you'll need to install the following dependencies:

```bash
pip install pytest pytest-asyncio pytest-mock
```

## Known Issues

When running the tests, you may encounter the following warnings/errors:

1. Type checking errors about protected methods: The tests deliberately access protected methods (prefixed with `_`) for better test coverage.
2. Mypy/Basedpyright may show errors related to fixture typing. This is intentional as we rely on pytest's dynamic fixture injection.

These warnings don't affect the functionality of the tests and can be safely ignored.

# Discord Message Vector DB

A tool for retrieving Discord messages and storing them in a vector database for semantic search and analysis.

## Overview

This project provides a secure, privacy-respecting way to retrieve messages from Discord channels using the Discord MCP Server, process them for privacy concerns, and store them in a vector database (ChromaDB) for semantic search and analysis.

## Features

- **Robust Message Retrieval**: Fetch all messages from Discord channels with pagination support
- **Privacy Protection**: PII detection and redaction, opt-out registry
- **Resilient Design**: Checkpointing, error recovery, and circuit breaker patterns
- **Vector Database Integration**: Convert messages to embeddings for semantic search
- **Ethical Considerations**: Built-in privacy controls and data minimization

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/discord_vector_db.git
cd discord_vector_db

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from discord_retriever.fetcher import DiscordMessageFetcher

# Initialize fetcher
fetcher = DiscordMessageFetcher(
    channel_id="731607577481314359",
    save_directory="messages"
)

# Retrieve all messages
fetcher.fetch_all()
```

### Processing for Vector Database

```python
from discord_retriever.processor import process_for_vector_db

# Process messages and add to vector database
collection = process_for_vector_db(
    messages_directory="messages",
    collection_name="discord_messages"
)

# Search for semantically similar messages
results = collection.query(
    query_texts=["tell me about security concerns"],
    n_results=5
)
```

### Command Line Interface

```bash
# Fetch messages from a Discord channel
python -m discord_retriever.cli fetch --channel-id 731607577481314359 --save-dir messages

# Process messages for vector database
python -m discord_retriever.cli process --messages-dir messages --collection discord_messages

# Search for messages
python -m discord_retriever.cli search --collection discord_messages --query "security concerns"
```

## Ethical Considerations

This tool is designed with privacy and ethics in mind:

- All personal identifiable information (PII) can be automatically redacted
- Users can opt-out of having their messages processed
- Data minimization principles are applied by default
- Secure storage options for sensitive data

## License

MIT

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

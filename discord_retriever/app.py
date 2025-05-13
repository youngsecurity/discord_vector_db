"""
Application setup and initialization for Discord Message Vector DB.

This module provides functions for initializing the application with proper
service registration and configuration.
"""

import logging
from pathlib import Path
from typing import Optional

from discord_retriever.config import load_settings, AppSettings, audit_security_config
from discord_retriever.api import MessageFetcher, MessageProcessor, VectorDatabase, EmbeddingModel
from discord_retriever.services import ServiceProvider
from discord_retriever.exceptions import ConfigurationError

# Configure logging
logger = logging.getLogger(__name__)


def configure_services(settings: AppSettings) -> None:
    """
    Configure application services based on settings.
    
    This function sets up all dependencies and registers them with the
    ServiceProvider for dependency injection.
    
    Args:
        settings: Application settings
        
    Raises:
        ConfigurationError: If configuration is invalid
        ImportError: If required dependencies are missing
    """
    # Check for security warnings
    security_warnings = audit_security_config(settings)
    for warning in security_warnings:
        logger.warning(warning)
    
    # Initialize and register vector database service
    try:
        import chromadb
        client = chromadb.Client()
        collection = client.get_or_create_collection(
            name=settings.processor.collection_name
        )
        ServiceProvider.register(VectorDatabase, collection)
        logger.info(f"Registered vector database collection: {settings.processor.collection_name}")
    except ImportError:
        logger.error("chromadb is not installed. Please install it with: pip install chromadb")
        raise
    except Exception as e:
        logger.error(f"Error initializing vector database: {e}")
        raise ConfigurationError(f"Vector database initialization failed: {e}")
    
    # Initialize and register embedding model service
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(settings.processor.embedding_model)
        ServiceProvider.register(EmbeddingModel, model)
        logger.info(f"Registered embedding model: {settings.processor.embedding_model}")
    except ImportError:
        logger.error("sentence-transformers is not installed. Please install it with: pip install sentence-transformers")
        raise
    except Exception as e:
        logger.error(f"Error initializing embedding model: {e}")
        raise ConfigurationError(f"Embedding model initialization failed: {e}")


def initialize_app(config_file: Optional[Path] = None) -> AppSettings:
    """
    Initialize the application with the given configuration.
    
    Args:
        config_file: Path to YAML config file (optional)
        
    Returns:
        AppSettings instance with the loaded configuration
        
    Raises:
        ConfigurationError: If configuration is invalid
        ImportError: If required dependencies are missing
    """
    # Load settings
    try:
        settings = load_settings(config_file)
        logger.info("Application settings loaded")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise ConfigurationError(f"Configuration loading failed: {e}")
    
    # Configure services
    configure_services(settings)
    
    return settings


def run_fetch(settings: AppSettings) -> None:
    """
    Run the message fetching process.
    
    Args:
        settings: Application settings
        
    Raises:
        Various exceptions from the fetcher implementation
    """
    from discord_retriever.fetcher import DiscordMessageFetcher
    
    logger.info(f"Starting fetch for channel: {settings.fetcher.channel_id}")
    
    # Initialize fetcher
    fetcher = DiscordMessageFetcher(
        channel_id=settings.fetcher.channel_id,
        save_directory=settings.fetcher.save_directory,
        checkpoint_file=settings.fetcher.checkpoint_file,
        rate_limit_delay=settings.fetcher.rate_limit_delay,
        max_retries=settings.fetcher.max_retries,
        start_date=settings.fetcher.start_date,
        end_date=settings.fetcher.end_date,
    )
    
    # Fetch messages
    total_messages = fetcher.fetch_all()
    
    logger.info(f"Completed fetch: {total_messages} messages retrieved")


def run_process(settings: AppSettings) -> None:
    """
    Run the message processing process.
    
    Args:
        settings: Application settings
        
    Raises:
        Various exceptions from the processor implementation
    """
    from discord_retriever.processor import VectorDBProcessor
    
    logger.info(f"Starting processing from: {settings.processor.messages_directory}")
    
    # Initialize processor
    processor = VectorDBProcessor(
        messages_directory=settings.processor.messages_directory,
        collection_name=settings.processor.collection_name,
        embedding_model=settings.processor.embedding_model,
        batch_size=settings.processor.batch_size
    )
    
    # Process messages
    total_count = processor.process_all()
    
    logger.info(f"Completed processing: {total_count} messages added to vector database")


def search(query: str, n_results: int, settings: AppSettings) -> None:
    """
    Search for messages in the vector database.
    
    Args:
        query: Search query
        n_results: Number of results to return
        settings: Application settings
        
    Raises:
        Various exceptions from the processor implementation
    """
    from discord_retriever.processor import VectorDBProcessor
    
    logger.info(f"Searching for: {query}")
    
    # Initialize processor
    processor = VectorDBProcessor(
        messages_directory="",  # Not used for search
        collection_name=settings.processor.collection_name,
        embedding_model=settings.processor.embedding_model
    )
    
    # Search for messages
    results = processor.search(query, n_results=n_results)
    
    # Display results
    logger.info(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        logger.info(f"{i}. {result['content']} (Similarity: {result['similarity']:.2f})")
        logger.info(f"   Author: {result['metadata']['author']}, Timestamp: {result['metadata']['timestamp']}")

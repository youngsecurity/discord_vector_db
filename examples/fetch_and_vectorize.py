#!/usr/bin/env python3
"""
Example script for fetching Discord messages and adding them to a vector database.

This script demonstrates how to use the discord_retriever package to fetch
messages from a Discord channel and add them to a vector database for
semantic search.
"""

import argparse
import datetime
import logging
import sys
from pathlib import Path

from discord_retriever import (
    DiscordMessageFetcher,
    PrivacyFilter,
    VectorDBProcessor,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("discord_retriever.log")
    ]
)
logger = logging.getLogger("discord_retriever_example")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Fetch Discord messages and add to vector database")
    parser.add_argument("channel_id", help="Discord channel ID to fetch messages from")
    parser.add_argument("--save-dir", default="messages", help="Directory to save message batches")
    parser.add_argument("--collection", default="discord_messages", help="Vector DB collection name")
    parser.add_argument("--rate-limit", type=float, default=1.0, help="Delay between API calls in seconds")
    parser.add_argument("--start-date", help="Only fetch messages after this date (ISO format)")
    parser.add_argument("--end-date", help="Only fetch messages before this date (ISO format)")
    parser.add_argument("--redact-pii", action="store_true", help="Redact personally identifiable information")
    parser.add_argument("--opt-out-file", help="File containing list of opted-out user IDs")
    
    return parser.parse_args()


def fetch_messages(args):
    """Fetch messages from Discord channel."""
    logger.info(f"Fetching messages from channel: {args.channel_id}")
    
    # Parse dates if provided
    start_date = None
    if args.start_date:
        start_date = datetime.datetime.fromisoformat(args.start_date)
        
    end_date = None
    if args.end_date:
        end_date = datetime.datetime.fromisoformat(args.end_date)
    
    # Initialize fetcher
    fetcher = DiscordMessageFetcher(
        channel_id=args.channel_id,
        save_directory=args.save_dir,
        rate_limit_delay=args.rate_limit,
        start_date=start_date,
        end_date=end_date,
    )
    
    # Fetch messages
    try:
        total_messages = fetcher.fetch_all()
        logger.info(f"Successfully fetched {total_messages} messages!")
        return total_messages
    except NotImplementedError:
        logger.error(
            "The Discord MCP integration is not implemented in this example. "
            "In a real environment, you would need to integrate with the MCP tool."
        )
        return 0
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return 0


def process_messages(args):
    """Process messages and add to vector database."""
    logger.info(f"Processing messages from: {args.save_dir}")
    
    # Initialize processor
    processor = VectorDBProcessor(
        messages_directory=args.save_dir,
        collection_name=args.collection,
    )
    
    # Process messages
    try:
        total_count = processor.process_all()
        logger.info(f"Successfully processed {total_count} messages!")
        return total_count
    except ImportError:
        logger.error(
            "Vector database dependencies not installed. "
            "Please install with: pip install chromadb sentence-transformers"
        )
        return 0
    except Exception as e:
        logger.error(f"Error processing messages: {e}")
        return 0


def main():
    """Main function."""
    args = parse_args()
    
    # Create directories
    Path(args.save_dir).mkdir(parents=True, exist_ok=True)
    
    # Fetch messages
    if fetch_messages(args) > 0:
        # Process messages
        process_messages(args)
        
        # Show example search prompt
        print("\nYou can now search the vector database with:")
        print(f"from discord_retriever import VectorDBProcessor")
        print(f"processor = VectorDBProcessor('', '{args.collection}')")
        print(f"results = processor.search('your search query here')")
        print("for result in results:")
        print("    print(f\"Content: {result['content']}\")")
        print("    print(f\"Author: {result['metadata']['author']}\")")
        print("    print(f\"Similarity: {result['similarity']:.2f}\\n\")")


if __name__ == "__main__":
    main()

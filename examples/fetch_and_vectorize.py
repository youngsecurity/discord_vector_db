#!/usr/bin/env python
"""
Example script demonstrating the use of Discord Message Vector DB.

This script shows how to fetch messages from Discord and process them for
vector database storage using the improved architecture with dependency
injection and centralized configuration.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from discord_retriever.app import initialize_app, run_fetch, run_process, search
from discord_retriever.config import AppSettings
from discord_retriever.exceptions import ConfigurationError


def setup_logging(verbose: bool = False) -> None:
    """Set up logging with rich formatting."""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Discord Message Vector DB Example"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch messages from Discord")
    fetch_parser.add_argument(
        "--channel-id",
        help="Discord channel ID (overrides config)"
    )
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process messages for vector database")
    process_parser.add_argument(
        "--messages-dir",
        type=Path,
        help="Directory containing message files (overrides config)"
    )
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for messages")
    search_parser.add_argument(
        "query",
        help="Search query"
    )
    search_parser.add_argument(
        "--results", "-n",
        type=int,
        default=5,
        help="Number of results to return"
    )
    
    return parser.parse_args()


def override_settings(args: argparse.Namespace, settings: AppSettings) -> None:
    """Override settings from command line arguments."""
    # Override fetcher settings
    if args.command == "fetch" and args.channel_id:
        settings.fetcher.channel_id = args.channel_id
    
    # Override processor settings
    if args.command == "process" and args.messages_dir:
        settings.processor.messages_directory = args.messages_dir


def main() -> int:
    """Run the example script."""
    console = Console()
    
    # Parse arguments
    args = parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Load configuration
    try:
        settings = initialize_app(args.config)
        
        # Override settings from command line
        override_settings(args, settings)
        
    except ConfigurationError as e:
        console.print(f"[bold red]Configuration error: {e}[/bold red]")
        return 1
    except ImportError as e:
        console.print(f"[bold red]Missing dependency: {e}[/bold red]")
        return 1
    
    # Run the specified command
    try:
        if args.command == "fetch":
            console.print(f"[bold blue]Fetching messages from channel: {settings.fetcher.channel_id}[/bold blue]")
            run_fetch(settings)
            console.print("[bold green]Fetch completed successfully![/bold green]")
            
        elif args.command == "process":
            console.print(f"[bold blue]Processing messages from: {settings.processor.messages_directory}[/bold blue]")
            run_process(settings)
            console.print("[bold green]Processing completed successfully![/bold green]")
            
        elif args.command == "search":
            console.print(f"[bold blue]Searching for: {args.query}[/bold blue]")
            search(args.query, args.results, settings)
            
        else:
            console.print("[yellow]Please specify a command: fetch, process, or search[/yellow]")
            return 1
            
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        if args.verbose:
            import traceback
            console.print("[bold red]" + traceback.format_exc() + "[/bold red]")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

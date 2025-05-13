"""
Command-line interface for the Discord Message Vector DB.

This module provides a command-line interface for the Discord Message Vector DB
package, allowing users to fetch messages, process them, and search the vector database.
"""

import datetime
import logging
import sys
from pathlib import Path
from typing import Any, Optional

# Import package modules first
from .fetcher import DiscordMessageFetcher
from .processor import VectorDBProcessor
from .privacy import PrivacyFilter

try:
    import typer  # type: ignore
    from rich.console import Console  # type: ignore
    from rich.logging import RichHandler  # type: ignore
    from rich.progress import Progress, SpinnerColumn, TextColumn  # type: ignore
    from rich.table import Table  # type: ignore
except ImportError:
    print("CLI dependencies not installed. Please install with: pip install typer rich")
    sys.exit(1)

# Type helpers for typer - using simple functions with type ignores
def path_argument(default: Any, help_text: str) -> Path:
    """Helper to properly type Path arguments."""
    # We're telling the type checker to trust us here
    return typer.Argument(default, help=help_text)  # type: ignore

def path_option(default: Any, help_text: str) -> Path:
    """Helper to properly type Path options."""
    return typer.Option(default, help=help_text)  # type: ignore

def str_argument(default: Any, help_text: str) -> str:
    """Helper to properly type str arguments."""
    return typer.Argument(default, help=help_text)  # type: ignore

def str_option(default: str, help_text: str) -> str:
    """Helper to properly type str options."""
    return typer.Option(default, help=help_text)  # type: ignore

def float_option(default: float, help_text: str) -> float:
    """Helper to properly type float options."""
    return typer.Option(default, help=help_text)  # type: ignore

def int_option(default: int, help_text: str) -> int:
    """Helper to properly type int options."""
    return typer.Option(default, help=help_text)  # type: ignore

def datetime_option(default: Optional[datetime.datetime], help_text: str) -> Optional[datetime.datetime]:
    """Helper to properly type datetime options."""
    return typer.Option(default, help=help_text)  # type: ignore

def bool_option(default: bool, help_text: str) -> bool:
    """Helper to properly type bool options."""
    return typer.Option(default, help=help_text)  # type: ignore


# Set up CLI app
app = typer.Typer(help="Discord Message Vector DB CLI")
console = Console()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("discord_retriever")


# Add an explicit path_option_optional helper for optional Path parameters
def path_option_optional(default: Any, help_text: str) -> Optional[Path]:
    """Helper to properly type optional Path options."""
    return typer.Option(default, help=help_text)  # type: ignore

@app.command()
def fetch(
    channel_id: str = str_argument(..., "Discord channel ID to fetch messages from"),  # type: ignore
    save_dir: Path = path_option(Path("messages"), "Directory to save message batches"),  # type: ignore
    checkpoint_file: Optional[Path] = path_option_optional(None, "Checkpoint file path"),  # type: ignore
    rate_limit: float = float_option(1.0, "Delay between API calls in seconds"),  # type: ignore
    max_retries: int = int_option(5, "Maximum number of retries for failed API calls"),  # type: ignore
    start_date: Optional[datetime.datetime] = datetime_option(None, "Only fetch messages after this date (ISO format)"),  # type: ignore
    end_date: Optional[datetime.datetime] = datetime_option(None, "Only fetch messages before this date (ISO format)"),  # type: ignore
    redact_pii: bool = bool_option(True, "Redact personally identifiable information"),  # type: ignore
    opt_out_file: Optional[Path] = path_option_optional(None, "File containing list of opted-out user IDs (one per line)"),  # type: ignore
):
    """
    Fetch messages from a Discord channel.
    
    This command retrieves messages from a Discord channel using the Discord MCP server
    and saves them as JSON files.
    """
    console.print(f"[bold blue]Fetching messages from channel: {channel_id}[/bold blue]")
    
    # Load opt-out users if file provided
    opt_out_users = []
    if opt_out_file and opt_out_file.exists():
        with open(opt_out_file, 'r') as f:
            opt_out_users = [line.strip() for line in f if line.strip()]
        console.print(f"Loaded {len(opt_out_users)} opted-out users from {opt_out_file}")
    
    # Initialize privacy filter if needed
    if redact_pii or opt_out_users:
        # Create but don't store privacy filter since it's not being used yet
        # Will be passed to processor in a future implementation
        PrivacyFilter(
            redact_pii=redact_pii,
            opt_out_users=opt_out_users
        )
        
    # Initialize fetcher
    fetcher = DiscordMessageFetcher(
        channel_id=channel_id,
        save_directory=save_dir,
        checkpoint_file=checkpoint_file,
        rate_limit_delay=rate_limit,
        max_retries=max_retries,
        start_date=start_date,
        end_date=end_date,
    )
    
    # Create a spinner
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Fetching messages...[/bold blue]"),
        transient=True,
    ) as progress:
        progress.add_task("fetch", total=None)
        
        try:
            # Fetch messages
            total_messages = fetcher.fetch_all()
            
            # Show summary
            console.print(f"[bold green]Successfully fetched {total_messages} messages![/bold green]")
            console.print(f"Messages saved to: {save_dir}")
            
        except KeyboardInterrupt:
            console.print("[bold yellow]Fetch interrupted by user.[/bold yellow]")
            console.print("Progress saved to checkpoint. Run again to resume.")
            return
        except Exception as e:
            console.print(f"[bold red]Error fetching messages: {e}[/bold red]")
            console.print("Progress saved to checkpoint. Run again to resume.")
            return


@app.command()
def process(
    messages_dir: Path = path_argument(..., "Directory containing message batch files"),  # type: ignore
    collection: str = str_option("discord_messages", "Name of the vector database collection"),  # type: ignore
    embedding_model: str = str_option("all-MiniLM-L6-v2", "Name of the sentence transformer model"),  # type: ignore
    batch_size: int = int_option(100, "Number of messages to process at once"),  # type: ignore
):
    """
    Process messages and add them to a vector database.
    
    This command processes message batch files and adds them to a vector database
    for semantic search.
    """
    console.print(f"[bold blue]Processing messages from: {messages_dir}[/bold blue]")
    console.print(f"Using model: {embedding_model}")
    
    try:
        # Process messages
        processor = VectorDBProcessor(
            messages_directory=messages_dir,
            collection_name=collection,
            embedding_model=embedding_model,
            batch_size=batch_size
        )
        
        # Create a spinner
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Processing messages...[/bold blue]"),
            transient=True,
        ) as progress:
            progress.add_task("process", total=None)
            
            # Process all messages
            total_count = processor.process_all()
            
        # Show summary
        console.print(f"[bold green]Successfully processed {total_count} messages![/bold green]")
        console.print(f"Vector database collection: {collection}")
        
    except KeyboardInterrupt:
        console.print("[bold yellow]Processing interrupted by user.[/bold yellow]")
        return
    except Exception as e:
        console.print(f"[bold red]Error processing messages: {e}[/bold red]")
        return


@app.command()
def search(
    query: str = str_argument(..., "Search query"),  # type: ignore
    collection: str = str_option("discord_messages", "Name of the vector database collection"),  # type: ignore
    embedding_model: str = str_option("all-MiniLM-L6-v2", "Name of the sentence transformer model"),  # type: ignore
    n_results: int = int_option(5, "Number of results to return"),  # type: ignore
):
    """
    Search for messages in the vector database.
    
    This command searches for messages in the vector database that are semantically
    similar to the query.
    """
    console.print(f"[bold blue]Searching for: {query}[/bold blue]")
    
    try:
        # Initialize processor
        processor = VectorDBProcessor(
            messages_directory="",  # Not used for search
            collection_name=collection,
            embedding_model=embedding_model
        )
        
        # Search for messages
        results = processor.search(query, n_results=n_results)
        
        # Display results
        table = Table(title=f"Search Results for: {query}")
        table.add_column("Content", style="green", no_wrap=False)
        table.add_column("Author", style="blue")
        table.add_column("Timestamp", style="magenta")
        table.add_column("Similarity", style="cyan")
        
        for result in results:
            content = result["content"]
            metadata = result["metadata"]
            similarity = result["similarity"]
            
            # Truncate content if too long
            if len(content) > 100:
                content = content[:97] + "..."
                
            table.add_row(
                content,
                metadata["author"],
                metadata["timestamp"],
                f"{similarity:.2f}"
            )
            
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Error searching messages: {e}[/bold red]")
        return
        

def main():
    """Entry point for the CLI."""
    app()
    

if __name__ == "__main__":
    main()

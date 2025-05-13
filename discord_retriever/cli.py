"""
Command-line interface for the Discord Message Vector DB.

This module provides a command-line interface for the Discord Message Vector DB
package, allowing users to fetch messages, process them, and search the vector database.
"""

import datetime
import logging
import sys
from pathlib import Path
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
except ImportError:
    print("CLI dependencies not installed. Please install with: pip install typer rich")
    sys.exit(1)

from .fetcher import DiscordMessageFetcher
from .processor import VectorDBProcessor
from .privacy import PrivacyFilter

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


@app.command()
def fetch(
    channel_id: str = typer.Argument(None, help="Discord channel ID to fetch messages from"),  # type: ignore
    save_dir: Path = typer.Option(Path("messages"), help="Directory to save message batches"),
    checkpoint_file: Optional[Path] = typer.Option(None, help="Checkpoint file path"),
    rate_limit: float = typer.Option(1.0, help="Delay between API calls in seconds"),
    max_retries: int = typer.Option(5, help="Maximum number of retries for failed API calls"),
    start_date: Optional[datetime.datetime] = typer.Option(None, help="Only fetch messages after this date (ISO format)"),
    end_date: Optional[datetime.datetime] = typer.Option(None, help="Only fetch messages before this date (ISO format)"),
    redact_pii: bool = typer.Option(True, help="Redact personally identifiable information"),
    opt_out_file: Optional[Path] = typer.Option(None, help="File containing list of opted-out user IDs (one per line)"),
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
    privacy_filter = None
    if redact_pii or opt_out_users:
        privacy_filter = PrivacyFilter(
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
    messages_dir: Path = typer.Argument(None, help="Directory containing message batch files"),  # type: ignore
    collection: str = typer.Option("discord_messages", help="Name of the vector database collection"),
    embedding_model: str = typer.Option("all-MiniLM-L6-v2", help="Name of the sentence transformer model"),
    batch_size: int = typer.Option(100, help="Number of messages to process at once"),
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
    query: str = typer.Argument(None, help="Search query"),  # type: ignore
    collection: str = typer.Option("discord_messages", help="Name of the vector database collection"),
    embedding_model: str = typer.Option("all-MiniLM-L6-v2", help="Name of the sentence transformer model"),
    n_results: int = typer.Option(5, help="Number of results to return"),
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

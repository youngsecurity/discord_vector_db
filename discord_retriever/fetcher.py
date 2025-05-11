"""
Discord message fetcher for retrieving messages through the Discord MCP server.

This module handles retrieving messages from Discord channels with features like
pagination, checkpointing, and error recovery.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .models import CheckpointData, CircuitBreaker, DiscordMessage, ProgressTracker

# Configure logging
logger = logging.getLogger(__name__)


class DiscordMessageFetcher:
    """
    Fetches messages from Discord channels using the Discord MCP server.
    
    This class handles pagination, rate limiting, and checkpointing to retrieve
    all messages from a specified Discord channel.
    """
    
    def __init__(
        self,
        channel_id: str,
        save_directory: Union[str, Path],
        checkpoint_file: Optional[Union[str, Path]] = None,
        rate_limit_delay: float = 1.0,
        max_retries: int = 5,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):
        """
        Initialize the Discord message fetcher.
        
        Args:
            channel_id: The Discord channel ID to fetch messages from
            save_directory: Directory to save message batches
            checkpoint_file: File to save/load checkpoint data (defaults to 'checkpoint_{channel_id}.json')
            rate_limit_delay: Delay between API calls in seconds
            max_retries: Maximum number of retries for failed API calls
            start_date: Only fetch messages after this date (optional)
            end_date: Only fetch messages before this date (optional)
        """
        self.channel_id = channel_id
        self.save_directory = Path(save_directory)
        self.save_directory.mkdir(parents=True, exist_ok=True)
        
        # Set checkpoint file
        if checkpoint_file is None:
            self.checkpoint_file = Path(f"checkpoint_{channel_id}.json")
        else:
            self.checkpoint_file = Path(checkpoint_file)
        
        # API settings
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        
        # Date filtering
        self.start_date = start_date
        self.end_date = end_date
        
        # State
        self._load_checkpoint()
        
        # Circuit breaker for handling repeated failures
        self.circuit_breaker = CircuitBreaker(max_failures=max_retries)
        
        # Progress tracking
        self.progress = ProgressTracker(stall_timeout=300)  # 5 minutes timeout
    
    def _load_checkpoint(self) -> None:
        """Load the previous checkpoint if it exists."""
        checkpoint = CheckpointData.load(self.checkpoint_file)
        
        if checkpoint and checkpoint.channel_id == self.channel_id:
            self.oldest_message_id = checkpoint.oldest_message_id
            self.batch_count = checkpoint.batch_count
            self.total_messages = checkpoint.total_messages
            
            logger.info(
                f"Resuming from checkpoint: Message ID {self.oldest_message_id}, "
                f"Batch {self.batch_count}, Total {self.total_messages} messages"
            )
        else:
            self.oldest_message_id = None
            self.batch_count = 0
            self.total_messages = 0
            logger.info("Starting fresh fetch")
    
    def _save_checkpoint(self) -> None:
        """Save current state to checkpoint file."""
        checkpoint = CheckpointData(
            channel_id=self.channel_id,
            oldest_message_id=self.oldest_message_id,
            batch_count=self.batch_count,
            total_messages=self.total_messages
        )
        
        checkpoint.save(self.checkpoint_file)
        logger.debug(f"Checkpoint saved: {self.checkpoint_file}")
    
    def _fetch_messages_batch(self) -> List[Dict[str, Any]]:
        """
        Fetch a batch of messages from Discord.
        
        This method handles retries and circuit breaking for API failures.
        
        Returns:
            List of message data dictionaries
        
        Raises:
            RuntimeError: If the circuit breaker is open or all retries fail
        """
        if not self.circuit_breaker.can_execute():
            logger.error("Circuit breaker is open - too many consecutive failures")
            raise RuntimeError("Circuit breaker is open")
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                # Construct arguments for MCP tool
                args = {
                    "channel_id": self.channel_id,
                    "limit": 100
                }
                
                # Add the 'before' parameter if we have an oldest message ID
                if self.oldest_message_id:
                    args["before"] = self.oldest_message_id
                
                # Call the MCP tool
                logger.debug(f"Fetching messages with args: {args}")
                raw_messages = self._call_discord_mcp(args)
                
                # Reset circuit breaker on success
                self.circuit_breaker.record_success()
                
                return raw_messages
            
            except Exception as e:
                retry_count += 1
                last_error = e
                
                # Record failure in circuit breaker
                self.circuit_breaker.record_failure()
                
                # If we have retries left, wait and try again
                if retry_count <= self.max_retries:
                    wait_time = self.rate_limit_delay * (2 ** (retry_count - 1))  # Exponential backoff
                    logger.warning(
                        f"Error fetching messages: {e}. "
                        f"Retrying in {wait_time:.2f} seconds... (Attempt {retry_count}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
        
        # If we get here, all retries failed
        logger.error(f"Failed to fetch messages after {self.max_retries} attempts: {last_error}")
        raise RuntimeError(f"Failed to fetch messages: {last_error}")
    
    def _call_discord_mcp(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Call the Discord MCP server to fetch messages.
        
        This is a wrapper around the MCP tool call that would normally use
        the system's use_mcp_tool function. In a real implementation, this
        would interact with the actual Discord MCP server.
        
        Args:
            args: Arguments for the Discord MCP read_messages tool
            
        Returns:
            List of raw message data from Discord
            
        Raises:
            RuntimeError: If the MCP call fails
        """
        # Since we can't directly call use_mcp_tool here, this is a placeholder
        # for the actual implementation that would be used in a real environment
        
        # In a real environment, this would be:
        # result = use_mcp_tool(
        #     server_name="mcp-discord",
        #     tool_name="read_messages",
        #     arguments=args
        # )
        # return result
        
        # For now, we'll raise an exception to indicate this needs to be implemented
        # in the actual runtime environment
        raise NotImplementedError(
            "Discord MCP call not implemented. This needs to be integrated "
            "with the actual MCP tool in the runtime environment."
        )
    
    def _filter_messages_by_date(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter messages by date range if start_date or end_date is specified.
        
        Args:
            messages: List of raw message data from Discord
            
        Returns:
            Filtered list of messages
        """
        if not (self.start_date or self.end_date):
            return messages
        
        filtered_messages = []
        for msg in messages:
            timestamp_str = msg.get("timestamp", "")
            if not timestamp_str:
                continue
                
            # Parse timestamp
            msg_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            
            # Apply date filters
            include_message = True
            if self.start_date and msg_time < self.start_date:
                include_message = False
            if self.end_date and msg_time > self.end_date:
                include_message = False
                
            if include_message:
                filtered_messages.append(msg)
        
        return filtered_messages
    
    def _save_messages_batch(self, messages: List[Dict[str, Any]]) -> Path:
        """
        Save a batch of messages to a file.
        
        Args:
            messages: List of message data dictionaries
            
        Returns:
            Path to the saved file
        """
        # Create batch filename
        batch_file = self.save_directory / f"messages_batch_{self.batch_count:04d}.json"
        
        # Save messages
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        
        return batch_file
    
    def fetch_all(self) -> int:
        """
        Fetch all messages from the Discord channel.
        
        This method handles pagination, checkpointing, and error recovery
        to fetch all messages from the specified channel.
        
        Returns:
            Total number of messages fetched
        """
        logger.info(f"Starting fetch for channel: {self.channel_id}")
        
        if self.start_date:
            logger.info(f"Filtering messages from {self.start_date.isoformat()}")
        if self.end_date:
            logger.info(f"Filtering messages until {self.end_date.isoformat()}")
        
        try:
            while True:
                # Check if processing appears stalled
                if self.progress.is_stalled():
                    logger.error("Process appears stalled - no progress in configured timeout period")
                    break
                
                # Fetch a batch of messages
                try:
                    raw_messages = self._fetch_messages_batch()
                except (RuntimeError, NotImplementedError) as e:
                    logger.error(f"Error fetching messages: {e}")
                    break
                
                # Filter messages by date if needed
                messages = self._filter_messages_by_date(raw_messages)
                
                # If no messages were returned or all were filtered out, we've reached the end
                if not messages:
                    logger.info("No more messages found or all filtered out. Fetching complete.")
                    break
                
                # Save this batch to a file
                self.batch_count += 1
                batch_file = self._save_messages_batch(messages)
                
                # Update our pagination reference to the oldest message in this batch
                self.oldest_message_id = messages[-1]["id"]
                self.total_messages += len(messages)
                
                # Update progress
                self.progress.update(len(messages))
                
                logger.info(
                    f"Saved batch {self.batch_count} with {len(messages)} messages to {batch_file}. "
                    f"Total so far: {self.total_messages}"
                )
                
                # Save checkpoint after each batch
                self._save_checkpoint()
                
                # Respect Discord's rate limits
                time.sleep(self.rate_limit_delay)
                
        except KeyboardInterrupt:
            logger.info("Process interrupted by user. Progress saved to checkpoint.")
        except Exception as e:
            logger.exception(f"Error fetching messages: {e}")
            logger.info("Progress saved to checkpoint. Run again to resume.")
        finally:
            # Always save checkpoint on exit
            self._save_checkpoint()
        
        logger.info(f"Fetch complete! Retrieved {self.total_messages} messages in {self.batch_count} batches.")
        return self.total_messages


# Function to parse a message list result from use_mcp_tool
def parse_messages(result: str) -> List[Dict[str, Any]]:
    """
    Parse the result string from mcp-discord read_messages tool.
    
    Args:
        result: The string result from the MCP tool
        
    Returns:
        List of message dictionaries
    """
    # Example implementation, would need to be adapted to actual MCP server output format
    messages = []
    
    # Extract messages from the result
    # This is a simplified example and would need to be updated based on the 
    # actual format of the MCP server's output
    lines = result.strip().split("\n")
    for i, line in enumerate(lines):
        if ")" in line:
            # Try to parse a message line like:
            # username (timestamp): content
            parts = line.split("(", 1)
            if len(parts) == 2:
                author = parts[0].strip()
                rest = parts[1]
                
                timestamp_part, content_part = rest.split(")", 1)
                timestamp = timestamp_part.strip()
                
                # Remove the colon after the timestamp if present
                content = content_part[1:].strip() if content_part.startswith(":") else content_part.strip()
                
                messages.append({
                    "id": str(i),  # Use line number as ID since we don't have actual IDs
                    "content": content,
                    "author": author,
                    "timestamp": timestamp,
                    "channel_id": "",  # No channel ID in this format
                    "attachments": [],
                    "reactions": [],
                    "mentions": []
                })
    
    return messages

"""
Data models for the Discord Message Vector DB project.

This module defines the core data structures used throughout the project,
including message representations, configuration models, and checkpoint structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import json


class MessageSource(str, Enum):
    """Enum representing the source of a message."""
    DISCORD = "discord"
    SLACK = "slack"
    CUSTOM = "custom"


@dataclass
class DiscordMessage:
    """
    Represents a Discord message with all relevant metadata.
    
    This is the core data structure for handling Discord messages throughout the system.
    """
    id: str
    content: str
    author: str
    timestamp: datetime
    channel_id: str
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    reactions: List[Dict[str, Any]] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    source: MessageSource = MessageSource.DISCORD
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "DiscordMessage":
        """
        Create a DiscordMessage from an API response dictionary.
        
        Args:
            data: The raw API response from Discord
            
        Returns:
            A structured DiscordMessage object
        """
        # Handle timestamp conversion
        timestamp_str = data.get("timestamp", "")
        if timestamp_str:
            # Discord timestamps end with Z for UTC
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            timestamp = datetime.now()
            
        # Extract author information
        author = data.get("author", {}).get("username", "unknown")
        
        # Extract mentions
        mentions = []
        for mention in data.get("mentions", []):
            if "id" in mention:
                mentions.append(mention["id"])
        
        # Extract reactions
        reactions = []
        for reaction in data.get("reactions", []):
            reactions.append({
                "emoji": reaction.get("emoji", {}).get("name", ""),
                "count": reaction.get("count", 0)
            })
            
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            author=author,
            timestamp=timestamp,
            channel_id=data.get("channel_id", ""),
            attachments=data.get("attachments", []),
            reactions=reactions,
            mentions=mentions
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary representation.
        
        Returns:
            A dictionary representation of the message
        """
        return {
            "id": self.id,
            "content": self.content,
            "author": self.author,
            "timestamp": self.timestamp.isoformat(),
            "channel_id": self.channel_id,
            "attachments": self.attachments,
            "reactions": self.reactions,
            "mentions": self.mentions,
            "source": self.source.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiscordMessage":
        """
        Create a message from a dictionary representation.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            A DiscordMessage object
        """
        # Create a copy to avoid modifying the original
        data_copy = data.copy()
        
        # Handle source enum conversion
        source_str = data_copy.pop("source", MessageSource.DISCORD.value)
        source = MessageSource(source_str)
        
        # Handle timestamp conversion
        timestamp_str = data_copy.pop("timestamp", "")
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str)
        else:
            timestamp = datetime.now()
        
        # Extract required fields with proper types
        id = str(data_copy.pop("id", ""))
        content = str(data_copy.pop("content", ""))
        author = str(data_copy.pop("author", ""))
        channel_id = str(data_copy.pop("channel_id", ""))
        
        # Extract optional fields with proper types
        attachments = data_copy.pop("attachments", [])
        reactions = data_copy.pop("reactions", [])
        mentions = data_copy.pop("mentions", [])
        
        return cls(
            id=id,
            content=content,
            author=author,
            timestamp=timestamp,
            channel_id=channel_id,
            attachments=attachments,
            reactions=reactions,
            mentions=mentions,
            source=source
        )


@dataclass
class CheckpointData:
    """Data structure for storing and resuming message retrieval progress."""
    channel_id: str
    oldest_message_id: Optional[str] = None
    batch_count: int = 0
    total_messages: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def save(self, file_path: Union[str, Path]) -> None:
        """
        Save checkpoint data to a file.
        
        Args:
            file_path: Path to save the checkpoint data
        """
        data = {
            "channel_id": self.channel_id,
            "oldest_message_id": self.oldest_message_id,
            "batch_count": self.batch_count,
            "total_messages": self.total_messages,
            "last_updated": self.last_updated.isoformat()
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, file_path: Union[str, Path]) -> Optional["CheckpointData"]:
        """
        Load checkpoint data from a file.
        
        Args:
            file_path: Path to load the checkpoint data from
            
        Returns:
            CheckpointData if file exists and is valid, None otherwise
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract and convert fields to proper types
            channel_id = str(data.get("channel_id", ""))
            oldest_message_id = data.get("oldest_message_id")
            if oldest_message_id is not None:
                oldest_message_id = str(oldest_message_id)
                
            batch_count = int(data.get("batch_count", 0))
            total_messages = int(data.get("total_messages", 0))
            
            # Convert timestamp string to datetime
            last_updated_str = data.get("last_updated", "")
            if last_updated_str:
                last_updated = datetime.fromisoformat(last_updated_str)
            else:
                last_updated = datetime.now()
                
            return cls(
                channel_id=channel_id,
                oldest_message_id=oldest_message_id,
                batch_count=batch_count,
                total_messages=total_messages,
                last_updated=last_updated
            )
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None


@dataclass
class ProgressTracker:
    """Tracks progress and detects stalls in processing."""
    total_items: int = 0
    processed_items: int = 0
    stall_timeout: int = 300  # seconds
    last_update_time: datetime = field(default_factory=datetime.now)
    
    def update(self, count: int = 1) -> None:
        """
        Update the progress tracker with newly processed items.
        
        Args:
            count: Number of items processed in this update
        """
        self.processed_items += count
        self.last_update_time = datetime.now()
    
    def is_stalled(self) -> bool:
        """
        Check if processing appears to be stalled.
        
        Returns:
            True if no updates have occurred within the stall timeout, False otherwise
        """
        seconds_since_update = (datetime.now() - self.last_update_time).total_seconds()
        return seconds_since_update > self.stall_timeout
    
    @property
    def percentage_complete(self) -> float:
        """
        Calculate the percentage of completion.
        
        Returns:
            Percentage as a float between 0 and 100
        """
        if self.total_items == 0:
            return 0.0
        return min(100.0, (self.processed_items / self.total_items) * 100)


@dataclass
class CircuitBreaker:
    """
    Circuit breaker pattern implementation to prevent repeated failures.
    
    This class follows the Circuit Breaker design pattern to avoid repeated 
    attempts that might fail predictably after a certain threshold.
    """
    max_failures: int = 3
    reset_timeout: int = 60  # seconds
    failures: int = 0
    last_failure_time: Optional[datetime] = None
    is_open: bool = False
    
    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.max_failures:
            self.is_open = True
    
    def record_success(self) -> None:
        """Record a successful operation and reset the circuit."""
        self.failures = 0
        self.is_open = False
        self.last_failure_time = None
    
    def can_execute(self) -> bool:
        """
        Check if operation can be executed.
        
        Returns:
            True if operation should be allowed, False otherwise
        """
        # If circuit is open but reset timeout has passed, allow one try
        if self.is_open and self.last_failure_time:
            seconds_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
            if seconds_since_failure > self.reset_timeout:
                return True
                
        return not self.is_open

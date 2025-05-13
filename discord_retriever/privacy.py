"""
Privacy module for handling PII detection and redaction in Discord messages.

This module provides functionality for detecting and redacting personally
identifiable information (PII) from Discord messages.
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Pattern, Set, Union, Any, Final
from typing_extensions import TypedDict

from .models import DiscordMessage

# Configure logging
logger = logging.getLogger(__name__)


class PatternDict(TypedDict):
    """Dictionary containing a pattern definition."""
    type: str
    regex: str
    replacement: str


@dataclass
class RedactionPattern:
    """Pattern for detecting and redacting specific PII types."""
    type: str
    regex: Pattern[str]
    replacement: str
    
    @classmethod
    def from_dict(cls, data: PatternDict) -> "RedactionPattern":
        """Create a RedactionPattern from a dictionary representation."""
        return cls(
            type=data["type"],
            regex=re.compile(data["regex"], re.IGNORECASE),
            replacement=data["replacement"]
        )


class PrivacyFilter:
    """
    Filter for applying privacy protections to Discord messages.
    
    This class handles PII detection and redaction, as well as
    filtering messages from opted-out users.
    """
    
    # Default PII patterns
    DEFAULT_PATTERNS: Final[List[PatternDict]] = [
        {
            "type": "email",
            "regex": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "replacement": "[EMAIL REDACTED]"
        },
        {
            "type": "phone",
            "regex": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "replacement": "[PHONE REDACTED]"
        },
        {
            "type": "ssn",
            "regex": r"\b\d{3}[-]?\d{2}[-]?\d{4}\b",
            "replacement": "[SSN REDACTED]"
        },
        {
            "type": "ip",
            "regex": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            "replacement": "[IP REDACTED]"
        },
        {
            "type": "credit_card",
            "regex": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            "replacement": "[CREDIT CARD REDACTED]"
        }
    ]
    
    def __init__(
        self,
        redact_pii: bool = True,
        redaction_patterns: Optional[List[PatternDict]] = None,
        opt_out_users: Optional[List[str]] = None
    ):
        """
        Initialize the privacy filter.
        
        Args:
            redact_pii: Whether to redact PII from messages
            redaction_patterns: List of patterns to use for redaction
            opt_out_users: List of user IDs who have opted out
        """
        self.redact_pii: bool = redact_pii
        self.opt_out_users: Set[str] = set(opt_out_users or [])
        
        # Set up redaction patterns
        self.patterns: List[RedactionPattern] = []
        if redaction_patterns:
            # Use provided patterns
            for pattern_dict in redaction_patterns:
                self.patterns.append(RedactionPattern.from_dict(pattern_dict))
        else:
            # Use default patterns
            for pattern_dict in self.DEFAULT_PATTERNS:
                self.patterns.append(RedactionPattern.from_dict(pattern_dict))
                
        logger.info(f"Initialized privacy filter with {len(self.patterns)} patterns and {len(self.opt_out_users)} opt-out users")
    
    def process_message(self, message: Union[DiscordMessage, Dict[str, Any]]) -> Optional[DiscordMessage]:
        """
        Process a message, applying privacy filters.
        
        Args:
            message: The Discord message to process
            
        Returns:
            Processed message, or None if it should be excluded
        """
        # Convert dict to DiscordMessage if needed
        if isinstance(message, dict):
            discord_msg = DiscordMessage.from_dict(message)
        else:
            discord_msg = message
            
        # Check for opt-out
        if discord_msg.author in self.opt_out_users:
            logger.debug(f"Excluding message from opted-out user: {discord_msg.author}")
            return None
            
        # Apply PII redaction if enabled
        if self.redact_pii:
            content = self._redact_pii(discord_msg.content)
            if content != discord_msg.content:
                # Create a copy with redacted content
                message_dict = discord_msg.to_dict()
                message_dict["content"] = content
                return DiscordMessage.from_dict(message_dict)
            
        return discord_msg
    
    def _redact_pii(self, text: str) -> str:
        """
        Redact personally identifiable information from text.
        
        Args:
            text: The text to redact
            
        Returns:
            Text with PII redacted
        """
        if not text:
            return text
            
        redacted = text
        for pattern in self.patterns:
            redacted = pattern.regex.sub(pattern.replacement, redacted)
            
        return redacted
    
    def add_opt_out_user(self, user_id: str) -> None:
        """
        Add a user to the opt-out list.
        
        Args:
            user_id: The user ID to add
        """
        self.opt_out_users.add(user_id)
        logger.info(f"Added user {user_id} to opt-out list")
    
    def remove_opt_out_user(self, user_id: str) -> bool:
        """
        Remove a user from the opt-out list.
        
        Args:
            user_id: The user ID to remove
            
        Returns:
            True if the user was in the list, False otherwise
        """
        if user_id in self.opt_out_users:
            self.opt_out_users.remove(user_id)
            logger.info(f"Removed user {user_id} from opt-out list")
            return True
        return False
    
    def add_redaction_pattern(self, pattern_type: str, regex: str, replacement: str) -> None:
        """
        Add a new redaction pattern.
        
        Args:
            pattern_type: Type of PII to detect
            regex: Regular expression pattern
            replacement: Text to use as replacement
        """
        pattern = RedactionPattern(
            type=pattern_type,
            regex=re.compile(regex, re.IGNORECASE),
            replacement=replacement
        )
        self.patterns.append(pattern)
        logger.info(f"Added new redaction pattern for {pattern_type}")

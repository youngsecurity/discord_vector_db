"""
Centralized configuration system for Discord Message Vector DB.

This module provides a Pydantic-based configuration management system
that supports loading settings from environment variables and/or config files.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any, cast
from datetime import datetime
from typing_extensions import Protocol, Annotated
from pydantic import BaseModel, Field, field_validator, ValidationInfo, ConfigDict


class FetcherSettings(BaseModel):
    """Settings for the Discord message fetcher."""
    channel_id: str
    save_directory: Path = Field(default=Path("messages"))
    checkpoint_file: Optional[Path] = None
    rate_limit_delay: float = 1.0
    max_retries: int = 5
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @field_validator('checkpoint_file', mode='before')
    def set_checkpoint_file(cls, v: Optional[Path], info: ValidationInfo) -> Optional[Path]:
        """Set default checkpoint file if not provided."""
        if v is None and 'channel_id' in info.data:
            return Path(f"checkpoint_{info.data['channel_id']}.json")
        return v
    
    # Type annotation workaround for basedpyright
    model_config: Any = ConfigDict(env_prefix="DISCORD_FETCHER_")


class ProcessorSettings(BaseModel):
    """Settings for the vector database processor."""
    messages_directory: Path
    collection_name: str = "discord_messages"
    embedding_model: str = "all-MiniLM-L6-v2"
    batch_size: int = 100
    
    # Type annotation workaround for basedpyright
    model_config: Any = ConfigDict(env_prefix="DISCORD_PROCESSOR_")


class PrivacySettings(BaseModel):
    """Settings for privacy filtering."""
    redact_pii: bool = True
    opt_out_file: Optional[Path] = None
    custom_patterns: List[Dict[str, str]] = Field(default_factory=list)
    
    # Type annotation workaround for basedpyright
    model_config: Any = ConfigDict(env_prefix="DISCORD_PRIVACY_")


class SecuritySettings(BaseModel):
    """Settings for security features."""
    encryption_enabled: bool = True
    key_file: Optional[Path] = Field(default=Path("discord_db.key"))
    data_directory: Path = Field(default=Path("secure_data"))
    
    # Type annotation workaround for basedpyright
    model_config: Any = ConfigDict(env_prefix="DISCORD_SECURITY_")


class AppSettings(BaseModel):
    """Main application settings."""
    fetcher: FetcherSettings
    processor: ProcessorSettings
    privacy: PrivacySettings = Field(default_factory=PrivacySettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    
    # Type annotation workaround for basedpyright
    model_config: Any = ConfigDict(
        env_prefix="DISCORD_",
        env_nested_delimiter="__"
    )


def load_settings(config_file: Optional[Path] = None) -> AppSettings:
    """
    Load application settings from config file and environment variables.
    
    Args:
        config_file: Path to YAML config file (optional)
        
    Returns:
        AppSettings instance with loaded configuration
        
    Raises:
        FileNotFoundError: If config_file is provided but doesn't exist
        ValueError: If config file contains invalid configuration
    """
    settings_dict: Dict[str, Any] = {}
    
    # Load from config file if provided
    if config_file and config_file.exists():
        try:
            import yaml  # type: ignore
            with open(config_file, "r", encoding="utf-8") as f:
                settings_dict = yaml.safe_load(f)
        except ImportError:
            raise ImportError("PyYAML is required for YAML config files. Install with 'pip install pyyaml'")
        except Exception as e:
            raise ValueError(f"Error loading config file: {e}")
    
    # Create settings instance
    return AppSettings(**settings_dict)


def audit_security_config(app_settings: AppSettings) -> List[str]:
    """
    Audit the security configuration and return warnings for insecure settings.
    
    Args:
        app_settings: Application settings to audit
        
    Returns:
        List of warning messages for insecure settings
    """
    warnings = []
    
    # Check security settings
    if not app_settings.security.encryption_enabled:
        warnings.append("WARNING: Encryption is disabled. This is not recommended for production use.")
    
    # Check privacy settings
    if not app_settings.privacy.redact_pii:
        warnings.append("WARNING: PII redaction is disabled. This may expose sensitive personal information.")
    
    # Check for key file in a standard location
    if (app_settings.security.encryption_enabled and app_settings.security.key_file and
            app_settings.security.key_file.name == "discord_db.key" and 
            app_settings.security.key_file.parent == Path(".")):
        warnings.append("WARNING: Using default key file location. Consider using a more secure location.")
    
    return warnings

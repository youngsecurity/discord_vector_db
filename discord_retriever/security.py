"""
Security module for Discord Message Vector DB.

This module provides functionality for secure storage of message data,
including encryption and secure deletion.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)


class SecureStorage:
    """
    Securely store message data.
    
    This class provides methods for encrypting and decrypting message data,
    as well as securely deleting files.
    """
    
    def __init__(
        self,
        data_dir: Union[str, Path],
        encryption_enabled: bool = False,
        key_file: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize the secure storage.
        
        Args:
            data_dir: Directory to store data
            encryption_enabled: Whether to encrypt data
            key_file: Path to encryption key file
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.encryption_enabled = encryption_enabled
        self.key_file = Path(key_file) if key_file else None
        
        # Initialize encryption if enabled
        if self.encryption_enabled:
            self._initialize_encryption()
            
        logger.info(f"Initialized secure storage in {self.data_dir} (encryption: {self.encryption_enabled})")
    
    def _initialize_encryption(self) -> None:
        """
        Initialize encryption.
        
        This loads or generates an encryption key.
        """
        try:
            from cryptography.fernet import Fernet
        except ImportError:
            logger.error("cryptography is not installed. Please install it with: pip install cryptography")
            raise
            
        # Check if key file exists
        if self.key_file and self.key_file.exists():
            # Load existing key
            try:
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                self._cipher = Fernet(key)
                logger.info(f"Loaded encryption key from {self.key_file}")
            except Exception as e:
                logger.error(f"Error loading encryption key: {e}")
                raise
        else:
            # Generate new key
            key = Fernet.generate_key()
            self._cipher = Fernet(key)
            
            # Save key if key file specified
            if self.key_file:
                # Set secure permissions (only for Unix)
                if hasattr(os, 'chmod'):
                    # Create parent directories
                    self.key_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Save key with secure permissions
                    try:
                        with open(self.key_file, 'wb') as f:
                            f.write(key)
                        os.chmod(self.key_file, 0o600)  # Owner read/write only
                        logger.info(f"Generated and saved new encryption key to {self.key_file}")
                    except Exception as e:
                        logger.error(f"Error saving encryption key: {e}")
                        raise
                else:
                    # Windows - just save the key
                    try:
                        with open(self.key_file, 'wb') as f:
                            f.write(key)
                        logger.info(f"Generated and saved new encryption key to {self.key_file}")
                    except Exception as e:
                        logger.error(f"Error saving encryption key: {e}")
                        raise
    
    def save_data(self, filename: str, data: Any) -> Path:
        """
        Save data to a file, optionally encrypting it.
        
        Args:
            filename: Name of the file to save
            data: Data to save (must be JSON serializable)
            
        Returns:
            Path to the saved file
        """
        import json
        
        # Determine file path
        file_path = self.data_dir / filename
        
        # Convert data to JSON
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        if self.encryption_enabled:
            # Encrypt data
            try:
                encrypted_data = self._cipher.encrypt(json_data)
                with open(file_path, 'wb') as f:
                    f.write(encrypted_data)
            except Exception as e:
                logger.error(f"Error encrypting data: {e}")
                raise
                
            logger.debug(f"Saved and encrypted data to {file_path}")
        else:
            # Save as plain JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_data.decode('utf-8'))
                
            # Set secure permissions (only for Unix)
            if hasattr(os, 'chmod'):
                try:
                    os.chmod(file_path, 0o600)  # Owner read/write only
                except Exception as e:
                    logger.warning(f"Could not set file permissions: {e}")
                    
            logger.debug(f"Saved data to {file_path}")
            
        return file_path
    
    def load_data(self, filename: str) -> Any:
        """
        Load data from a file, decrypting if necessary.
        
        Args:
            filename: Name of the file to load
            
        Returns:
            Loaded data
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file cannot be decrypted or parsed
        """
        import json
        
        # Determine file path
        file_path = self.data_dir / filename
        
        # Check if file exists
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if self.encryption_enabled:
            # Decrypt data
            try:
                with open(file_path, 'rb') as f:
                    encrypted_data = f.read()
                    
                decrypted_data = self._cipher.decrypt(encrypted_data)
                data = json.loads(decrypted_data.decode('utf-8'))
                
                logger.debug(f"Loaded and decrypted data from {file_path}")
                return data
            except Exception as e:
                logger.error(f"Error decrypting data: {e}")
                raise ValueError(f"Error decrypting data: {e}")
        else:
            # Load plain JSON
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                logger.debug(f"Loaded data from {file_path}")
                return data
            except Exception as e:
                logger.error(f"Error loading data: {e}")
                raise ValueError(f"Error loading data: {e}")
    
    def secure_delete(self, filename: str) -> None:
        """
        Securely delete a file by overwriting it before deletion.
        
        Args:
            filename: Name of the file to delete
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        # Determine file path
        file_path = self.data_dir / filename
        
        # Check if file exists
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Get file size
        file_size = file_path.stat().st_size
        
        try:
            # Open file in binary mode
            with open(file_path, 'wb') as f:
                # Overwrite with random data
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
                
            # Delete the file
            os.unlink(file_path)
            logger.info(f"Securely deleted {file_path}")
            
        except Exception as e:
            logger.error(f"Error securely deleting {file_path}: {e}")
            raise
    
    def encrypt_existing_file(self, file_path: Union[str, Path]) -> Path:
        """
        Encrypt an existing file.
        
        Args:
            file_path: Path to the file to encrypt
            
        Returns:
            Path to the encrypted file
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If encryption is not enabled
        """
        if not self.encryption_enabled:
            logger.error("Encryption is not enabled")
            raise ValueError("Encryption is not enabled")
            
        file_path = Path(file_path)
        
        # Check if file exists
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Determine destination path
        dest_path = self.data_dir / file_path.name
        
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
                
            # Encrypt content
            encrypted_content = self._cipher.encrypt(content)
            
            # Write encrypted content
            with open(dest_path, 'wb') as f:
                f.write(encrypted_content)
                
            logger.info(f"Encrypted {file_path} to {dest_path}")
            return dest_path
            
        except Exception as e:
            logger.error(f"Error encrypting file: {e}")
            raise

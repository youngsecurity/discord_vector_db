"""
Type stubs for cryptography.fernet module.
"""
from typing import Any, Callable, ClassVar, Optional, Union

class Fernet:
    """The Fernet symmetric encryption algorithm."""
    
    def __init__(self, key: bytes) -> None:
        """Initialize a Fernet instance with the given key."""
        ...
    
    @classmethod
    def generate_key(cls) -> bytes:
        """Generate a new fernet key."""
        ...
    
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data."""
        ...
    
    def decrypt(self, data: bytes, ttl: Optional[int] = None) -> bytes:
        """
        Decrypt data.
        
        Args:
            data: The ciphertext to decrypt.
            ttl: Time to live in seconds. If the message is older than ttl seconds,
                 and ttl is not None, an exception will be raised.
        
        Returns:
            The original plaintext.
        """
        ...

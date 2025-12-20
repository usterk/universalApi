"""API key utilities for source authentication."""

import secrets
import hashlib

from app.config import settings


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        Tuple of (full_key, key_hash, key_prefix)
        - full_key: The actual key to give to the user (shown once)
        - key_hash: Hash to store in database
        - key_prefix: First chars for identification
    """
    # Generate random key
    random_part = secrets.token_urlsafe(32)
    full_key = f"{settings.api_key_prefix}{random_part}"

    # Hash for storage
    key_hash = hash_api_key(full_key)

    # Prefix for identification (first 8 chars after prefix)
    key_prefix = f"{settings.api_key_prefix}{random_part[:8]}"

    return full_key, key_hash, key_prefix


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, key_hash: str) -> bool:
    """Verify an API key against a hash."""
    return hash_api_key(api_key) == key_hash

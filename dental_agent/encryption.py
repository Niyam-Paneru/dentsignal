"""
encryption.py - Database Field Encryption Helpers

Provides encryption for sensitive database fields:
- PII (Personally Identifiable Information)
- Phone numbers
- Email addresses (optional)
- API keys/secrets

Uses Fernet symmetric encryption from cryptography library.

Usage:
    from encryption import encrypt_field, decrypt_field, EncryptedString
    
    # In model
    phone_encrypted: str = Field(default="")
    
    @property
    def phone(self) -> str:
        return decrypt_field(self.phone_encrypted) if self.phone_encrypted else ""
    
    @phone.setter
    def phone(self, value: str):
        self.phone_encrypted = encrypt_field(value) if value else ""
"""

import os
import base64
import hashlib
import hmac
import logging
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configure encryption logger
logger = logging.getLogger(__name__)


# =============================================================================
# ENCRYPTION CONFIGURATION
# =============================================================================

# Encryption key should be set via environment variable
# Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

# Salt for key derivation (should be constant for same database)
ENCRYPTION_SALT = os.getenv("ENCRYPTION_SALT", "dentsignal_default_salt").encode()


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


class EncryptionNotConfiguredError(EncryptionError):
    """Raised when encryption is not properly configured."""
    pass


# =============================================================================
# KEY MANAGEMENT
# =============================================================================

def _get_fernet() -> Fernet:
    """
    Get or create Fernet instance with encryption key.
    
    Returns:
        Configured Fernet instance
        
    Raises:
        EncryptionNotConfiguredError: If encryption key is not set
    """
    global _fernet_instance
    
    if '_fernet_instance' not in globals():
        if not ENCRYPTION_KEY:
            raise EncryptionNotConfiguredError(
                "ENCRYPTION_KEY environment variable not set. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        
        # If key is provided as base64 string, use directly
        # Otherwise, derive key from password
        try:
            key = ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
            # Validate it's a valid Fernet key
            Fernet(key)
            _fernet_instance = Fernet(key)
        except Exception:
            # Derive key from password using PBKDF2
            logger.warning("ENCRYPTION_KEY is not a valid Fernet key, deriving from password")
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=ENCRYPTION_SALT,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY.encode()))
            _fernet_instance = Fernet(key)
    
    return _fernet_instance


def generate_encryption_key() -> str:
    """
    Generate a new encryption key.
    
    Returns:
        Base64-encoded encryption key
    """
    return Fernet.generate_key().decode()


# =============================================================================
# FIELD ENCRYPTION
# =============================================================================

def encrypt_field(value: str) -> str:
    """
    Encrypt a string field.
    
    Args:
        value: Plain text value to encrypt
        
    Returns:
        Encrypted value as base64 string
        
    Raises:
        EncryptionNotConfiguredError: If encryption is not configured
        EncryptionError: If encryption fails
    """
    if not value:
        return ""
    
    if not isinstance(value, str):
        value = str(value)
    
    try:
        fernet = _get_fernet()
        encrypted = fernet.encrypt(value.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise EncryptionError(f"Failed to encrypt field: {e}")


def decrypt_field(encrypted_value: str) -> str:
    """
    Decrypt an encrypted field.
    
    Args:
        encrypted_value: Encrypted value from database
        
    Returns:
        Decrypted plain text value
        
    Raises:
        EncryptionError: If decryption fails
    """
    if not encrypted_value:
        return ""
    
    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted_value.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise EncryptionError(f"Failed to decrypt field: {e}")


def encrypt_optional_field(value: Optional[str]) -> Optional[str]:
    """Encrypt a field that may be None."""
    if value is None:
        return None
    return encrypt_field(value)


def decrypt_optional_field(encrypted_value: Optional[str]) -> Optional[str]:
    """Decrypt a field that may be None."""
    if encrypted_value is None:
        return None
    return decrypt_field(encrypted_value)


# =============================================================================
# ENCRYPTED STRING TYPE
# =============================================================================

class EncryptedString:
    """
    Helper class for encrypted string fields.
    
    Usage in SQLModel:
        phone_encrypted: Optional[str] = Field(default=None)
        
        @property
        def phone(self) -> Optional[str]:
            return EncryptedString.decrypt(self.phone_encrypted)
        
        @phone.setter
        def phone(self, value: Optional[str]):
            self.phone_encrypted = EncryptedString.encrypt(value)
    """
    
    @staticmethod
    def encrypt(value: Optional[str]) -> Optional[str]:
        """Encrypt a string value."""
        return encrypt_optional_field(value)
    
    @staticmethod
    def decrypt(value: Optional[str]) -> Optional[str]:
        """Decrypt an encrypted value."""
        return decrypt_optional_field(value)


# =============================================================================
# MASKED DISPLAY
# =============================================================================

def mask_for_display(value: str, visible_chars: int = 4) -> str:
    """
    Mask a value for display, showing only last N characters.
    
    Args:
        value: Value to mask
        visible_chars: Number of characters to show at end
        
    Returns:
        Masked string like '*****1234'
    """
    if not value:
        return ""
    
    if len(value) <= visible_chars:
        return "*" * len(value)
    
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]


# =============================================================================
# ENCRYPTION STATUS CHECK
# =============================================================================

def is_encryption_configured() -> bool:
    """Check if encryption is properly configured."""
    return ENCRYPTION_KEY is not None and ENCRYPTION_KEY != ""


def validate_encryption_setup() -> tuple[bool, str]:
    """
    Validate encryption configuration.
    
    Returns:
        Tuple of (is_valid, message)
    """
    if not ENCRYPTION_KEY:
        return False, "ENCRYPTION_KEY not set"
    
    try:
        fernet = _get_fernet()
        # Test encryption/decryption
        test_value = "test_encryption_setup"
        encrypted = fernet.encrypt(test_value.encode())
        decrypted = fernet.decrypt(encrypted).decode()
        
        if decrypted == test_value:
            return True, "Encryption configured and working"
        else:
            return False, "Encryption test failed - decryption mismatch"
    except Exception as e:
        return False, f"Encryption test failed: {e}"


# =============================================================================
# DATABASE COLUMN ENCRYPTION HELPERS
# =============================================================================

def encrypt_dict_values(data: dict, sensitive_fields: list) -> dict:
    """
    Encrypt sensitive fields in a dictionary.
    
    Args:
        data: Dictionary with data
        sensitive_fields: List of field names to encrypt
        
    Returns:
        Dictionary with encrypted fields
    """
    result = data.copy()
    for field in sensitive_fields:
        if field in result and result[field]:
            result[field] = encrypt_field(str(result[field]))
    return result


def decrypt_dict_values(data: dict, encrypted_fields: list) -> dict:
    """
    Decrypt encrypted fields in a dictionary.
    
    Args:
        data: Dictionary with encrypted data
        encrypted_fields: List of field names to decrypt
        
    Returns:
        Dictionary with decrypted fields
    """
    result = data.copy()
    for field in encrypted_fields:
        if field in result and result[field]:
            result[field] = decrypt_field(result[field])
    return result


# =============================================================================
# SQLALCHEMY TYPE DECORATOR — TRANSPARENT FIELD ENCRYPTION (AG-8)
# =============================================================================

try:
    from sqlalchemy import Text
    from sqlalchemy.types import TypeDecorator
    _HAS_SQLALCHEMY = True
except ImportError:
    _HAS_SQLALCHEMY = False
    TypeDecorator = None  # type: ignore[misc,assignment]


if _HAS_SQLALCHEMY:
    class EncryptedType(TypeDecorator):
        """
        SQLAlchemy type that transparently encrypts on write and decrypts on read.

        Usage with SQLModel::

            phone: str = Field(sa_column=Column("phone", EncryptedType()))

        Behaviour:
        - INSERT/UPDATE: plaintext → Fernet ciphertext
        - SELECT: ciphertext → plaintext
        - NULL values pass through unchanged
        - When ENCRYPTION_KEY is not configured → passthrough (dev mode)
        - Pre-migration plaintext rows → returned as-is (graceful fallback)
        """
        impl = Text
        cache_ok = True

        def process_bind_param(self, value, dialect):
            """Encrypt value before writing to DB."""
            if value is None:
                return None
            if not is_encryption_configured():
                return value
            try:
                return encrypt_field(str(value))
            except EncryptionError:
                logger.warning("PHI encrypt failed — storing plaintext")
                return value

        def process_result_value(self, value, dialect):
            """Decrypt value after reading from DB."""
            if value is None:
                return None
            if not is_encryption_configured():
                return value
            try:
                return decrypt_field(value)
            except (EncryptionError, Exception):
                # Pre-migration plaintext — return as-is
                return value


def phi_hash(value: Optional[str]) -> str:
    """
    Deterministic HMAC-SHA256 hash for encrypted PHI field lookups.

    Produces a 64-char hex digest keyed with ENCRYPTION_KEY so hashes
    cannot be rainbow-tabled without the key.

    Normalises input (strip + lowercase) for consistent matching.

    Args:
        value: Plaintext PHI value (phone, email, etc.)

    Returns:
        64-char hex HMAC-SHA256 digest, or empty string if value is None/empty
    """
    if not value:
        return ""
    normalized = value.strip().lower()
    if not normalized:
        return ""
    key = (ENCRYPTION_KEY or "default-dev-hash-key").encode()
    return hmac.new(key, normalized.encode(), hashlib.sha256).hexdigest()


# =============================================================================
# EXAMPLE USAGE FOR MODELS
# =============================================================================

"""
Example of encrypted field in a SQLModel model:

from sqlmodel import SQLModel, Field
from encryption import encrypt_field, decrypt_field

class Patient(SQLModel, table=True):
    __tablename__ = "patients"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    # Store encrypted phone
    phone_encrypted: Optional[str] = Field(default=None, alias="phone")
    email: str
    
    @property
    def phone(self) -> Optional[str]:
        \"\"\"Get decrypted phone number.\"\"\"
        return decrypt_field(self.phone_encrypted) if self.phone_encrypted else None
    
    @phone.setter
    def phone(self, value: Optional[str]):
        \"\"\"Set and encrypt phone number.\"\"\"
        self.phone_encrypted = encrypt_field(value) if value else None
"""

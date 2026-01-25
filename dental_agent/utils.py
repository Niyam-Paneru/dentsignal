"""
Utility functions for the Dental AI Voice Agent.

Provides:
- Phone number validation and normalization (E.164)
- PII masking for logs
- Rotating file logger
- Input sanitization
- Standardized error responses
"""

import re
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
from functools import wraps
import time

# Optional: phonenumbers for robust E.164 validation
try:
    import phonenumbers
    from phonenumbers import NumberParseException
    HAS_PHONENUMBERS = True
except ImportError:
    HAS_PHONENUMBERS = False


# -----------------------------------------------------------------------------
# Phone Number Validation & Normalization
# -----------------------------------------------------------------------------

def normalize_phone(phone: str, default_region: str = "US") -> Optional[str]:
    """
    Normalize a phone number to E.164 format.
    
    Args:
        phone: Raw phone number string
        default_region: Default region code (ISO 3166-1 alpha-2)
        
    Returns:
        E.164 formatted phone number or None if invalid
        
    Examples:
        >>> normalize_phone("(555) 123-4567")
        '+15551234567'
        >>> normalize_phone("555-123-4567", "US")
        '+15551234567'
        >>> normalize_phone("+44 20 7946 0958")
        '+442079460958'
    """
    if not phone:
        return None
    
    # Strip whitespace
    phone = phone.strip()
    
    if HAS_PHONENUMBERS:
        try:
            parsed = phonenumbers.parse(phone, default_region)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.E164
                )
            return None
        except NumberParseException:
            return None
    else:
        # Fallback: basic regex normalization
        # Remove all non-digit characters except leading +
        digits = re.sub(r'[^\d+]', '', phone)
        
        # Handle various formats
        if digits.startswith('+'):
            # Already has country code
            if len(digits) >= 11:  # +1 + 10 digits minimum
                return digits
        elif digits.startswith('1') and len(digits) == 11:
            # US number with country code but no +
            return f'+{digits}'
        elif len(digits) == 10:
            # US number without country code
            return f'+1{digits}'
        
        return None


def is_valid_phone(phone: str, default_region: str = "US") -> bool:
    """
    Check if a phone number is valid.
    
    Args:
        phone: Phone number string
        default_region: Default region for parsing
        
    Returns:
        True if valid, False otherwise
    """
    return normalize_phone(phone, default_region) is not None


# -----------------------------------------------------------------------------
# PII Masking
# -----------------------------------------------------------------------------

def mask_phone(phone: str) -> str:
    """
    Mask a phone number for logging (show only last 4 digits).
    
    Args:
        phone: Phone number to mask
        
    Returns:
        Masked phone number
        
    Examples:
        >>> mask_phone("+15551234567")
        '+1*****4567'
        >>> mask_phone("555-123-4567")
        '***-***-4567'
    """
    if not phone:
        return "***"
    
    # Extract digits
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) <= 4:
        return "****"
    
    # Show last 4 digits only
    last_four = digits[-4:]
    masked_prefix = '*' * (len(digits) - 4)
    
    # If original had +, keep it
    prefix = '+' if phone.startswith('+') else ''
    
    return f"{prefix}{masked_prefix}{last_four}"


def mask_email(email: str) -> str:
    """
    Mask an email address for logging.
    
    Args:
        email: Email to mask
        
    Returns:
        Masked email
        
    Examples:
        >>> mask_email("john.doe@example.com")
        'j***e@example.com'
    """
    if not email or '@' not in email:
        return "***@***"
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 2:
        masked_local = '*' * len(local)
    else:
        masked_local = f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}"
    
    return f"{masked_local}@{domain}"


def mask_name(name: str) -> str:
    """
    Mask a name for logging (show only first initial).
    
    Args:
        name: Name to mask
        
    Returns:
        Masked name
        
    Examples:
        >>> mask_name("John Doe")
        'J*** D***'
    """
    if not name:
        return "***"
    
    parts = name.split()
    masked_parts = []
    
    for part in parts:
        if len(part) <= 1:
            masked_parts.append('*')
        else:
            masked_parts.append(f"{part[0]}{'*' * (len(part) - 1)}")
    
    return ' '.join(masked_parts)


class PIIMaskingFilter(logging.Filter):
    """
    Logging filter that masks PII in log messages.
    
    Detects and masks:
    - Phone numbers (various formats)
    - Email addresses
    """
    
    # Regex patterns for PII
    PHONE_PATTERN = re.compile(
        r'(\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
    )
    EMAIL_PATTERN = re.compile(
        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    )
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Mask PII in the log record message."""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Mask phone numbers
            record.msg = self.PHONE_PATTERN.sub(
                lambda m: mask_phone(m.group(1)), record.msg
            )
            # Mask emails
            record.msg = self.EMAIL_PATTERN.sub(
                lambda m: mask_email(m.group(1)), record.msg
            )
        return True


# -----------------------------------------------------------------------------
# Logging Setup
# -----------------------------------------------------------------------------

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    mask_pii: bool = True,
) -> logging.Logger:
    """
    Set up a logger with rotating file handler and optional PII masking.
    
    Args:
        name: Logger name
        log_file: Path to log file (None for console only)
        level: Logging level
        max_bytes: Max size before rotation
        backup_count: Number of backup files to keep
        mask_pii: Whether to mask PII in logs
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # PII masking filter
    if mask_pii:
        pii_filter = PIIMaskingFilter()
        for handler in logger.handlers:
            handler.addFilter(pii_filter)
    
    return logger


# -----------------------------------------------------------------------------
# Input Sanitization
# -----------------------------------------------------------------------------

# Dangerous patterns to reject
DANGEROUS_PATTERNS = [
    re.compile(r'<script', re.IGNORECASE),
    re.compile(r'javascript:', re.IGNORECASE),
    re.compile(r'on\w+\s*=', re.IGNORECASE),  # onclick, onerror, etc.
    re.compile(r'eval\s*\(', re.IGNORECASE),
    re.compile(r'exec\s*\(', re.IGNORECASE),
]


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize a string input.
    
    - Strips whitespace
    - Truncates to max length
    - Removes null bytes
    - Escapes HTML special characters
    
    Args:
        value: Input string
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
        
    Raises:
        ValueError: If dangerous patterns detected
    """
    if not value:
        return ""
    
    # Strip and truncate
    value = value.strip()[:max_length]
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(value):
            raise ValueError(f"Dangerous pattern detected in input")
    
    # Escape HTML special characters
    value = (
        value
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#x27;')
    )
    
    return value


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and other attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    if not filename:
        return "unnamed"
    
    # Get just the filename, no path
    filename = os.path.basename(filename)
    
    # Remove any null bytes
    filename = filename.replace('\x00', '')
    
    # Replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext
    
    return filename or "unnamed"


# -----------------------------------------------------------------------------
# Standardized Error Responses
# -----------------------------------------------------------------------------

class APIError(Exception):
    """
    Standardized API error.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code
        error_code: Machine-readable error code
        details: Additional error details
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{status_code}"
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "error": True,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


def api_error(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    **details
) -> APIError:
    """
    Create a standardized API error.
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Optional error code
        **details: Additional details
        
    Returns:
        APIError instance
    """
    return APIError(message, status_code, error_code, details or None)


# -----------------------------------------------------------------------------
# Retry Decorator
# -----------------------------------------------------------------------------

def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential: bool = True,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for retrying a function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay between attempts (seconds)
        max_delay: Maximum delay between attempts
        exponential: Use exponential backoff
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        raise
                    
                    # Calculate delay
                    if exponential:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    else:
                        delay = base_delay
                    
                    logging.warning(
                        f"Attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


# -----------------------------------------------------------------------------
# File Validation
# -----------------------------------------------------------------------------

# Allowed MIME types for uploads
ALLOWED_AUDIO_MIMES = {
    'audio/wav', 'audio/x-wav', 'audio/wave',
    'audio/mpeg', 'audio/mp3',
    'audio/ogg', 'audio/vorbis',
    'audio/webm',
}

ALLOWED_CSV_MIMES = {
    'text/csv',
    'text/plain',
    'application/csv',
    'application/vnd.ms-excel',
}

# Max file sizes
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_CSV_SIZE = 10 * 1024 * 1024    # 10 MB


def validate_file_upload(
    filename: str,
    content_type: str,
    size: int,
    allowed_mimes: set,
    max_size: int,
) -> tuple[bool, Optional[str]]:
    """
    Validate a file upload.
    
    Args:
        filename: Original filename
        content_type: MIME type
        size: File size in bytes
        allowed_mimes: Set of allowed MIME types
        max_size: Maximum allowed size
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check MIME type
    if content_type not in allowed_mimes:
        return False, f"Invalid file type: {content_type}. Allowed: {', '.join(allowed_mimes)}"
    
    # Check size
    if size > max_size:
        return False, f"File too large: {size} bytes. Maximum: {max_size} bytes"
    
    # Check filename
    if not filename or filename.startswith('.'):
        return False, "Invalid filename"
    
    return True, None


def validate_audio_upload(filename: str, content_type: str, size: int) -> tuple[bool, Optional[str]]:
    """Validate an audio file upload."""
    return validate_file_upload(filename, content_type, size, ALLOWED_AUDIO_MIMES, MAX_AUDIO_SIZE)


def validate_csv_upload(filename: str, content_type: str, size: int) -> tuple[bool, Optional[str]]:
    """Validate a CSV file upload."""
    return validate_file_upload(filename, content_type, size, ALLOWED_CSV_MIMES, MAX_CSV_SIZE)


# -----------------------------------------------------------------------------
# Slack Notifications (24/7 alerts - works without VS Code)
# -----------------------------------------------------------------------------

import httpx

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#dentsignal-alerts")

async def send_slack_notification(
    message: str,
    channel: str = None,
    emoji: str = "🔔",
    title: str = None
) -> bool:
    """
    Send a Slack notification. Works 24/7 without VS Code.
    
    Args:
        message: The notification message
        channel: Slack channel (defaults to SLACK_CHANNEL env var)
        emoji: Emoji prefix for the message
        title: Optional bold title
        
    Returns:
        True if sent successfully, False otherwise
    """
    if not SLACK_BOT_TOKEN:
        logging.warning("SLACK_BOT_TOKEN not set, skipping notification")
        return False
    
    channel = channel or SLACK_CHANNEL
    
    # Format message
    text = f"{emoji} "
    if title:
        text += f"*{title}*\n"
    text += message
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "channel": channel,
                    "text": text,
                    "mrkdwn": True
                }
            )
            result = response.json()
            if not result.get("ok"):
                logging.error(f"Slack API error: {result.get('error')}")
                return False
            return True
    except Exception as e:
        logging.error(f"Failed to send Slack notification: {e}")
        return False


def send_slack_notification_sync(
    message: str,
    channel: str = None,
    emoji: str = "🔔",
    title: str = None
) -> bool:
    """Synchronous version of send_slack_notification."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, create task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    send_slack_notification(message, channel, emoji, title)
                )
                return future.result(timeout=10)
        else:
            return loop.run_until_complete(
                send_slack_notification(message, channel, emoji, title)
            )
    except Exception as e:
        logging.error(f"Sync Slack notification failed: {e}")
        return False


# Pre-built notification helpers
async def notify_new_signup(email: str, clinic_name: str = None):
    """Send notification when a new user signs up."""
    msg = f"New user signed up!\n• Email: `{email}`"
    if clinic_name:
        msg += f"\n• Clinic: {clinic_name}"
    msg += f"\n• Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    await send_slack_notification(msg, emoji="🎉", title="New Signup!")


async def notify_new_call(caller: str, duration: int, booked: bool):
    """Send notification when a call completes."""
    status = "✅ Appointment Booked" if booked else "📞 Call Completed"
    msg = f"• Caller: `{mask_pii(caller)}`\n• Duration: {duration}s\n• Result: {status}"
    await send_slack_notification(msg, emoji="📞", title="Call Completed")


async def notify_error(error: str, context: str = None):
    """Send notification when an error occurs."""
    msg = f"Error: `{error}`"
    if context:
        msg += f"\n• Context: {context}"
    await send_slack_notification(msg, emoji="🚨", title="Error Alert")


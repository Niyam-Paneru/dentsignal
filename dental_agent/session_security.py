"""
session_security.py - Session Security Helpers

Provides secure session management:
- Secure cookie attributes
- Session token generation
- CSRF protection
- Session fixation prevention

Usage:
    from session_security import generate_csrf_token, validate_session
    
    csrf_token = generate_csrf_token()
    is_valid = validate_session(session_token)
"""

import os
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass


# =============================================================================
# SESSION CONFIGURATION
# =============================================================================

SESSION_SECRET = os.getenv("SESSION_SECRET", os.getenv("JWT_SECRET", secrets.token_urlsafe(32)))
SESSION_DURATION_HOURS = int(os.getenv("SESSION_DURATION_HOURS", "24"))
CSRF_TOKEN_LENGTH = 32


# =============================================================================
# CSRF PROTECTION
# =============================================================================

def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)


def validate_csrf_token(token: str, expected_token: str) -> bool:
    """
    Validate a CSRF token using constant-time comparison.
    
    Args:
        token: The token provided by the client
        expected_token: The expected token stored server-side
        
    Returns:
        True if tokens match
    """
    if not token or not expected_token:
        return False
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(token, expected_token)


# =============================================================================
# SECURE SESSION TOKENS
# =============================================================================

def generate_session_token() -> str:
    """
    Generate a cryptographically secure session token.
    
    Returns:
        A URL-safe base64-encoded random token
    """
    return secrets.token_urlsafe(32)


def generate_session_id() -> str:
    """
    Generate a unique session ID.
    
    Returns:
        Hex-encoded random string
    """
    return secrets.token_hex(16)


def hash_session_token(token: str) -> str:
    """
    Hash a session token for storage.
    
    Args:
        token: The raw session token
        
    Returns:
        SHA-256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


# =============================================================================
# SESSION DATA
# =============================================================================

@dataclass
class SessionData:
    """Session data structure."""
    session_id: str
    user_id: str
    user_email: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    csrf_token: Optional[str] = None
    is_admin: bool = False
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "csrf_token": self.csrf_token,
            "is_admin": self.is_admin,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            user_email=data["user_email"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            csrf_token=data.get("csrf_token"),
            is_admin=data.get("is_admin", False),
        )


def create_session(
    user_id: str,
    user_email: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    is_admin: bool = False
) -> SessionData:
    """
    Create a new secure session.
    
    Args:
        user_id: User identifier
        user_email: User email address
        ip_address: Client IP address
        user_agent: Client user agent
        is_admin: Whether user is admin
        
    Returns:
        New SessionData object
    """
    now = datetime.utcnow()
    return SessionData(
        session_id=generate_session_id(),
        user_id=user_id,
        user_email=user_email,
        created_at=now,
        expires_at=now + timedelta(hours=SESSION_DURATION_HOURS),
        ip_address=ip_address,
        user_agent=user_agent,
        csrf_token=generate_csrf_token(),
        is_admin=is_admin,
    )


def validate_session(
    session: SessionData,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> tuple[bool, str]:
    """
    Validate a session.
    
    Args:
        session: Session data to validate
        ip_address: Current IP address (for binding check)
        user_agent: Current user agent (for binding check)
        
    Returns:
        Tuple of (is_valid, reason)
    """
    if session.is_expired():
        return False, "Session expired"
    
    # Optional: Validate IP address hasn't changed significantly
    # (You may want to skip this for mobile users)
    if session.ip_address and ip_address:
        # Simple check - could be more sophisticated
        if session.ip_address != ip_address:
            # Log suspicious activity but don't necessarily invalidate
            pass
    
    return True, "Valid"


# =============================================================================
# COOKIE SECURITY
# =============================================================================

def get_secure_cookie_settings() -> Dict[str, Any]:
    """
    Get secure cookie settings for production.
    
    Returns:
        Dictionary of cookie settings
    """
    is_production = os.getenv("ENVIRONMENT") == "production"
    
    return {
        "httponly": True,  # Prevent JavaScript access
        "secure": is_production,  # Only send over HTTPS in production
        "samesite": "lax",  # CSRF protection
        "max_age": SESSION_DURATION_HOURS * 3600,  # Convert to seconds
    }


def validate_cookie_name(name: str) -> bool:
    """
    Validate cookie name doesn't contain dangerous characters.
    
    Args:
        name: Cookie name to validate
        
    Returns:
        True if valid
    """
    # Cookie names should be alphanumeric with limited special chars
    import re
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))


# =============================================================================
# SESSION FIXATION PREVENTION
# =============================================================================

def regenerate_session_id(old_session: SessionData) -> SessionData:
    """
    Regenerate session ID after authentication.
    
    This prevents session fixation attacks by changing the session ID
    after login.
    
    Args:
        old_session: The old session data
        
    Returns:
        New session with same data but new ID
    """
    new_session = SessionData(
        session_id=generate_session_id(),
        user_id=old_session.user_id,
        user_email=old_session.user_email,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=SESSION_DURATION_HOURS),
        ip_address=old_session.ip_address,
        user_agent=old_session.user_agent,
        csrf_token=generate_csrf_token(),  # New CSRF token too
        is_admin=old_session.is_admin,
    )
    return new_session


# =============================================================================
# RATE LIMITING FOR SESSIONS
# =============================================================================

class SessionRateLimiter:
    """Rate limiter for session operations to prevent brute force."""
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: Dict[str, list] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if operation is allowed for identifier."""
        from time import time
        
        now = time()
        window_start = now - self.window_seconds
        
        # Get attempts for this identifier
        attempts = self._attempts.get(identifier, [])
        
        # Filter to recent attempts
        recent_attempts = [t for t in attempts if t > window_start]
        
        # Update stored attempts
        self._attempts[identifier] = recent_attempts
        
        return len(recent_attempts) < self.max_attempts
    
    def record_attempt(self, identifier: str):
        """Record an attempt for identifier."""
        from time import time
        
        if identifier not in self._attempts:
            self._attempts[identifier] = []
        
        self._attempts[identifier].append(time())


# Global session rate limiter
session_rate_limiter = SessionRateLimiter()

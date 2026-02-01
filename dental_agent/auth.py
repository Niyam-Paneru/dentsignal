"""
auth.py - Authentication utilities for the Dental Agent API.

This module is separated from api_main.py to avoid circular imports.
Route modules can import auth functions from here instead of from api_main.
"""

from __future__ import annotations

import os
import re
import logging
from typing import Optional

import jwt
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET")


def _validate_jwt_secret(secret: Optional[str]) -> None:
    """
    Validate JWT secret meets security requirements.
    
    Requirements:
    - Minimum 32 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - Not a commonly used weak secret
    """
    if not secret:
        raise ValueError(
            "JWT_SECRET environment variable is required. "
            "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    
    # Check minimum length
    if len(secret) < 32:
        raise ValueError(
            f"JWT_SECRET must be at least 32 characters (current: {len(secret)}). "
            "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    
    # Check for common weak secrets
    weak_secrets = [
        "changeme", "changeme-insecure-secret", "password", "secret",
        "admin", "123456", "qwerty", "letmein", "welcome"
    ]
    if secret.lower() in weak_secrets or any(ws in secret.lower() for ws in weak_secrets):
        raise ValueError(
            "JWT_SECRET appears to be a commonly used weak secret. "
            "Generate a secure one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    
    # Check complexity requirements
    has_upper = bool(re.search(r'[A-Z]', secret))
    has_lower = bool(re.search(r'[a-z]', secret))
    has_digit = bool(re.search(r'\d', secret))
    has_special = bool(re.search(r'[!@#$%^&*()\-_=+{}\[\]:;|\'",.<>/?`~\\]', secret))
    
    if not (has_upper and has_lower and has_digit and has_special):
        missing = []
        if not has_upper:
            missing.append("uppercase letter")
        if not has_lower:
            missing.append("lowercase letter")
        if not has_digit:
            missing.append("digit")
        if not has_special:
            missing.append("special character")
        raise ValueError(
            f"JWT_SECRET must contain at least one: {', '.join(missing)}. "
            "Generate a secure one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )


# Validate JWT secret on module load
_validate_jwt_secret(JWT_SECRET)
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 1


def get_current_user(authorization: str = None) -> Optional[dict]:
    """
    Decode JWT token from Authorization header.
    For demo: returns decoded payload or raises 401.
    """
    if not authorization:
        return None
    
    try:
        # Expect "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")


def require_auth(authorization: str = None) -> dict:
    """
    Dependency to require valid JWT authentication.
    Raises 401 if no valid token provided.
    """
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

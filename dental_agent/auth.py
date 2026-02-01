"""
auth.py - Authentication utilities for the Dental Agent API.

This module is separated from api_main.py to avoid circular imports.
Route modules can import auth functions from here instead of from api_main.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

import jwt
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET or JWT_SECRET == "changeme" or JWT_SECRET == "changeme-insecure-secret":
    raise ValueError(
        "JWT_SECRET environment variable is required and must be a secure random string. "
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )
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

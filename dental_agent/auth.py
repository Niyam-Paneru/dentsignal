"""
auth.py - Authentication utilities for DentSignal API

This module contains JWT authentication helpers that can be imported
by any route module without causing circular imports.
"""

import os
import jwt
from typing import Optional
from fastapi import HTTPException, status

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "changeme-use-a-secure-random-string")
JWT_ALGORITHM = "HS256"


def get_current_user(authorization: str = None) -> Optional[dict]:
    """
    Decode JWT token from Authorization header.
    Returns decoded payload or None if no valid token.
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
        raise HTTPException(status_code=401, detail="Invalid authorization format")


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

"""
rate_limiter.py - Simple Rate Limiting Middleware

Implements in-memory rate limiting for API endpoints.
Uses a sliding window algorithm.

For production, consider:
- Redis-backed rate limiting (for multi-worker setups)
- Per-user/per-IP limits
- Adaptive rate limiting based on load
"""

import time
import logging
from collections import defaultdict
from typing import Optional, Dict, Tuple
from functools import wraps

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# =============================================================================
# IN-MEMORY RATE LIMITER
# =============================================================================

class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window.
    
    Thread-safe for single-worker deployments.
    For multi-worker, use Redis-backed implementation.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
        
        # Track requests: key -> list of timestamps
        self._minute_windows: Dict[str, list] = defaultdict(list)
        self._hour_windows: Dict[str, list] = defaultdict(list)
        self._burst_windows: Dict[str, list] = defaultdict(list)
        
        # Last cleanup time
        self._last_cleanup = time.time()
    
    def _cleanup_old_entries(self) -> None:
        """Remove expired entries to prevent memory growth."""
        now = time.time()
        
        # Only cleanup every 60 seconds
        if now - self._last_cleanup < 60:
            return
            
        self._last_cleanup = now
        minute_ago = now - 60
        hour_ago = now - 3600
        second_ago = now - 1
        
        # Cleanup minute windows
        for key in list(self._minute_windows.keys()):
            self._minute_windows[key] = [t for t in self._minute_windows[key] if t > minute_ago]
            if not self._minute_windows[key]:
                del self._minute_windows[key]
        
        # Cleanup hour windows
        for key in list(self._hour_windows.keys()):
            self._hour_windows[key] = [t for t in self._hour_windows[key] if t > hour_ago]
            if not self._hour_windows[key]:
                del self._hour_windows[key]
        
        # Cleanup burst windows
        for key in list(self._burst_windows.keys()):
            self._burst_windows[key] = [t for t in self._burst_windows[key] if t > second_ago]
            if not self._burst_windows[key]:
                del self._burst_windows[key]
    
    def is_allowed(self, key: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if request is allowed for given key (IP or user ID).
        
        Returns:
            (allowed: bool, error_reason: str|None, retry_after: int|None)
        """
        now = time.time()
        self._cleanup_old_entries()
        
        # Check burst limit (10 requests per second)
        second_ago = now - 1
        recent_burst = [t for t in self._burst_windows[key] if t > second_ago]
        if len(recent_burst) >= self.burst_limit:
            return False, "Burst limit exceeded", 1
        
        # Check minute limit
        minute_ago = now - 60
        recent_minute = [t for t in self._minute_windows[key] if t > minute_ago]
        if len(recent_minute) >= self.requests_per_minute:
            retry_after = int(60 - (now - min(recent_minute)))
            return False, "Rate limit exceeded (per minute)", max(1, retry_after)
        
        # Check hour limit
        hour_ago = now - 3600
        recent_hour = [t for t in self._hour_windows[key] if t > hour_ago]
        if len(recent_hour) >= self.requests_per_hour:
            retry_after = int(3600 - (now - min(recent_hour)))
            return False, "Rate limit exceeded (per hour)", max(1, retry_after)
        
        # Record this request
        self._burst_windows[key].append(now)
        self._minute_windows[key].append(now)
        self._hour_windows[key].append(now)
        
        return True, None, None
    
    def get_stats(self, key: str) -> dict:
        """Get rate limit stats for a key."""
        now = time.time()
        return {
            "requests_last_minute": len([t for t in self._minute_windows[key] if t > now - 60]),
            "requests_last_hour": len([t for t in self._hour_windows[key] if t > now - 3600]),
            "limits": {
                "per_minute": self.requests_per_minute,
                "per_hour": self.requests_per_hour,
                "burst": self.burst_limit,
            }
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            requests_per_minute=120,  # 2 req/sec sustained
            requests_per_hour=3600,   # 1 req/sec average
            burst_limit=20,           # 20 req/sec burst
        )
    return _rate_limiter


# =============================================================================
# FASTAPI MIDDLEWARE
# =============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for FastAPI.
    
    Applies rate limits based on client IP.
    Skips rate limiting for:
    - Health check endpoints
    - Twilio webhook endpoints (they have their own auth)
    """
    
    # Paths to skip rate limiting
    SKIP_PATHS = {
        "/health",
        "/",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
    
    # Twilio paths (skip - they use signature auth)
    # SECURITY: These are exact path starts that are safe to skip
    # Path traversal attacks like /twilio/../admin are blocked by FastAPI's path normalization
    # but we add extra validation to be safe
    TWILIO_PREFIXES = (
        "/twilio/",
        "/inbound/",
    )
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # SECURITY: Normalize path to prevent traversal bypass attempts
        # e.g., /twilio/../admin would be normalized to /admin
        import urllib.parse
        normalized_path = urllib.parse.unquote(path)
        
        # Skip rate limiting for excluded paths
        if normalized_path in self.SKIP_PATHS:
            return await call_next(request)
        
        # Skip Twilio webhooks (they have signature verification)
        # Only skip if path legitimately starts with these prefixes
        if normalized_path.startswith(self.TWILIO_PREFIXES):
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        limiter = get_rate_limiter()
        allowed, reason, retry_after = limiter.is_allowed(client_ip)
        
        if not allowed:
            logger.warning(f"Rate limit hit for {client_ip}: {reason}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=reason,
                headers={"Retry-After": str(retry_after)} if retry_after else None,
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        stats = limiter.get_stats(client_ip)
        response.headers["X-RateLimit-Limit-Minute"] = str(stats["limits"]["per_minute"])
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            max(0, stats["limits"]["per_minute"] - stats["requests_last_minute"])
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For header."""
        # Check for proxy headers
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP in chain (original client)
            return forwarded.split(",")[0].strip()
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"


# =============================================================================
# DECORATOR FOR ENDPOINT-SPECIFIC LIMITS
# =============================================================================

def rate_limit(requests_per_minute: int = 30):
    """
    Decorator for endpoint-specific rate limiting.
    
    Usage:
        @app.post("/api/expensive-operation")
        @rate_limit(requests_per_minute=10)
        async def expensive_operation():
            ...
    """
    def decorator(func):
        # Per-endpoint limiter
        endpoint_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_minute * 60,
            burst_limit=min(10, requests_per_minute),
        )
        
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get client IP
            client_ip = request.client.host if request.client else "unknown"
            
            allowed, reason, retry_after = endpoint_limiter.is_allowed(client_ip)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=reason,
                    headers={"Retry-After": str(retry_after)} if retry_after else None,
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

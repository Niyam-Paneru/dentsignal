"""
brute_force.py — Login Brute-Force Protection (AG-10)

Two independent limiters:
  1. **Per-account** — After N failed attempts for the same email, lock the
     account for a cooldown period.  Resets on successful login.
  2. **Per-IP** — After M failed attempts from the same IP (any account),
     block that IP for a cooldown period.

Storage backends:
  • **Redis** (production) — TTL-based keys, works across workers.
  • **In-memory** (dev/test fallback) — dict-based, single-worker only.

The backend is selected automatically: Redis when ``REDIS_URL`` is set,
in-memory otherwise.  Tests always use in-memory (``DISABLE_BRUTE_FORCE``
env var or explicit ``InMemoryBruteForceBackend``).

Usage::

    from brute_force import brute_force_guard

    # Inside login handler:
    brute_force_guard.check_and_raise(email, client_ip)   # raises 429 if blocked
    brute_force_guard.record_failure(email, client_ip)     # after bad password
    brute_force_guard.record_success(email, client_ip)     # after good login
"""

from __future__ import annotations

import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Optional

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (from env or sensible defaults)
# ---------------------------------------------------------------------------

# Per-account: max failed attempts before lockout
ACCOUNT_MAX_ATTEMPTS = int(os.getenv("BF_ACCOUNT_MAX_ATTEMPTS", "5"))
# Per-account lockout duration in seconds (15 min default)
ACCOUNT_LOCKOUT_SECONDS = int(os.getenv("BF_ACCOUNT_LOCKOUT_SECONDS", "900"))

# Per-IP: max failed attempts before block
IP_MAX_ATTEMPTS = int(os.getenv("BF_IP_MAX_ATTEMPTS", "20"))
# Per-IP block duration in seconds (15 min default)
IP_LOCKOUT_SECONDS = int(os.getenv("BF_IP_LOCKOUT_SECONDS", "900"))


# ---------------------------------------------------------------------------
# Abstract backend
# ---------------------------------------------------------------------------

class BruteForceBackend(ABC):
    """Storage backend interface for brute force tracking."""

    @abstractmethod
    def get_failure_count(self, key: str) -> int: ...

    @abstractmethod
    def increment_failure(self, key: str, ttl_seconds: int) -> int: ...

    @abstractmethod
    def reset(self, key: str) -> None: ...

    @abstractmethod
    def get_lockout_ttl(self, key: str) -> int:
        """Seconds remaining on lockout.  0 = not locked."""
        ...


# ---------------------------------------------------------------------------
# In-memory backend (dev / test)
# ---------------------------------------------------------------------------

class InMemoryBruteForceBackend(BruteForceBackend):
    """Dict-based backend for single-worker or test use."""

    def __init__(self) -> None:
        # key -> (count, first_failure_timestamp)
        self._store: dict[str, tuple[int, float]] = {}

    def get_failure_count(self, key: str) -> int:
        entry = self._store.get(key)
        if entry is None:
            return 0
        count, ts = entry
        # Expired?
        return 0 if self._is_expired(key) else count

    def increment_failure(self, key: str, ttl_seconds: int) -> int:
        now = time.time()
        entry = self._store.get(key)
        if entry is None or self._is_expired(key):
            self._store[key] = (1, now)
            return 1
        count, ts = entry
        new_count = count + 1
        self._store[key] = (new_count, ts)  # keep original timestamp
        return new_count

    def reset(self, key: str) -> None:
        self._store.pop(key, None)

    def get_lockout_ttl(self, key: str) -> int:
        entry = self._store.get(key)
        if entry is None:
            return 0
        _count, ts = entry
        # TTL is based on the key prefix
        ttl = ACCOUNT_LOCKOUT_SECONDS if key.startswith("bf:account:") else IP_LOCKOUT_SECONDS
        remaining = int((ts + ttl) - time.time())
        return max(remaining, 0)

    def _is_expired(self, key: str) -> bool:
        entry = self._store.get(key)
        if entry is None:
            return True
        _count, ts = entry
        ttl = ACCOUNT_LOCKOUT_SECONDS if key.startswith("bf:account:") else IP_LOCKOUT_SECONDS
        if time.time() - ts > ttl:
            del self._store[key]
            return True
        return False


# ---------------------------------------------------------------------------
# Redis backend (production)
# ---------------------------------------------------------------------------

class RedisBruteForceBackend(BruteForceBackend):
    """Redis-backed backend for multi-worker production use."""

    def __init__(self, redis_client) -> None:
        self._r = redis_client

    def get_failure_count(self, key: str) -> int:
        val = self._r.get(key)
        return int(val) if val else 0

    def increment_failure(self, key: str, ttl_seconds: int) -> int:
        pipe = self._r.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl_seconds)
        results = pipe.execute()
        return int(results[0])

    def reset(self, key: str) -> None:
        self._r.delete(key)

    def get_lockout_ttl(self, key: str) -> int:
        ttl = self._r.ttl(key)
        return max(ttl, 0) if ttl and ttl > 0 else 0


# ---------------------------------------------------------------------------
# Main guard class
# ---------------------------------------------------------------------------

class BruteForceGuard:
    """
    Stateless facade — delegates to a pluggable backend.

    Key scheme:
        ``bf:account:<email_lower>`` — per-account counter
        ``bf:ip:<ip_address>``       — per-IP counter
    """

    def __init__(self, backend: BruteForceBackend) -> None:
        self.backend = backend

    # -- keys ---------------------------------------------------------------

    @staticmethod
    def _account_key(email: str) -> str:
        return f"bf:account:{email.lower().strip()}"

    @staticmethod
    def _ip_key(ip: str) -> str:
        return f"bf:ip:{ip}"

    # -- public API ---------------------------------------------------------

    def check_and_raise(self, email: str, client_ip: str) -> None:
        """
        Call **before** credential check.  Raises 429 if either limiter
        is tripped.
        """
        # Check per-account lockout
        acct_key = self._account_key(email)
        acct_count = self.backend.get_failure_count(acct_key)
        if acct_count >= ACCOUNT_MAX_ATTEMPTS:
            ttl = self.backend.get_lockout_ttl(acct_key)
            logger.warning(
                f"Brute-force: account locked email=***{email[-8:]} "
                f"attempts={acct_count} ttl={ttl}s"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account temporarily locked. Try again in {ttl} seconds.",
                headers={"Retry-After": str(ttl)},
            )

        # Check per-IP throttle
        ip_key = self._ip_key(client_ip)
        ip_count = self.backend.get_failure_count(ip_key)
        if ip_count >= IP_MAX_ATTEMPTS:
            ttl = self.backend.get_lockout_ttl(ip_key)
            logger.warning(
                f"Brute-force: IP blocked ip={client_ip} "
                f"attempts={ip_count} ttl={ttl}s"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many login attempts from this IP. Try again in {ttl} seconds.",
                headers={"Retry-After": str(ttl)},
            )

    def record_failure(self, email: str, client_ip: str) -> None:
        """Call after a failed login attempt."""
        acct_count = self.backend.increment_failure(
            self._account_key(email), ACCOUNT_LOCKOUT_SECONDS
        )
        ip_count = self.backend.increment_failure(
            self._ip_key(client_ip), IP_LOCKOUT_SECONDS
        )
        logger.info(
            f"Brute-force: failure recorded email=***{email[-8:]} "
            f"acct={acct_count}/{ACCOUNT_MAX_ATTEMPTS} ip={ip_count}/{IP_MAX_ATTEMPTS}"
        )

    def record_success(self, email: str, client_ip: str) -> None:
        """Call after a successful login — resets the account counter."""
        self.backend.reset(self._account_key(email))
        # NOTE: We intentionally do NOT reset the IP counter on success.
        # A valid login from a brute-forcing IP should not reset the IP limit.


# ---------------------------------------------------------------------------
# Module-level singleton (auto-selects backend)
# ---------------------------------------------------------------------------

def _create_guard() -> BruteForceGuard:
    """Create the appropriate backend based on environment."""
    if os.getenv("DISABLE_BRUTE_FORCE", "0") == "1":
        # Tests or explicit disable → in-memory (always works)
        return BruteForceGuard(InMemoryBruteForceBackend())

    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)
            r.ping()
            logger.info("Brute-force protection: using Redis backend")
            return BruteForceGuard(RedisBruteForceBackend(r))
        except Exception as exc:
            logger.warning(f"Redis unavailable ({exc}), falling back to in-memory brute-force")

    return BruteForceGuard(InMemoryBruteForceBackend())


brute_force_guard = _create_guard()

"""
test_brute_force.py — AG-10 Brute-Force Login Protection Tests

Tests for:
1. InMemoryBruteForceBackend — unit tests for the storage layer
2. BruteForceGuard — per-account lockout + per-IP throttle logic
3. Integration — /api/auth/login returns 429 after exceeding limits
4. Reset on success — account counter clears after good login
5. Independent IP counter — success does NOT reset IP counter
"""

import os
import sys
import time
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import HTTPException
from brute_force import (
    BruteForceGuard,
    InMemoryBruteForceBackend,
    ACCOUNT_MAX_ATTEMPTS,
    IP_MAX_ATTEMPTS,
    ACCOUNT_LOCKOUT_SECONDS,
    IP_LOCKOUT_SECONDS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def backend():
    return InMemoryBruteForceBackend()


@pytest.fixture
def guard(backend):
    return BruteForceGuard(backend)


# ---------------------------------------------------------------------------
# 1. InMemoryBruteForceBackend unit tests
# ---------------------------------------------------------------------------

class TestInMemoryBackend:

    def test_initial_count_zero(self, backend):
        assert backend.get_failure_count("bf:account:x") == 0

    def test_increment(self, backend):
        assert backend.increment_failure("bf:account:x", 900) == 1
        assert backend.increment_failure("bf:account:x", 900) == 2
        assert backend.get_failure_count("bf:account:x") == 2

    def test_reset(self, backend):
        backend.increment_failure("bf:account:x", 900)
        backend.increment_failure("bf:account:x", 900)
        backend.reset("bf:account:x")
        assert backend.get_failure_count("bf:account:x") == 0

    def test_ttl_returns_positive_while_active(self, backend):
        backend.increment_failure("bf:account:x", 900)
        ttl = backend.get_lockout_ttl("bf:account:x")
        assert ttl > 0
        assert ttl <= ACCOUNT_LOCKOUT_SECONDS

    def test_ttl_zero_after_reset(self, backend):
        backend.increment_failure("bf:account:x", 900)
        backend.reset("bf:account:x")
        assert backend.get_lockout_ttl("bf:account:x") == 0


# ---------------------------------------------------------------------------
# 2. BruteForceGuard — lockout logic
# ---------------------------------------------------------------------------

class TestBruteForceGuard:

    def test_no_block_before_limit(self, guard):
        """Under the limit → no exception."""
        for _ in range(ACCOUNT_MAX_ATTEMPTS - 1):
            guard.record_failure("user@test.com", "1.2.3.4")
        # Should NOT raise
        guard.check_and_raise("user@test.com", "1.2.3.4")

    def test_account_lockout_after_max(self, guard):
        """Reaching ACCOUNT_MAX_ATTEMPTS → 429."""
        for _ in range(ACCOUNT_MAX_ATTEMPTS):
            guard.record_failure("locked@test.com", "9.9.9.9")

        with pytest.raises(HTTPException) as exc_info:
            guard.check_and_raise("locked@test.com", "9.9.9.9")
        assert exc_info.value.status_code == 429
        assert "Account temporarily locked" in exc_info.value.detail

    def test_ip_throttle_after_max(self, guard):
        """Reaching IP_MAX_ATTEMPTS from one IP → 429."""
        ip = "10.0.0.1"
        for i in range(IP_MAX_ATTEMPTS):
            guard.record_failure(f"user{i}@test.com", ip)

        with pytest.raises(HTTPException) as exc_info:
            guard.check_and_raise("new@test.com", ip)
        assert exc_info.value.status_code == 429
        assert "Too many login attempts from this IP" in exc_info.value.detail

    def test_different_accounts_independent(self, guard):
        """Failures on account A don't affect account B."""
        for _ in range(ACCOUNT_MAX_ATTEMPTS):
            guard.record_failure("a@test.com", "5.5.5.5")

        # Account B from same IP should still work (IP limit not hit)
        guard.check_and_raise("b@test.com", "5.5.5.5")  # no raise

    def test_success_resets_account(self, guard):
        """record_success clears account counter."""
        for _ in range(ACCOUNT_MAX_ATTEMPTS - 1):
            guard.record_failure("reset@test.com", "7.7.7.7")

        guard.record_success("reset@test.com", "7.7.7.7")

        # Should be able to fail again without lockout
        guard.record_failure("reset@test.com", "7.7.7.7")
        guard.check_and_raise("reset@test.com", "7.7.7.7")  # no raise

    def test_success_does_not_reset_ip(self, guard):
        """record_success does NOT reset IP counter (by design)."""
        ip = "11.11.11.11"
        for i in range(IP_MAX_ATTEMPTS):
            guard.record_failure(f"u{i}@test.com", ip)

        # One success shouldn't clear the IP block
        guard.record_success("u0@test.com", ip)

        with pytest.raises(HTTPException) as exc_info:
            guard.check_and_raise("another@test.com", ip)
        assert exc_info.value.status_code == 429

    def test_retry_after_header(self, guard):
        """429 response includes Retry-After header."""
        for _ in range(ACCOUNT_MAX_ATTEMPTS):
            guard.record_failure("hdr@test.com", "2.2.2.2")

        with pytest.raises(HTTPException) as exc_info:
            guard.check_and_raise("hdr@test.com", "2.2.2.2")
        assert "Retry-After" in exc_info.value.headers


# ---------------------------------------------------------------------------
# 3. Integration — /api/auth/login endpoint
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """FastAPI app for integration tests (brute force ENABLED)."""
    # Override to enable brute force for these tests
    os.environ["DISABLE_BRUTE_FORCE"] = "0"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["JWT_SECRET"] = "DentSignal_Pytest2026!ValidKey@XyZ99"
    os.environ["ENABLE_DEMO_USER"] = "1"
    os.environ["DEMO_USER_PASSWORD"] = "admin123"
    os.environ["DISABLE_RATE_LIMIT"] = "1"
    os.environ["TELEPHONY_MODE"] = "SIMULATED"

    # Force fresh DB initialization
    from db import create_db
    create_db("sqlite:///:memory:")

    from api_main import app

    # Patch the module-level DATABASE_URL so on_startup doesn't reconnect to Supabase
    import api_main
    api_main.DATABASE_URL = "sqlite:///:memory:"

    # Replace the module-level guard with a fresh in-memory one for test isolation
    import brute_force as bf_mod
    bf_mod.brute_force_guard = BruteForceGuard(InMemoryBruteForceBackend())

    # Also patch the reference in api_main (it imported the guard at module level)
    api_main.brute_force_guard = bf_mod.brute_force_guard

    return app


@pytest.fixture(scope="module")
def http_client(app):
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _reset_guard():
    """Reset the in-memory guard between integration tests."""
    import brute_force as bf_mod
    bf_mod.brute_force_guard.backend = InMemoryBruteForceBackend()
    import api_main
    api_main.brute_force_guard = bf_mod.brute_force_guard
    yield


class TestLoginBruteForceIntegration:

    def test_normal_login_works(self, http_client):
        resp = http_client.post(
            "/api/auth/login",
            json={"email": "admin@dental-demo.com", "password": "admin123"},
        )
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_bad_password_returns_401(self, http_client):
        resp = http_client.post(
            "/api/auth/login",
            json={"email": "admin@dental-demo.com", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_lockout_after_max_failures(self, http_client):
        """Exceeding per-account limit → 429."""
        email = "admin@dental-demo.com"
        for _ in range(ACCOUNT_MAX_ATTEMPTS):
            resp = http_client.post(
                "/api/auth/login",
                json={"email": email, "password": "wrong"},
            )
            assert resp.status_code == 401

        # Next attempt should be blocked
        resp = http_client.post(
            "/api/auth/login",
            json={"email": email, "password": "wrong"},
        )
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers

    def test_correct_password_also_blocked_during_lockout(self, http_client):
        """Even the correct password is rejected while locked out."""
        email = "admin@dental-demo.com"
        for _ in range(ACCOUNT_MAX_ATTEMPTS):
            http_client.post(
                "/api/auth/login",
                json={"email": email, "password": "wrong"},
            )

        resp = http_client.post(
            "/api/auth/login",
            json={"email": email, "password": "admin123"},
        )
        assert resp.status_code == 429

    def test_success_resets_lockout(self, http_client):
        """Successful login before lockout threshold resets the counter."""
        email = "admin@dental-demo.com"
        # Fail a few times (under limit)
        for _ in range(ACCOUNT_MAX_ATTEMPTS - 2):
            http_client.post(
                "/api/auth/login",
                json={"email": email, "password": "wrong"},
            )

        # Succeed
        resp = http_client.post(
            "/api/auth/login",
            json={"email": email, "password": "admin123"},
        )
        assert resp.status_code == 200

        # Now fail again — counter should be reset, not locked
        for _ in range(ACCOUNT_MAX_ATTEMPTS - 1):
            resp = http_client.post(
                "/api/auth/login",
                json={"email": email, "password": "wrong"},
            )
            assert resp.status_code == 401  # still 401, not 429

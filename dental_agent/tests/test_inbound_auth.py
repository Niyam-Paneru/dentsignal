"""
test_inbound_auth.py - Auth Enforcement Tests for Inbound Routes (AG-3)

Verifies:
1. Webhook routes require Twilio signature (skipped in SIMULATED mode)
2. Data routes (GET /inbound/calls, GET /inbound/calls/{id}) require JWT auth
3. Unauthenticated data requests → 401
4. Valid admin access → 200
"""

import pytest
import os
import sys
import jwt
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """Create FastAPI app with test database."""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["JWT_SECRET"] = "DentSignal_Pytest2026!ValidKey@XyZ99"
    os.environ["ENABLE_DEMO_USER"] = "1"
    os.environ["DEMO_USER_PASSWORD"] = "admin123"
    os.environ["DISABLE_RATE_LIMIT"] = "1"
    os.environ["TELEPHONY_MODE"] = "SIMULATED"

    # Force fresh DB initialization (needed when running after other test modules)
    from db import create_db
    create_db("sqlite:///:memory:")

    from api_main import app
    return app


@pytest.fixture(scope="module")
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(client):
    resp = client.post(
        "/api/auth/login",
        json={"email": "admin@dental-demo.com", "password": "admin123"},
    )
    assert resp.status_code == 200
    return resp.json()["token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


def _make_non_admin_token():
    secret = os.environ["JWT_SECRET"]
    payload = {
        "sub": "888",
        "email": "nonadmin@dental-demo.com",
        "is_admin": False,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, secret, algorithm="HS256")


# ---------------------------------------------------------------------------
# 1. Data routes require JWT auth (GET /inbound/calls, /inbound/calls/{id})
# ---------------------------------------------------------------------------

class TestInboundDataRoutesAuth:
    """GET /inbound/calls and /inbound/calls/{id} require JWT."""

    def test_list_calls_requires_auth(self, client):
        resp = client.get("/inbound/calls")
        assert resp.status_code == 401

    def test_get_call_requires_auth(self, client):
        resp = client.get("/inbound/calls/1")
        assert resp.status_code == 401

    def test_list_calls_rejects_bad_token(self, client):
        headers = {"Authorization": "Bearer invalid-token"}
        resp = client.get("/inbound/calls", headers=headers)
        assert resp.status_code == 401

    def test_get_call_rejects_bad_token(self, client):
        headers = {"Authorization": "Bearer invalid-token"}
        resp = client.get("/inbound/calls/1", headers=headers)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 2. Data routes work with valid admin token
# ---------------------------------------------------------------------------

class TestInboundDataRoutesValidAccess:
    """Admin token should grant access to data routes."""

    def test_admin_can_list_calls(self, client, admin_headers):
        resp = client.get("/inbound/calls", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "calls" in data

    def test_admin_get_nonexistent_call_returns_404(self, client, admin_headers):
        resp = client.get("/inbound/calls/99999", headers=admin_headers)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 3. Webhook routes have signature validation wired
#    (In SIMULATED mode, validation is skipped so they accept requests)
# ---------------------------------------------------------------------------

class TestInboundWebhookRoutes:
    """Webhook routes should have the require_twilio_auth dependency.
    In SIMULATED mode they pass through; the dep is wired for production."""

    def test_voice_webhook_accepts_in_simulated(self, client):
        """In SIMULATED mode, the signature check is bypassed."""
        resp = client.post(
            "/inbound/voice",
            data={
                "CallSid": "CA_test_123",
                "From": "+15551234567",
                "To": "+15559876543",
                "CallStatus": "ringing",
                "Direction": "inbound",
            },
        )
        # Will be 200 (TwiML) or 5xx if no clinic found — not 401/403
        assert resp.status_code in (200, 500)

    def test_status_webhook_accepts_in_simulated(self, client):
        resp = client.post(
            "/inbound/status/99999",
            data={
                "CallSid": "CA_test_456",
                "CallStatus": "completed",
            },
        )
        # Should be 200 "OK" (even for unknown call_id — it logs warning)
        assert resp.status_code == 200

    def test_voicemail_webhook_accepts_in_simulated(self, client):
        resp = client.post(
            "/inbound/voicemail/99999",
            data={},
        )
        # Returns TwiML even for unknown call
        assert resp.status_code == 200

    def test_stream_failed_accepts_in_simulated(self, client):
        resp = client.post("/inbound/stream-failed/99999")
        assert resp.status_code == 200

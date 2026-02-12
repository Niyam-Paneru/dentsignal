"""
test_auth_enforcement.py - Auth Enforcement Tests (AG-2)

Verifies that all 5 critical routes reject unauthenticated requests (401)
and that cross-tenant access is blocked (403).

Routes under test:
  1. POST /api/clients/{client_id}/leads
  2. POST /api/clients/{client_id}/uploads
  3. POST /api/calls/{call_id}/status
  4. GET  /api/clients/{client_id}/batches/{batch_id}/calls
  5. POST /api/twilio/webhook
"""

import pytest
import os
import sys
import jwt
from datetime import datetime, timedelta, timezone

# Add parent directory to path
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
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(client):
    """Get a valid admin JWT token."""
    resp = client.post(
        "/api/auth/login",
        json={"email": "admin@dental-demo.com", "password": "admin123"},
    )
    assert resp.status_code == 200
    return resp.json()["token"]


@pytest.fixture
def admin_headers(admin_token):
    """Authorization header for the admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


def _make_expired_token():
    """Create a JWT that expired 1 hour ago."""
    secret = os.environ["JWT_SECRET"]
    payload = {
        "sub": "999",
        "email": "expired@dental-demo.com",
        "is_admin": False,
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "type": "access",
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def _make_non_admin_token(email="nonadmin@dental-demo.com"):
    """Create a JWT for a non-admin user (not tied to any client)."""
    secret = os.environ["JWT_SECRET"]
    payload = {
        "sub": "888",
        "email": email,
        "is_admin": False,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, secret, algorithm="HS256")


# ---------------------------------------------------------------------------
# 1. Unauthenticated access → 401
# ---------------------------------------------------------------------------

class TestUnauthenticatedAccess:
    """All protected routes must return 401 without a valid token."""

    def test_leads_upload_requires_auth(self, client):
        resp = client.post(
            "/api/clients/1/leads",
            json={"leads": [{"name": "Test", "phone": "+15551234567"}]},
        )
        assert resp.status_code == 401

    def test_csv_upload_requires_auth(self, client):
        files = {"file": ("leads.csv", "name,phone\nA,+15551234567", "text/csv")}
        resp = client.post("/api/clients/1/uploads", files=files)
        assert resp.status_code == 401

    def test_call_status_requires_auth(self, client):
        resp = client.post(
            "/api/calls/1/status",
            json={"status": "completed", "result": "booked"},
        )
        assert resp.status_code == 401

    def test_batch_calls_requires_auth(self, client):
        resp = client.get("/api/clients/1/batches/1/calls")
        assert resp.status_code == 401

    # Twilio webhook uses signature validation, not JWT.
    # In SIMULATED mode the signature check is skipped, so we cannot
    # reliably assert 401/403 here. Covered by signature-specific tests.


# ---------------------------------------------------------------------------
# 2. Expired / invalid token → 401
# ---------------------------------------------------------------------------

class TestInvalidTokens:
    """Expired, malformed, or tampered tokens must be rejected."""

    def test_expired_token_rejected(self, client):
        headers = {"Authorization": f"Bearer {_make_expired_token()}"}
        resp = client.post(
            "/api/clients/1/leads",
            json={"leads": [{"name": "X", "phone": "+15551234567"}]},
            headers=headers,
        )
        assert resp.status_code == 401

    def test_malformed_token_rejected(self, client):
        headers = {"Authorization": "Bearer not-a-real-jwt"}
        resp = client.get("/api/clients/1/batches/1/calls", headers=headers)
        assert resp.status_code == 401

    def test_missing_bearer_prefix_rejected(self, client):
        headers = {"Authorization": "Token somevalue"}
        resp = client.post(
            "/api/calls/1/status",
            json={"status": "completed", "result": "booked"},
            headers=headers,
        )
        assert resp.status_code == 401

    def test_wrong_secret_rejected(self, client):
        """Token signed with a different secret must be rejected."""
        payload = {
            "sub": "1",
            "email": "admin@dental-demo.com",
            "is_admin": True,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }
        bad_token = jwt.encode(payload, "WrongSecret_1234567890!Abcdefgh", algorithm="HS256")
        headers = {"Authorization": f"Bearer {bad_token}"}
        resp = client.post(
            "/api/clients/1/leads",
            json={"leads": [{"name": "X", "phone": "+15551234567"}]},
            headers=headers,
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 3. Cross-tenant access → 403
# ---------------------------------------------------------------------------

class TestCrossTenantAccess:
    """Non-admin users must not access other tenants' clients."""

    def test_non_admin_denied_client_leads(self, client):
        """Non-admin with no matching owner_email → 403."""
        headers = {"Authorization": f"Bearer {_make_non_admin_token()}"}
        resp = client.post(
            "/api/clients/1/leads",
            json={"leads": [{"name": "X", "phone": "+15551234567", "consent": True}]},
            headers=headers,
        )
        assert resp.status_code == 403

    def test_non_admin_denied_client_uploads(self, client):
        headers = {"Authorization": f"Bearer {_make_non_admin_token()}"}
        files = {"file": ("leads.csv", "name,phone\nA,+15551234567", "text/csv")}
        resp = client.post("/api/clients/1/uploads", files=files, headers=headers)
        assert resp.status_code == 403

    def test_non_admin_denied_batch_calls(self, client):
        headers = {"Authorization": f"Bearer {_make_non_admin_token()}"}
        resp = client.get("/api/clients/1/batches/1/calls", headers=headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 4. Valid admin access → 2xx
# ---------------------------------------------------------------------------

class TestValidAdminAccess:
    """Admin token should succeed on all protected client routes."""

    def test_admin_can_upload_leads(self, client, admin_headers):
        resp = client.post(
            "/api/clients/1/leads",
            json={"leads": [{"name": "Auth OK", "phone": "+15559990001", "consent": True}]},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_admin_can_upload_csv(self, client, admin_headers):
        csv = "name,phone,consent\nCSV Auth,+15559990002,true"
        files = {"file": ("leads.csv", csv, "text/csv")}
        resp = client.post("/api/clients/1/uploads", files=files, headers=admin_headers)
        assert resp.status_code == 200

    def test_admin_can_list_batch_calls(self, client, admin_headers):
        # First create a batch so we can list it
        upload = client.post(
            "/api/clients/1/leads",
            json={"leads": [{"name": "Batch Auth", "phone": "+15559990003", "consent": True}]},
            headers=admin_headers,
        )
        batch_id = upload.json()["batch_id"]
        resp = client.get(
            f"/api/clients/1/batches/{batch_id}/calls",
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_admin_can_update_call_status(self, client, admin_headers):
        # Create a call first
        upload = client.post(
            "/api/clients/1/leads",
            json={"leads": [{"name": "Status Auth", "phone": "+15559990004", "consent": True}]},
            headers=admin_headers,
        )
        batch_id = upload.json()["batch_id"]
        calls = client.get(
            f"/api/clients/1/batches/{batch_id}/calls",
            headers=admin_headers,
        ).json()
        call_id = calls["calls"][0]["id"]

        resp = client.post(
            f"/api/calls/{call_id}/status",
            json={"status": "completed", "result": "booked", "transcript": "test"},
            headers=admin_headers,
        )
        assert resp.status_code == 200

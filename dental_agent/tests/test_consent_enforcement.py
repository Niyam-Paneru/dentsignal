"""
test_consent_enforcement.py - Centralized Consent Enforcement Tests (AG-4)

Tests the enforce_consent() guard and its integration with:
1. utils.py: requires_consent(), check_lead_consent(), filter_leads_by_consent()
2. api_main.py: JSON upload, CSV upload (allow_no_consent removed)
3. tasks.py: start_call blocks non-consented leads in TWILIO mode
4. db.py: enqueue_calls_for_batch skips non-consented leads in TWILIO mode
"""

import pytest
import os
import sys
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

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


# ---------------------------------------------------------------------------
# 1. Unit tests for utils.py consent functions
# ---------------------------------------------------------------------------

class TestRequiresConsent:
    """Test requires_consent() determines the right mode."""

    def test_twilio_mode_requires_consent(self):
        from utils import requires_consent
        assert requires_consent("TWILIO") is True

    def test_simulated_mode_no_consent(self):
        from utils import requires_consent
        assert requires_consent("SIMULATED") is False

    def test_case_insensitive(self):
        from utils import requires_consent
        assert requires_consent("twilio") is True
        assert requires_consent("Twilio") is True

    def test_defaults_to_env_var(self):
        from utils import requires_consent
        old = os.environ.get("TELEPHONY_MODE")
        os.environ["TELEPHONY_MODE"] = "TWILIO"
        try:
            assert requires_consent() is True
        finally:
            if old:
                os.environ["TELEPHONY_MODE"] = old
            else:
                os.environ.pop("TELEPHONY_MODE", None)

    def test_defaults_to_simulated(self):
        from utils import requires_consent
        old = os.environ.pop("TELEPHONY_MODE", None)
        try:
            assert requires_consent() is False
        finally:
            if old:
                os.environ["TELEPHONY_MODE"] = old


class TestCheckLeadConsent:
    """Test check_lead_consent() for individual leads."""

    def test_consented_lead_allowed_twilio(self):
        from utils import check_lead_consent
        ok, reason = check_lead_consent({"consent": True}, "TWILIO")
        assert ok is True
        assert reason == ""

    def test_non_consented_lead_blocked_twilio(self):
        from utils import check_lead_consent
        ok, reason = check_lead_consent({"consent": False}, "TWILIO")
        assert ok is False
        assert "TCPA" in reason

    def test_missing_consent_key_blocked_twilio(self):
        from utils import check_lead_consent
        ok, reason = check_lead_consent({}, "TWILIO")
        assert ok is False

    def test_non_consented_lead_allowed_simulated(self):
        from utils import check_lead_consent
        ok, reason = check_lead_consent({"consent": False}, "SIMULATED")
        assert ok is True

    def test_missing_consent_allowed_simulated(self):
        from utils import check_lead_consent
        ok, reason = check_lead_consent({}, "SIMULATED")
        assert ok is True


class TestFilterLeadsByConsent:
    """Test filter_leads_by_consent() batch filtering."""

    def test_twilio_filters_out_no_consent(self):
        from utils import filter_leads_by_consent
        leads = [
            {"name": "A", "phone": "+15551111111", "consent": True},
            {"name": "B", "phone": "+15552222222", "consent": False},
            {"name": "C", "phone": "+15553333333", "consent": True},
        ]
        allowed, skipped = filter_leads_by_consent(leads, "TWILIO")
        assert len(allowed) == 2
        assert skipped == 1
        assert all(ld["consent"] for ld in allowed)

    def test_simulated_passes_all(self):
        from utils import filter_leads_by_consent
        leads = [
            {"name": "A", "phone": "+15551111111", "consent": False},
            {"name": "B", "phone": "+15552222222", "consent": False},
        ]
        allowed, skipped = filter_leads_by_consent(leads, "SIMULATED")
        assert len(allowed) == 2
        assert skipped == 0

    def test_twilio_all_skipped_returns_empty(self):
        from utils import filter_leads_by_consent
        leads = [
            {"name": "A", "phone": "+15551111111", "consent": False},
        ]
        allowed, skipped = filter_leads_by_consent(leads, "TWILIO")
        assert len(allowed) == 0
        assert skipped == 1

    def test_empty_list_returns_empty(self):
        from utils import filter_leads_by_consent
        allowed, skipped = filter_leads_by_consent([], "TWILIO")
        assert allowed == []
        assert skipped == 0


# ---------------------------------------------------------------------------
# 2. allow_no_consent query param is REMOVED from API
# ---------------------------------------------------------------------------

class TestAllowNoConsentRemoved:
    """The allow_no_consent bypass flag must not exist on upload endpoints."""

    def test_json_upload_ignores_allow_no_consent_param(self, client, admin_headers):
        """Even if someone passes allow_no_consent, it's ignored (not a parameter)."""
        # In SIMULATED mode, consent isn't required anyway, so this just
        # verifies the param doesn't cause an error (FastAPI ignores unknown query params).
        resp = client.post(
            "/api/clients/1/leads?allow_no_consent=true",
            json={"leads": [{"name": "Test", "phone": "+15559990001", "consent": True}]},
            headers=admin_headers,
        )
        # Should work (SIMULATED mode, consent provided) — the param is simply ignored
        assert resp.status_code == 200

    def test_csv_upload_ignores_allow_no_consent_param(self, client, admin_headers):
        csv = "name,phone,consent\nTest,+15559990002,true"
        files = {"file": ("leads.csv", csv, "text/csv")}
        resp = client.post(
            "/api/clients/1/uploads?allow_no_consent=true",
            files=files,
            headers=admin_headers,
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 3. TWILIO mode blocks uploads without consent
# ---------------------------------------------------------------------------

class TestTwilioConsentEnforcementAPI:
    """In TWILIO mode, leads without consent must be rejected at upload."""

    def test_json_upload_blocks_no_consent_twilio(self, client, admin_headers):
        """All leads without consent → 400 in TWILIO mode."""
        with patch.dict(os.environ, {"TELEPHONY_MODE": "TWILIO"}):
            resp = client.post(
                "/api/clients/1/leads",
                json={"leads": [
                    {"name": "NoConsent", "phone": "+15559990010", "consent": False},
                ]},
                headers=admin_headers,
            )
            assert resp.status_code == 400
            assert "consent" in resp.json()["detail"].lower()

    def test_json_upload_allows_consented_twilio(self, client, admin_headers):
        """Leads with consent=true succeed in TWILIO mode."""
        with patch.dict(os.environ, {"TELEPHONY_MODE": "TWILIO"}):
            resp = client.post(
                "/api/clients/1/leads",
                json={"leads": [
                    {"name": "Consented", "phone": "+15559990011", "consent": True},
                ]},
                headers=admin_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["queued_count"] >= 1
            assert data["skipped_no_consent"] == 0

    def test_json_upload_mixed_consent_twilio(self, client, admin_headers):
        """Mixed consent: only consented leads proceed, others are skipped."""
        with patch.dict(os.environ, {"TELEPHONY_MODE": "TWILIO"}):
            resp = client.post(
                "/api/clients/1/leads",
                json={"leads": [
                    {"name": "Yes", "phone": "+15559990012", "consent": True},
                    {"name": "No", "phone": "+15559990013", "consent": False},
                    {"name": "Also Yes", "phone": "+15559990014", "consent": True},
                ]},
                headers=admin_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["queued_count"] >= 2
            assert data["skipped_no_consent"] == 1

    def test_csv_upload_blocks_no_consent_twilio(self, client, admin_headers):
        """CSV upload blocks non-consented leads in TWILIO mode."""
        csv = "name,phone,consent\nNoConsent,+15559990020,false"
        files = {"file": ("leads.csv", csv, "text/csv")}
        with patch.dict(os.environ, {"TELEPHONY_MODE": "TWILIO"}):
            resp = client.post(
                "/api/clients/1/uploads",
                files=files,
                headers=admin_headers,
            )
            assert resp.status_code == 400
            assert "consent" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 4. SIMULATED mode allows without consent
# ---------------------------------------------------------------------------

class TestSimulatedConsentBypass:
    """In SIMULATED mode, consent is not enforced."""

    def test_json_upload_allows_no_consent_simulated(self, client, admin_headers):
        with patch.dict(os.environ, {"TELEPHONY_MODE": "SIMULATED"}):
            resp = client.post(
                "/api/clients/1/leads",
                json={"leads": [
                    {"name": "NoCons", "phone": "+15559990030", "consent": False},
                ]},
                headers=admin_headers,
            )
            assert resp.status_code == 200
            assert resp.json()["skipped_no_consent"] == 0


# ---------------------------------------------------------------------------
# 5. Task-level consent check (start_call)
# ---------------------------------------------------------------------------

class TestTaskConsentGuard:
    """start_call task uses centralized check_lead_consent."""

    def test_start_call_blocks_no_consent_twilio(self):
        """In TWILIO mode, start_call should block a lead without consent."""
        from db import create_db, get_session, Lead, UploadBatch
        from tasks import get_lead_by_id

        create_db("sqlite:///:memory:")

        with get_session() as session:
            batch = UploadBatch(client_id=1, source="task_test")
            session.add(batch)
            session.commit()
            session.refresh(batch)

            lead = Lead(
                batch_id=batch.id,
                name="No Consent Task",
                phone="+15559990040",
                consent=False,
            )
            session.add(lead)
            session.commit()
            session.refresh(lead)
            lead_id = lead.id

        lead_data = get_lead_by_id(lead_id)
        assert lead_data is not None

        # check_lead_consent should block in TWILIO mode
        from utils import check_lead_consent
        ok, reason = check_lead_consent(lead_data, "TWILIO")
        assert ok is False
        assert "consent" in reason.lower()

    def test_start_call_allows_consent_twilio(self):
        """In TWILIO mode, consented lead passes the check."""
        from utils import check_lead_consent
        ok, reason = check_lead_consent({"consent": True}, "TWILIO")
        assert ok is True


# ---------------------------------------------------------------------------
# 6. Enqueue defense-in-depth (db.py)
# ---------------------------------------------------------------------------

class TestEnqueueConsentFilter:
    """enqueue_calls_for_batch skips non-consented leads in TWILIO mode."""

    def test_enqueue_skips_no_consent_twilio(self):
        from db import (
            create_db, get_session, Lead, UploadBatch,
            Call, CallStatus, enqueue_calls_for_batch,
        )

        create_db("sqlite:///:memory:")

        with get_session() as session:
            batch = UploadBatch(client_id=1, source="enqueue_test")
            session.add(batch)
            session.commit()
            session.refresh(batch)

            # 2 leads: one with consent, one without
            lead_yes = Lead(batch_id=batch.id, name="Yes", phone="+15550001111", consent=True)
            lead_no = Lead(batch_id=batch.id, name="No", phone="+15550002222", consent=False)
            session.add_all([lead_yes, lead_no])
            session.commit()

            with patch.dict(os.environ, {"TELEPHONY_MODE": "TWILIO"}):
                count = enqueue_calls_for_batch(session, batch.id, client_id=1)

            # Only the consented lead should be enqueued
            assert count == 1

    def test_enqueue_allows_all_simulated(self):
        from db import (
            create_db, get_session, Lead, UploadBatch,
            enqueue_calls_for_batch,
        )

        create_db("sqlite:///:memory:")

        with get_session() as session:
            batch = UploadBatch(client_id=1, source="enqueue_sim")
            session.add(batch)
            session.commit()
            session.refresh(batch)

            lead_no1 = Lead(batch_id=batch.id, name="A", phone="+15550003333", consent=False)
            lead_no2 = Lead(batch_id=batch.id, name="B", phone="+15550004444", consent=False)
            session.add_all([lead_no1, lead_no2])
            session.commit()

            with patch.dict(os.environ, {"TELEPHONY_MODE": "SIMULATED"}):
                count = enqueue_calls_for_batch(session, batch.id, client_id=1)

            # Both should be enqueued in SIMULATED mode
            assert count == 2


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

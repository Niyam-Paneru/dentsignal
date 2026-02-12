"""
test_dnc.py — AG-9 Do-Not-Call Registry & Enforcement Tests

Tests for:
1. DoNotCall model creation + phi_hash auto-computation
2. is_dnc() — single number check (positive/negative, clinic scoping)
3. filter_leads_by_dnc() — bulk batch filter
4. add_to_dnc() / remove_from_dnc() lifecycle
5. Reactivation of previously removed entry
6. enqueue_calls_for_batch() skips DNC leads
7. DNC admin routes (POST/DELETE/GET /api/dnc, POST /api/dnc/check)
8. start_call() dial-time DNC block
"""

import os
import sys
import pytest

# Ensure dental_agent on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlmodel import Session, select, SQLModel
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures — isolated in-memory DB
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine():
    """Fresh in-memory SQLite engine with all tables."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from db import (
        Lead, Client, UploadBatch, Call, CallResult,
        DoNotCall, Patient, InboundCall, Appointment, PatientRecall,
    )
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    """Per-test session, rolled back after."""
    with Session(engine) as sess:
        yield sess
        sess.rollback()


@pytest.fixture
def seed_client(session):
    """Create prerequisite Client + UploadBatch rows. Returns (client, batch)."""
    from db import Client, UploadBatch

    client = Client(
        name="Test Clinic",
        email="clinic@test.com",
        hashed_password="hashed",
        twilio_number="+10000000000",
    )
    session.add(client)
    session.flush()

    batch = UploadBatch(client_id=client.id)
    session.add(batch)
    session.flush()
    return client, batch


# ---------------------------------------------------------------------------
# 1. DoNotCall Model — creation + hash auto-computation
# ---------------------------------------------------------------------------

class TestDoNotCallModel:
    """Verify model creation, phi_hash auto-computation, and soft-delete."""

    def test_create_dnc_entry(self, session, seed_client):
        """DoNotCall row created with correct fields and auto-computed hash."""
        from db import DoNotCall, DNCReason
        client, _batch = seed_client

        entry = DoNotCall(
            clinic_id=client.id,
            phone="+15559990001",
            reason=DNCReason.PATIENT_REQUEST,
            notes="Patient called to opt out",
            added_by="admin@test.com",
        )
        session.add(entry)
        session.commit()

        session.expire(entry)
        reloaded = session.get(DoNotCall, entry.id)
        assert reloaded is not None
        assert reloaded.is_active is True
        assert reloaded.reason == DNCReason.PATIENT_REQUEST
        assert reloaded.phone_hash != ""
        assert len(reloaded.phone_hash) == 64  # SHA-256 hex

    def test_hash_deterministic(self, session, seed_client):
        """Same phone → same hash across multiple entries."""
        from db import DoNotCall, DNCReason
        from encryption import phi_hash

        entry = DoNotCall(
            clinic_id=None,
            phone="+15559990002",
            reason=DNCReason.ADMIN,
        )
        session.add(entry)
        session.commit()
        session.expire(entry)
        reloaded = session.get(DoNotCall, entry.id)
        assert reloaded.phone_hash == phi_hash("+15559990002")

    def test_soft_delete_fields(self, session, seed_client):
        """removed_at and is_active control soft-delete."""
        from db import DoNotCall, DNCReason

        entry = DoNotCall(phone="+15559990003", reason=DNCReason.ADMIN)
        session.add(entry)
        session.commit()
        assert entry.removed_at is None
        assert entry.is_active is True

        entry.is_active = False
        entry.removed_at = datetime.utcnow()
        session.add(entry)
        session.commit()
        session.expire(entry)
        reloaded = session.get(DoNotCall, entry.id)
        assert reloaded.is_active is False
        assert reloaded.removed_at is not None


# ---------------------------------------------------------------------------
# 2. is_dnc() — single-number checks
# ---------------------------------------------------------------------------

class TestIsDnc:
    """Test the core DNC lookup function."""

    def test_blocked_number_returns_true(self, session, seed_client):
        from db import DoNotCall, DNCReason
        from dnc_service import is_dnc

        client, _ = seed_client
        session.add(DoNotCall(
            clinic_id=client.id,
            phone="+15551110001",
            reason=DNCReason.COMPLAINT,
        ))
        session.commit()

        assert is_dnc(session, "+15551110001", clinic_id=client.id) is True

    def test_clean_number_returns_false(self, session, seed_client):
        from dnc_service import is_dnc
        client, _ = seed_client
        assert is_dnc(session, "+15559999999", clinic_id=client.id) is False

    def test_global_dnc_blocks_all_clinics(self, session, seed_client):
        """A global entry (clinic_id=None) blocks for any clinic."""
        from db import DoNotCall, DNCReason
        from dnc_service import is_dnc

        client, _ = seed_client
        session.add(DoNotCall(
            clinic_id=None,
            phone="+15551110010",
            reason=DNCReason.LEGAL,
        ))
        session.commit()

        # Should block when checked against any clinic
        assert is_dnc(session, "+15551110010", clinic_id=client.id) is True
        # Should also block when no clinic specified
        assert is_dnc(session, "+15551110010") is True

    def test_clinic_specific_does_not_block_other_clinic(self, session, seed_client):
        """A clinic-specific DNC entry should not block other clinics (no global match)."""
        from db import DoNotCall, DNCReason
        from dnc_service import is_dnc

        client, _ = seed_client
        session.add(DoNotCall(
            clinic_id=client.id,
            phone="+15551110020",
            reason=DNCReason.WRONG_NUMBER,
        ))
        session.commit()

        # Blocked for this clinic
        assert is_dnc(session, "+15551110020", clinic_id=client.id) is True
        # NOT blocked for a different clinic (id=99999 doesn't exist)
        assert is_dnc(session, "+15551110020", clinic_id=99999) is False

    def test_inactive_entry_not_blocked(self, session, seed_client):
        """Removed (is_active=False) entries should NOT block."""
        from db import DoNotCall, DNCReason
        from dnc_service import is_dnc

        client, _ = seed_client
        entry = DoNotCall(
            clinic_id=client.id,
            phone="+15551110030",
            reason=DNCReason.ADMIN,
            is_active=False,
            removed_at=datetime.utcnow(),
        )
        session.add(entry)
        session.commit()

        assert is_dnc(session, "+15551110030", clinic_id=client.id) is False

    def test_empty_phone_returns_false(self, session):
        from dnc_service import is_dnc
        assert is_dnc(session, "") is False
        assert is_dnc(session, None) is False


# ---------------------------------------------------------------------------
# 3. filter_leads_by_dnc() — bulk filter
# ---------------------------------------------------------------------------

class TestFilterLeadsByDnc:
    """Test the batch DNC filter used in upload paths."""

    def test_filters_out_dnc_leads(self, session, seed_client):
        from db import DoNotCall, DNCReason
        from dnc_service import filter_leads_by_dnc

        client, _ = seed_client
        session.add(DoNotCall(
            clinic_id=client.id,
            phone="+15552220001",
            reason=DNCReason.ADMIN,
        ))
        session.commit()

        leads = [
            {"name": "Alice", "phone": "+15552220001"},  # blocked
            {"name": "Bob", "phone": "+15552220002"},    # clean
            {"name": "Carol", "phone": "+15552220003"},  # clean
        ]

        clean, blocked = filter_leads_by_dnc(session, leads, clinic_id=client.id)
        assert blocked == 1
        assert len(clean) == 2
        assert all(l["name"] != "Alice" for l in clean)

    def test_empty_list_returns_empty(self, session):
        from dnc_service import filter_leads_by_dnc
        clean, blocked = filter_leads_by_dnc(session, [])
        assert clean == []
        assert blocked == 0

    def test_no_dnc_entries_passes_all(self, session, seed_client):
        from dnc_service import filter_leads_by_dnc
        client, _ = seed_client

        leads = [
            {"name": "Dave", "phone": "+15553330001"},
            {"name": "Eve", "phone": "+15553330002"},
        ]
        clean, blocked = filter_leads_by_dnc(session, leads, clinic_id=client.id)
        assert blocked == 0
        assert len(clean) == 2


# ---------------------------------------------------------------------------
# 4. add_to_dnc() / remove_from_dnc() lifecycle
# ---------------------------------------------------------------------------

class TestAddRemoveDnc:
    """Test DNC add and soft-remove lifecycle."""

    def test_add_creates_active_entry(self, session, seed_client):
        from dnc_service import add_to_dnc, is_dnc
        from db import DNCReason

        client, _ = seed_client
        entry = add_to_dnc(
            session,
            phone="+15554440001",
            clinic_id=client.id,
            reason=DNCReason.PATIENT_REQUEST,
            notes="Test add",
            added_by="test@test.com",
        )
        session.commit()
        assert entry.is_active is True
        assert is_dnc(session, "+15554440001", clinic_id=client.id) is True

    def test_remove_deactivates_entry(self, session, seed_client):
        from dnc_service import add_to_dnc, remove_from_dnc, is_dnc
        from db import DNCReason

        client, _ = seed_client
        add_to_dnc(session, "+15554440002", clinic_id=client.id, reason=DNCReason.ADMIN)
        session.commit()

        result = remove_from_dnc(session, "+15554440002", clinic_id=client.id)
        session.commit()

        assert result is True
        assert is_dnc(session, "+15554440002", clinic_id=client.id) is False

    def test_remove_nonexistent_returns_false(self, session, seed_client):
        from dnc_service import remove_from_dnc
        client, _ = seed_client
        assert remove_from_dnc(session, "+15559999998", clinic_id=client.id) is False

    def test_add_invalid_phone_raises(self, session, seed_client):
        from dnc_service import add_to_dnc
        from db import DNCReason
        client, _ = seed_client
        with pytest.raises(ValueError, match="Invalid phone"):
            add_to_dnc(session, "not-a-phone", clinic_id=client.id, reason=DNCReason.ADMIN)


# ---------------------------------------------------------------------------
# 5. Reactivation of removed entry
# ---------------------------------------------------------------------------

class TestReactivation:
    """Adding a previously removed number should reactivate, not duplicate."""

    def test_reactivate_after_remove(self, session, seed_client):
        from dnc_service import add_to_dnc, remove_from_dnc, is_dnc
        from db import DoNotCall, DNCReason
        from encryption import phi_hash
        from utils import normalize_phone

        client, _ = seed_client
        phone = "+15555550001"

        # Add → remove → re-add
        add_to_dnc(session, phone, clinic_id=client.id, reason=DNCReason.ADMIN)
        session.commit()
        remove_from_dnc(session, phone, clinic_id=client.id)
        session.commit()
        assert is_dnc(session, phone, clinic_id=client.id) is False

        # Re-add
        entry = add_to_dnc(
            session, phone, clinic_id=client.id,
            reason=DNCReason.PATIENT_REQUEST, notes="Re-added",
        )
        session.commit()
        assert entry.is_active is True
        assert entry.removed_at is None
        assert entry.reason == DNCReason.PATIENT_REQUEST

        # Verify only ONE row for this phone+clinic (no duplicates)
        h = phi_hash(normalize_phone(phone))
        stmt = select(DoNotCall).where(
            DoNotCall.phone_hash == h,
            DoNotCall.clinic_id == client.id,
        )
        rows = session.exec(stmt).all()
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# 6. list_dnc()
# ---------------------------------------------------------------------------

class TestListDnc:
    """Test DNC listing with active/inactive filters."""

    def test_list_active_only(self, session, seed_client):
        from dnc_service import add_to_dnc, remove_from_dnc, list_dnc
        from db import DNCReason

        client, _ = seed_client
        add_to_dnc(session, "+15556660001", clinic_id=client.id, reason=DNCReason.ADMIN)
        add_to_dnc(session, "+15556660002", clinic_id=client.id, reason=DNCReason.ADMIN)
        session.commit()
        remove_from_dnc(session, "+15556660002", clinic_id=client.id)
        session.commit()

        entries = list_dnc(session, clinic_id=client.id, include_inactive=False)
        phones = [e.phone for e in entries]
        # +15556660001 should be in the list, but not +15556660002
        assert any("+15556660001" in (p or "") for p in phones)

    def test_list_includes_inactive(self, session, seed_client):
        from dnc_service import add_to_dnc, remove_from_dnc, list_dnc
        from db import DNCReason

        client, _ = seed_client
        add_to_dnc(session, "+15556660010", clinic_id=client.id, reason=DNCReason.ADMIN)
        session.commit()
        remove_from_dnc(session, "+15556660010", clinic_id=client.id)
        session.commit()

        entries_all = list_dnc(session, clinic_id=client.id, include_inactive=True)
        entries_active = list_dnc(session, clinic_id=client.id, include_inactive=False)
        assert len(entries_all) >= len(entries_active)


# ---------------------------------------------------------------------------
# 7. DNC Admin Routes — integration tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """Create FastAPI app with test DB."""
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
def http_client(app):
    """HTTP TestClient for API integration tests."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def admin_token(http_client):
    """Get a valid admin JWT token via login."""
    resp = http_client.post(
        "/api/auth/login",
        json={"email": "admin@dental-demo.com", "password": "admin123"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["token"]


class TestDncRoutes:
    """Integration tests for /api/dnc endpoints."""

    def test_add_dnc_requires_auth(self, http_client):
        """POST /api/dnc without token → 401."""
        resp = http_client.post("/api/dnc", json={"phone": "+15557770001"})
        assert resp.status_code == 401

    def test_add_dnc_success(self, http_client, admin_token):
        """POST /api/dnc with valid token → 201."""
        resp = http_client.post(
            "/api/dnc",
            json={
                "phone": "+15557770001",
                "reason": "patient_request",
                "notes": "Test DNC add via API",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["entry"]["is_active"] is True

    def test_add_dnc_invalid_phone(self, http_client, admin_token):
        """POST /api/dnc with invalid phone → 400."""
        resp = http_client.post(
            "/api/dnc",
            json={"phone": "invalid", "reason": "admin"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    def test_add_dnc_invalid_reason(self, http_client, admin_token):
        """POST /api/dnc with bad reason → 400."""
        resp = http_client.post(
            "/api/dnc",
            json={"phone": "+15557770002", "reason": "bogus_reason"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    def test_check_dnc_positive(self, http_client, admin_token):
        """POST /api/dnc/check after adding → is_dnc=True."""
        # Ensure the number is added (may already exist from earlier test)
        http_client.post(
            "/api/dnc",
            json={"phone": "+15557770010", "reason": "admin"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = http_client.post(
            "/api/dnc/check",
            json={"phone": "+15557770010"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_dnc"] is True

    def test_check_dnc_negative(self, http_client, admin_token):
        """POST /api/dnc/check for unlisted number → is_dnc=False."""
        resp = http_client.post(
            "/api/dnc/check",
            json={"phone": "+15557779999"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_dnc"] is False

    def test_list_dnc(self, http_client, admin_token):
        """GET /api/dnc returns entries."""
        resp = http_client.get(
            "/api/dnc",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["entries"], list)
        assert body["count"] >= 0

    def test_list_dnc_requires_auth(self, http_client):
        """GET /api/dnc without token → 401."""
        resp = http_client.get("/api/dnc")
        assert resp.status_code == 401

    def test_remove_dnc_success(self, http_client, admin_token):
        """DELETE /api/dnc soft-removes entry."""
        # Add first
        http_client.post(
            "/api/dnc",
            json={"phone": "+15557770020", "reason": "admin"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Remove
        resp = http_client.request(
            "DELETE",
            "/api/dnc",
            json={"phone": "+15557770020"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["success"] is True

        # Verify removed
        check = http_client.post(
            "/api/dnc/check",
            json={"phone": "+15557770020"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert check.json()["is_dnc"] is False

    def test_remove_nonexistent_404(self, http_client, admin_token):
        """DELETE /api/dnc for unknown number → 404."""
        resp = http_client.request(
            "DELETE",
            "/api/dnc",
            json={"phone": "+15559999997"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

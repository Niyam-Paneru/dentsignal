"""
test_compliance.py — AG-11 Compliance (BAA, Retention, Deletion) Tests

Tests for:
1. BusinessAssociateAgreement model CRUD
2. RetentionPolicy model defaults + updates
3. DataDeletionRequest lifecycle
4. BAA compliance status endpoint (signed vs missing)
5. Retention policy API (get defaults, upsert)
6. Deletion request API (create, list, execute)
"""

import os
import sys
import json
import pytest

# Ensure dental_agent on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
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
        BusinessAssociateAgreement, RetentionPolicy, DataDeletionRequest,
        Client, Lead, UploadBatch, Call, CallResult,
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


# ---------------------------------------------------------------------------
# JWT helper for API tests
# ---------------------------------------------------------------------------
import jwt as pyjwt

JWT_SECRET = os.environ.get("JWT_SECRET", "DentSignal_Pytest2026!ValidKey@XyZ99")
JWT_ALGORITHM = "HS256"


def make_token(email: str = "admin@clinic.com", clinic_id: int = 1) -> str:
    payload = {
        "sub": email,
        "email": email,
        "client_id": clinic_id,
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


AUTH_HEADERS = {"Authorization": f"Bearer {make_token()}"}


# ---------------------------------------------------------------------------
# 1. BusinessAssociateAgreement Model
# ---------------------------------------------------------------------------

class TestBAAModel:
    """Verify BAA model creation and defaults."""

    def test_create_baa(self, session):
        from db import BusinessAssociateAgreement, BAAStatus, VendorType
        baa = BusinessAssociateAgreement(
            clinic_id="clinic-1",
            vendor_name="Supabase",
            vendor_type=VendorType.DATABASE,
            baa_status=BAAStatus.SIGNED,
            signed_date=datetime(2025, 6, 1),
        )
        session.add(baa)
        session.commit()
        session.refresh(baa)
        assert baa.id is not None
        assert baa.vendor_name == "Supabase"
        assert baa.baa_status == BAAStatus.SIGNED
        assert baa.vendor_type == VendorType.DATABASE

    def test_default_status_is_pending(self, session):
        from db import BusinessAssociateAgreement, BAAStatus
        baa = BusinessAssociateAgreement(
            clinic_id="clinic-2",
            vendor_name="TestVendor",
        )
        session.add(baa)
        session.commit()
        assert baa.baa_status == BAAStatus.PENDING

    def test_baa_repr(self, session):
        from db import BusinessAssociateAgreement, BAAStatus
        baa = BusinessAssociateAgreement(
            clinic_id="clinic-3",
            vendor_name="Deepgram",
            baa_status=BAAStatus.EXPIRED,
        )
        session.add(baa)
        session.commit()
        r = repr(baa)
        assert "Deepgram" in r
        assert "EXPIRED" in r.upper()


# ---------------------------------------------------------------------------
# 2. RetentionPolicy Model
# ---------------------------------------------------------------------------

class TestRetentionPolicyModel:

    def test_create_with_defaults(self, session):
        from db import RetentionPolicy
        policy = RetentionPolicy(clinic_id="ret-clinic-1")
        session.add(policy)
        session.commit()
        session.refresh(policy)
        assert policy.call_recording_days == 90
        assert policy.call_transcript_days == 365
        assert policy.patient_data_days == 2555
        assert policy.audit_log_days == 2555

    def test_custom_retention(self, session):
        from db import RetentionPolicy
        policy = RetentionPolicy(
            clinic_id="ret-clinic-2",
            call_recording_days=30,
            call_transcript_days=180,
        )
        session.add(policy)
        session.commit()
        assert policy.call_recording_days == 30
        assert policy.call_transcript_days == 180


# ---------------------------------------------------------------------------
# 3. DataDeletionRequest Model
# ---------------------------------------------------------------------------

class TestDeletionRequestModel:

    def test_create_deletion_request(self, session):
        from db import DataDeletionRequest
        dr = DataDeletionRequest(
            clinic_id="del-clinic-1",
            patient_identifier="hash-abc123",
            requested_by="admin@clinic.com",
            reason="Patient requested full data removal",
        )
        session.add(dr)
        session.commit()
        session.refresh(dr)
        assert dr.id is not None
        assert dr.status == "pending"
        assert dr.completed_at is None

    def test_complete_deletion_request(self, session):
        from db import DataDeletionRequest
        dr = DataDeletionRequest(
            clinic_id="del-clinic-2",
            patient_identifier="hash-xyz789",
            requested_by="admin@clinic.com",
        )
        session.add(dr)
        session.commit()
        dr.status = "completed"
        dr.data_types_deleted = json.dumps(["call_recordings", "patient_record"])
        dr.completed_at = datetime.utcnow()
        session.commit()
        session.refresh(dr)
        assert dr.status == "completed"
        assert "call_recordings" in json.loads(dr.data_types_deleted)


# ---------------------------------------------------------------------------
# 4. BAA API Routes
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """TestClient for the FastAPI app with patched DB."""
    os.environ["DISABLE_RATE_LIMIT"] = "1"
    os.environ["DISABLE_BRUTE_FORCE"] = "1"
    import api_main
    api_main.DATABASE_URL = "sqlite:///:memory:"
    from starlette.testclient import TestClient as _TC
    with _TC(api_main.app) as c:
        yield c


class TestBAARoutes:

    def test_create_baa(self, client):
        resp = client.post("/api/compliance/baa", json={
            "clinic_id": "api-clinic-1",
            "vendor_name": "Supabase",
            "vendor_type": "database",
            "baa_status": "signed",
            "signed_date": "2025-06-01T00:00:00",
        }, headers=AUTH_HEADERS)
        assert resp.status_code == 201
        data = resp.json()
        assert data["ok"] is True
        assert data["vendor"] == "Supabase"

    def test_list_baas(self, client):
        resp = client.get(
            "/api/compliance/baa",
            params={"clinic_id": "api-clinic-1"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["count"] >= 1

    def test_update_baa(self, client):
        # Create first
        resp = client.post("/api/compliance/baa", json={
            "clinic_id": "api-clinic-up",
            "vendor_name": "Telnyx",
            "baa_status": "pending",
        }, headers=AUTH_HEADERS)
        baa_id = resp.json()["baa_id"]
        # Update
        resp = client.put(f"/api/compliance/baa/{baa_id}", json={
            "baa_status": "signed",
            "signed_date": "2025-07-15T00:00:00",
        }, headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "signed"

    def test_delete_baa(self, client):
        resp = client.post("/api/compliance/baa", json={
            "clinic_id": "api-clinic-del",
            "vendor_name": "TempVendor",
        }, headers=AUTH_HEADERS)
        baa_id = resp.json()["baa_id"]
        resp = client.delete(f"/api/compliance/baa/{baa_id}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["deleted"] == baa_id

    def test_delete_nonexistent_baa(self, client):
        resp = client.delete("/api/compliance/baa/99999", headers=AUTH_HEADERS)
        assert resp.status_code == 404

    def test_baa_status_missing_vendors(self, client):
        resp = client.get(
            "/api/compliance/baa/status",
            params={"clinic_id": "api-clinic-empty"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["hipaa_ready"] is False
        assert len(data["vendors"]) == 5  # 5 required vendors
        assert "missing" in data["message"].lower() or "HIPAA-ready" in data["message"]

    def test_baa_status_all_signed(self, client):
        """When all required vendors have signed BAAs."""
        clinic = "api-clinic-full"
        for vendor in ["Supabase", "Telnyx", "Deepgram", "Azure OpenAI", "DigitalOcean"]:
            client.post("/api/compliance/baa", json={
                "clinic_id": clinic,
                "vendor_name": vendor,
                "baa_status": "signed",
            }, headers=AUTH_HEADERS)
        resp = client.get(
            "/api/compliance/baa/status",
            params={"clinic_id": clinic},
            headers=AUTH_HEADERS,
        )
        data = resp.json()
        assert data["hipaa_ready"] is True

    def test_baa_requires_auth(self, client):
        resp = client.get("/api/compliance/baa", params={"clinic_id": "x"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 5. Retention Policy API Routes
# ---------------------------------------------------------------------------

class TestRetentionRoutes:

    def test_get_default_policy(self, client):
        resp = client.get(
            "/api/compliance/retention",
            params={"clinic_id": "ret-api-1"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_default"] is True
        assert data["call_recording_days"] == 90

    def test_upsert_policy(self, client):
        resp = client.put("/api/compliance/retention", json={
            "clinic_id": "ret-api-2",
            "call_recording_days": 30,
            "call_transcript_days": 180,
            "patient_data_days": 2555,
            "audit_log_days": 2555,
        }, headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["policy"]["call_recording_days"] == 30

    def test_update_existing_policy(self, client):
        # Create
        client.put("/api/compliance/retention", json={
            "clinic_id": "ret-api-3",
            "call_recording_days": 60,
            "call_transcript_days": 365,
            "patient_data_days": 2555,
            "audit_log_days": 2555,
        }, headers=AUTH_HEADERS)
        # Update
        resp = client.put("/api/compliance/retention", json={
            "clinic_id": "ret-api-3",
            "call_recording_days": 120,
            "call_transcript_days": 365,
            "patient_data_days": 2555,
            "audit_log_days": 2555,
        }, headers=AUTH_HEADERS)
        assert resp.json()["policy"]["call_recording_days"] == 120

    def test_retention_requires_auth(self, client):
        resp = client.get("/api/compliance/retention", params={"clinic_id": "x"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 6. Data Deletion Request API Routes
# ---------------------------------------------------------------------------

class TestDeletionRoutes:

    def test_create_request(self, client):
        resp = client.post("/api/compliance/deletion-request", json={
            "clinic_id": "del-api-1",
            "patient_identifier": "hash-patient-abc",
            "requested_by": "admin@clinic.com",
            "reason": "Patient requested removal",
        }, headers=AUTH_HEADERS)
        assert resp.status_code == 201
        data = resp.json()
        assert data["ok"] is True
        assert data["status"] == "pending"

    def test_list_requests(self, client):
        # Create one first
        client.post("/api/compliance/deletion-request", json={
            "clinic_id": "del-api-2",
            "patient_identifier": "hash-patient-xyz",
            "requested_by": "admin@clinic.com",
        }, headers=AUTH_HEADERS)
        resp = client.get(
            "/api/compliance/deletion-request",
            params={"clinic_id": "del-api-2"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1

    def test_execute_deletion(self, client):
        resp = client.post("/api/compliance/deletion-request", json={
            "clinic_id": "del-api-3",
            "patient_identifier": "hash-exec",
            "requested_by": "admin@clinic.com",
        }, headers=AUTH_HEADERS)
        req_id = resp.json()["request_id"]
        resp = client.post(
            f"/api/compliance/deletion-request/{req_id}/execute",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert "call_recordings" in data["data_types_deleted"]

    def test_execute_already_completed(self, client):
        resp = client.post("/api/compliance/deletion-request", json={
            "clinic_id": "del-api-4",
            "patient_identifier": "hash-double",
            "requested_by": "admin@clinic.com",
        }, headers=AUTH_HEADERS)
        req_id = resp.json()["request_id"]
        client.post(f"/api/compliance/deletion-request/{req_id}/execute", headers=AUTH_HEADERS)
        # Second execution should fail
        resp = client.post(
            f"/api/compliance/deletion-request/{req_id}/execute",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 409

    def test_execute_nonexistent(self, client):
        resp = client.post(
            "/api/compliance/deletion-request/99999/execute",
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 404

    def test_deletion_requires_auth(self, client):
        resp = client.get("/api/compliance/deletion-request", params={"clinic_id": "x"})
        assert resp.status_code == 401

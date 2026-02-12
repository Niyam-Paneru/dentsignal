"""
test_phi_encryption.py — AG-8 PHI Field-Level Encryption Tests

Tests for:
1. EncryptedType TypeDecorator (transparent encrypt/decrypt)
2. phi_hash deterministic hashing
3. Hash-based lookups on encrypted fields
4. Event listeners auto-computing hash columns
5. Roundtrip: create → commit → reload → read
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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine():
    """Create a fresh in-memory SQLite engine for encryption tests."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Import models AFTER env is set (conftest.py sets ENCRYPTION_KEY)
    from db import (
        Lead, Patient, InboundCall, Appointment, PatientRecall,
        Client, UploadBatch,
    )
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    """Yield a session per test, rolled back after."""
    with Session(engine) as sess:
        yield sess
        sess.rollback()


@pytest.fixture
def seed_client(session):
    """Create the prerequisite Client + UploadBatch rows."""
    from db import Client, UploadBatch
    client = Client(
        name="Test Clinic", email="clinic@test.com",
        hashed_password="hashed", twilio_number="+10000000000",
    )
    session.add(client)
    session.flush()

    batch = UploadBatch(client_id=client.id)
    session.add(batch)
    session.flush()
    return client, batch


# ---------------------------------------------------------------------------
# EncryptedType — transparent roundtrip
# ---------------------------------------------------------------------------

class TestEncryptedTypeRoundtrip:
    """Verify that PHI fields are encrypted at rest and decrypted on read."""

    def test_lead_phone_roundtrip(self, session, seed_client):
        from db import Lead
        _client, batch = seed_client

        lead = Lead(batch_id=batch.id, name="Alice Smith", phone="+15551234567", consent=True)
        session.add(lead)
        session.commit()

        # Reload from DB
        session.expire(lead)
        reloaded = session.get(Lead, lead.id)
        assert reloaded.phone == "+15551234567"
        assert reloaded.name == "Alice Smith"

    def test_lead_email_roundtrip(self, session, seed_client):
        from db import Lead
        _client, batch = seed_client

        lead = Lead(
            batch_id=batch.id, name="Bob", phone="+15550000001",
            email="bob@example.com", consent=True,
        )
        session.add(lead)
        session.commit()
        session.expire(lead)

        reloaded = session.get(Lead, lead.id)
        assert reloaded.email == "bob@example.com"

    def test_patient_roundtrip(self, session, seed_client):
        from db import Patient
        client, _ = seed_client

        patient = Patient(
            clinic_id=client.id, first_name="Carol", last_name="Davis",
            phone="+15559998877", email="carol@test.com",
        )
        session.add(patient)
        session.commit()
        session.expire(patient)

        reloaded = session.get(Patient, patient.id)
        assert reloaded.first_name == "Carol"
        assert reloaded.last_name == "Davis"
        assert reloaded.phone == "+15559998877"
        assert reloaded.email == "carol@test.com"

    def test_inbound_call_roundtrip(self, session, seed_client):
        from db import InboundCall
        client, _ = seed_client

        call = InboundCall(
            clinic_id=client.id, from_number="+15553334444",
            to_number="+18005551234", twilio_call_sid="CA_test_roundtrip_001",
            caller_name="Dave Johnson",
        )
        session.add(call)
        session.commit()
        session.expire(call)

        reloaded = session.get(InboundCall, call.id)
        assert reloaded.from_number == "+15553334444"
        assert reloaded.caller_name == "Dave Johnson"

    def test_appointment_roundtrip(self, session, seed_client):
        from db import Appointment
        client, _ = seed_client

        appt = Appointment(
            clinic_id=client.id, scheduled_time=datetime(2025, 6, 15, 10, 0),
            patient_name="Eve Martin", patient_phone="+15557778888",
            patient_email="eve@test.com",
        )
        session.add(appt)
        session.commit()
        session.expire(appt)

        reloaded = session.get(Appointment, appt.id)
        assert reloaded.patient_name == "Eve Martin"
        assert reloaded.patient_phone == "+15557778888"
        assert reloaded.patient_email == "eve@test.com"

    def test_recall_roundtrip(self, session, seed_client):
        from db import PatientRecall
        client, _ = seed_client

        recall = PatientRecall(
            clinic_id=client.id, patient_name="Frank Lee",
            patient_phone="+15551112233", patient_email="frank@test.com",
            due_date=datetime(2025, 7, 1),
        )
        session.add(recall)
        session.commit()
        session.expire(recall)

        reloaded = session.get(PatientRecall, recall.id)
        assert reloaded.patient_name == "Frank Lee"
        assert reloaded.patient_phone == "+15551112233"
        assert reloaded.patient_email == "frank@test.com"

    def test_none_values_passthrough(self, session, seed_client):
        """NULL fields should stay NULL, not become encrypted empty strings."""
        from db import Lead
        _client, batch = seed_client

        lead = Lead(batch_id=batch.id, name="NoEmail", phone="+15550000002", consent=True)
        session.add(lead)
        session.commit()
        session.expire(lead)

        reloaded = session.get(Lead, lead.id)
        assert reloaded.email is None


# ---------------------------------------------------------------------------
# Data at rest is actually ciphertext
# ---------------------------------------------------------------------------

class TestDataAtRest:
    """Verify that the raw DB values are NOT plaintext."""

    def test_raw_phone_is_ciphertext(self, session, seed_client):
        from db import Lead
        from sqlalchemy import text
        _client, batch = seed_client

        lead = Lead(batch_id=batch.id, name="RawTest", phone="+15559876543", consent=True)
        session.add(lead)
        session.commit()

        # Read raw value bypassing ORM
        raw = session.execute(
            text("SELECT phone FROM leads WHERE id = :id"), {"id": lead.id}
        ).scalar()

        # Raw value should NOT be the plaintext phone
        assert raw != "+15559876543", "Phone stored in plaintext — encryption not working!"
        # It should be a long Fernet token
        assert len(raw) > 40, f"Encrypted value too short: {raw}"

    def test_raw_name_is_ciphertext(self, session, seed_client):
        from db import Lead
        from sqlalchemy import text
        _client, batch = seed_client

        lead = Lead(batch_id=batch.id, name="SecretName", phone="+15550000003", consent=True)
        session.add(lead)
        session.commit()

        raw = session.execute(
            text("SELECT name FROM leads WHERE id = :id"), {"id": lead.id}
        ).scalar()
        assert raw != "SecretName", "Name stored in plaintext — encryption not working!"


# ---------------------------------------------------------------------------
# phi_hash — deterministic hashing
# ---------------------------------------------------------------------------

class TestPhiHash:
    """Test the deterministic hashing function."""

    def test_deterministic(self):
        from encryption import phi_hash
        h1 = phi_hash("+15551234567")
        h2 = phi_hash("+15551234567")
        assert h1 == h2

    def test_case_insensitive(self):
        from encryption import phi_hash
        assert phi_hash("Alice@Example.Com") == phi_hash("alice@example.com")

    def test_strips_whitespace(self):
        from encryption import phi_hash
        assert phi_hash("  +15551234567  ") == phi_hash("+15551234567")

    def test_empty_returns_empty(self):
        from encryption import phi_hash
        assert phi_hash("") == ""
        assert phi_hash(None) == ""

    def test_different_values_different_hashes(self):
        from encryption import phi_hash
        assert phi_hash("+15551111111") != phi_hash("+15552222222")

    def test_hash_length(self):
        from encryption import phi_hash
        h = phi_hash("+15551234567")
        assert len(h) == 64, f"Expected 64-char hex digest, got {len(h)}"


# ---------------------------------------------------------------------------
# Event listeners — auto-computed hash columns
# ---------------------------------------------------------------------------

class TestHashAutoCompute:
    """Verify event listeners auto-populate hash columns on insert/update."""

    def test_lead_hashes_on_insert(self, session, seed_client):
        from db import Lead
        from encryption import phi_hash
        _client, batch = seed_client

        lead = Lead(batch_id=batch.id, name="HashTest", phone="+15550001111", email="hash@test.com", consent=True)
        session.add(lead)
        session.commit()
        session.expire(lead)

        reloaded = session.get(Lead, lead.id)
        assert reloaded.phone_hash == phi_hash("+15550001111")
        assert reloaded.email_hash == phi_hash("hash@test.com")

    def test_patient_hashes_on_insert(self, session, seed_client):
        from db import Patient
        from encryption import phi_hash
        client, _ = seed_client

        patient = Patient(
            clinic_id=client.id, first_name="Hash", last_name="Patient",
            phone="+15550002222", email="hp@test.com",
        )
        session.add(patient)
        session.commit()
        session.expire(patient)

        reloaded = session.get(Patient, patient.id)
        assert reloaded.phone_hash == phi_hash("+15550002222")
        assert reloaded.email_hash == phi_hash("hp@test.com")

    def test_inbound_call_hash_on_insert(self, session, seed_client):
        from db import InboundCall
        from encryption import phi_hash
        client, _ = seed_client

        call = InboundCall(
            clinic_id=client.id, from_number="+15550003333",
            to_number="+18005551234", twilio_call_sid="CA_hash_test_001",
        )
        session.add(call)
        session.commit()
        session.expire(call)

        reloaded = session.get(InboundCall, call.id)
        assert reloaded.from_number_hash == phi_hash("+15550003333")

    def test_appointment_hash_on_insert(self, session, seed_client):
        from db import Appointment
        from encryption import phi_hash
        client, _ = seed_client

        appt = Appointment(
            clinic_id=client.id, scheduled_time=datetime(2025, 7, 1, 9, 0),
            patient_phone="+15550004444",
        )
        session.add(appt)
        session.commit()
        session.expire(appt)

        reloaded = session.get(Appointment, appt.id)
        assert reloaded.patient_phone_hash == phi_hash("+15550004444")

    def test_recall_hash_on_insert(self, session, seed_client):
        from db import PatientRecall
        from encryption import phi_hash
        client, _ = seed_client

        recall = PatientRecall(
            clinic_id=client.id, patient_name="Recall Hash",
            patient_phone="+15550005555", due_date=datetime(2025, 8, 1),
        )
        session.add(recall)
        session.commit()
        session.expire(recall)

        reloaded = session.get(PatientRecall, recall.id)
        assert reloaded.patient_phone_hash == phi_hash("+15550005555")

    def test_none_phone_hash_empty(self, session, seed_client):
        """When patient_phone is None, hash should be None (Appointment)."""
        from db import Appointment
        client, _ = seed_client

        appt = Appointment(
            clinic_id=client.id, scheduled_time=datetime(2025, 7, 2, 10, 0),
        )
        session.add(appt)
        session.commit()
        session.expire(appt)

        reloaded = session.get(Appointment, appt.id)
        assert reloaded.patient_phone_hash is None


# ---------------------------------------------------------------------------
# Hash-based lookups (the whole point of hash columns)
# ---------------------------------------------------------------------------

class TestHashLookups:
    """Verify that WHERE phone_hash = phi_hash(value) finds the right rows."""

    def test_lead_lookup_by_phone_hash(self, session, seed_client):
        from db import Lead
        from encryption import phi_hash
        _client, batch = seed_client

        lead = Lead(batch_id=batch.id, name="Lookup", phone="+15556667777", consent=True)
        session.add(lead)
        session.commit()

        found = session.exec(
            select(Lead).where(Lead.phone_hash == phi_hash("+15556667777"))
        ).first()
        assert found is not None
        assert found.phone == "+15556667777"

    def test_patient_lookup_by_phone_hash(self, session, seed_client):
        from db import Patient
        from encryption import phi_hash
        client, _ = seed_client

        patient = Patient(
            clinic_id=client.id, first_name="Lookup", last_name="Patient",
            phone="+15558889999",
        )
        session.add(patient)
        session.commit()

        found = session.exec(
            select(Patient)
            .where(Patient.clinic_id == client.id)
            .where(Patient.phone_hash == phi_hash("+15558889999"))
        ).first()
        assert found is not None
        assert found.phone == "+15558889999"

    def test_appointment_lookup_by_phone_hash(self, session, seed_client):
        from db import Appointment
        from encryption import phi_hash
        client, _ = seed_client

        appt = Appointment(
            clinic_id=client.id, scheduled_time=datetime(2025, 7, 3, 11, 0),
            patient_phone="+15551119999",
        )
        session.add(appt)
        session.commit()

        found = session.exec(
            select(Appointment).where(
                Appointment.patient_phone_hash == phi_hash("+15551119999")
            )
        ).first()
        assert found is not None
        assert found.patient_phone == "+15551119999"

    def test_no_match_returns_none(self, session, seed_client):
        from db import Lead
        from encryption import phi_hash
        _client, batch = seed_client

        lead = Lead(batch_id=batch.id, name="NoMatch", phone="+15550000099", consent=True)
        session.add(lead)
        session.commit()

        found = session.exec(
            select(Lead).where(Lead.phone_hash == phi_hash("+19999999999"))
        ).first()
        assert found is None

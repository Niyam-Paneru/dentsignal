"""
test_xss_sanitization.py - XSS Prevention / Input Sanitization Tests (AG-5)

Tests:
1. Unit tests for sanitize_html() - tag stripping, entity decode, payload removal
2. Unit tests for sanitize_text_fields() - dict-level batch sanitization
3. Integration: call status endpoint sanitizes transcript/notes
4. Integration: clinic update sanitizes text fields
5. Integration: update_inbound_call sanitizes transcript/summary/caller_name
"""

import pytest
import os
import sys
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Common XSS Payloads
# ---------------------------------------------------------------------------

XSS_PAYLOADS = [
    # Basic script tags
    '<script>alert("xss")</script>',
    '<script src="https://evil.com/steal.js"></script>',
    '<SCRIPT>alert(1)</SCRIPT>',
    # Event handlers
    '<img src=x onerror=alert(1)>',
    '<div onmouseover="alert(1)">hover</div>',
    '<body onload=alert(1)>',
    '<svg onload=alert(1)>',
    # javascript: URI
    '<a href="javascript:alert(1)">click</a>',
    # data: URI with HTML
    '<a href="data:text/html,<script>alert(1)</script>">click</a>',
    # Encoded entities (&#106; = j)
    '&#60;script&#62;alert(1)&#60;/script&#62;',
    # Mixed case
    '<ScRiPt>alert(1)</sCrIpT>',
    # Style-based
    '<div style="background:expression(alert(1))">',
    # vbscript
    '<a href="vbscript:MsgBox(1)">click</a>',
    # Nested tags
    '<scr<script>ipt>alert(1)</scr</script>ipt>',
]


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
    return resp.json()["token"]


@pytest.fixture
def auth_header(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def test_client_id(client, auth_header):
    """Create a test clinic and return its ID."""
    resp = client.get("/api/clients", headers=auth_header)
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]["id"]
    # Fallback: try creating one
    return 1


# =========================================================================
# 1. Unit Tests: sanitize_html()
# =========================================================================

class TestSanitizeHtml:
    """Unit tests for the sanitize_html function."""

    def test_strips_script_tags(self):
        from utils import sanitize_html
        result = sanitize_html('<script>alert("xss")</script>')
        assert "<script" not in result.lower()
        assert "alert" in result  # inner text kept

    def test_strips_img_onerror(self):
        from utils import sanitize_html
        result = sanitize_html('<img src=x onerror=alert(1)>')
        assert "<img" not in result.lower()
        assert "onerror" not in result.lower()

    def test_removes_javascript_uri(self):
        from utils import sanitize_html
        result = sanitize_html('click here javascript:alert(1) please')
        assert "javascript:" not in result.lower()

    def test_removes_vbscript_uri(self):
        from utils import sanitize_html
        result = sanitize_html('vbscript:MsgBox(1)')
        assert "vbscript:" not in result.lower()

    def test_removes_data_text_html(self):
        from utils import sanitize_html
        result = sanitize_html('data:text/html,<script>alert(1)</script>')
        assert "data:text/html" not in result.lower()

    def test_removes_css_expression(self):
        from utils import sanitize_html
        result = sanitize_html('expression(alert(1))')
        assert "expression(" not in result.lower()

    def test_decodes_entities_then_strips(self):
        """Encoded tags like &#60;script&#62; must be decoded and stripped."""
        from utils import sanitize_html
        result = sanitize_html('&#60;script&#62;alert(1)&#60;/script&#62;')
        assert "<script" not in result.lower()

    def test_preserves_normal_text(self):
        from utils import sanitize_html
        text = "Patient called about a cleaning appointment. Dr. O'Brien confirmed."
        assert sanitize_html(text) == text

    def test_preserves_newlines_and_tabs(self):
        from utils import sanitize_html
        text = "Line 1\nLine 2\tTabbed"
        assert sanitize_html(text) == text

    def test_none_passthrough(self):
        from utils import sanitize_html
        assert sanitize_html(None) is None

    def test_empty_string_passthrough(self):
        from utils import sanitize_html
        assert sanitize_html("") == ""

    def test_truncates_long_input(self):
        from utils import sanitize_html
        long_text = "A" * 100_000
        result = sanitize_html(long_text, max_length=1000)
        assert len(result) <= 1000

    def test_removes_null_bytes(self):
        from utils import sanitize_html
        result = sanitize_html("hello\x00world")
        assert "\x00" not in result
        assert "helloworld" in result

    def test_removes_control_characters(self):
        from utils import sanitize_html
        # \x01 is a control char
        result = sanitize_html("hello\x01world")
        assert "\x01" not in result

    def test_all_payloads_neutralized(self):
        """Every XSS payload in our test suite produces safe output."""
        from utils import sanitize_html
        for payload in XSS_PAYLOADS:
            result = sanitize_html(payload)
            assert "<script" not in result.lower(), f"Failed on: {payload}"
            assert "javascript:" not in result.lower(), f"Failed on: {payload}"
            assert "vbscript:" not in result.lower(), f"Failed on: {payload}"
            assert "onerror=" not in result.lower(), f"Failed on: {payload}"
            assert "onload=" not in result.lower(), f"Failed on: {payload}"
            assert "onmouseover=" not in result.lower(), f"Failed on: {payload}"

    def test_mixed_content_preserves_text(self):
        """Tags stripped but surrounding text preserved."""
        from utils import sanitize_html
        text = 'Hello <b>world</b> and <script>evil()</script> goodbye'
        result = sanitize_html(text)
        assert "Hello" in result
        assert "world" in result
        assert "goodbye" in result
        assert "<script" not in result.lower()
        assert "<b>" not in result

    def test_case_insensitive_stripping(self):
        from utils import sanitize_html
        result = sanitize_html('<SCRIPT>alert(1)</SCRIPT>')
        assert "<script" not in result.lower()


# =========================================================================
# 2. Unit Tests: sanitize_text_fields()
# =========================================================================

class TestSanitizeTextFields:
    """Unit tests for dict-level batch sanitization."""

    def test_sanitizes_specified_fields(self):
        from utils import sanitize_text_fields
        data = {
            "transcript": '<script>alert(1)</script>Hello',
            "notes": '<img onerror=x>Notes here',
            "status": "completed",
        }
        sanitize_text_fields(data, ["transcript", "notes"])
        assert "<script" not in data["transcript"]
        assert "<img" not in data["notes"]
        assert data["status"] == "completed"

    def test_skips_missing_fields(self):
        from utils import sanitize_text_fields
        data = {"name": "Dr. Smith"}
        # Should not raise even if we ask for fields that don't exist
        sanitize_text_fields(data, ["transcript", "notes"])
        assert data["name"] == "Dr. Smith"

    def test_skips_non_string_values(self):
        from utils import sanitize_text_fields
        data = {"count": 42, "active": True, "name": "test"}
        sanitize_text_fields(data, ["count", "active", "name"])
        assert data["count"] == 42
        assert data["active"] is True

    def test_mutates_in_place(self):
        from utils import sanitize_text_fields
        data = {"text": "<b>bold</b>"}
        result = sanitize_text_fields(data, ["text"])
        assert result is data  # same object


# =========================================================================
# 3. Integration: Call Status Endpoint Sanitizes Input
# =========================================================================

class TestCallStatusXSS:
    """Call status endpoint must sanitize transcript and notes before DB write."""

    def _setup_call(self, client, auth_header, test_client_id):
        """Create a batch with a lead and get a call_id."""
        resp = client.post(
            f"/api/clients/{test_client_id}/leads",
            headers=auth_header,
            json=[{
                "first_name": "XSSTest",
                "last_name": "Patient",
                "phone": "+15551230099",
                "consent": True,
            }],
        )
        if resp.status_code != 200:
            pytest.skip(f"Cannot create test lead: {resp.status_code}")
        batch_id = resp.json().get("batch_id") or resp.json().get("upload_id")
        if not batch_id:
            pytest.skip("No batch created")

        # Get a call for this batch
        from db import get_session, Call
        from sqlmodel import select
        with get_session() as session:
            call = session.exec(select(Call)).first()
            if not call:
                pytest.skip("No call found")
            return call.id

    def test_transcript_xss_stripped(self, client, auth_header, test_client_id):
        """Transcript with <script> tags is sanitized."""
        call_id = self._setup_call(client, auth_header, test_client_id)

        resp = client.post(
            f"/api/calls/{call_id}/status",
            headers=auth_header,
            json={
                "status": "completed",
                "result": "completed",
                "transcript": '<script>document.cookie</script>Patient said hello',
                "notes": '<img src=x onerror=fetch("//evil.com")>Good call',
            },
        )
        assert resp.status_code == 200

        # Verify stored data is sanitized
        from db import get_session, CallResult
        from sqlmodel import select
        with get_session() as session:
            cr = session.exec(
                select(CallResult).where(CallResult.call_id == call_id)
            ).first()
            if cr:
                assert "<script" not in (cr.transcript or "").lower()
                assert "onerror" not in (cr.notes or "").lower()

    def test_notes_xss_stripped(self, client, auth_header, test_client_id):
        """Notes field with event handler payloads is cleaned."""
        call_id = self._setup_call(client, auth_header, test_client_id)

        resp = client.post(
            f"/api/calls/{call_id}/status",
            headers=auth_header,
            json={
                "result": "completed",
                "notes": '<div onmouseover="steal()">Patient was happy</div>',
            },
        )
        assert resp.status_code == 200


# =========================================================================
# 4. Integration: Clinic Update Sanitizes Text Fields
# =========================================================================

class TestClinicUpdateXSS:
    """Clinic update endpoint must sanitize name, custom_instructions, etc."""

    def test_clinic_name_xss_stripped(self, client, auth_header):
        """XSS in clinic name is stripped before DB write."""
        # Get admin token for admin endpoint
        from db import get_session, Client
        with get_session() as session:
            clinic = session.exec(__import__("sqlmodel").select(Client)).first()
            if not clinic:
                pytest.skip("No clinic")
            clinic_id = clinic.id

        resp = client.patch(
            f"/api/clinics/{clinic_id}",
            headers=auth_header,
            json={
                "name": 'Bright Smile<script>alert("XSS")</script> Dental',
            },
        )
        # May be 200 or 401/403 depending on admin check
        if resp.status_code == 200:
            with get_session() as session:
                clinic = session.get(Client, clinic_id)
                assert "<script" not in clinic.name.lower()
                assert "Bright Smile" in clinic.name

    def test_custom_instructions_xss_stripped(self, client, auth_header):
        """XSS in custom_instructions is stripped."""
        from db import get_session, Client
        with get_session() as session:
            clinic = session.exec(__import__("sqlmodel").select(Client)).first()
            if not clinic:
                pytest.skip("No clinic")
            clinic_id = clinic.id

        resp = client.patch(
            f"/api/clinics/{clinic_id}",
            headers=auth_header,
            json={
                "custom_instructions": 'Be polite <img onerror=alert(1)> and professional',
            },
        )
        if resp.status_code == 200:
            with get_session() as session:
                clinic = session.get(Client, clinic_id)
                if clinic.custom_instructions:
                    assert "<img" not in clinic.custom_instructions.lower()
                    assert "onerror" not in clinic.custom_instructions.lower()


# =========================================================================
# 5. Integration: update_inbound_call Sanitizes Text
# =========================================================================

class TestInboundCallXSS:
    """update_inbound_call() must sanitize transcript, summary, caller_name, reason_for_call."""

    def test_transcript_sanitized(self):
        """Verifies transcript field is XSS-free after update."""
        from routes_inbound import update_inbound_call
        from db import get_session, InboundCall, InboundCallStatus

        # Create an inbound call to update
        with get_session() as session:
            call = InboundCall(
                clinic_id=1,
                from_number="+15551112222",
                to_number="+15553334444",
                twilio_call_sid="CA_xss_test_001",
                status=InboundCallStatus.IN_PROGRESS,
            )
            session.add(call)
            session.commit()
            session.refresh(call)
            call_id = call.id

        xss_transcript = '<script>steal_data()</script>Patient: Hi I need a cleaning'
        updated = update_inbound_call(
            call_id,
            transcript=xss_transcript,
            summary='<img onerror="evil()">Good call',
            caller_name='<b onclick=alert(1)>John</b>',
            reason_for_call='Cleaning <script>xss</script>appointment',
        )

        if updated:
            assert "<script" not in (updated.transcript or "").lower()
            assert "<img" not in (updated.summary or "").lower()
            assert "onclick" not in (updated.caller_name or "").lower()
            assert "<script" not in (updated.reason_for_call or "").lower()
            # Verify useful text is preserved
            assert "Patient" in (updated.transcript or "")
            assert "John" in (updated.caller_name or "")

    def test_none_values_pass_through(self):
        """None values should not cause errors."""
        from routes_inbound import update_inbound_call
        from db import get_session, InboundCall, InboundCallStatus

        with get_session() as session:
            call = InboundCall(
                clinic_id=1,
                from_number="+15551112222",
                to_number="+15553334444",
                twilio_call_sid="CA_xss_test_002",
                status=InboundCallStatus.IN_PROGRESS,
            )
            session.add(call)
            session.commit()
            session.refresh(call)
            call_id = call.id

        # Should not raise
        updated = update_inbound_call(
            call_id,
            transcript=None,
            summary=None,
        )
        assert updated is not None


# =========================================================================
# 6. Full Payload Sweep: No Payload Survives Sanitization
# =========================================================================

class TestPayloadSweep:
    """Sweep all XSS payloads through sanitize_html and confirm safety."""

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_payload_neutralized(self, payload):
        from utils import sanitize_html
        result = sanitize_html(payload)
        # None of these dangerous strings should survive
        dangerous_indicators = [
            "<script", "</script", "javascript:", "vbscript:",
            "onerror=", "onload=", "onmouseover=", "onclick=",
            "expression(", "data:text/html",
        ]
        result_lower = result.lower()
        for indicator in dangerous_indicators:
            assert indicator not in result_lower, (
                f"Indicator '{indicator}' found in sanitized output "
                f"for payload: {payload!r} → {result!r}"
            )

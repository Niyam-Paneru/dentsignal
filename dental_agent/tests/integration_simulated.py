"""
integration_simulated.py - Integration Tests with Simulated Calls

Tests the full flow:
1. Start FastAPI app in test client mode
2. Upload leads via API
3. Run agent worker to process calls
4. Verify call results are saved

Uses pytest and TestClient. All calls are simulated (no external network).
"""

import pytest
import threading
import time
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_db_url():
    """Use in-memory SQLite for tests."""
    return "sqlite:///:memory:"


@pytest.fixture(scope="module")
def app(test_db_url):
    """Create FastAPI app with test database."""
    # Set environment before importing
    os.environ["DATABASE_URL"] = test_db_url
    os.environ["JWT_SECRET"] = "DentSignal_Pytest2026!ValidKey@XyZ99"
    os.environ["ENABLE_DEMO_USER"] = "1"
    os.environ["DEMO_USER_PASSWORD"] = "admin123"
    os.environ["DISABLE_RATE_LIMIT"] = "1"
    
    # Import after setting env
    from api_main import app
    
    return app


@pytest.fixture(scope="module")
def client(app):
    """Create test client."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def auth_token(client):
    """Get auth token for API calls."""
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@dental-demo.com", "password": "admin123"}
    )
    assert response.status_code == 200
    return response.json()["token"]


@pytest.fixture
def auth_headers(auth_token):
    """Auth headers for API calls."""
    return {"Authorization": f"Bearer {auth_token}"}


# -----------------------------------------------------------------------------
# API Tests
# -----------------------------------------------------------------------------

class TestHealthCheck:
    """Test health endpoints."""
    
    def test_health_check(self, client):
        """Health endpoint should return ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self, client):
        """Root should return API info."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Dental AI Voice Agent API" in response.json()["name"]


class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_login_success(self, client):
        """Valid credentials should return token."""
        response = client.post(
            "/api/auth/login",
            json={"email": "admin@dental-demo.com", "password": "admin123"}
        )
        assert response.status_code == 200
        assert "token" in response.json()
    
    def test_login_invalid_password(self, client):
        """Invalid password should return 401."""
        response = client.post(
            "/api/auth/login",
            json={"email": "admin@dental-demo.com", "password": "wrongpassword"}
        )
    def test_login_invalid_email(self, client):
        """Unknown email should return 401."""
        response = client.post(
            "/api/auth/login",
            json={"email": "unknown@example.com", "password": "admin123"}
        )
        assert response.status_code == 401


class TestLeadUpload:
    """Test lead upload functionality."""
    
    def test_upload_json_leads(self, client, auth_headers):
        """Should accept JSON lead upload."""
        leads = {
            "leads": [
                {"name": "Alice Test", "phone": "+15551111111", "email": "alice@test.com"},
                {"name": "Bob Test", "phone": "+15552222222"},
                {"name": "Carol Test", "phone": "+15553333333", "notes": "Prefers morning"}
            ]
        }
        
        response = client.post(
            "/api/clients/1/leads",
            json=leads,
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["queued_count"] == 3
        assert "batch_id" in data
    
    def test_upload_requires_phone(self, client, auth_headers):
        """Should reject leads without phone."""
        leads = {
            "leads": [
                {"name": "No Phone", "phone": "", "email": "test@test.com"}
            ]
        }
        
        response = client.post(
            "/api/clients/1/leads",
            json=leads,
            headers=auth_headers,
        )
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_upload_invalid_client(self, client, auth_headers):
        """Should return 404 for invalid client."""
        leads = {
            "leads": [
                {"name": "Test", "phone": "+15551234567"}
            ]
        }
        
        response = client.post(
            "/api/clients/999/leads",
            json=leads,
            headers=auth_headers,
        )
        
        assert response.status_code == 404


class TestCallStatus:
    """Test call status update endpoint."""
    
    def test_update_call_status(self, client, auth_headers):
        """Should update call status."""
        # Create a call first
        leads = {"leads": [{"name": "Status Test", "phone": "+15551234567"}]}
        upload = client.post("/api/clients/1/leads", json=leads, headers=auth_headers)
        
        # Get the call ID (first call for this batch)
        batch_id = upload.json()["batch_id"]
        calls_response = client.get(f"/api/clients/1/batches/{batch_id}/calls", headers=auth_headers)
        call_id = calls_response.json()["calls"][0]["id"]
        
        # Update status
        update = {
            "status": "completed",
            "result": "booked",
            "transcript": "Test transcript",
            "notes": "Test notes"
        }
        
        response = client.post(f"/api/calls/{call_id}/status", json=update, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
    
    def test_update_nonexistent_call(self, client, auth_headers):
        """Should return 404 for nonexistent call."""
        update = {"status": "completed"}
        response = client.post("/api/calls/99999/status", json=update, headers=auth_headers)
        assert response.status_code == 404


class TestCallList:
    """Test call listing endpoint."""
    
    def test_list_batch_calls(self, client, auth_headers):
        """Should list calls for a batch."""
        # Create batch with leads
        leads = {
            "leads": [
                {"name": "List Test 1", "phone": "+15551111111"},
                {"name": "List Test 2", "phone": "+15552222222"},
            ]
        }
        upload = client.post("/api/clients/1/leads", json=leads, headers=auth_headers)
        batch_id = upload.json()["batch_id"]
        
        # List calls
        response = client.get(f"/api/clients/1/batches/{batch_id}/calls", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["calls"]) == 2
    
    def test_list_with_pagination(self, client, auth_headers):
        """Should respect limit and offset."""
        # Create batch with leads
        leads = {"leads": [{"name": f"Page Test {i}", "phone": f"+1555{i:07d}"} for i in range(5)]}
        upload = client.post("/api/clients/1/leads", json=leads, headers=auth_headers)
        batch_id = upload.json()["batch_id"]
        
        # Get with limit
        response = client.get(f"/api/clients/1/batches/{batch_id}/calls?limit=2&offset=0", headers=auth_headers)
        data = response.json()
        
        assert len(data["calls"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 0


# -----------------------------------------------------------------------------
# Integration Tests with Agent Worker
# -----------------------------------------------------------------------------

class TestAgentWorkerIntegration:
    """Test full integration with agent worker."""
    
    def test_worker_processes_queued_calls(self, client, auth_headers):
        """Worker should process queued calls and save results."""
        # 1. Upload leads
        leads = {
            "leads": [
                {"name": "Worker Test 1", "phone": "+15551234001"},
                {"name": "Worker Test 2", "phone": "+15551234002"},
                {"name": "Worker Test 3", "phone": "+15551234003"},
            ]
        }
        
        upload_response = client.post("/api/clients/1/leads", json=leads, headers=auth_headers)
        assert upload_response.status_code == 200
        
        batch_id = upload_response.json()["batch_id"]
        queued_count = upload_response.json()["queued_count"]
        assert queued_count == 3
        
        # 2. Verify calls are queued
        calls_response = client.get(f"/api/clients/1/batches/{batch_id}/calls", headers=auth_headers)
        initial_calls = calls_response.json()["calls"]
        assert all(c["status"] == "queued" for c in initial_calls)
        
        # 3. Run agent worker in background thread
        from agent_server import AgentSessionManager
        
        # Override API base URL to use test server
        manager = AgentSessionManager(
            api_base_url="http://testserver",  # DevSkim: ignore DS137138 - test fixture
            config_path=None,
        )
        
        # Process calls using the test client's app
        def process_calls():
            # We need to simulate what the worker does
            # but posting back through the test client
            from db import get_session, Call, Lead, CallStatus
            from sqlmodel import select
            
            with get_session() as session:
                stmt = select(Call).where(Call.batch_id == batch_id)
                calls = session.exec(stmt).all()
                
                for call in calls:
                    # Mark in progress
                    call.status = CallStatus.IN_PROGRESS
                    session.commit()
                    
                    # Get lead
                    lead = session.get(Lead, call.lead_id)
                    
                    # Simulate conversation
                    from agent_server import ConversationContext, ConversationFSM, run_simulated_conversation
                    
                    context = ConversationContext(
                        call_id=call.id,
                        lead_name=lead.name if lead else "Test",
                        lead_phone=lead.phone if lead else "",
                    )
                    fsm = ConversationFSM()
                    result, transcript, slot = run_simulated_conversation(context, fsm, seed=call.id)
                    
                    # Post result via API
                    update = {
                        "status": "completed",
                        "result": result.value,
                        "transcript": transcript,
                        "notes": "Processed by test worker"
                    }
                    if slot:
                        update["booked_slot"] = slot.isoformat()
                    
                    client.post(f"/api/calls/{call.id}/status", json=update, headers=auth_headers)
        
        # Run worker
        worker_thread = threading.Thread(target=process_calls)
        worker_thread.start()
        worker_thread.join(timeout=10)  # Wait max 10 seconds
        
        # 4. Verify calls are completed
        final_response = client.get(f"/api/clients/1/batches/{batch_id}/calls", headers=auth_headers)
        final_calls = final_response.json()["calls"]
        
        assert all(c["status"] == "completed" for c in final_calls)
        assert all(c["call_result"] is not None for c in final_calls)
    
    def test_call_results_have_transcripts(self, client, auth_headers):
        """Completed calls should have transcripts."""
        # Upload and process a call
        leads = {"leads": [{"name": "Transcript Test", "phone": "+15551234999"}]}
        upload = client.post("/api/clients/1/leads", json=leads, headers=auth_headers)
        batch_id = upload.json()["batch_id"]
        
        # Get call and update with result
        calls_response = client.get(f"/api/clients/1/batches/{batch_id}/calls", headers=auth_headers)
        call_id = calls_response.json()["calls"][0]["id"]
        
        # Simulate agent completion
        from agent_server import ConversationContext, ConversationFSM, run_simulated_conversation
        
        context = ConversationContext(call_id=call_id, lead_name="Transcript Test", lead_phone="+15551234999")
        fsm = ConversationFSM()
        result, transcript, slot = run_simulated_conversation(context, fsm, seed=call_id)
        
        update = {
            "result": result.value,
            "transcript": transcript,
        }
        client.post(f"/api/calls/{call_id}/status", json=update, headers=auth_headers)
        
        # Verify transcript
        final_response = client.get(f"/api/clients/1/batches/{batch_id}/calls", headers=auth_headers)
        call_result = final_response.json()["calls"][0]["call_result"]
        
        assert call_result is not None
        assert call_result["transcript"] is not None
        assert len(call_result["transcript"]) > 0


# -----------------------------------------------------------------------------
# CSV Upload Test
# -----------------------------------------------------------------------------

class TestCSVUpload:
    """Test CSV file upload."""
    
    def test_upload_csv_file(self, client, auth_headers):
        """Should accept CSV file upload."""
        csv_content = """name,phone,email,source_url,notes,consent
John CSV,+15551234567,john@csv.com,https://example.com,Test note,true
Jane CSV,+15559876543,jane@csv.com,,,true
Bob CSV,+15555555555,,,Morning preferred,true"""
        
        files = {"file": ("leads.csv", csv_content, "text/csv")}
        
        response = client.post("/api/clients/1/uploads", files=files, headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["queued_count"] == 3


class TestConsentIntegration:
    """Test TCPA consent enforcement in integration flow."""
    
    def test_consent_field_saved_on_lead(self, client, auth_headers):
        """Consent field should be saved on lead record."""
        from db import get_session, Lead
        from encryption import phi_hash
        from sqlmodel import select
        
        leads = {
            "leads": [
                {"name": "Consented Lead", "phone": "+15551112222", "consent": True},
            ]
        }
        
        response = client.post("/api/clients/1/leads", json=leads, headers=auth_headers)
        assert response.status_code == 200
        
        # Verify in database
        with get_session() as session:
            lead = session.exec(
                select(Lead).where(Lead.phone_hash == phi_hash("+15551112222"))
            ).first()
            assert lead is not None
            assert lead.consent == True
    
    def test_skipped_no_consent_returned_in_response(self, client, auth_headers):
        """Upload response should include skipped_no_consent count."""
        leads = {
            "leads": [
                {"name": "Lead 1", "phone": "+15551110001", "consent": True},
                {"name": "Lead 2", "phone": "+15551110002", "consent": True},
            ]
        }
        
        response = client.post("/api/clients/1/leads", json=leads, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "skipped_no_consent" in data
        # In SIMULATED mode, should be 0
        assert data["skipped_no_consent"] == 0


# -----------------------------------------------------------------------------
# Run Tests
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

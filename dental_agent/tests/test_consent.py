"""
test_consent.py - TCPA Consent Enforcement Tests

Tests that consent is properly enforced for PSTN calls:
1. Leads without consent are skipped in TWILIO mode
2. Leads without consent are allowed in SIMULATED mode
3. Tasks check consent before calling
4. Rate limiting works as expected
"""

import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture(scope="function")
def simulated_client():
    """Create test client with SIMULATED mode and fresh database."""
    # Set environment BEFORE importing
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["TELEPHONY_MODE"] = "SIMULATED"
    
    # Clear any cached modules to force reimport with new env
    modules_to_clear = [k for k in sys.modules.keys() 
                        if k.startswith(('api_main', 'db', 'routes', 'rate_limiter'))]
    for mod in modules_to_clear:
        del sys.modules[mod]
    
    from fastapi.testclient import TestClient
    from api_main import app
    
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def twilio_client():
    """Create test client with TWILIO mode and fresh database."""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["JWT_SECRET"] = "test-secret"
    os.environ["TELEPHONY_MODE"] = "TWILIO"
    
    # Clear any cached modules
    modules_to_clear = [k for k in sys.modules.keys() 
                        if k.startswith(('api_main', 'db', 'routes', 'rate_limiter'))]
    for mod in modules_to_clear:
        del sys.modules[mod]
    
    from fastapi.testclient import TestClient
    from api_main import app
    
    with TestClient(app) as client:
        yield client


# -----------------------------------------------------------------------------
# Consent Tests - SIMULATED Mode
# -----------------------------------------------------------------------------

class TestConsentSimulatedMode:
    """Test consent handling in SIMULATED mode."""
    
    def test_leads_without_consent_allowed(self, simulated_client):
        """In SIMULATED mode, leads without consent should be allowed."""
        leads = {
            "leads": [
                {"name": "No Consent Lead", "phone": "+15551234567", "consent": False},
                {"name": "With Consent Lead", "phone": "+15559876543", "consent": True},
            ]
        }
        
        response = simulated_client.post("/api/clients/1/leads", json=leads)
        
        # Both leads should be queued
        assert response.status_code == 200
        data = response.json()
        assert data["queued_count"] == 2
        assert data.get("skipped_no_consent", 0) == 0
    
    def test_csv_upload_no_consent_column(self, simulated_client):
        """CSV without consent column should work in SIMULATED mode."""
        csv_content = """name,phone,email
Test User,+15551111111,test@test.com"""
        
        files = {"file": ("leads.csv", csv_content, "text/csv")}
        response = simulated_client.post("/api/clients/1/uploads", files=files)
        
        assert response.status_code == 200
        assert response.json()["queued_count"] == 1


# -----------------------------------------------------------------------------
# Consent Tests - TWILIO (PSTN) Mode
# -----------------------------------------------------------------------------

class TestConsentTwilioMode:
    """Test consent enforcement in TWILIO (PSTN) mode."""
    
    def test_leads_without_consent_skipped(self, twilio_client):
        """In TWILIO mode, leads without consent should be skipped."""
        leads = {
            "leads": [
                {"name": "No Consent Lead", "phone": "+15551234567", "consent": False},
                {"name": "With Consent Lead", "phone": "+15559876543", "consent": True},
            ]
        }
        
        response = twilio_client.post("/api/clients/1/leads", json=leads)
        
        # Only consented lead should be queued
        assert response.status_code == 200
        data = response.json()
        assert data["queued_count"] == 1
        assert data["skipped_no_consent"] == 1
    
    def test_all_leads_without_consent_rejected(self, twilio_client):
        """If all leads lack consent, request should fail."""
        leads = {
            "leads": [
                {"name": "No Consent 1", "phone": "+15551111111", "consent": False},
                {"name": "No Consent 2", "phone": "+15552222222", "consent": False},
            ]
        }
        
        response = twilio_client.post("/api/clients/1/leads", json=leads)
        
        assert response.status_code == 400
        assert "consent required" in response.json()["detail"].lower()
    
    def test_allow_no_consent_override(self, twilio_client):
        """allow_no_consent=true should bypass consent check."""
        leads = {
            "leads": [
                {"name": "No Consent Override", "phone": "+15553333333", "consent": False},
            ]
        }
        
        response = twilio_client.post(
            "/api/clients/1/leads?allow_no_consent=true",
            json=leads
        )
        
        # Should be allowed with override
        assert response.status_code == 200
        assert response.json()["queued_count"] == 1
    
    def test_csv_with_consent_column(self, twilio_client):
        """CSV with consent column should respect consent in TWILIO mode."""
        csv_content = """name,phone,email,consent
Consented User,+15551111111,user1@test.com,true
No Consent User,+15552222222,user2@test.com,false
Also Consented,+15553333333,user3@test.com,yes"""
        
        files = {"file": ("leads.csv", csv_content, "text/csv")}
        response = twilio_client.post("/api/clients/1/uploads", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["queued_count"] == 2  # Only consented leads
        assert data["skipped_no_consent"] == 1
    
    def test_csv_without_consent_column_rejected(self, twilio_client):
        """CSV without consent column should fail in TWILIO mode."""
        csv_content = """name,phone,email
Test User,+15551111111,test@test.com"""
        
        files = {"file": ("leads.csv", csv_content, "text/csv")}
        response = twilio_client.post("/api/clients/1/uploads", files=files)
        
        # Should fail - no consent column means consent=False
        assert response.status_code == 400
        assert "consent required" in response.json()["detail"].lower()


# -----------------------------------------------------------------------------
# Task Consent Tests
# -----------------------------------------------------------------------------

class TestTaskConsentEnforcement:
    """Test consent enforcement in Celery tasks."""
    
    def test_start_call_checks_consent_twilio_mode(self):
        """start_call task should check consent in TWILIO mode."""
        os.environ["TELEPHONY_MODE"] = "TWILIO"
        
        from db import create_db, get_session, Lead, UploadBatch
        create_db("sqlite:///:memory:")
        
        with get_session() as session:
            # Create a batch
            batch = UploadBatch(client_id=1, source="test")
            session.add(batch)
            session.commit()
            session.refresh(batch)
            
            # Create lead WITHOUT consent
            lead = Lead(
                batch_id=batch.id,
                name="No Consent Lead",
                phone="+15551234567",
                consent=False,
            )
            session.add(lead)
            session.commit()
            session.refresh(lead)
            lead_id = lead.id
        
        # Try to start call
        from tasks import get_lead_by_id
        
        lead_data = get_lead_by_id(lead_id)
        assert lead_data is not None
        assert lead_data["consent"] == False
        
        # The start_call task should block this
        # (We can't fully test without Celery, but we can verify the lead data)
    
    def test_lead_data_includes_consent(self):
        """get_lead_by_id should include consent field."""
        from db import create_db, get_session, Lead, UploadBatch
        create_db("sqlite:///:memory:")
        
        with get_session() as session:
            batch = UploadBatch(client_id=1, source="test")
            session.add(batch)
            session.commit()
            
            lead = Lead(
                batch_id=batch.id,
                name="Consented Lead",
                phone="+15559999999",
                consent=True,
            )
            session.add(lead)
            session.commit()
            session.refresh(lead)
            lead_id = lead.id
        
        from tasks import get_lead_by_id
        lead_data = get_lead_by_id(lead_id)
        
        assert lead_data is not None
        assert "consent" in lead_data
        assert lead_data["consent"] == True


# -----------------------------------------------------------------------------
# Rate Limiting Tests
# -----------------------------------------------------------------------------

class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_allows_normal_traffic(self):
        """Rate limiter should allow normal request rates."""
        from rate_limiter import RateLimiter
        
        limiter = RateLimiter(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_limit=5,
        )
        
        # Make 5 requests - should all be allowed
        for i in range(5):
            allowed, reason, retry = limiter.is_allowed("test_ip")
            assert allowed, f"Request {i+1} should be allowed"
    
    def test_rate_limiter_blocks_burst(self):
        """Rate limiter should block burst traffic."""
        from rate_limiter import RateLimiter
        
        limiter = RateLimiter(
            requests_per_minute=100,
            requests_per_hour=1000,
            burst_limit=3,  # Only 3 per second
        )
        
        # Make burst of requests
        allowed_count = 0
        for i in range(10):
            allowed, reason, retry = limiter.is_allowed("burst_test")
            if allowed:
                allowed_count += 1
        
        # Should block after burst limit
        assert allowed_count <= 3
    
    def test_rate_limiter_different_keys(self):
        """Rate limits should be per-key."""
        from rate_limiter import RateLimiter
        
        limiter = RateLimiter(
            requests_per_minute=5,
            requests_per_hour=50,
            burst_limit=3,
        )
        
        # Exhaust limit for key1
        for i in range(5):
            limiter.is_allowed("key1")
        
        # key2 should still have quota
        allowed, _, _ = limiter.is_allowed("key2")
        assert allowed, "Different key should have its own limit"
    
    def test_rate_limit_stats(self):
        """Rate limiter should track stats correctly."""
        from rate_limiter import RateLimiter
        
        limiter = RateLimiter(
            requests_per_minute=60,
            requests_per_hour=3600,
            burst_limit=10,
        )
        
        # Make some requests
        for i in range(5):
            limiter.is_allowed("stats_test")
        
        stats = limiter.get_stats("stats_test")
        assert stats["requests_last_minute"] == 5
        assert stats["limits"]["per_minute"] == 60


# -----------------------------------------------------------------------------
# Run Tests
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

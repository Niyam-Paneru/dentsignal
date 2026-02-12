"""Quick debug script to test the upload endpoint."""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "DentSignal_Pytest2026!ValidKey@XyZ99")
os.environ.setdefault("TELEPHONY_MODE", "SIMULATED")
os.environ.setdefault("ENABLE_DEMO_USER", "1")
os.environ.setdefault("DEMO_USER_PASSWORD", "admin123")
os.environ.setdefault("DISABLE_RATE_LIMIT", "1")

from fastapi.testclient import TestClient
from api_main import app

with TestClient(app) as c:
    r = c.post("/api/auth/login", json={"email": "admin@dental-demo.com", "password": "admin123"})
    print(f"LOGIN: {r.status_code}")
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    r2 = c.post(
        "/api/clients/1/leads",
        json={"leads": [{"name": "OK", "phone": "+15559990001", "consent": True}]},
        headers=headers,
    )
    print(f"UPLOAD: {r2.status_code}")
    print(f"BODY: {r2.text[:500]}")

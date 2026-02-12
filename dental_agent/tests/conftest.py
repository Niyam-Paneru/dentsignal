# Pytest configuration and shared fixtures
import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set default test environment variables BEFORE any imports
# JWT_SECRET must be 32+ chars with upper, lower, digit, and special char
_TEST_JWT_SECRET = "DentSignal_Pytest2026!ValidKey@XyZ99"
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", _TEST_JWT_SECRET)
os.environ.setdefault("TELEPHONY_MODE", "SIMULATED")
os.environ.setdefault("DEEPGRAM_API_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("TWILIO_SID", "test-sid")
os.environ.setdefault("TWILIO_TOKEN", "test-token")
os.environ.setdefault("TWILIO_NUMBER", "+15551234567")
os.environ.setdefault("ENABLE_DEMO_USER", "1")
os.environ.setdefault("ENCRYPTION_KEY", "dGVzdC1lbmNyeXB0aW9uLWtleS1mb3ItdGVzdGluZw==")
os.environ.setdefault("DISABLE_BRUTE_FORCE", "1")  # AG-10: avoid lockout in unrelated tests


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment once for the entire test session."""
    # This runs once before all tests
    yield
    # Cleanup after all tests


@pytest.fixture(scope="function")
def clean_db():
    """Provide a clean in-memory database for each test."""
    from db import create_db, engine
    from sqlmodel import SQLModel
    
    # Create fresh tables
    SQLModel.metadata.create_all(engine)
    yield
    # Tables will be dropped when in-memory db connection closes

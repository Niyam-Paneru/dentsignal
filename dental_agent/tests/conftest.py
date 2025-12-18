# Pytest configuration and shared fixtures
import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set default test environment variables BEFORE any imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing")
os.environ.setdefault("TELEPHONY_MODE", "SIMULATED")
os.environ.setdefault("DEEPGRAM_API_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("TWILIO_SID", "test-sid")
os.environ.setdefault("TWILIO_TOKEN", "test-token")
os.environ.setdefault("TWILIO_NUMBER", "+15551234567")


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

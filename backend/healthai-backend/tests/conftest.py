import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use an in-memory SQLite database for tests
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_healthai.db")
os.environ.setdefault("JWT_SECRET", "test_secret_key_for_tests")
os.environ.setdefault("ANTHROPIC_API_KEY", "test_key")

from app.main import app
from app.db import Base, SessionLocal, engine as _prod_engine

TEST_DB_URL = "sqlite:///./test_healthai_pytest.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("test_healthai_pytest.db"):
        os.remove("test_healthai_pytest.db")


@pytest.fixture
def client():
    # Override DB dependency in all routers
    from app.db import SessionLocal as _SessionLocal
    from app import db as _db_module
    _db_module.SessionLocal = TestingSessionLocal
    with TestClient(app) as c:
        yield c
    _db_module.SessionLocal = _SessionLocal


@pytest.fixture
def registered_user(client):
    """Create a test user and return credentials."""
    payload = {"email": "testuser@example.com", "password": "Test123!", "plan": "premium"}
    resp = client.post("/auth/register", json=payload)
    if resp.status_code == 409:
        # Already registered, just login
        resp = client.post("/auth/login", json={"email": "testuser@example.com", "password": "Test123!"})
    return resp.json()


@pytest.fixture
def auth_headers(registered_user):
    token = registered_user["access_token"]
    return {"Authorization": f"Bearer {token}"}

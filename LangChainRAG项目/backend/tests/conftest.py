"""Shared fixtures for the backend test suite.

Creates a fresh SQLite temp-file database per test function and provides
a FastAPI TestClient with the 'get_db' dependency overridden so all
requests hit the test database rather than the production one.
"""

import sys
import os
import tempfile

# ── Ensure the backend/ package is importable ────────────────────────
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# ── Ensure the data/ directories exist so the *real* engine (created
#    at module level in database.py) doesn't choke when lifespan fires.
project_root = os.path.dirname(backend_dir)
os.makedirs(os.path.join(project_root, "data"), exist_ok=True)
os.makedirs(os.path.join(project_root, "data", "uploads"), exist_ok=True)
os.makedirs(os.path.join(project_root, "data", "chroma_db"), exist_ok=True)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from auth import hash_password, create_access_token
from models import User


# =====================================================================
# Function-scoped test database
# =====================================================================

@pytest.fixture
def test_db():
    """Create a brand-new SQLite database file for a single test.

    Returns a dict with keys ``engine``, ``Session``, and ``path`` so
    other fixtures (client, tokens) can share the same database.
    """
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield {"engine": engine, "Session": TestSession, "path": db_path}

    engine.dispose()
    try:
        os.unlink(db_path)
    except OSError:
        pass


# =====================================================================
# FastAPI TestClient with overridden get_db
# =====================================================================

@pytest.fixture
def client(test_db):
    """FastAPI TestClient that talks to the test database."""
    TestSession = test_db["Session"]

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as tc:
        yield tc

    app.dependency_overrides.clear()


# =====================================================================
# Auth helpers – direct DB access (bypass HTTP) for speed
# =====================================================================

def _create_user(session_factory, username: str, password: str, is_admin: bool = False):
    """Insert a user directly into the test DB and return (token, user_id)."""
    db = session_factory()
    try:
        user = User(
            username=username,
            password_hash=hash_password(password),
            is_admin=is_admin,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token({"sub": str(user.id)})
        return token, user.id
    finally:
        db.close()


@pytest.fixture
def admin_token(test_db):
    """JWT token for a pre-seeded admin user."""
    token, _ = _create_user(test_db["Session"], "admin", "123456", is_admin=True)
    return token


@pytest.fixture
def user_token(test_db):
    """JWT token for a freshly-created regular (non-admin) user."""
    import secrets
    username = f"testuser_{secrets.token_hex(4)}"
    token, uid = _create_user(test_db["Session"], username, "password123")
    return token

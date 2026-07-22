"""
Ready2Go CRM — Pytest Shared Configuration and Fixtures

Settings are overridden at module level BEFORE any application
modules are imported, ensuring the test configuration (SQLite
file-based database, test secret keys) is used consistently
across all tests.

Fixtures provided:
    setup_database (session)  — Create all tables on the module-level engine
    db_session                — Per-test transactional database session
    client                    — FastAPI TestClient with overridden get_db
    admin_user / employee_user — Test user records
    admin_token / employee_token — JWT tokens for test users
    admin_headers / employee_headers — Authorization header dicts
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# ── Ensure backend directory is on sys.path ──────
_backend_root = str(Path(__file__).resolve().parent.parent)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

# ── Override settings BEFORE any app imports ─────
# Create a temporary directory for the test database so it never
# collides with the real crm.db and gets cleaned up automatically.
_test_dir = Path(tempfile.mkdtemp(prefix="r2g_test_"))
_test_db_path = _test_dir / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-for-pytest-only"
os.environ["FRONTEND_URL"] = "http://test-frontend.local"
os.environ["SUPABASE_URL"] = "https://test.supabase.local"
os.environ["SUPABASE_KEY"] = "test-supabase-key-for-pytest-only"
os.environ["CRM_API_KEY"] = "test-crm-api-key-for-pytest-only"

# ── Now import application modules ──────────────
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import get_db, engine
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.constants.roles import ADMIN, EMPLOYEE

from main import app

# ── Prevent alembic migration on TestClient startup ──
# The startup event runs ``alembic upgrade head`` in a subprocess
# which conflicts with our fixture-based table creation (tables
# are already created by setup_database).  Clearing the handlers
# avoids noisy errors and prevents subprocess overhead on every
# test.
app.router.on_startup.clear()


# ── Pytest Hooks ─────────────────────────────────

def pytest_configure(config):
    """Register custom markers so --strict-markers never complains."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests that interact with external services",
    )


def pytest_sessionfinish(session, exitstatus):
    """Clean up the temporary test directory after the test session."""
    if _test_dir.exists():
        shutil.rmtree(_test_dir, ignore_errors=True)


# ── Database Fixtures ────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Create all schema objects on the module-level engine once per
    test session.  Because the engine is shared, code that obtains
    its own connection via SessionLocal() (e.g. the /ready endpoint)
    will see the same database.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_database):
    """
    Provide a database session within a transaction that is always
    rolled back, giving every test function a clean, isolated view.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="session")
def db_session_simple():
    """
    A session-scoped database session for use by session-scoped
    fixtures that need to set up data once before all tests.

    Use with caution — data created here persists across the whole
    session.  Prefer the function-scoped ``db_session`` for per-test
    setup.
    """
    connection = engine.connect()
    session = Session(bind=connection)
    yield session
    session.close()
    connection.close()


# ── TestClient Fixture ───────────────────────────

@pytest.fixture
def client(db_session):
    """
    FastAPI TestClient with the ``get_db`` dependency overridden so
    that every request made through the client uses the same
    transactional session that the test controls.
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Auth Helper Fixtures ─────────────────────────

_DEFAULT_PASSWORD = "testpass123"


@pytest.fixture
def admin_user(db_session):
    """Create and return a deactivated admin user for testing."""
    user = User(
        name="Admin User",
        email="admin@example.com",
        password_hash=hash_password(_DEFAULT_PASSWORD),
        role=ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    db_session.refresh(user)
    return user


@pytest.fixture
def employee_user(db_session):
    """Create and return a standard employee user for testing."""
    user = User(
        name="Employee User",
        email="employee@example.com",
        password_hash=hash_password(_DEFAULT_PASSWORD),
        role=EMPLOYEE,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    db_session.refresh(user)
    return user


@pytest.fixture
def deactivated_user(db_session):
    """Create a deactivated (is_active=False) user for auth-edge-case tests."""
    user = User(
        name="Deactivated User",
        email="deactivated@example.com",
        password_hash=hash_password(_DEFAULT_PASSWORD),
        role=EMPLOYEE,
        is_active=False,
    )
    db_session.add(user)
    db_session.flush()
    db_session.refresh(user)
    return user


# ── Token Fixtures ───────────────────────────────

@pytest.fixture
def admin_token(admin_user):
    """Return a valid JWT access token for the admin test user."""
    return create_access_token(
        subject=admin_user.id,
        role=admin_user.role,
        name=admin_user.name,
    )


@pytest.fixture
def employee_token(employee_user):
    """Return a valid JWT access token for the employee test user."""
    return create_access_token(
        subject=employee_user.id,
        role=employee_user.role,
        name=employee_user.name,
    )


# ── Header Fixtures ──────────────────────────────

@pytest.fixture
def admin_headers(admin_token):
    """Return ``Authorization: Bearer <admin_token>`` header dict."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def employee_headers(employee_token):
    """Return ``Authorization: Bearer <employee_token>`` header dict."""
    return {"Authorization": f"Bearer {employee_token}"}

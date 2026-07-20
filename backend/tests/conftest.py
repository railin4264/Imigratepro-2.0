import os
import uuid
from pathlib import Path

TEST_DB_PATH = Path(__file__).parent / "test_migratepro.db"
# Every test that generates a form (test_forms.py's parametrized suite over
# the whole catalog, run repeatedly during any session) writes a real PDF to
# disk via app.services.pdf_filler even though its DB row lives in the
# isolated TEST_DB_PATH above and disappears when _clean_schema drops the
# schema -- without this, the PDFs themselves aren't isolated the same way
# and just accumulate as orphans in the dev generated_forms/ dir on every run.
TEST_GENERATED_FORMS_DIR = Path(__file__).parent / "test_generated_forms"
# Must be set before any `app.*` module is imported -- pydantic-settings
# reads the environment once, at `Settings()` construction time in
# app/core/config.py.
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["SMTP_HOST"] = ""  # keep email.send() in its log-only fallback
os.environ["SCHEDULER_ENABLED"] = "false"  # don't run the background loop during tests
os.environ["GENERATED_FORMS_DIR"] = str(TEST_GENERATED_FORMS_DIR)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.rate_limit import reset_all as reset_rate_limits  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _database_file():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    yield
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(scope="session", autouse=True)
def _generated_forms_dir():
    import shutil

    if TEST_GENERATED_FORMS_DIR.exists():
        shutil.rmtree(TEST_GENERATED_FORMS_DIR)
    TEST_GENERATED_FORMS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    shutil.rmtree(TEST_GENERATED_FORMS_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def _clean_schema():
    # Full drop/recreate per test rather than a shared session-scoped schema:
    # tests hit the API through TestClient (real commits, not a rollback-able
    # nested transaction), so without this, cases/invoices/etc. created by
    # one test would leak into the next and make assertions like
    # `total_cases == 0` order-dependent.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    reset_rate_limits()
    yield


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _make_user(db_session, role: UserRole, password: str = "testpassword123") -> User:
    user = User(
        full_name=f"Test {role.value}",
        email=f"{role.value}-{uuid.uuid4().hex[:8]}@test.local",
        role=role,
        hashed_password=hash_password(password),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    return _make_user(db_session, UserRole.ADMIN)


@pytest.fixture
def paralegal_user(db_session):
    return _make_user(db_session, UserRole.PARALEGAL)


def _login(client, email: str, password: str = "testpassword123") -> dict:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()


@pytest.fixture
def admin_tokens(client, admin_user):
    return _login(client, admin_user.email)


@pytest.fixture
def auth_headers(admin_tokens):
    return {"Authorization": f"Bearer {admin_tokens['access_token']}"}


@pytest.fixture
def paralegal_tokens(client, paralegal_user):
    return _login(client, paralegal_user.email)


@pytest.fixture
def paralegal_headers(paralegal_tokens):
    return {"Authorization": f"Bearer {paralegal_tokens['access_token']}"}


@pytest.fixture
def make_case(client, auth_headers):
    def _make(case_number: str | None = None):
        res = client.post(
            "/api/v1/cases",
            json={
                "case_number": case_number or f"TEST-{uuid.uuid4().hex[:8]}",
                "case_type": "family_based",
                "status": "intake",
            },
            headers=auth_headers,
        )
        assert res.status_code == 201, res.text
        return res.json()

    return _make

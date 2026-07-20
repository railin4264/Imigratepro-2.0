import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.user import User, UserRole


def _make_user(db, role: UserRole, email: str) -> User:
    u = User(full_name=f"{role.value} user", email=email, hashed_password=hash_password("password123"), role=role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _login(client: TestClient, email: str) -> dict:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture
def seeded_roles(client, auth_headers):
    # wipe any pre-existing users, then create one per role
    db = SessionLocal()
    db.query(User).delete()
    db.commit()
    users = {}
    for role in UserRole:
        email = f"{role.value}@example.com"
        users[role] = _make_user(db, role, email)
    db.close()
    return users


def _headers_for(client: TestClient, email: str) -> dict:
    tok = _login(client, email)["access_token"]
    return {"Authorization": f"Bearer {tok}"}


# --- Destructive action: delete case -> owner/admin only ---
@pytest.mark.parametrize("role,expected", [
    (UserRole.OWNER, 204),
    (UserRole.ADMIN, 204),
    (UserRole.ATTORNEY, 403),
    (UserRole.BILLING, 403),
    (UserRole.INTAKE, 403),
    (UserRole.PARALEGAL, 403),
    (UserRole.LEGAL_ASSISTANT, 403),
    (UserRole.CONTRACT_ATTORNEY, 403),
])
def test_delete_case_gating(client, auth_headers, seeded_roles, role, expected):
    # create a case as admin
    admin_h = _headers_for(client, "admin@example.com")
    case = client.post("/api/v1/cases", json={"case_number": "T-001", "case_type": "family_based", "title": "t", "client_ids": []}, headers=admin_h).json()
    h = _headers_for(client, f"{role.value}@example.com")
    r = client.delete(f"/api/v1/cases/{case['id']}", headers=h)
    assert r.status_code == expected


# --- Financial action: create invoice -> owner/admin/attorney/billing ---
@pytest.mark.parametrize("role,expected", [
    (UserRole.OWNER, 201),
    (UserRole.ADMIN, 201),
    (UserRole.ATTORNEY, 201),
    (UserRole.BILLING, 201),
    (UserRole.INTAKE, 403),
    (UserRole.PARALEGAL, 403),
    (UserRole.LEGAL_ASSISTANT, 403),
    (UserRole.CONTRACT_ATTORNEY, 403),
])
def test_create_invoice_gating(client, auth_headers, seeded_roles, role, expected):
    admin_h = _headers_for(client, "admin@example.com")
    case = client.post("/api/v1/cases", json={"case_number": "T-001", "case_type": "family_based", "title": "t", "client_ids": []}, headers=admin_h).json()
    h = _headers_for(client, f"{role.value}@example.com")
    r = client.post(
        f"/api/v1/cases/{case['id']}/invoices",
        json={"amount": "100.00", "description": "fee", "due_date": "2026-12-31"},
        headers=h,
    )
    assert r.status_code == expected


# --- Intake: can create a client, cannot delete one ---
def test_intake_can_create_client(client, auth_headers, seeded_roles):
    h = _headers_for(client, "intake@example.com")
    r = client.post("/api/v1/clients", json={"first_name": "A", "last_name": "B", "email": "new@example.com"}, headers=h)
    assert r.status_code == 201


def test_intake_cannot_delete_client(client, auth_headers, seeded_roles):
    h = _headers_for(client, "intake@example.com")
    # create a client via admin first
    admin_h = _headers_for(client, "admin@example.com")
    c = client.post("/api/v1/clients", json={"first_name": "X", "last_name": "Y", "email": "x@example.com"}, headers=admin_h).json()
    r = client.delete(f"/api/v1/clients/{c['id']}", headers=h)
    assert r.status_code == 403


# --- Audit log readable by owner/admin, not attorney ---
@pytest.mark.parametrize("role,expected", [
    (UserRole.OWNER, 200),
    (UserRole.ADMIN, 200),
    (UserRole.ATTORNEY, 403),
])
def test_audit_log_gating(client, auth_headers, seeded_roles, role, expected):
    h = _headers_for(client, f"{role.value}@example.com")
    r = client.get("/api/v1/audit-log", headers=h)
    assert r.status_code == expected

import uuid
import pytest
from app.models.client import Client
from app.models.auth_token import RefreshToken
from app.seed_forms import seed as seed_forms


@pytest.fixture
def seeded_forms():
    seed_forms()

@pytest.fixture
def test_client_model(db_session):
    client = Client(
        first_name="Client",
        last_name="Test",
        email="client-test@test.local",
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client


def test_client_register(client, auth_headers, test_client_model):
    # Only staff can register client passwords
    res = client.post(
        "/api/v1/client-auth/register",
        json={"email": test_client_model.email, "password": "newpassword123"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["email"] == test_client_model.email


def test_client_register_unauthorized(client, test_client_model):
    # Non-staff cannot register client passwords
    res = client.post(
        "/api/v1/client-auth/register",
        json={"email": test_client_model.email, "password": "newpassword123"},
    )
    assert res.status_code == 401


def test_client_register_nonexistent(client, auth_headers):
    # Try to register password for non-existent email
    res = client.post(
        "/api/v1/client-auth/register",
        json={"email": "nonexistent@test.local", "password": "newpassword123"},
        headers=auth_headers,
    )
    assert res.status_code == 404


def test_client_login_success(client, test_client_model, auth_headers):
    # Setup password first
    client.post(
        "/api/v1/client-auth/register",
        json={"email": test_client_model.email, "password": "clientpassword123"},
        headers=auth_headers,
    )

    # Login
    res = client.post(
        "/api/v1/client-auth/login",
        json={"email": test_client_model.email, "password": "clientpassword123"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["client"]["email"] == test_client_model.email


def test_client_login_wrong_password(client, test_client_model, auth_headers):
    # Setup password first
    client.post(
        "/api/v1/client-auth/register",
        json={"email": test_client_model.email, "password": "clientpassword123"},
        headers=auth_headers,
    )

    # Login with wrong password
    res = client.post(
        "/api/v1/client-auth/login",
        json={"email": test_client_model.email, "password": "wrongpassword"},
    )
    assert res.status_code == 401


def test_client_me(client, test_client_model, auth_headers):
    # Register and login
    client.post(
        "/api/v1/client-auth/register",
        json={"email": test_client_model.email, "password": "clientpassword123"},
        headers=auth_headers,
    )
    login_res = client.post(
        "/api/v1/client-auth/login",
        json={"email": test_client_model.email, "password": "clientpassword123"},
    )
    access_token = login_res.json()["access_token"]

    # Get me
    me_res = client.get(
        "/api/v1/client-auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == test_client_model.email


def test_client_me_unauthorized(client):
    me_res = client.get("/api/v1/client-auth/me")
    assert me_res.status_code == 401


def test_client_refresh(client, test_client_model, auth_headers):
    # Register and login
    client.post(
        "/api/v1/client-auth/register",
        json={"email": test_client_model.email, "password": "clientpassword123"},
        headers=auth_headers,
    )
    login_res = client.post(
        "/api/v1/client-auth/login",
        json={"email": test_client_model.email, "password": "clientpassword123"},
    )
    old_tokens = login_res.json()
    old_refresh = old_tokens["refresh_token"]

    # Refresh
    refresh_res = client.post(
        "/api/v1/client-auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert new_tokens["access_token"] != old_tokens["access_token"]
    assert new_tokens["refresh_token"] != old_refresh

    # Try replay refresh
    replay_res = client.post(
        "/api/v1/client-auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert replay_res.status_code == 401


def test_client_logout(client, test_client_model, auth_headers, db_session):
    # Register and login
    client.post(
        "/api/v1/client-auth/register",
        json={"email": test_client_model.email, "password": "clientpassword123"},
        headers=auth_headers,
    )
    login_res = client.post(
        "/api/v1/client-auth/login",
        json={"email": test_client_model.email, "password": "clientpassword123"},
    )
    tokens = login_res.json()
    refresh_token = tokens["refresh_token"]

    # Logout
    logout_res = client.post(
        "/api/v1/client-auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert logout_res.status_code == 204

    # Verify refresh token is revoked in DB
    stored = (
        db_session.query(RefreshToken)
        .filter(RefreshToken.client_id == test_client_model.id)
        .all()
    )
    assert any(t.revoked_at is not None for t in stored)

    # Verify refresh fails
    refresh_res = client.post(
        "/api/v1/client-auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 401


def test_client_forgot_and_reset_flow(client, test_client_model, auth_headers, monkeypatch):
    # Register first
    client.post(
        "/api/v1/client-auth/register",
        json={"email": test_client_model.email, "password": "oldpassword123"},
        headers=auth_headers,
    )

    captured = {}
    def fake_send(to, subject, body):
        captured["to"] = to
        captured["body"] = body
        return False

    monkeypatch.setattr("app.api.v1.endpoints.client_auth.email.send", fake_send)

    # Forgot password request
    res = client.post(
        "/api/v1/client-auth/forgot-password",
        json={"email": test_client_model.email},
    )
    assert res.status_code == 204
    assert captured["to"] == [test_client_model.email]

    # Extract token from the body of email
    body = captured["body"]
    token = body.split("/reset-password/")[-1].split()[0]

    # Reset password
    reset_res = client.post(
        "/api/v1/client-auth/reset-password",
        json={"token": token, "password": "newpassword123"},
    )
    assert reset_res.status_code == 204

    # Try login with new password
    login_res = client.post(
        "/api/v1/client-auth/login",
        json={"email": test_client_model.email, "password": "newpassword123"},
    )
    assert login_res.status_code == 200


def _login_client(client, auth_headers, client_model, password="clientpassword123"):
    client.post(
        "/api/v1/client-auth/register",
        json={"email": client_model.email, "password": password},
        headers=auth_headers,
    )
    res = client.post("/api/v1/client-auth/login", json={"email": client_model.email, "password": password})
    return res.json()["access_token"]


def test_my_cases_returns_only_cases_the_client_participates_in(
    client, auth_headers, test_client_model, make_case, seeded_forms
):
    my_case = make_case()
    other_case = make_case()

    client.post(
        f"/api/v1/cases/{my_case['id']}/participants",
        json={"client_id": str(test_client_model.id), "role": "petitioner"},
        headers=auth_headers,
    )

    access_token = _login_client(client, auth_headers, test_client_model)
    res = client.get("/api/v1/client-auth/me/cases", headers={"Authorization": f"Bearer {access_token}"})
    assert res.status_code == 200
    body = res.json()

    case_ids = {c["id"] for c in body}
    assert my_case["id"] in case_ids
    assert other_case["id"] not in case_ids

    mine = next(c for c in body if c["id"] == my_case["id"])
    assert mine["my_role"] == "petitioner"
    assert mine["case_number"] == my_case["case_number"]


def test_my_cases_includes_generated_forms_with_client_link_enabled(
    client, auth_headers, test_client_model, make_case, seeded_forms
):
    case = make_case()
    client.post(
        f"/api/v1/cases/{case['id']}/participants",
        json={"client_id": str(test_client_model.id), "role": "petitioner"},
        headers=auth_headers,
    )
    generate = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    )
    assert generate.status_code == 201, generate.text
    form_id = generate.json()["id"]

    access_token = _login_client(client, auth_headers, test_client_model)
    res = client.get("/api/v1/client-auth/me/cases", headers={"Authorization": f"Bearer {access_token}"})
    body = res.json()
    mine = next(c for c in body if c["id"] == case["id"])
    assert len(mine["forms"]) == 1
    assert mine["forms"][0]["id"] == form_id
    assert mine["forms"][0]["form_code"] == "G-28"
    assert mine["forms"][0]["access_token"]


def test_my_cases_requires_authentication(client):
    res = client.get("/api/v1/client-auth/me/cases")
    assert res.status_code == 401

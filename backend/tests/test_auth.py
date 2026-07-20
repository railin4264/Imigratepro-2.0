import uuid

from app.models.auth_token import RefreshToken


def test_login_success(client, admin_user):
    res = client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "testpassword123"})
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["email"] == admin_user.email


def test_login_wrong_password(client, admin_user):
    res = client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "wrong"})
    assert res.status_code == 401


def test_login_email_is_case_insensitive(client, admin_user):
    # Regression test: a browser/OS auto-capitalizing the first letter of an
    # email field shouldn't turn a valid login into "invalid email or
    # password" -- see auth.py::login.
    res = client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email.upper(), "password": "testpassword123"},
    )
    assert res.status_code == 200


def test_me_requires_auth(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_me_with_valid_token(client, auth_headers, admin_user):
    res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == admin_user.email


def test_protected_endpoint_rejects_missing_token(client):
    res = client.get("/api/v1/clients")
    assert res.status_code == 401


def test_refresh_issues_new_tokens_and_rotates(client, admin_tokens, db_session):
    old_refresh = admin_tokens["refresh_token"]

    res = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert res.status_code == 200
    new_tokens = res.json()
    assert new_tokens["access_token"] != admin_tokens["access_token"]
    assert new_tokens["refresh_token"] != old_refresh

    # The old refresh token must be revoked (rotation) -- replaying it fails.
    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert replay.status_code == 401

    # The new one still works.
    again = client.post("/api/v1/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]})
    assert again.status_code == 200


def test_refresh_with_garbage_token_fails(client):
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert res.status_code == 401


def test_logout_revokes_refresh_token(client, admin_tokens, db_session):
    refresh_token = admin_tokens["refresh_token"]

    res = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert res.status_code == 204

    stored = (
        db_session.query(RefreshToken)
        .filter(RefreshToken.user_id == uuid.UUID(admin_tokens["user"]["id"]))
        .all()
    )
    assert any(t.revoked_at is not None for t in stored)

    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert replay.status_code == 401


def test_forgot_password_unknown_email_still_returns_204(client):
    res = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@nowhere.local"})
    assert res.status_code == 204


def test_forgot_password_and_reset_flow(client, admin_user, monkeypatch):
    captured = {}

    def fake_send(to, subject, body):
        captured["to"] = to
        captured["body"] = body
        return False

    monkeypatch.setattr("app.api.v1.endpoints.auth.email.send", fake_send)

    res = client.post("/api/v1/auth/forgot-password", json={"email": admin_user.email})
    assert res.status_code == 204
    assert captured["to"] == [admin_user.email]

    # Pull the raw token out of the emailed reset URL.
    token = captured["body"].split("reset-password/")[1].split("\n")[0].strip()

    reset = client.post("/api/v1/auth/reset-password", json={"token": token, "password": "brandnewpassword123"})
    assert reset.status_code == 204

    # Old password no longer works, new one does.
    old_login = client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "testpassword123"})
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login", json={"email": admin_user.email, "password": "brandnewpassword123"}
    )
    assert new_login.status_code == 200

    # Reusing the same reset token must fail (single use).
    reuse = client.post(
        "/api/v1/auth/reset-password", json={"token": token, "password": "yetanotherpassword123"}
    )
    assert reuse.status_code == 400


def test_only_admin_can_create_users(client, auth_headers, paralegal_user):
    # Admin can.
    res = client.post(
        "/api/v1/users",
        json={"full_name": "New Hire", "email": "newhire@test.local", "role": "paralegal"},
        headers=auth_headers,
    )
    assert res.status_code == 201

    # A non-admin can't.
    login = client.post(
        "/api/v1/auth/login", json={"email": paralegal_user.email, "password": "testpassword123"}
    )
    paralegal_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    res = client.post(
        "/api/v1/users",
        json={"full_name": "Blocked", "email": "blocked@test.local", "role": "paralegal"},
        headers=paralegal_headers,
    )
    assert res.status_code == 403


def test_account_locks_after_repeated_failed_logins(client, admin_user, monkeypatch):
    import app.api.v1.endpoints.auth as auth_module

    monkeypatch.setattr(auth_module.settings, "MAX_LOGIN_ATTEMPTS", 3)

    for _ in range(3):
        res = client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "wrong"})
        assert res.status_code == 401

    # Now locked -- even the correct password is rejected.
    locked = client.post(
        "/api/v1/auth/login", json={"email": admin_user.email, "password": "testpassword123"}
    )
    assert locked.status_code == 423


def test_successful_login_resets_failed_attempt_counter(client, admin_user, db_session, monkeypatch):
    import app.api.v1.endpoints.auth as auth_module

    monkeypatch.setattr(auth_module.settings, "MAX_LOGIN_ATTEMPTS", 3)

    client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "wrong"})
    client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "wrong"})

    ok = client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "testpassword123"})
    assert ok.status_code == 200

    db_session.refresh(admin_user)
    assert admin_user.failed_login_attempts == 0

    # A subsequent bad attempt shouldn't immediately lock (counter was reset).
    res = client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "wrong"})
    assert res.status_code == 401


def test_login_rate_limited_per_ip(client, admin_user, monkeypatch):
    import app.api.v1.endpoints.auth as auth_module

    monkeypatch.setattr(auth_module.settings, "LOGIN_RATE_LIMIT_PER_IP", 3)
    monkeypatch.setattr(auth_module.settings, "MAX_LOGIN_ATTEMPTS", 100)  # don't hit lockout first

    for _ in range(3):
        client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "wrong"})

    res = client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "wrong"})
    assert res.status_code == 429


def test_forgot_password_rate_limited(client, admin_user, monkeypatch):
    import app.api.v1.endpoints.auth as auth_module

    monkeypatch.setattr(auth_module.settings, "FORGOT_PASSWORD_RATE_LIMIT_PER_IP", 2)
    monkeypatch.setattr(auth_module.email, "send", lambda to, subject, body: True)

    for _ in range(2):
        res = client.post("/api/v1/auth/forgot-password", json={"email": admin_user.email})
        assert res.status_code == 204

    # Third request in the window is silently rate-limited -- still 204 (no
    # enumeration signal to a caller watching status codes).
    third = client.post("/api/v1/auth/forgot-password", json={"email": admin_user.email})
    assert third.status_code == 204


def test_new_forgot_password_request_invalidates_prior_reset_link(client, admin_user, monkeypatch):
    import app.api.v1.endpoints.auth as auth_module

    tokens = []

    def fake_send(to, subject, body):
        tokens.append(body.split("reset-password/")[1].split("\n")[0].strip())
        return True

    monkeypatch.setattr(auth_module.email, "send", fake_send)

    client.post("/api/v1/auth/forgot-password", json={"email": admin_user.email})
    client.post("/api/v1/auth/forgot-password", json={"email": admin_user.email})
    assert len(tokens) == 2
    old_token, new_token = tokens

    # The first (older) link no longer works...
    stale = client.post(
        "/api/v1/auth/reset-password", json={"token": old_token, "password": "somenewpassword123"}
    )
    assert stale.status_code == 400

    # ...but the newest one does.
    fresh = client.post(
        "/api/v1/auth/reset-password", json={"token": new_token, "password": "somenewpassword123"}
    )
    assert fresh.status_code == 204


def test_user_can_change_own_password_but_not_someone_elses(client, auth_headers, admin_user, paralegal_user):
    login = client.post(
        "/api/v1/auth/login", json={"email": paralegal_user.email, "password": "testpassword123"}
    )
    paralegal_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    own = client.post(
        f"/api/v1/users/{paralegal_user.id}/password",
        json={"password": "newpassword456"},
        headers=paralegal_headers,
    )
    assert own.status_code == 200

    others = client.post(
        f"/api/v1/users/{admin_user.id}/password",
        json={"password": "newpassword456"},
        headers=paralegal_headers,
    )
    assert others.status_code == 403

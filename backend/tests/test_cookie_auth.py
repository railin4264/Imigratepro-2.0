"""The browser frontend authenticates via httpOnly cookies now (set by
/auth/login, read by get_current_user as a fallback behind the Authorization
header) instead of storing tokens in localStorage. TestClient keeps its own
cookie jar across requests on the same instance, so these tests don't pass
any Authorization header at all -- they're specifically exercising the
cookie-only path a real browser would take."""


def test_login_sets_httponly_auth_cookies(client, admin_user):
    res = client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "testpassword123"})
    assert res.status_code == 200
    assert "access_token" in res.cookies
    assert "refresh_token" in res.cookies

    set_cookie_headers = res.headers.get_list("set-cookie")
    access_cookie_header = next(h for h in set_cookie_headers if h.startswith("access_token="))
    assert "HttpOnly" in access_cookie_header
    assert "SameSite=lax" in access_cookie_header


def test_cookie_alone_authenticates_a_request(client, admin_user):
    login_res = client.post(
        "/api/v1/auth/login", json={"email": admin_user.email, "password": "testpassword123"}
    )
    assert login_res.status_code == 200

    # No Authorization header at all -- TestClient's cookie jar carries the
    # access_token cookie set by the login response above.
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 200
    assert res.json()["email"] == admin_user.email


def test_no_cookie_and_no_header_is_unauthenticated(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_refresh_via_cookie_alone_rotates_and_resets_cookies(client, admin_user):
    client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "testpassword123"})

    # Body has no refresh_token -- must fall back to the refresh_token cookie.
    res = client.post("/api/v1/auth/refresh", json={})
    assert res.status_code == 200
    assert "access_token" in res.cookies
    assert "refresh_token" in res.cookies

    # The new access_token cookie still authenticates.
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200


def test_logout_via_cookie_clears_cookies_and_revokes_session(client, admin_user):
    client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "testpassword123"})

    res = client.post("/api/v1/auth/logout", json={})
    assert res.status_code == 204

    # The refresh token that was in the (now-cleared) cookie must be revoked
    # server-side, not just forgotten client-side.
    refresh_res = client.post("/api/v1/auth/refresh", json={})
    assert refresh_res.status_code == 401


def test_bearer_header_still_works_unchanged(client, admin_user):
    # Non-browser API clients (and the rest of this test suite) never adopt
    # cookies -- the header-based flow must be untouched.
    res = client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": "testpassword123"})
    token = res.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200

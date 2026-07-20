import pytest


@pytest.fixture
def seeded_forms():
    from app.seed_forms import seed as seed_forms

    seed_forms()


def test_login_with_nonexistent_email_returns_same_generic_error(client):
    # Regression test: the response message must not distinguish "no such
    # account" from "wrong password" -- both are exactly this, so a client
    # can't enumerate registered emails from the response body. (Response
    # *timing* is also equalized in auth.py::login via a dummy password
    # hash, but that's not practical to assert in a unit test.)
    res = client.post("/api/v1/auth/login", json={"email": "nobody@test.local", "password": "whatever123"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


def test_create_user_rejects_short_password(client, auth_headers):
    res = client.post(
        "/api/v1/users",
        json={"full_name": "New Hire", "email": "newhire@test.local", "role": "paralegal", "password": "short"},
        headers=auth_headers,
    )
    assert res.status_code == 422


def test_create_user_accepts_password_at_minimum_length(client, auth_headers):
    res = client.post(
        "/api/v1/users",
        json={"full_name": "New Hire", "email": "newhire2@test.local", "role": "paralegal", "password": "12345678"},
        headers=auth_headers,
    )
    assert res.status_code == 201


def test_create_user_without_password_still_works(client, auth_headers):
    # Staff can be created without ever setting a login (see User.hashed_password
    # docstring) -- the validator must not reject the absence of a password.
    res = client.post(
        "/api/v1/users",
        json={"full_name": "No Login Yet", "email": "nologin@test.local", "role": "paralegal"},
        headers=auth_headers,
    )
    assert res.status_code == 201


def test_generated_form_update_rejects_oversized_field_value(client, auth_headers, make_case, seeded_forms):
    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()

    res = client.patch(
        f"/api/v1/forms/{generated['id']}",
        json={"data": {"some_field": "x" * 20_001}},
        headers=auth_headers,
    )
    assert res.status_code == 422


def test_generated_form_update_rejects_too_many_fields(client, auth_headers, make_case, seeded_forms):
    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()

    oversized = {f"field_{i}": "x" for i in range(2001)}
    res = client.patch(f"/api/v1/forms/{generated['id']}", json={"data": oversized}, headers=auth_headers)
    assert res.status_code == 422


def test_public_form_endpoint_rate_limits_per_token(client, auth_headers, make_case, seeded_forms, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "PUBLIC_FORM_RATE_LIMIT_PER_TOKEN", 3)

    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()
    token = generated["access_token"]

    for _ in range(3):
        res = client.get(f"/api/v1/public/forms/{token}")
        assert res.status_code == 200

    limited = client.get(f"/api/v1/public/forms/{token}")
    assert limited.status_code == 429


def test_public_form_rejects_unknown_field_names(client, auth_headers, make_case, seeded_forms):
    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()
    token = generated["access_token"]

    res = client.patch(f"/api/v1/public/forms/{token}", json={"data": {"not_a_real_field": "x"}})
    assert res.status_code == 422


def test_public_form_silently_ignores_attorney_only_fields_instead_of_erroring(
    client, auth_headers, make_case, seeded_forms
):
    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()
    token = generated["access_token"]

    # form1[0].#subform[0].Line6_EMail[0] is sourced from attorney.mobile_phone
    # -- a real field on the schema, but not one the client wizard should be
    # able to overwrite. The client-portal autosave always echoes the whole
    # form back (including fields it never showed), so this must be
    # silently dropped, not rejected as "unknown".
    res = client.patch(
        f"/api/v1/public/forms/{token}", json={"data": {"form1[0].#subform[0].Line6_EMail[0]": "hacked@evil.com"}}
    )
    assert res.status_code == 200
    assert res.json()["data"].get("form1[0].#subform[0].Line6_EMail[0]") != "hacked@evil.com"


def test_public_form_still_saves_normal_client_fields(client, auth_headers, make_case, seeded_forms):
    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()
    token = generated["access_token"]

    # form1[0].#subform[1].Pt3Line5a_FamilyName[0] is G-28's beneficiary last
    # name -- not attorney-owned, so a normal client-portal save of it must
    # go through untouched. (Field *name* alone isn't a reliable "is this
    # attorney-owned" signal -- e.g. Pt1Line2a_FamilyName[0] has no
    # "Attorney" substring despite being attorney.last_name -- so this uses a
    # known-good field rather than a name heuristic.)
    res = client.patch(
        f"/api/v1/public/forms/{token}",
        json={"data": {"form1[0].#subform[1].Pt3Line5a_FamilyName[0]": "Perez"}},
    )
    assert res.status_code == 200
    assert res.json()["data"]["form1[0].#subform[1].Pt3Line5a_FamilyName[0]"] == "Perez"


def test_internal_editor_rejects_unknown_field_names(client, auth_headers, make_case, seeded_forms):
    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()

    res = client.patch(
        f"/api/v1/forms/{generated['id']}", json={"data": {"not_a_real_field": "x"}}, headers=auth_headers
    )
    assert res.status_code == 422

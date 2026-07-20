import pytest

from app.services import uscis_case_status


class FakeResponse:
    def __init__(self, status_code: int, json_data: dict | None = None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self) -> dict:
        return self._json_data


@pytest.fixture(autouse=True)
def _reset_token_cache():
    # Module-level cache (see uscis_case_status.py) leaks across tests
    # otherwise -- a token cached by one test would let a later test skip
    # the POST /oauth/accesstoken call it's asserting on.
    uscis_case_status._cached_token = None
    uscis_case_status._cached_token_expires_at = 0.0
    yield
    uscis_case_status._cached_token = None
    uscis_case_status._cached_token_expires_at = 0.0


@pytest.fixture
def configured(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "USCIS_API_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings, "USCIS_API_CLIENT_SECRET", "test-client-secret")


@pytest.fixture
def seeded_forms():
    from app.seed_forms import seed as seed_forms

    seed_forms()


SAMPLE_CASE_STATUS = {
    "case_status": {
        "receiptNumber": "EAC9999103403",
        "formType": "I-130",
        "submittedDate": "09-05-2023 14:28:46",
        "modifiedDate": "09-05-2023 14:28:46",
        "current_case_status_text_en": "Case Was Approved",
        "current_case_status_desc_en": "We approved your Form I-130.",
        "current_case_status_text_es": "Caso Fue Aprobado",
        "current_case_status_desc_es": "Aprobamos su Formulario I-130.",
        "hist_case_status": [
            {
                "date": "2023-09-05",
                "completed_text_en": "We approved your Form I-130.",
                "completed_text_es": "Aprobamos su Formulario I-130.",
            }
        ],
    },
    "message": "Query was successful",
}


# --- Service-level unit tests ------------------------------------------


def test_is_configured_false_by_default():
    assert uscis_case_status.is_configured() is False


def test_is_configured_true_when_credentials_set(configured):
    assert uscis_case_status.is_configured() is True


def test_get_case_status_requires_configuration():
    with pytest.raises(uscis_case_status.USCISAPIError):
        uscis_case_status.get_case_status("EAC9999103403")


def test_get_case_status_success(configured, monkeypatch):
    def fake_post(url, **kwargs):
        return FakeResponse(200, {"access_token": "tok-1", "expires_in": 3600})

    def fake_get(url, **kwargs):
        assert url.endswith("/case-status/EAC9999103403")
        assert kwargs["headers"]["Authorization"] == "Bearer tok-1"
        return FakeResponse(200, SAMPLE_CASE_STATUS)

    monkeypatch.setattr(uscis_case_status.httpx, "post", fake_post)
    monkeypatch.setattr(uscis_case_status.httpx, "get", fake_get)

    result = uscis_case_status.get_case_status("eac9999103403")
    assert result == SAMPLE_CASE_STATUS


def test_get_case_status_normalizes_receipt_number(configured, monkeypatch):
    seen = {}

    def fake_post(url, **kwargs):
        return FakeResponse(200, {"access_token": "tok-1"})

    def fake_get(url, **kwargs):
        seen["url"] = url
        return FakeResponse(200, SAMPLE_CASE_STATUS)

    monkeypatch.setattr(uscis_case_status.httpx, "post", fake_post)
    monkeypatch.setattr(uscis_case_status.httpx, "get", fake_get)

    uscis_case_status.get_case_status("  eac9999103403  ")
    assert seen["url"].endswith("/case-status/EAC9999103403")


def test_token_is_cached_across_calls(configured, monkeypatch):
    post_calls = []

    def fake_post(url, **kwargs):
        post_calls.append(1)
        return FakeResponse(200, {"access_token": "tok-1", "expires_in": 3600})

    def fake_get(url, **kwargs):
        return FakeResponse(200, SAMPLE_CASE_STATUS)

    monkeypatch.setattr(uscis_case_status.httpx, "post", fake_post)
    monkeypatch.setattr(uscis_case_status.httpx, "get", fake_get)

    uscis_case_status.get_case_status("EAC9999103403")
    uscis_case_status.get_case_status("EAC9999103404")
    assert len(post_calls) == 1


def test_get_case_status_retries_once_on_401_then_succeeds(configured, monkeypatch):
    post_calls = []
    get_calls = []

    def fake_post(url, **kwargs):
        post_calls.append(1)
        return FakeResponse(200, {"access_token": f"tok-{len(post_calls)}", "expires_in": 3600})

    def fake_get(url, **kwargs):
        get_calls.append(kwargs["headers"]["Authorization"])
        if len(get_calls) == 1:
            return FakeResponse(401, {"code": 401, "message": "Invalid Access Token"})
        return FakeResponse(200, SAMPLE_CASE_STATUS)

    monkeypatch.setattr(uscis_case_status.httpx, "post", fake_post)
    monkeypatch.setattr(uscis_case_status.httpx, "get", fake_get)

    result = uscis_case_status.get_case_status("EAC9999103403")
    assert result == SAMPLE_CASE_STATUS
    assert len(post_calls) == 2  # refreshed the token once
    assert get_calls == ["Bearer tok-1", "Bearer tok-2"]


def test_get_case_status_404_raises_with_receipt_number_in_message(configured, monkeypatch):
    monkeypatch.setattr(uscis_case_status.httpx, "post", lambda url, **kw: FakeResponse(200, {"access_token": "tok"}))
    monkeypatch.setattr(uscis_case_status.httpx, "get", lambda url, **kw: FakeResponse(404, {"code": 404}))

    with pytest.raises(uscis_case_status.USCISAPIError, match="EAC9999103403"):
        uscis_case_status.get_case_status("EAC9999103403")


@pytest.mark.parametrize("status_code", [422, 429, 503])
def test_get_case_status_documented_error_codes_raise(configured, monkeypatch, status_code):
    monkeypatch.setattr(uscis_case_status.httpx, "post", lambda url, **kw: FakeResponse(200, {"access_token": "tok"}))
    monkeypatch.setattr(uscis_case_status.httpx, "get", lambda url, **kw: FakeResponse(status_code, {"code": status_code}))

    with pytest.raises(uscis_case_status.USCISAPIError):
        uscis_case_status.get_case_status("EAC9999103403")


def test_get_case_status_auth_failure_raises(configured, monkeypatch):
    monkeypatch.setattr(uscis_case_status.httpx, "post", lambda url, **kw: FakeResponse(500))

    with pytest.raises(uscis_case_status.USCISAPIError):
        uscis_case_status.get_case_status("EAC9999103403")


# --- Endpoint tests ------------------------------------------------------


def test_uscis_status_endpoint_reflects_configuration(client, auth_headers):
    res = client.get("/api/v1/uscis/status", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == {"configured": False}


def test_uscis_status_endpoint_true_when_configured(client, auth_headers, configured):
    res = client.get("/api/v1/uscis/status", headers=auth_headers)
    assert res.json() == {"configured": True}


def test_set_receipt_number_normalizes_and_saves(client, auth_headers, make_case, seeded_forms):
    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()

    res = client.patch(
        f"/api/v1/forms/{generated['id']}/receipt-number",
        json={"uscis_receipt_number": "  eac9999103403  "},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["uscis_receipt_number"] == "EAC9999103403"


def test_set_receipt_number_rejects_too_long(client, auth_headers, make_case, seeded_forms):
    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()

    res = client.patch(
        f"/api/v1/forms/{generated['id']}/receipt-number",
        json={"uscis_receipt_number": "X" * 21},
        headers=auth_headers,
    )
    assert res.status_code == 422


def test_setting_new_receipt_number_clears_stale_status(client, auth_headers, make_case, seeded_forms, configured, monkeypatch):
    monkeypatch.setattr(uscis_case_status.httpx, "post", lambda url, **kw: FakeResponse(200, {"access_token": "tok"}))
    monkeypatch.setattr(uscis_case_status.httpx, "get", lambda url, **kw: FakeResponse(200, SAMPLE_CASE_STATUS))

    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()
    client.patch(
        f"/api/v1/forms/{generated['id']}/receipt-number",
        json={"uscis_receipt_number": "EAC9999103403"},
        headers=auth_headers,
    )
    checked = client.post(f"/api/v1/forms/{generated['id']}/check-status", headers=auth_headers)
    assert checked.json()["uscis_status_raw"] == SAMPLE_CASE_STATUS

    # Changing the receipt number should drop the stale status tied to the old one.
    updated = client.patch(
        f"/api/v1/forms/{generated['id']}/receipt-number",
        json={"uscis_receipt_number": "SRC9999102777"},
        headers=auth_headers,
    )
    assert updated.json()["uscis_status_checked_at"] is None

    detail = client.get(f"/api/v1/forms/{generated['id']}", headers=auth_headers)
    assert detail.json()["uscis_status_raw"] is None


def test_check_status_requires_receipt_number_first(client, auth_headers, make_case, seeded_forms, configured):
    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()

    res = client.post(f"/api/v1/forms/{generated['id']}/check-status", headers=auth_headers)
    assert res.status_code == 400


def test_check_status_returns_503_when_not_configured(client, auth_headers, make_case, seeded_forms):
    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()
    client.patch(
        f"/api/v1/forms/{generated['id']}/receipt-number",
        json={"uscis_receipt_number": "EAC9999103403"},
        headers=auth_headers,
    )

    res = client.post(f"/api/v1/forms/{generated['id']}/check-status", headers=auth_headers)
    assert res.status_code == 503


def test_check_status_success_stores_result(client, auth_headers, make_case, seeded_forms, configured, monkeypatch):
    monkeypatch.setattr(uscis_case_status.httpx, "post", lambda url, **kw: FakeResponse(200, {"access_token": "tok"}))
    monkeypatch.setattr(uscis_case_status.httpx, "get", lambda url, **kw: FakeResponse(200, SAMPLE_CASE_STATUS))

    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()
    client.patch(
        f"/api/v1/forms/{generated['id']}/receipt-number",
        json={"uscis_receipt_number": "EAC9999103403"},
        headers=auth_headers,
    )

    res = client.post(f"/api/v1/forms/{generated['id']}/check-status", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["uscis_status_raw"] == SAMPLE_CASE_STATUS
    assert body["uscis_status_checked_at"] is not None


def test_check_status_maps_uscis_error_to_502(client, auth_headers, make_case, seeded_forms, configured, monkeypatch):
    monkeypatch.setattr(uscis_case_status.httpx, "post", lambda url, **kw: FakeResponse(200, {"access_token": "tok"}))
    monkeypatch.setattr(uscis_case_status.httpx, "get", lambda url, **kw: FakeResponse(404, {"code": 404}))

    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()
    client.patch(
        f"/api/v1/forms/{generated['id']}/receipt-number",
        json={"uscis_receipt_number": "EAC9999103403"},
        headers=auth_headers,
    )

    res = client.post(f"/api/v1/forms/{generated['id']}/check-status", headers=auth_headers)
    assert res.status_code == 502

from app.seed_data.uscis_requirements import USCIS_REQUIREMENTS_BY_FORM_CODE


def test_requirements_require_auth(client):
    res = client.get("/api/v1/form-templates/I-130/requirements")
    assert res.status_code == 401


def test_requirements_for_covered_form(client, auth_headers):
    res = client.get("/api/v1/form-templates/I-485/requirements", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["form_code"] == "I-485"
    assert body["source_url"]
    assert body["verified_on"]
    assert len(body["categories"]) > 0
    assert all(cat["items"] for cat in body["categories"])


def test_requirements_for_uncovered_form_returns_404_not_empty(client, auth_headers):
    # G-28 deliberately has no library entry -- 404 (not 200 with an empty
    # list) so the frontend can tell "nothing required" apart from "not
    # covered yet" and hide the section instead of implying zero requirements.
    res = client.get("/api/v1/form-templates/G-28/requirements", headers=auth_headers)
    assert res.status_code == 404


def test_requirements_for_unknown_code_returns_404(client, auth_headers):
    res = client.get("/api/v1/form-templates/NOT-A-FORM/requirements", headers=auth_headers)
    assert res.status_code == 404


def test_every_library_entry_has_a_uscis_source_and_nonempty_categories():
    for code, entry in USCIS_REQUIREMENTS_BY_FORM_CODE.items():
        assert entry.source_url.startswith("https://www.uscis.gov/"), code
        assert entry.categories, code
        for category in entry.categories:
            assert category.items, f"{code}/{category.title}"

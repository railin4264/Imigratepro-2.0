import pytest


@pytest.fixture
def seeded_forms():
    from app.seed_forms import seed as seed_forms

    seed_forms()


@pytest.fixture
def public_token(client, auth_headers, make_case, seeded_forms):
    case = make_case()
    generated = client.post(
        f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers
    ).json()
    return generated["access_token"]


def test_fresh_form_starts_at_wizard_step_zero(client, public_token):
    res = client.get(f"/api/v1/public/forms/{public_token}")
    assert res.status_code == 200
    assert res.json()["client_wizard_step"] == 0


def test_patch_persists_wizard_step(client, public_token):
    res = client.patch(f"/api/v1/public/forms/{public_token}", json={"data": {}, "client_wizard_step": 3})
    assert res.status_code == 200
    assert res.json()["client_wizard_step"] == 3

    refetched = client.get(f"/api/v1/public/forms/{public_token}")
    assert refetched.json()["client_wizard_step"] == 3


def test_patch_without_wizard_step_does_not_reset_it(client, public_token):
    client.patch(f"/api/v1/public/forms/{public_token}", json={"data": {}, "client_wizard_step": 4})

    # A save that omits client_wizard_step (the field the internal staff
    # editor's PATCH /forms/{id} always omits) must not silently reset the
    # client's saved position back to the start.
    res = client.patch(f"/api/v1/public/forms/{public_token}", json={"data": {"some_field": "x"}})
    assert res.status_code == 200
    assert res.json()["client_wizard_step"] == 4


def test_patch_updates_data_and_wizard_step_together(client, public_token):
    res = client.patch(
        f"/api/v1/public/forms/{public_token}",
        json={"data": {"form1[0].#subform[0].Pt1Line2a_FamilyName[0]": "Perez"}, "client_wizard_step": 1},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["client_wizard_step"] == 1
    assert body["data"]["form1[0].#subform[0].Pt1Line2a_FamilyName[0]"] == "Perez"

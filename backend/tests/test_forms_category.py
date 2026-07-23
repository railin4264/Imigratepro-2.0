import pytest

from app.seed_forms import seed as seed_forms


@pytest.fixture
def seeded_forms():
    seed_forms()


def test_seeder_categorizes_known_forms_by_code(client, auth_headers, seeded_forms):
    templates = client.get("/api/v1/form-templates", headers=auth_headers).json()
    by_code = {t["code"]: t for t in templates}
    assert by_code["I-130"]["category"] == "family"
    assert by_code["I-140"]["category"] == "employment"
    assert by_code["I-589"]["category"] == "asylum"
    assert by_code["N-400"]["category"] == "naturalization"


def test_grouped_endpoint_groups_by_category(client, auth_headers, seeded_forms):
    res = client.get("/api/v1/form-templates/grouped", headers=auth_headers)
    assert res.status_code == 200
    groups = res.json()

    # No empty groups, and every form landed in exactly one group.
    total_forms = sum(len(g["forms"]) for g in groups)
    all_templates = client.get("/api/v1/form-templates", headers=auth_headers).json()
    assert total_forms == len(all_templates)
    assert all(len(g["forms"]) > 0 for g in groups)

    family_group = next(g for g in groups if g["category"] == "family")
    assert any(f["code"] == "I-130" for f in family_group["forms"])

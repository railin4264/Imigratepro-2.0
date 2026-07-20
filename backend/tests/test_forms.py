from io import BytesIO

import pytest

from app.seed_data.form_field_maps import FORM_TEMPLATES
from app.seed_forms import seed as seed_forms


@pytest.fixture
def seeded_forms():
    seed_forms()


@pytest.fixture
def client_trio(client, auth_headers, make_case):
    """A case with a petitioner, beneficiary, and sponsor -- covers every
    role referenced by any form's autofill map (see
    app/seed_data/form_field_maps.py)."""

    case = make_case()
    for role, first, last in [("petitioner", "Maria", "Garcia"), ("beneficiary", "Jose", "Garcia"), ("sponsor", "Ana", "Lopez")]:
        c = client.post(
            "/api/v1/clients",
            json={
                "first_name": first,
                "last_name": last,
                "date_of_birth": "1990-01-15",
                "country_of_birth": "Mexico",
                "a_number": "123456789",
                "ssn": "123-45-6789",
                "sex": "female" if first in ("Maria", "Ana") else "male",
                "marital_status": "married",
                "address_line": "123 Main St",
                "city": "Miami",
                "state": "FL",
                "zip_code": "33101",
                "country": "United States",
                "email": f"{first.lower()}@example.com",
                "phone": "3051234567",
            },
            headers=auth_headers,
        ).json()
        client.post(
            f"/api/v1/cases/{case['id']}/participants",
            json={"client_id": c["id"], "role": role},
            headers=auth_headers,
        )
    return case


def test_form_catalog_has_all_99_forms(client, auth_headers, seeded_forms):
    res = client.get("/api/v1/form-templates", headers=auth_headers)
    assert res.status_code == 200
    codes = {t["code"] for t in res.json()}
    assert codes == {
        "AR-11", "EOIR-29", "G-1041", "G-1041A", "G-1055", "G-1145", "G-1256", "G-1450",
        "G-1566", "G-1650", "G-1651", "G-28", "G-28I", "G-325A", "G-325R", "G-845", "G-884",
        "I-102", "I-129", "I-129F", "I-129S", "I-130", "I-130A", "I-131", "I-131A", "I-134",
        "I-140", "I-140G", "I-191", "I-192", "I-193", "I-212", "I-290B", "I-356", "I-360",
        "I-361", "I-363", "I-407", "I-485", "I-508", "I-526", "I-526E", "I-539", "I-566",
        "I-589", "I-600", "I-600A", "I-601", "I-601A", "I-602", "I-612", "I-687", "I-690",
        "I-693", "I-694", "I-698", "I-730", "I-751", "I-765", "I-765V", "I-800", "I-800A",
        "I-817", "I-821", "I-821D", "I-824", "I-829", "I-854A", "I-854B", "I-864", "I-864A",
        "I-865", "I-881", "I-9", "I-90", "I-905", "I-907", "I-910", "I-912", "I-914", "I-918",
        "I-929", "I-941", "I-945", "I-956", "I-956F", "I-956G", "I-956H", "I-956K", "N-300",
        "N-336", "N-400", "N-426", "N-470", "N-565", "N-600", "N-600K", "N-644", "N-648",
    }


@pytest.mark.parametrize("template", FORM_TEMPLATES, ids=[t["code"] for t in FORM_TEMPLATES])
def test_form_generates_a_complete_downloadable_pdf(client, auth_headers, seeded_forms, client_trio, template):
    code = template["code"]
    case_id = client_trio["id"]

    generate = client.post(f"/api/v1/cases/{case_id}/forms", json={"form_code": code}, headers=auth_headers)
    assert generate.status_code == 201, generate.text
    form_id = generate.json()["id"]

    schema = client.get(f"/api/v1/form-templates/{code}/schema", headers=auth_headers).json()
    # Every field in the official inventory is present and editable -- the
    # "100% field coverage" guarantee, independent of how much of it autofilled.
    assert len(schema["fields"]) == _inventory_field_count(code)

    download = client.get(f"/api/v1/forms/{form_id}/download", headers=auth_headers)
    assert download.status_code == 200
    assert download.content[:4] == b"%PDF"


def _inventory_field_count(code: str) -> int:
    import json
    from pathlib import Path

    entry = next(t for t in FORM_TEMPLATES if t["code"] == code)
    path = Path(__file__).resolve().parents[1] / "app" / "seed_data" / "field_inventories" / entry["inventory_file"]
    return len(json.loads(path.read_text(encoding="utf-8")))


@pytest.mark.parametrize("template", FORM_TEMPLATES, ids=[t["code"] for t in FORM_TEMPLATES])
def test_autofill_map_only_references_real_pdf_fields(template):
    """Regression test: pypdf's update_page_form_field_values() silently
    ignores field names it doesn't recognize, so a typo'd `pdf_field` in an
    autofill map entry fails silently -- the PDF still generates, still has
    100% field coverage (it's just never filled in), and nothing in
    test_form_generates_a_complete_downloadable_pdf catches it. Caught for
    real once (N-565 had 3 entries pointing at a nonexistent subform index)."""

    import json
    from pathlib import Path

    entry = next(t for t in FORM_TEMPLATES if t["code"] == template["code"])
    inventory_path = (
        Path(__file__).resolve().parents[1] / "app" / "seed_data" / "field_inventories" / entry["inventory_file"]
    )
    real_field_names = {f["name"] for f in json.loads(inventory_path.read_text(encoding="utf-8"))}

    for autofill_entry in entry.get("autofill_map") or []:
        assert autofill_entry["pdf_field"] in real_field_names, (
            f"{template['code']}: autofill entry references nonexistent field "
            f"'{autofill_entry['pdf_field']}' -- it will silently never fill in"
        )


def test_i130_autofill_prefills_petitioner_and_beneficiary_names(client, auth_headers, seeded_forms, client_trio):
    case_id = client_trio["id"]
    generate = client.post(f"/api/v1/cases/{case_id}/forms", json={"form_code": "I-130"}, headers=auth_headers)
    form_id = generate.json()["id"]

    detail = client.get(f"/api/v1/forms/{form_id}", headers=auth_headers).json()
    data = detail["data"]
    assert data["form1[0].#subform[0].Pt2Line4a_FamilyName[0]"] == "Garcia"  # petitioner
    assert data["form1[0].#subform[4].Pt4Line4a_FamilyName[0]"] == "Garcia"  # beneficiary


@pytest.mark.parametrize("template", FORM_TEMPLATES, ids=[t["code"] for t in FORM_TEMPLATES])
def test_autofilled_values_actually_land_in_the_downloaded_pdf(client, auth_headers, seeded_forms, client_trio, template):
    """Closes the loop end-to-end: generate a form for a fully-populated
    case, then read the *actual* PDF's AcroForm field values back out with
    pypdf and confirm they match what GeneratedForm.data says was set --
    not just that the field name exists (see
    test_autofill_map_only_references_real_pdf_fields), but that the value
    really made it into the rendered file a client would download."""

    from pypdf import PdfReader

    code = template["code"]
    generate = client.post(
        f"/api/v1/cases/{client_trio['id']}/forms", json={"form_code": code}, headers=auth_headers
    )
    form_id = generate.json()["id"]
    expected_data = client.get(f"/api/v1/forms/{form_id}", headers=auth_headers).json()["data"]

    non_empty = {k: v for k, v in expected_data.items() if v}
    if not non_empty:
        pytest.skip(f"{code}: no autofill entries resolved for this test's client_trio data")

    download = client.get(f"/api/v1/forms/{form_id}/download", headers=auth_headers)
    reader = PdfReader(BytesIO(download.content))
    if reader.is_encrypted:
        reader.decrypt("")
    real_fields = reader.get_fields() or {}

    for pdf_field, expected_value in non_empty.items():
        actual = real_fields.get(pdf_field)
        actual_value = actual.get("/V") if actual else None
        assert str(actual_value) == str(expected_value), f"{code}: field '{pdf_field}' expected {expected_value!r}, PDF has {actual_value!r}"


def test_deleting_a_case_with_everything_attached_does_not_500(client, auth_headers, seeded_forms, client_trio):
    """Regression test: Case's one-to-many relationships (participants,
    documents, generated_forms, appointments, invoices, checklist_items) had
    no delete cascade, so deleting any case that had ever been used (i.e. had
    a participant) raised IntegrityError -> 500, since those FK columns
    aren't nullable. Found while generating forms against a case with
    participants during this batch. Fixed in app/models/case.py."""

    case_id = client_trio["id"]

    client.post(f"/api/v1/cases/{case_id}/forms", json={"form_code": "G-28"}, headers=auth_headers)
    client.post(
        f"/api/v1/cases/{case_id}/appointments",
        json={"appointment_type": "consultation", "scheduled_at": "2030-01-01T10:00:00Z"},
        headers=auth_headers,
    )
    client.post(f"/api/v1/cases/{case_id}/invoices", json={"amount": 100}, headers=auth_headers)

    res = client.delete(f"/api/v1/cases/{case_id}", headers=auth_headers)
    assert res.status_code == 204

    listed = client.get("/api/v1/cases", headers=auth_headers).json()
    assert case_id not in [c["id"] for c in listed]

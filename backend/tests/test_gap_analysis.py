import uuid


def _make_client(client, auth_headers, **overrides):
    payload = {"first_name": "Juan", "last_name": "Perez"}
    payload.update(overrides)
    res = client.post("/api/v1/clients", json=payload, headers=auth_headers)
    assert res.status_code == 201, res.text
    return res.json()


def test_gap_analysis_requires_auth(client, make_case):
    case = make_case()
    # make_case logs in via auth_headers/admin_tokens, which leaves valid
    # session cookies on this shared TestClient -- clear them so this
    # request is genuinely unauthenticated.
    client.cookies.clear()
    res = client.get(f"/api/v1/cases/{case['id']}/gap-analysis")
    assert res.status_code == 401


def test_gap_analysis_for_missing_case_returns_404(client, auth_headers):
    res = client.get("/api/v1/cases/00000000-0000-0000-0000-000000000000/gap-analysis", headers=auth_headers)
    assert res.status_code == 404


def test_gap_analysis_flags_case_with_no_participants(client, auth_headers, make_case):
    case = make_case()
    res = client.get(f"/api/v1/cases/{case['id']}/gap-analysis", headers=auth_headers)
    assert res.status_code == 200
    gaps = res.json()["gaps"]
    assert len(gaps) == 1
    assert gaps[0]["code"] == "no_participants"


def test_gap_analysis_flags_missing_petitioner_and_documents(client, auth_headers, make_case):
    case = make_case()  # family_based
    beneficiary = _make_client(client, auth_headers, marital_status="married")
    client.post(
        f"/api/v1/cases/{case['id']}/participants",
        json={"client_id": beneficiary["id"], "role": "beneficiary"},
        headers=auth_headers,
    )

    gaps = client.get(f"/api/v1/cases/{case['id']}/gap-analysis", headers=auth_headers).json()["gaps"]
    codes = {g["code"] for g in gaps}
    assert "missing_petitioner" in codes
    assert "missing_photo_id" in codes
    assert "missing_birth_certificate" in codes
    assert "missing_marriage_certificate" in codes
    assert "incomplete_profile" in codes


def test_gap_analysis_clears_once_requirements_are_met(client, auth_headers, make_case, db_session):
    from app.models.document import Document, DocumentType

    case = make_case()
    common_profile = dict(
        date_of_birth="1990-01-01",
        country_of_birth="Mexico",
        nationality="Mexican",
        address_line="123 Main St",
    )
    petitioner = _make_client(client, auth_headers, first_name="Maria", last_name="Lopez", **common_profile)
    beneficiary = _make_client(
        client, auth_headers, marital_status="married", **common_profile
    )
    client.post(
        f"/api/v1/cases/{case['id']}/participants",
        json={"client_id": petitioner["id"], "role": "petitioner"},
        headers=auth_headers,
    )
    client.post(
        f"/api/v1/cases/{case['id']}/participants",
        json={"client_id": beneficiary["id"], "role": "beneficiary"},
        headers=auth_headers,
    )

    # Petitioner only needs a photo ID (that check applies to every
    # participant); beneficiary additionally needs a birth certificate
    # (beneficiary/derivative-only) and a marriage certificate (married-only).
    db_session.add(
        Document(
            client_id=uuid.UUID(petitioner["id"]),
            case_id=uuid.UUID(case["id"]),
            document_type=DocumentType.PASSPORT,
            original_filename="passport.pdf",
            storage_path="/tmp/passport.pdf",
        )
    )
    for doc_type in (DocumentType.PASSPORT, DocumentType.BIRTH_CERTIFICATE, DocumentType.MARRIAGE_CERTIFICATE):
        db_session.add(
            Document(
                client_id=uuid.UUID(beneficiary["id"]),
                case_id=uuid.UUID(case["id"]),
                document_type=doc_type,
                original_filename=f"{doc_type.value}.pdf",
                storage_path=f"/tmp/{doc_type.value}.pdf",
            )
        )
    db_session.commit()

    gaps = client.get(f"/api/v1/cases/{case['id']}/gap-analysis", headers=auth_headers).json()["gaps"]
    assert gaps == []


def test_gap_analysis_reference_checklist_is_empty_with_no_generated_forms(client, auth_headers, make_case):
    case = make_case()
    body = client.get(f"/api/v1/cases/{case['id']}/gap-analysis", headers=auth_headers).json()
    assert body["reference_checklist"] == []


def test_gap_analysis_reference_checklist_includes_forms_with_a_library_entry(client, auth_headers, make_case):
    from app.seed_forms import seed as seed_forms

    seed_forms()
    case = make_case()

    # I-130 has a curated requirements entry (see app/seed_data/uscis_requirements.py);
    # G-28 deliberately does not.
    client.post(f"/api/v1/cases/{case['id']}/forms", json={"form_code": "I-130"}, headers=auth_headers)
    client.post(f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers)

    body = client.get(f"/api/v1/cases/{case['id']}/gap-analysis", headers=auth_headers).json()
    codes = {ref["form_code"] for ref in body["reference_checklist"]}
    assert codes == {"I-130"}
    entry = body["reference_checklist"][0]
    assert entry["source_url"].startswith("https://www.uscis.gov/")
    assert len(entry["categories"]) > 0

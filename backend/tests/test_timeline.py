import pytest

from app.seed_forms import seed as seed_forms


@pytest.fixture
def seeded_forms():
    seed_forms()


def test_timeline_requires_auth(client, make_case):
    case = make_case()
    # make_case logs in via auth_headers/admin_tokens, which leaves valid
    # session cookies on this shared TestClient -- clear them so this
    # request is genuinely unauthenticated.
    client.cookies.clear()
    res = client.get(f"/api/v1/cases/{case['id']}/timeline")
    assert res.status_code == 401


def test_timeline_for_missing_case_returns_404(client, auth_headers):
    res = client.get("/api/v1/cases/00000000-0000-0000-0000-000000000000/timeline", headers=auth_headers)
    assert res.status_code == 404


def test_fresh_case_timeline_is_intake_done_contract_current(client, auth_headers, make_case):
    case = make_case()
    res = client.get(f"/api/v1/cases/{case['id']}/timeline", headers=auth_headers)
    assert res.status_code == 200
    steps = {s["key"]: s["status"] for s in res.json()["steps"]}
    assert steps["intake"] == "done"
    assert steps["contract"] == "current"
    assert steps["forms"] == "pending"
    assert steps["decision"] == "pending"


def test_timeline_advances_as_service_and_documents_are_added(client, auth_headers, make_case, seeded_forms, db_session):
    import uuid

    from app.models.document import Document, DocumentType

    case = make_case()

    service = client.post(
        "/api/v1/services",
        json={
            "name": "Family Petition",
            "form_template_codes": ["G-28"],
            "checklist_items": [],
            "stages": ["Intake"],
        },
        headers=auth_headers,
    ).json()
    client.post(f"/api/v1/cases/{case['id']}/apply-service", json={"service_id": service["id"]}, headers=auth_headers)

    # Applying a service both attaches the contract and auto-generates every
    # form it bundles (see services.py::apply_service), so both gates clear
    # in the same step.
    steps = {
        s["key"]: s["status"]
        for s in client.get(f"/api/v1/cases/{case['id']}/timeline", headers=auth_headers).json()["steps"]
    }
    assert steps["contract"] == "done"
    assert steps["forms"] == "done"
    assert steps["evidence"] == "current"

    db_session.add(
        Document(
            case_id=uuid.UUID(case["id"]),
            document_type=DocumentType.EVIDENCE,
            original_filename="evidence.pdf",
            storage_path="/tmp/evidence.pdf",
        )
    )
    db_session.commit()

    steps = {
        s["key"]: s["status"]
        for s in client.get(f"/api/v1/cases/{case['id']}/timeline", headers=auth_headers).json()["steps"]
    }
    assert steps["evidence"] == "done"
    # This service bundled no checklist items, so "prepared" (which requires
    # a non-empty, fully-done checklist) can never be satisfied -- it becomes
    # the permanent blocking gate, which is the correct/expected outcome.
    assert steps["prepared"] == "current"


def test_timeline_gating_stays_sequential_even_if_a_later_condition_is_already_true(client, auth_headers, make_case):
    case = make_case()
    # Jump straight to "approved" without ever setting up a service, forms,
    # or documents -- "decision" is technically true, but the display must
    # not skip ahead of the earlier gates that were never actually met.
    client.patch(f"/api/v1/cases/{case['id']}", json={"status": "approved"}, headers=auth_headers)

    steps = {
        s["key"]: s["status"]
        for s in client.get(f"/api/v1/cases/{case['id']}/timeline", headers=auth_headers).json()["steps"]
    }
    assert steps["contract"] == "current"
    assert steps["filed"] == "pending"
    assert steps["decision"] == "pending"


def test_public_portal_exposes_the_same_timeline(client, auth_headers, make_case, seeded_forms):
    case = make_case()
    generated = client.post(f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=auth_headers).json()
    token = generated["access_token"]

    res = client.get(f"/api/v1/public/forms/{token}/timeline")
    assert res.status_code == 200
    body = res.json()
    assert body["case_number"] == case["case_number"]
    assert body["steps"][0] == {"key": "intake", "status": "done"}

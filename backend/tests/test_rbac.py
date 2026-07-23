"""A paralegal account is fully trusted for routine casework (intake,
checklist, applying a service, RFE/appointment creation) -- this despacho's
existing design is shared firm-wide visibility, not per-user siloing (see
notifications' global feed). What a paralegal must NOT be able to do alone
is delete case/client/billing/RFE/document/appointment records or move
money (create/edit invoices, record/delete payments): see
app.api.deps.require_roles for the reasoning."""

import pytest


@pytest.fixture
def seeded_forms():
    from app.seed_forms import seed as seed_forms

    seed_forms()


def test_paralegal_cannot_delete_case(client, auth_headers, paralegal_headers, make_case):
    case = make_case()
    res = client.delete(f"/api/v1/cases/{case['id']}", headers=paralegal_headers)
    assert res.status_code == 403

    # An admin/attorney doing the exact same request still works.
    res = client.delete(f"/api/v1/cases/{case['id']}", headers=auth_headers)
    assert res.status_code == 204


def test_paralegal_cannot_delete_client(client, auth_headers, paralegal_headers):
    client_res = client.post(
        "/api/v1/clients", json={"first_name": "Test", "last_name": "Client"}, headers=auth_headers
    )
    client_id = client_res.json()["id"]

    res = client.delete(f"/api/v1/clients/{client_id}", headers=paralegal_headers)
    assert res.status_code == 403


def test_paralegal_cannot_create_or_edit_invoices(client, auth_headers, paralegal_headers, make_case):
    case = make_case()

    res = client.post(f"/api/v1/cases/{case['id']}/invoices", json={"amount": 100}, headers=paralegal_headers)
    assert res.status_code == 403

    invoice = client.post(f"/api/v1/cases/{case['id']}/invoices", json={"amount": 100}, headers=auth_headers).json()
    res = client.patch(f"/api/v1/invoices/{invoice['id']}", json={"amount": 200}, headers=paralegal_headers)
    assert res.status_code == 403


def test_paralegal_cannot_delete_invoice(client, auth_headers, paralegal_headers, make_case):
    case = make_case()
    invoice = client.post(f"/api/v1/cases/{case['id']}/invoices", json={"amount": 100}, headers=auth_headers).json()

    res = client.delete(f"/api/v1/invoices/{invoice['id']}", headers=paralegal_headers)
    assert res.status_code == 403


def test_paralegal_cannot_add_or_delete_payments(client, auth_headers, paralegal_headers, make_case):
    case = make_case()
    invoice = client.post(f"/api/v1/cases/{case['id']}/invoices", json={"amount": 100}, headers=auth_headers).json()

    res = client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"amount": 50, "method": "cash"},
        headers=paralegal_headers,
    )
    assert res.status_code == 403

    payment = client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"amount": 50, "method": "cash"},
        headers=auth_headers,
    ).json()["payments"][0]
    res = client.delete(
        f"/api/v1/invoices/{invoice['id']}/payments/{payment['id']}", headers=paralegal_headers
    )
    assert res.status_code == 403


def test_paralegal_cannot_delete_rfe(client, auth_headers, paralegal_headers, make_case):
    case = make_case()
    rfe = client.post(
        f"/api/v1/cases/{case['id']}/rfes", json={"received_date": "2026-01-01"}, headers=auth_headers
    ).json()

    res = client.delete(f"/api/v1/rfes/{rfe['id']}", headers=paralegal_headers)
    assert res.status_code == 403


def test_paralegal_cannot_delete_document(client, auth_headers, paralegal_headers, make_case):
    case = make_case()
    doc = client.post(
        f"/api/v1/cases/{case['id']}/documents",
        files={"file": ("passport.pdf", b"%PDF-1.4 test", "application/pdf")},
        data={"document_type": "passport"},
        headers=auth_headers,
    ).json()

    res = client.delete(f"/api/v1/documents/{doc['id']}", headers=paralegal_headers)
    assert res.status_code == 403


def test_paralegal_cannot_delete_appointment(client, auth_headers, paralegal_headers, make_case):
    case = make_case()
    appt = client.post(
        f"/api/v1/cases/{case['id']}/appointments",
        json={"appointment_type": "consultation", "scheduled_at": "2030-01-01T10:00:00Z"},
        headers=auth_headers,
    ).json()

    res = client.delete(f"/api/v1/appointments/{appt['id']}", headers=paralegal_headers)
    assert res.status_code == 403


def test_paralegal_can_still_do_routine_casework(client, auth_headers, paralegal_headers, make_case, seeded_forms):
    # The point of this RBAC pass isn't to lock paralegals out of day-to-day
    # work -- only destructive/financial actions AND case/client creation
    # (CLAUDE.md H1: "paralegal must NOT create cases/invoices/delete
    # everything", reaffirmed by the 2026-07-22 security review). Checklist,
    # RFE creation, appointment creation, and form generation on an existing
    # case all stay open -- only the initial case record itself now requires
    # intake/legal_assistant/attorney/admin/owner.
    case = make_case()

    res = client.post(
        f"/api/v1/cases/{case['id']}/rfes", json={"received_date": "2026-01-01"}, headers=paralegal_headers
    )
    assert res.status_code == 201

    res = client.post(
        f"/api/v1/cases/{case['id']}/appointments",
        json={"appointment_type": "consultation", "scheduled_at": "2030-01-01T10:00:00Z"},
        headers=paralegal_headers,
    )
    assert res.status_code == 201

    res = client.post(f"/api/v1/cases/{case['id']}/forms", json={"form_code": "G-28"}, headers=paralegal_headers)
    assert res.status_code == 201


def test_paralegal_cannot_create_a_case(client, paralegal_headers):
    res = client.post(
        "/api/v1/cases",
        json={"case_number": "PARALEGAL-TEST-2", "case_type": "family_based", "status": "intake"},
        headers=paralegal_headers,
    )
    assert res.status_code == 403

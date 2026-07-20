"""The audit log records who did what for destructive/financial actions
(see app.services.audit.log_action, wired into cases/clients/billing/
rfes/documents/appointments delete + billing create/update). Reviewing it
is admin-only (RequireAdmin, narrower than RequireAdminOrAttorney) -- see
app.api.deps for the reasoning."""


def test_deleting_a_case_creates_an_audit_log_entry(client, auth_headers, make_case):
    case = make_case()
    res = client.delete(f"/api/v1/cases/{case['id']}", headers=auth_headers)
    assert res.status_code == 204

    res = client.get("/api/v1/audit-log", headers=auth_headers)
    assert res.status_code == 200
    entries = res.json()
    matches = [e for e in entries if e["action"] == "case.deleted" and e["entity_id"] == case["id"]]
    assert len(matches) == 1
    entry = matches[0]
    assert entry["entity_type"] == "case"
    assert entry["details"]["case_number"] == case["case_number"]
    assert entry["user_name"] == "Test admin"


def test_invoice_actions_create_audit_log_entries(client, auth_headers, make_case):
    case = make_case()
    invoice = client.post(
        f"/api/v1/cases/{case['id']}/invoices", json={"amount": 100}, headers=auth_headers
    ).json()
    client.patch(f"/api/v1/invoices/{invoice['id']}", json={"amount": 150}, headers=auth_headers)
    payment = client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"amount": 50, "method": "cash"},
        headers=auth_headers,
    ).json()["payments"][0]
    client.delete(f"/api/v1/invoices/{invoice['id']}/payments/{payment['id']}", headers=auth_headers)
    client.delete(f"/api/v1/invoices/{invoice['id']}", headers=auth_headers)

    res = client.get("/api/v1/audit-log?entity_type=invoice", headers=auth_headers)
    actions = {e["action"] for e in res.json() if e["entity_id"] == invoice["id"]}
    assert actions == {"invoice.created", "invoice.updated", "invoice.deleted"}

    res = client.get("/api/v1/audit-log?entity_type=payment", headers=auth_headers)
    payment_actions = {e["action"] for e in res.json() if e["entity_id"] == payment["id"]}
    assert payment_actions == {"invoice.payment_added", "invoice.payment_deleted"}

    # amount/date fields in the details payload must have survived the
    # mode="json" dump (Enum/date -> JSON-safe) intact.
    updated_entry = next(
        e for e in res.json() if e["action"] == "invoice.payment_added" and e["entity_id"] == payment["id"]
    )
    assert updated_entry["details"]["method"] == "cash"


def test_audit_log_requires_admin(client, auth_headers, paralegal_headers, make_case):
    case = make_case()
    client.delete(f"/api/v1/cases/{case['id']}", headers=auth_headers)

    res = client.get("/api/v1/audit-log", headers=paralegal_headers)
    assert res.status_code == 403


def test_audit_log_requires_auth(client, auth_headers, make_case):
    case = make_case()
    client.delete(f"/api/v1/cases/{case['id']}", headers=auth_headers)

    client.cookies.clear()
    res = client.get("/api/v1/audit-log")
    assert res.status_code == 401

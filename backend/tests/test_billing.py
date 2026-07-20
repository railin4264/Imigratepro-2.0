from datetime import date, timedelta


def test_invoices_require_auth(client, make_case):
    case = make_case()
    res = client.post(f"/api/v1/cases/{case['id']}/invoices", json={"amount": 100})
    assert res.status_code == 401


def test_invoice_number_autoincrements(client, auth_headers, make_case):
    case = make_case()
    first = client.post(f"/api/v1/cases/{case['id']}/invoices", json={"amount": 100}, headers=auth_headers)
    second = client.post(f"/api/v1/cases/{case['id']}/invoices", json={"amount": 200}, headers=auth_headers)
    assert first.json()["invoice_number"] != second.json()["invoice_number"]


def test_payment_recalculates_balance_and_status(client, auth_headers, make_case):
    case = make_case()
    invoice = client.post(
        f"/api/v1/cases/{case['id']}/invoices",
        json={"description": "Filing fee", "amount": 500},
        headers=auth_headers,
    ).json()
    assert invoice["status"] == "draft"
    assert invoice["amount_paid"] == 0

    partial = client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"amount": 200, "method": "card"},
        headers=auth_headers,
    )
    assert partial.status_code == 201
    assert partial.json()["status"] == "partially_paid"
    assert partial.json()["amount_paid"] == 200

    full = client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"amount": 300, "method": "cash"},
        headers=auth_headers,
    )
    assert full.json()["status"] == "paid"
    assert full.json()["amount_paid"] == 500
    assert full.json()["paid_at"] is not None


def test_deleting_a_payment_recalculates_balance(client, auth_headers, make_case):
    case = make_case()
    invoice = client.post(
        f"/api/v1/cases/{case['id']}/invoices", json={"amount": 400}, headers=auth_headers
    ).json()
    payment = client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"amount": 400, "method": "cash"},
        headers=auth_headers,
    ).json()
    assert payment["status"] == "paid"

    after_delete = client.delete(
        f"/api/v1/invoices/{invoice['id']}/payments/{payment['payments'][0]['id']}", headers=auth_headers
    )
    assert after_delete.status_code == 200
    assert after_delete.json()["amount_paid"] == 0
    assert after_delete.json()["status"] != "paid"


def test_invoice_rejects_zero_or_negative_amount(client, auth_headers, make_case):
    case = make_case()
    for amount in (0, -50):
        res = client.post(f"/api/v1/cases/{case['id']}/invoices", json={"amount": amount}, headers=auth_headers)
        assert res.status_code == 422, amount


def test_invoice_update_rejects_zero_or_negative_amount(client, auth_headers, make_case):
    case = make_case()
    invoice = client.post(f"/api/v1/cases/{case['id']}/invoices", json={"amount": 100}, headers=auth_headers).json()
    res = client.patch(f"/api/v1/invoices/{invoice['id']}", json={"amount": -10}, headers=auth_headers)
    assert res.status_code == 422


def test_payment_rejects_zero_or_negative_amount(client, auth_headers, make_case):
    case = make_case()
    invoice = client.post(f"/api/v1/cases/{case['id']}/invoices", json={"amount": 100}, headers=auth_headers).json()
    for amount in (0, -25):
        res = client.post(
            f"/api/v1/invoices/{invoice['id']}/payments", json={"amount": amount, "method": "cash"}, headers=auth_headers
        )
        assert res.status_code == 422, amount


def test_mark_overdue_flags_past_due_invoices_and_notifies(client, auth_headers, make_case, monkeypatch):
    monkeypatch.setattr("app.services.reminders.email.send", lambda to, subject, body: True)

    case = make_case()
    invoice = client.post(
        f"/api/v1/cases/{case['id']}/invoices",
        json={"amount": 300, "due_date": str(date.today() - timedelta(days=5))},
        headers=auth_headers,
    ).json()
    # Move it out of draft so it's eligible for the overdue sweep.
    client.patch(f"/api/v1/invoices/{invoice['id']}", json={"status": "sent"}, headers=auth_headers)

    res = client.post("/api/v1/invoices/mark-overdue", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["marked_overdue"] == 1

    refreshed = client.get(f"/api/v1/invoices/{invoice['id']}", headers=auth_headers).json()
    assert refreshed["status"] == "overdue"

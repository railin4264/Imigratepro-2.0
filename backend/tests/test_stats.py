from datetime import datetime, timedelta, timezone


def test_stats_require_auth(client):
    res = client.get("/api/v1/stats/overview")
    assert res.status_code == 401


def test_overview_with_no_data(client, auth_headers):
    res = client.get("/api/v1/stats/overview", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total_cases"] == 0
    assert body["total_invoiced"] == 0


def test_overview_with_upcoming_appointment_does_not_crash(client, auth_headers, make_case):
    """Regression test: SQLite hands back naive datetimes for
    DateTime(timezone=True) columns, and comparing those directly against an
    aware `datetime.now(timezone.utc)` in Python (not in a SQL filter) used
    to raise `TypeError: can't compare offset-naive and offset-aware
    datetimes` -- see app/api/v1/endpoints/stats.py's _as_aware helper."""

    case = make_case()
    soon = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    client.post(
        f"/api/v1/cases/{case['id']}/appointments",
        json={"appointment_type": "consultation", "scheduled_at": soon},
        headers=auth_headers,
    )

    res = client.get("/api/v1/stats/overview", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["upcoming_appointments_7d"] == 1


def test_overview_reflects_invoices_and_payments(client, auth_headers, make_case):
    case = make_case()
    invoice = client.post(
        f"/api/v1/cases/{case['id']}/invoices", json={"amount": 500}, headers=auth_headers
    ).json()
    client.post(
        f"/api/v1/invoices/{invoice['id']}/payments",
        json={"amount": 200, "method": "cash"},
        headers=auth_headers,
    )

    res = client.get("/api/v1/stats/overview", headers=auth_headers)
    body = res.json()
    assert body["total_invoiced"] == 500
    assert body["total_collected"] == 200
    assert body["total_outstanding"] == 300


def test_revenue_by_month(client, auth_headers, make_case):
    case = make_case()
    client.post(f"/api/v1/cases/{case['id']}/invoices", json={"amount": 100}, headers=auth_headers)

    res = client.get("/api/v1/stats/revenue", params={"months": 3}, headers=auth_headers)
    assert res.status_code == 200
    points = res.json()
    assert len(points) == 3
    assert sum(p["invoiced"] for p in points) == 100

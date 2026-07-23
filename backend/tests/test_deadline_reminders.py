import uuid
from datetime import date, datetime, timedelta, timezone


def test_send_case_deadline_reminders_marks_due_cases_and_notifies(client, auth_headers, make_case, monkeypatch):
    sent_emails = []
    monkeypatch.setattr(
        "app.services.reminders.email.send",
        lambda to, subject, body: sent_emails.append((to, subject)) or True,
    )

    case = make_case()
    soon = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    updated = client.patch(f"/api/v1/cases/{case['id']}", json={"decision_deadline": soon}, headers=auth_headers)
    assert updated.status_code == 200

    res = client.post("/api/v1/cases/send-deadline-reminders", params={"days_ahead": 14}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["reminders_sent"] == 1
    assert len(sent_emails) == 1

    # Running it again shouldn't re-send.
    res2 = client.post("/api/v1/cases/send-deadline-reminders", params={"days_ahead": 14}, headers=auth_headers)
    assert res2.json()["reminders_sent"] == 0


def test_send_case_deadline_reminders_ignores_deadlines_outside_the_window(client, auth_headers, make_case):
    case = make_case()
    far_future = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
    client.patch(f"/api/v1/cases/{case['id']}", json={"decision_deadline": far_future}, headers=auth_headers)

    res = client.post("/api/v1/cases/send-deadline-reminders", params={"days_ahead": 14}, headers=auth_headers)
    assert res.json()["reminders_sent"] == 0


def test_send_rfe_deadline_reminders_marks_due_open_rfes_and_notifies(client, auth_headers, make_case, monkeypatch):
    sent_emails = []
    monkeypatch.setattr(
        "app.services.reminders.email.send",
        lambda to, subject, body: sent_emails.append((to, subject)) or True,
    )

    case = make_case()
    due_soon = (date.today() + timedelta(days=3)).isoformat()
    create = client.post(
        f"/api/v1/cases/{case['id']}/rfes",
        json={"received_date": date.today().isoformat(), "response_due_date": due_soon},
        headers=auth_headers,
    )
    assert create.status_code == 201

    res = client.post("/api/v1/rfes/send-deadline-reminders", params={"days_ahead": 7}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["reminders_sent"] == 1
    assert len(sent_emails) == 1

    # Running it again shouldn't re-send.
    res2 = client.post("/api/v1/rfes/send-deadline-reminders", params={"days_ahead": 7}, headers=auth_headers)
    assert res2.json()["reminders_sent"] == 0


def test_send_rfe_deadline_reminders_ignores_responded_rfes(client, auth_headers, make_case):
    case = make_case()
    due_soon = (date.today() + timedelta(days=3)).isoformat()
    create = client.post(
        f"/api/v1/cases/{case['id']}/rfes",
        json={"received_date": date.today().isoformat(), "response_due_date": due_soon},
        headers=auth_headers,
    )
    rfe_id = create.json()["id"]

    patched = client.patch(f"/api/v1/rfes/{rfe_id}", json={"status": "responded"}, headers=auth_headers)
    assert patched.status_code == 200

    res = client.post("/api/v1/rfes/send-deadline-reminders", params={"days_ahead": 7}, headers=auth_headers)
    assert res.json()["reminders_sent"] == 0

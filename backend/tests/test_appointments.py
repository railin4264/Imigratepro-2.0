import uuid
from datetime import datetime, timedelta, timezone


def test_appointments_require_auth(client, make_case):
    case = make_case()
    res = client.post(f"/api/v1/cases/{case['id']}/appointments", json={"appointment_type": "consultation", "scheduled_at": "2030-01-01T10:00:00Z"})
    assert res.status_code == 401


def test_create_appointment_for_missing_case_returns_404(client, auth_headers):
    res = client.post(
        "/api/v1/cases/00000000-0000-0000-0000-000000000000/appointments",
        json={"appointment_type": "consultation", "scheduled_at": "2030-01-01T10:00:00Z"},
        headers=auth_headers,
    )
    assert res.status_code == 404


def test_appointment_crud_flow(client, auth_headers, make_case):
    case = make_case()
    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()

    create = client.post(
        f"/api/v1/cases/{case['id']}/appointments",
        json={
            "appointment_type": "biometrics",
            "scheduled_at": scheduled_at,
            "location": "USCIS Field Office",
        },
        headers=auth_headers,
    )
    assert create.status_code == 201
    appointment = create.json()
    assert appointment["case_number"] == case["case_number"]
    assert appointment["reminder_sent"] is False

    listed = client.get(f"/api/v1/cases/{case['id']}/appointments", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch(
        f"/api/v1/appointments/{appointment['id']}",
        json={"location": "Different office"},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["location"] == "Different office"

    deleted = client.delete(f"/api/v1/appointments/{appointment['id']}", headers=auth_headers)
    assert deleted.status_code == 204

    listed_again = client.get(f"/api/v1/cases/{case['id']}/appointments", headers=auth_headers)
    assert listed_again.json() == []


def test_rescheduling_clears_reminder_sent_flag(client, auth_headers, make_case, db_session):
    from app.models.appointment import Appointment

    case = make_case()
    scheduled_at = datetime.now(timezone.utc) + timedelta(hours=1)
    create = client.post(
        f"/api/v1/cases/{case['id']}/appointments",
        json={"appointment_type": "interview", "scheduled_at": scheduled_at.isoformat()},
        headers=auth_headers,
    )
    appointment_id = create.json()["id"]

    # Force reminder_sent True directly, then reschedule via the API.
    row = db_session.get(Appointment, uuid.UUID(appointment_id))
    row.reminder_sent = True
    db_session.commit()

    new_time = (scheduled_at + timedelta(days=1)).isoformat()
    updated = client.patch(
        f"/api/v1/appointments/{appointment_id}", json={"scheduled_at": new_time}, headers=auth_headers
    )
    assert updated.status_code == 200
    assert updated.json()["reminder_sent"] is False


def test_send_reminders_marks_due_appointments_and_notifies(client, auth_headers, make_case, monkeypatch):
    sent_emails = []
    monkeypatch.setattr(
        "app.services.reminders.email.send",
        lambda to, subject, body: sent_emails.append((to, subject)) or True,
    )

    case = make_case()
    soon = (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat()
    create = client.post(
        f"/api/v1/cases/{case['id']}/appointments",
        json={"appointment_type": "court_hearing", "scheduled_at": soon},
        headers=auth_headers,
    )
    appointment_id = create.json()["id"]

    res = client.post("/api/v1/appointments/send-reminders", params={"hours_ahead": 48}, headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["reminders_sent"] == 1

    refreshed = client.get(f"/api/v1/cases/{case['id']}/appointments", headers=auth_headers).json()
    assert next(a for a in refreshed if a["id"] == appointment_id)["reminder_sent"] is True

    # Running it again shouldn't re-send.
    res2 = client.post("/api/v1/appointments/send-reminders", params={"hours_ahead": 48}, headers=auth_headers)
    assert res2.json()["reminders_sent"] == 0

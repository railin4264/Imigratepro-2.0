import uuid
from datetime import date, timedelta


def test_my_day_requires_auth(client):
    res = client.get("/api/v1/dashboard/me")
    assert res.status_code == 401


def test_my_day_empty_for_user_with_no_cases(client, auth_headers):
    res = client.get("/api/v1/dashboard/me", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body == {
        "assigned_case_count": 0,
        "appointments_today": [],
        "checklist_due": [],
        "open_rfes": [],
        "cases_ready_for_review": [],
    }


def test_my_day_counts_assigned_cases_and_open_rfes(client, auth_headers, admin_user, make_case):
    case = make_case()
    client.patch(
        f"/api/v1/cases/{case['id']}", json={"assigned_attorney_id": str(admin_user.id)}, headers=auth_headers
    )
    client.post(f"/api/v1/cases/{case['id']}/rfes", json={"received_date": "2026-01-01"}, headers=auth_headers)

    # A case assigned to someone else shouldn't count.
    other_case = make_case()
    client.post(f"/api/v1/cases/{other_case['id']}/rfes", json={"received_date": "2026-01-01"}, headers=auth_headers)

    body = client.get("/api/v1/dashboard/me", headers=auth_headers).json()
    assert body["assigned_case_count"] == 1
    assert len(body["open_rfes"]) == 1
    assert body["open_rfes"][0]["case_id"] == case["id"]


def test_my_day_checklist_due_ignores_future_due_dates(client, auth_headers, admin_user, make_case, db_session):
    from app.models.service import CaseChecklistItem, ChecklistPriority

    case = make_case()
    overdue_item = CaseChecklistItem(
        case_id=uuid.UUID(case["id"]),
        label="Gather birth certificate",
        order=0,
        assigned_to_id=admin_user.id,
        due_date=date.today() - timedelta(days=1),
        priority=ChecklistPriority.HIGH,
    )
    future_item = CaseChecklistItem(
        case_id=uuid.UUID(case["id"]),
        label="Schedule biometrics",
        order=1,
        assigned_to_id=admin_user.id,
        due_date=date.today() + timedelta(days=30),
        priority=ChecklistPriority.LOW,
    )
    db_session.add_all([overdue_item, future_item])
    db_session.commit()

    body = client.get("/api/v1/dashboard/me", headers=auth_headers).json()
    assert len(body["checklist_due"]) == 1
    assert body["checklist_due"][0]["label"] == "Gather birth certificate"
    assert body["checklist_due"][0]["overdue"] is True


def test_my_day_ready_for_review_requires_preparing_status_and_complete_checklist(
    client, auth_headers, admin_user, make_case, db_session
):
    from app.models.service import CaseChecklistItem, ChecklistPriority

    case = make_case()
    client.patch(
        f"/api/v1/cases/{case['id']}",
        json={"assigned_attorney_id": str(admin_user.id), "status": "preparing"},
        headers=auth_headers,
    )
    item = CaseChecklistItem(
        case_id=uuid.UUID(case["id"]), label="Collect passport", order=0, priority=ChecklistPriority.MEDIUM
    )
    db_session.add(item)
    db_session.commit()

    not_ready = client.get("/api/v1/dashboard/me", headers=auth_headers).json()
    assert not_ready["cases_ready_for_review"] == []

    db_session.refresh(item)
    item.done = True
    db_session.commit()

    ready = client.get("/api/v1/dashboard/me", headers=auth_headers).json()
    assert len(ready["cases_ready_for_review"]) == 1
    assert ready["cases_ready_for_review"][0]["id"] == case["id"]

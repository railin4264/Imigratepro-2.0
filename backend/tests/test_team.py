import uuid
from datetime import date, timedelta


def test_workload_requires_auth(client):
    res = client.get("/api/v1/users/workload")
    assert res.status_code == 401


def test_workload_route_not_shadowed_by_user_id_route(client, auth_headers):
    # Regression test: /users/workload must be registered *before*
    # /users/{user_id}, or FastAPI matches "workload" as a user_id path
    # param first and returns 422 instead of ever reaching this route --
    # same class of bug fixed for /rfes/ai-status.
    res = client.get("/api/v1/users/workload", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_workload_reflects_assigned_cases_rfes_and_overdue_checklist(
    client, auth_headers, admin_user, make_case, db_session
):
    from app.models.service import CaseChecklistItem

    case = make_case()
    client.patch(
        f"/api/v1/cases/{case['id']}", json={"assigned_attorney_id": str(admin_user.id)}, headers=auth_headers
    )
    client.post(f"/api/v1/cases/{case['id']}/rfes", json={"received_date": "2026-01-01"}, headers=auth_headers)
    db_session.add(
        CaseChecklistItem(
            case_id=uuid.UUID(case["id"]),
            label="Overdue item",
            order=0,
            assigned_to_id=admin_user.id,
            due_date=date.today() - timedelta(days=3),
        )
    )
    db_session.commit()

    workload = client.get("/api/v1/users/workload", headers=auth_headers).json()
    mine = next(w for w in workload if w["user"]["id"] == str(admin_user.id))
    assert mine["assigned_case_count"] == 1
    # Recording an RFE moves the case to "rfe" status (see rfes.py::create_rfe).
    assert mine["cases_by_status"] == {"rfe": 1}
    assert mine["open_rfe_count"] == 1
    assert mine["overdue_checklist_count"] == 1


def test_admin_can_update_another_users_role(client, auth_headers, paralegal_user):
    res = client.patch(f"/api/v1/users/{paralegal_user.id}", json={"role": "attorney"}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["role"] == "attorney"


def test_non_admin_cannot_update_another_user(client, paralegal_user):
    login = client.post("/api/v1/auth/login", json={"email": paralegal_user.email, "password": "testpassword123"})
    paralegal_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    forbidden = client.patch(
        f"/api/v1/users/{paralegal_user.id}", json={"role": "admin"}, headers=paralegal_headers
    )
    assert forbidden.status_code == 403


def test_admin_cannot_deactivate_own_account(client, auth_headers, admin_user):
    res = client.patch(f"/api/v1/users/{admin_user.id}", json={"is_active": False}, headers=auth_headers)
    assert res.status_code == 400


def test_cannot_demote_the_last_active_admin(client, auth_headers, admin_user):
    res = client.patch(f"/api/v1/users/{admin_user.id}", json={"role": "attorney"}, headers=auth_headers)
    assert res.status_code == 400


def test_can_demote_admin_when_another_active_admin_exists(client, auth_headers, admin_user, db_session):
    from app.core.security import hash_password
    from app.models.user import User, UserRole

    other_admin = User(
        full_name="Other Admin", email="other-admin@test.local", role=UserRole.ADMIN, hashed_password=hash_password("x")
    )
    db_session.add(other_admin)
    db_session.commit()

    res = client.patch(f"/api/v1/users/{admin_user.id}", json={"role": "attorney"}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["role"] == "attorney"


def test_deactivated_staff_can_still_be_read_but_flagged_inactive(client, auth_headers, db_session):
    from app.core.security import hash_password
    from app.models.user import User, UserRole

    staff = User(
        full_name="Some Paralegal",
        email="some-paralegal@test.local",
        role=UserRole.PARALEGAL,
        hashed_password=hash_password("x"),
    )
    db_session.add(staff)
    db_session.commit()

    deactivated = client.patch(f"/api/v1/users/{staff.id}", json={"is_active": False}, headers=auth_headers)
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    fetched = client.get(f"/api/v1/users/{staff.id}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["is_active"] is False

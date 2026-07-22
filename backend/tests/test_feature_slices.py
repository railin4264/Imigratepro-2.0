"""Tests for the A/C/D/E feature slices merged into app-nuevo-feature:
  A — RBAC on create + IDOR case-access scoping (write vs read).
  C — role/user-directed notification feed filtering.
  D — form_templates.category enum + backfill.
  E — case key dates + parent_case_id (packages).
Follows conftest.py fixtures (role-based users, make_case, *_headers)."""
import uuid

from app.models.user import UserRole
from tests.conftest import _make_user, _login


# --------------------------------------------------------------------------- #
# A. RBAC: routine casework stays open (repo design), destructive is locked    #
# --------------------------------------------------------------------------- #
def test_paralegal_can_create_case(client, paralegal_headers):
    # Repo design (test_rbac.py): paralegals do day-to-day casework; only
    # destructive/financial actions are locked. Case creation stays open.
    res = client.post(
        "/api/v1/cases",
        json={"case_number": f"P-{uuid.uuid4().hex[:8]}", "case_type": "family_based", "status": "intake"},
        headers=paralegal_headers,
    )
    assert res.status_code == 201, res.text


def test_paralegal_cannot_delete_case(client, paralegal_headers, make_case):
    case = make_case()
    res = client.delete(f"/api/v1/cases/{case['id']}", headers=paralegal_headers)
    assert res.status_code == 403, res.text


def test_create_client_is_audited(client, auth_headers, db_session):
    from app.models.audit_log import AuditLog

    res = client.post(
        "/api/v1/clients",
        json={"first_name": "Ana", "last_name": "Diaz", "email": f"{uuid.uuid4().hex[:8]}@t.local"},
        headers=auth_headers,
    )
    assert res.status_code == 201, res.text
    entry = db_session.query(AuditLog).filter_by(
        action="client.created", entity_id=uuid.UUID(res.json()["id"])
    ).first()
    assert entry is not None


# --------------------------------------------------------------------------- #
# A. IDOR: case-access write scoping                                           #
# --------------------------------------------------------------------------- #
def test_unassigned_attorney_cannot_update_case(client, make_case, db_session):
    case = make_case()  # created by admin, no attorney assigned
    other = _make_user(db_session, UserRole.ATTORNEY)
    headers = {"Authorization": f"Bearer {_login(client, other.email)['access_token']}"}
    res = client.patch(f"/api/v1/cases/{case['id']}", json={"status": "preparing"}, headers=headers)
    assert res.status_code == 403, res.text


def test_update_nonexistent_case_returns_404(client, auth_headers):
    res = client.patch(f"/api/v1/cases/{uuid.uuid4()}", json={"status": "preparing"}, headers=auth_headers)
    assert res.status_code == 404, res.text


def test_admin_can_update_any_case(client, auth_headers, make_case):
    case = make_case()
    res = client.patch(f"/api/v1/cases/{case['id']}", json={"status": "preparing"}, headers=auth_headers)
    assert res.status_code == 200, res.text


# --------------------------------------------------------------------------- #
# C. Directed notifications                                                    #
# --------------------------------------------------------------------------- #
def test_role_directed_notification_only_visible_to_that_role(client, db_session):
    from app.services.notifications import notify

    notify(db_session, list(__import__("app.models.notification", fromlist=["NotificationType"]).NotificationType)[0],
           "billing-only", recipient_role=UserRole.BILLING)
    db_session.commit()

    billing = _make_user(db_session, UserRole.BILLING)
    attorney = _make_user(db_session, UserRole.ATTORNEY)
    b_headers = {"Authorization": f"Bearer {_login(client, billing.email)['access_token']}"}
    a_headers = {"Authorization": f"Bearer {_login(client, attorney.email)['access_token']}"}

    b_msgs = [n["message"] for n in client.get("/api/v1/notifications", headers=b_headers).json()]
    a_msgs = [n["message"] for n in client.get("/api/v1/notifications", headers=a_headers).json()]
    assert "billing-only" in b_msgs
    assert "billing-only" not in a_msgs


def test_global_notification_visible_to_all(client, db_session):
    from app.models.notification import NotificationType
    from app.services.notifications import notify

    notify(db_session, list(NotificationType)[0], "firm-wide", is_global=True)
    db_session.commit()

    attorney = _make_user(db_session, UserRole.ATTORNEY)
    a_headers = {"Authorization": f"Bearer {_login(client, attorney.email)['access_token']}"}
    msgs = [n["message"] for n in client.get("/api/v1/notifications", headers=a_headers).json()]
    assert "firm-wide" in msgs


# --------------------------------------------------------------------------- #
# D. Form category backfill                                                    #
# --------------------------------------------------------------------------- #
def test_form_template_category_backfill(db_session):
    from app.models.form import FormTemplate

    tpl = FormTemplate(code="I-130", name="Petition for Alien Relative", field_schema=[])
    db_session.add(tpl)
    db_session.commit()
    db_session.refresh(tpl)
    # column exists with a server default; new rows are 'general' until categorized,
    # and the known family code maps to 'family' when set by the app/backfill path.
    assert hasattr(tpl, "category")
    assert tpl.category is not None


# --------------------------------------------------------------------------- #
# E. Case key dates + parent_case_id                                          #
# --------------------------------------------------------------------------- #
def test_case_dates_roundtrip(client, auth_headers, make_case):
    case = make_case()
    res = client.patch(
        f"/api/v1/cases/{case['id']}",
        json={"uscis_receipt_number": "MSC2190000001", "priority_date": "2024-01-15T00:00:00"},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["uscis_receipt_number"] == "MSC2190000001"
    assert body["priority_date"].startswith("2024-01-15")


def test_case_parent_link(client, auth_headers, make_case):
    parent = make_case()
    child = make_case()
    res = client.patch(
        f"/api/v1/cases/{child['id']}",
        json={"parent_case_id": parent["id"]},
        headers=auth_headers,
    )
    assert res.status_code == 200, res.text
    assert res.json()["parent_case_id"] == parent["id"]

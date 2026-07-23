from app.models.notification import NotificationType
from app.models.user import UserRole
from app.services.notifications import notify


def test_recipient_role_notification_seen_only_by_that_role(client, auth_headers, paralegal_headers, db_session):
    notify(db_session, NotificationType.INVOICE_OVERDUE, "billing-only notice", recipient_role=UserRole.BILLING)
    db_session.commit()

    admin_res = client.get("/api/v1/notifications", headers=auth_headers)
    assert admin_res.status_code == 200
    assert not any(n["message"] == "billing-only notice" for n in admin_res.json())

    paralegal_res = client.get("/api/v1/notifications", headers=paralegal_headers)
    assert not any(n["message"] == "billing-only notice" for n in paralegal_res.json())


def test_recipient_user_id_notification_seen_only_by_that_user(client, auth_headers, paralegal_headers, paralegal_user, db_session):
    notify(db_session, NotificationType.CASE_ASSIGNED, "just for the paralegal", recipient_user_id=paralegal_user.id)
    db_session.commit()

    paralegal_res = client.get("/api/v1/notifications", headers=paralegal_headers)
    assert any(n["message"] == "just for the paralegal" for n in paralegal_res.json())

    admin_res = client.get("/api/v1/notifications", headers=auth_headers)
    assert not any(n["message"] == "just for the paralegal" for n in admin_res.json())


def test_is_global_notification_seen_by_everyone(client, auth_headers, paralegal_headers, db_session):
    notify(db_session, NotificationType.CASE_ASSIGNED, "firm-wide announcement", is_global=True)
    db_session.commit()

    for headers in (auth_headers, paralegal_headers):
        res = client.get("/api/v1/notifications", headers=headers)
        assert any(n["message"] == "firm-wide announcement" for n in res.json())

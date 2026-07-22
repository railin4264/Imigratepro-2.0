from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.models.notification import Notification, NotificationSeen
from app.schemas.notification import MarkReadRequest, NotificationRead

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationRead])
def list_notifications(db: DbSession, current_user: CurrentUser, skip: int = 0, limit: int = 50):
    notifications = (
        db.query(Notification)
        .filter(
            (Notification.recipient_user_id == current_user.id)
            | (Notification.recipient_role == current_user.role)
            | (Notification.is_global == True)  # noqa: E712
            | (
                (Notification.recipient_user_id == None)  # noqa: E711
                & (Notification.recipient_role == None)  # noqa: E711
                & (Notification.is_global == False)  # noqa: E712
            )
        )
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    seen_ids = {
        row.notification_id
        for row in db.query(NotificationSeen.notification_id).filter(NotificationSeen.user_id == current_user.id)
    }
    return [
        NotificationRead(
            id=n.id,
            type=n.type,
            message=n.message,
            case_id=n.case_id,
            case_number=n.case.case_number if n.case else None,
            created_at=n.created_at,
            read=n.id in seen_ids,
        )
        for n in notifications
    ]


@router.post("/notifications/mark-read", status_code=204)
def mark_read(payload: MarkReadRequest, db: DbSession, current_user: CurrentUser):
    existing = {
        row.notification_id
        for row in db.query(NotificationSeen.notification_id).filter(
            NotificationSeen.user_id == current_user.id,
            NotificationSeen.notification_id.in_(payload.notification_ids),
        )
    }
    for notification_id in payload.notification_ids:
        if notification_id not in existing:
            db.add(NotificationSeen(user_id=current_user.id, notification_id=notification_id))
    db.commit()


@router.post("/notifications/mark-all-read", status_code=204)
def mark_all_read(db: DbSession, current_user: CurrentUser):
    already_seen = {
        row.notification_id
        for row in db.query(NotificationSeen.notification_id).filter(NotificationSeen.user_id == current_user.id)
    }
    query = db.query(Notification.id)
    if already_seen:
        query = query.filter(~Notification.id.in_(already_seen))
    for (notification_id,) in query:
        db.add(NotificationSeen(user_id=current_user.id, notification_id=notification_id))
    db.commit()

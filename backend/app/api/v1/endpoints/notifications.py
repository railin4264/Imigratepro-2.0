from fastapi import APIRouter

from app.api.deps import DbSession
from app.models.notification import Notification
from app.schemas.notification import NotificationRead

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationRead])
def list_notifications(db: DbSession, limit: int = 50):
    notifications = (
        db.query(Notification).order_by(Notification.created_at.desc()).limit(limit).all()
    )
    return [
        NotificationRead(
            id=n.id,
            type=n.type,
            message=n.message,
            case_id=n.case_id,
            case_number=n.case.case_number if n.case else None,
            created_at=n.created_at,
        )
        for n in notifications
    ]

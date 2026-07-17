import uuid

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType


def notify(db: Session, type: NotificationType, message: str, case_id: uuid.UUID | None = None) -> None:
    """Record an event in the shared notification feed. Callers are expected to
    commit as part of their existing transaction -- this only adds the row."""

    db.add(Notification(type=type, message=message, case_id=case_id))

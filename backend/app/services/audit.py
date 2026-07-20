import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def log_action(
    db: Session,
    user: User,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """Record a destructive/financial action for the compliance trail.
    Callers are expected to commit as part of their existing transaction --
    this only adds the row (same pattern as app.services.notifications.notify)."""

    db.add(
        AuditLog(
            user_id=user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
        )
    )

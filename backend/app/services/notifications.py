import uuid

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType
from app.models.user import UserRole


def notify(
    db: Session,
    type: NotificationType,
    message: str,
    case_id: uuid.UUID | None = None,
    *,
    recipient_user_id: uuid.UUID | None = None,
    recipient_role: UserRole | None = None,
    is_global: bool = False,
) -> None:
    """Record an event in the notification feed.

    Targeting (pick one):
      recipient_user_id — delivers only to that user.
      recipient_role    — delivers to all users with that role.
      is_global=True    — firm-wide announcement.

    When all three are at defaults (None/False) the row is visible to everyone,
    matching the old global-feed behavior for backward compatibility."""

    db.add(
        Notification(
            type=type,
            message=message,
            case_id=case_id,
            recipient_user_id=recipient_user_id,
            recipient_role=recipient_role,
            is_global=is_global,
        )
    )

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.user import UserRole


class NotificationType(str, enum.Enum):
    CASE_ASSIGNED = "case_assigned"
    STAGE_ADVANCED = "stage_advanced"
    DOCUMENT_UPLOADED = "document_uploaded"
    AI_REVIEW_FLAGGED = "ai_review_flagged"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    APPOINTMENT_REMINDER = "appointment_reminder"
    INVOICE_OVERDUE = "invoice_overdue"
    PAYMENT_RECEIVED = "payment_received"
    RFE_RECEIVED = "rfe_received"


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An event worth surfacing in the in-app notification center.

    Supports three targeting modes (mutually exclusive, checked in order):
      - recipient_user_id: 1-to-1 targeted notification for a specific user.
      - recipient_role: broadcast to all users with a given role.
      - is_global: firm-wide announcement visible to everyone.

    Rows with all three fields at their defaults (NULL/False) behave like the
    old global feed and are visible to everyone, preserving backward compat."""

    __tablename__ = "notifications"

    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType))
    message: Mapped[str] = mapped_column(String(500))
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cases.id"), nullable=True, index=True)

    recipient_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    recipient_role: Mapped[UserRole | None] = mapped_column(
        Enum(UserRole), nullable=True, index=True
    )
    is_global: Mapped[bool] = mapped_column(Boolean, default=False)

    case: Mapped["Case"] = relationship()


class NotificationSeen(UUIDPrimaryKeyMixin, Base):
    """Marks that `user_id` has seen `notification_id` -- lets the unread
    count be computed server-side and stay consistent across browsers/devices
    for the same person, instead of each browser tracking its own "last seen"
    timestamp in localStorage."""

    __tablename__ = "notification_reads"
    __table_args__ = (UniqueConstraint("user_id", "notification_id", name="uq_notification_read_user_notification"),)

    # No index=True on user_id: the UniqueConstraint below already leads with
    # user_id, so it doubles as that index -- a separate one would be redundant.
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    notification_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("notifications.id"), index=True)

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class NotificationType(str, enum.Enum):
    CASE_ASSIGNED = "case_assigned"
    STAGE_ADVANCED = "stage_advanced"
    DOCUMENT_UPLOADED = "document_uploaded"
    AI_REVIEW_FLAGGED = "ai_review_flagged"


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An event worth surfacing in the in-app notification center. There is no
    login/session system yet, so this is a shared, global feed rather than
    scoped to a specific user -- the frontend tracks "seen" per-browser via
    localStorage rather than a server-side read flag."""

    __tablename__ = "notifications"

    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType))
    message: Mapped[str] = mapped_column(String(500))
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cases.id"), nullable=True)

    case: Mapped["Case"] = relationship()

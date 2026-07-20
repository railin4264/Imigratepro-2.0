import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AppointmentType(str, enum.Enum):
    BIOMETRICS = "biometrics"
    INTERVIEW = "interview"
    RFE_DEADLINE = "rfe_deadline"
    COURT_HEARING = "court_hearing"
    CONSULTATION = "consultation"
    OTHER = "other"


class Appointment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A tracked date/deadline for a case (appointment, hearing, or filing deadline)."""

    __tablename__ = "appointments"

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"), index=True)
    appointment_type: Mapped[AppointmentType] = mapped_column(Enum(AppointmentType))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    reminder_sent: Mapped[bool] = mapped_column(default=False)

    case: Mapped["Case"] = relationship(back_populates="appointments")

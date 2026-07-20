import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RFEStatus(str, enum.Enum):
    OPEN = "open"
    RESPONDED = "responded"
    CLOSED = "closed"


class RFEEvidenceStatus(str, enum.Enum):
    PENDING = "pending"
    GATHERED = "gathered"
    SUBMITTED = "submitted"


class RFE(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A Request for Evidence USCIS sent on a case. `raw_text` is what the
    preparer pastes in from the notice (used both as a record and as the
    input to the optional AI evidence-checklist assistant, see
    app/services/rfe_ai.py) -- the actual response checklist lives in
    RFEEvidenceItem, always reviewed/edited by a human before anything is
    submitted."""

    __tablename__ = "rfes"

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"), index=True)
    status: Mapped[RFEStatus] = mapped_column(Enum(RFEStatus), default=RFEStatus.OPEN)
    received_date: Mapped[date] = mapped_column(Date)
    response_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    case: Mapped["Case"] = relationship(back_populates="rfes")
    evidence_items: Mapped[list["RFEEvidenceItem"]] = relationship(
        back_populates="rfe", order_by="RFEEvidenceItem.order", cascade="all, delete-orphan"
    )


class RFEEvidenceItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "rfe_evidence_items"

    rfe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rfes.id"), index=True)
    description: Mapped[str] = mapped_column(String(500))
    status: Mapped[RFEEvidenceStatus] = mapped_column(Enum(RFEEvidenceStatus), default=RFEEvidenceStatus.PENDING)
    order: Mapped[int] = mapped_column(Integer, default=0)

    rfe: Mapped["RFE"] = relationship(back_populates="evidence_items")

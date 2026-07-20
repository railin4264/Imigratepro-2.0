import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    OTHER = "other"


class Invoice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A bill issued to a case for services rendered. Balance/status are
    derived from the linked Payments rather than edited directly, so they
    can't drift out of sync (see app/services/billing.py:recalculate)."""

    __tablename__ = "invoices"

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"), index=True)
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    amount: Mapped[float] = mapped_column(Float)
    amount_paid: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    case: Mapped["Case"] = relationship(back_populates="invoices")
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan", order_by="Payment.paid_at"
    )


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), default=PaymentMethod.OTHER)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    invoice: Mapped["Invoice"] = relationship(back_populates="payments")

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.billing import InvoiceStatus, PaymentMethod


def _positive_amount(value: float | None) -> float | None:
    # billing.py::recalculate derives amount_paid/status by summing payments
    # against amount -- a zero/negative invoice or a negative "payment" both
    # produce a nonsensical-but-not-crashing state (e.g. a negative
    # amount_paid) instead of an error, so this has to be caught here.
    if value is not None and value <= 0:
        raise ValueError("Amount must be greater than 0")
    return value


class InvoiceCreate(BaseModel):
    description: str | None = None
    amount: float
    due_date: date | None = None

    _validate_amount = field_validator("amount")(_positive_amount)


class InvoiceUpdate(BaseModel):
    description: str | None = None
    amount: float | None = None
    due_date: date | None = None
    status: InvoiceStatus | None = None

    _validate_amount = field_validator("amount")(_positive_amount)


class PaymentCreate(BaseModel):
    amount: float
    method: PaymentMethod = PaymentMethod.OTHER
    paid_at: datetime | None = None
    notes: str | None = None

    _validate_amount = field_validator("amount")(_positive_amount)


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_id: uuid.UUID
    amount: float
    method: PaymentMethod
    paid_at: datetime
    notes: str | None


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    invoice_number: str
    description: str | None
    amount: float
    amount_paid: float
    status: InvoiceStatus
    due_date: date | None
    paid_at: datetime | None
    created_at: datetime
    case_number: str | None = None


class InvoiceDetail(InvoiceRead):
    payments: list[PaymentRead] = []

import uuid

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Append-only record of destructive/financial actions -- who deleted a
    case, who recorded or deleted a payment, and so on. Compliance-driven
    (legal/audit trail for a practice handling immigration case records), not
    a general activity feed -- see the notifications table for that. Rows are
    never updated or deleted by application code; nothing writes to this
    table except log_action, and nothing reads it except the admin-only
    listing endpoint."""

    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    # Dotted verb like "case.deleted", "invoice.payment_added" -- free-form
    # rather than an enum so a new destructive endpoint doesn't need a schema
    # migration just to start logging.
    action: Mapped[str] = mapped_column(String(100), index=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    # Small, human-readable context (e.g. {"case_number": "1520", "amount": 250.0})
    # -- not a diff/snapshot of the deleted row, which would duplicate PII
    # into a table that's kept indefinitely for compliance.
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    user: Mapped["User"] = relationship()


class AICallAudit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Append-only record of AI calls (Claude/vision etc.) including metadata,
    tokens used, and estimated cost. Stores only the SHA-256 prompt_hash,
    never raw prompts or completions, to comply with strict PII requirements."""

    __tablename__ = "ai_call_audits"

    prompt_hash: Mapped[str] = mapped_column(String(64), index=True)
    model: Mapped[str] = mapped_column(String(50), index=True)
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    estimated_cost: Mapped[float] = mapped_column(default=0.0)


import enum
import secrets
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class GeneratedFormStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    FILED = "filed"


class FormTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Registry entry for an official USCIS form (e.g. I-130, I-485, I-765)."""

    __tablename__ = "form_templates"

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # "I-130"
    name: Mapped[str] = mapped_column(String(255))
    edition_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pdf_template_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Complete inventory of every PDF field: [{name, type, label, page, on_value?/options?}, ...]
    # Drives the full-field electronic form editor in the frontend.
    field_schema: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Curated subset that can be pre-filled automatically from Client/Case data:
    # [{pdf_field, source}, ...], resolved by app.services.form_data.resolve_source.
    autofill_map: Mapped[list | None] = mapped_column(JSON, nullable=True)

    generated_forms: Mapped[list["GeneratedForm"]] = relationship(back_populates="template")


class GeneratedForm(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A filled instance of a FormTemplate for a specific Case."""

    __tablename__ = "generated_forms"

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"))
    form_template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("form_templates.id"))
    status: Mapped[GeneratedFormStatus] = mapped_column(
        Enum(GeneratedFormStatus), default=GeneratedFormStatus.DRAFT
    )

    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Last AI consistency review: {overall_assessment, findings: [{severity, field_label, issue}]}.
    # A review aid for the attorney/paralegal, not a legal determination.
    ai_review: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Lets the client fill this specific form themselves via a link with no
    # login, e.g. /client/forms/{access_token}. Revoke access by flipping
    # client_link_enabled rather than deleting the token (keeps the link
    # stable if re-enabled).
    access_token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=lambda: secrets.token_urlsafe(24)
    )
    client_link_enabled: Mapped[bool] = mapped_column(default=True)

    case: Mapped["Case"] = relationship(back_populates="generated_forms")
    template: Mapped["FormTemplate"] = relationship(back_populates="generated_forms")

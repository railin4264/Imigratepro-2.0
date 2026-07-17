import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ChecklistPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Service(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A sellable service package (e.g. "Family Petition"): bundles the forms,
    checklist, and workflow stages a case of this kind needs. This is the
    catalog entry -- applying it to a Case materializes the checklist and
    stage onto that case (see CaseChecklistItem, Case.workflow_stage)."""

    __tablename__ = "services"

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    stages: Mapped[list["WorkflowStage"]] = relationship(
        back_populates="service", order_by="WorkflowStage.order", cascade="all, delete-orphan"
    )
    checklist_items: Mapped[list["ServiceChecklistItem"]] = relationship(
        back_populates="service", order_by="ServiceChecklistItem.order", cascade="all, delete-orphan"
    )
    form_links: Mapped[list["ServiceFormTemplate"]] = relationship(
        back_populates="service", cascade="all, delete-orphan"
    )


class WorkflowStage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "workflow_stages"

    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id"))
    name: Mapped[str] = mapped_column(String(255))
    order: Mapped[int] = mapped_column(Integer)

    service: Mapped["Service"] = relationship(back_populates="stages")


class ServiceChecklistItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "service_checklist_items"

    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id"))
    label: Mapped[str] = mapped_column(String(255))
    order: Mapped[int] = mapped_column(Integer)

    service: Mapped["Service"] = relationship(back_populates="checklist_items")


class ServiceFormTemplate(UUIDPrimaryKeyMixin, Base):
    """Which FormTemplate(s) a Service bundles (e.g. Family Petition -> I-130, G-28)."""

    __tablename__ = "service_form_templates"

    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id"))
    form_template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("form_templates.id"))

    service: Mapped["Service"] = relationship(back_populates="form_links")
    form_template: Mapped["FormTemplate"] = relationship()


class CaseChecklistItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A per-case materialized checklist item, snapshotted from
    ServiceChecklistItem when the service was applied to the case (so later
    edits to the catalog item don't retroactively change existing cases)."""

    __tablename__ = "case_checklist_items"

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"))
    label: Mapped[str] = mapped_column(String(255))
    order: Mapped[int] = mapped_column(Integer)
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[ChecklistPriority] = mapped_column(Enum(ChecklistPriority), default=ChecklistPriority.MEDIUM)

    case: Mapped["Case"] = relationship(back_populates="checklist_items")
    assigned_to: Mapped["User"] = relationship()

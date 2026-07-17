import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CaseType(str, enum.Enum):
    FAMILY_BASED = "family_based"
    EMPLOYMENT_BASED = "employment_based"
    ASYLUM = "asylum"
    NATURALIZATION = "naturalization"
    ADJUSTMENT_OF_STATUS = "adjustment_of_status"
    WORK_PERMIT = "work_permit"
    OTHER = "other"


class CaseStatus(str, enum.Enum):
    INTAKE = "intake"
    PREPARING = "preparing"
    FILED = "filed"
    RFE = "rfe"  # Request for Evidence
    APPROVED = "approved"
    DENIED = "denied"
    CLOSED = "closed"


class ParticipantRole(str, enum.Enum):
    PETITIONER = "petitioner"
    BENEFICIARY = "beneficiary"
    DERIVATIVE = "derivative"
    SPONSOR = "sponsor"


class Case(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cases"

    case_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    case_type: Mapped[CaseType] = mapped_column(Enum(CaseType))
    status: Mapped[CaseStatus] = mapped_column(Enum(CaseStatus), default=CaseStatus.INTAKE)

    assigned_attorney_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Service package applied to this case (e.g. "Family Petition"), and which
    # of that service's workflow stages the case is currently in.
    service_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("services.id"), nullable=True)
    workflow_stage_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workflow_stages.id"), nullable=True
    )

    participants: Mapped[list["CaseParticipant"]] = relationship(back_populates="case")
    documents: Mapped[list["Document"]] = relationship(back_populates="case")
    generated_forms: Mapped[list["GeneratedForm"]] = relationship(back_populates="case")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="case")
    checklist_items: Mapped[list["CaseChecklistItem"]] = relationship(
        back_populates="case", order_by="CaseChecklistItem.order"
    )
    service: Mapped["Service"] = relationship()
    workflow_stage: Mapped["WorkflowStage"] = relationship()


class CaseParticipant(UUIDPrimaryKeyMixin, Base):
    """Links a Client to a Case with a specific role (petitioner, beneficiary, etc.)."""

    __tablename__ = "case_participants"

    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id"))
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    role: Mapped[ParticipantRole] = mapped_column(Enum(ParticipantRole))

    case: Mapped["Case"] = relationship(back_populates="participants")
    client: Mapped["Client"] = relationship(back_populates="case_links")

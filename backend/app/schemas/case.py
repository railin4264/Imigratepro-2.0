import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.case import CaseStatus, CaseType, ParticipantRole


class CaseBase(BaseModel):
    case_number: str
    case_type: CaseType
    status: CaseStatus = CaseStatus.INTAKE
    assigned_attorney_id: uuid.UUID | None = None
    notes: str | None = None
    priority_date: datetime | None = None
    filed_date: datetime | None = None
    decision_deadline: datetime | None = None
    uscis_receipt_number: str | None = None
    parent_case_id: uuid.UUID | None = None


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    case_type: CaseType | None = None
    status: CaseStatus | None = None
    assigned_attorney_id: uuid.UUID | None = None
    notes: str | None = None
    priority_date: datetime | None = None
    filed_date: datetime | None = None
    decision_deadline: datetime | None = None
    uscis_receipt_number: str | None = None
    parent_case_id: uuid.UUID | None = None


class CaseRead(CaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ParticipantCreate(BaseModel):
    client_id: uuid.UUID
    role: ParticipantRole


class ParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    client_id: uuid.UUID
    role: ParticipantRole

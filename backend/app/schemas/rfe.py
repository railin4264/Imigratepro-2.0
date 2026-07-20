import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.rfe import RFEEvidenceStatus, RFEStatus


class RFECreate(BaseModel):
    received_date: date
    response_due_date: date | None = None
    raw_text: str | None = None
    notes: str | None = None


class RFEUpdate(BaseModel):
    status: RFEStatus | None = None
    response_due_date: date | None = None
    raw_text: str | None = None
    notes: str | None = None


class EvidenceItemCreate(BaseModel):
    description: str


class EvidenceItemUpdate(BaseModel):
    description: str | None = None
    status: RFEEvidenceStatus | None = None


class EvidenceItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    description: str
    status: RFEEvidenceStatus
    order: int


class RFERead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    case_number: str | None = None
    status: RFEStatus
    received_date: date
    response_due_date: date | None
    notes: str | None
    created_at: datetime
    evidence_count: int = 0
    evidence_gathered_count: int = 0


class RFEDetail(RFERead):
    raw_text: str | None
    evidence_items: list[EvidenceItemRead] = []


class RFESuggestRequest(BaseModel):
    raw_text: str | None = None


class RFESuggestion(BaseModel):
    description: str
    reason: str


class RFESuggestResponse(BaseModel):
    suggestions: list[RFESuggestion]

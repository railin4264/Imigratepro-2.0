import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.service import ChecklistPriority


class ServiceCreate(BaseModel):
    name: str
    description: str | None = None
    price: float | None = None
    estimated_days: int | None = None
    form_template_codes: list[str] = []
    checklist_items: list[str] = []
    stages: list[str] = []


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    price: float | None
    estimated_days: int | None
    created_at: datetime
    form_codes: list[str] = []
    checklist_items: list[str] = []
    stages: list[str] = []


class ApplyServiceRequest(BaseModel):
    service_id: uuid.UUID


class ChecklistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    order: int
    done: bool
    done_at: datetime | None
    assigned_to_id: uuid.UUID | None
    due_date: date | None
    priority: ChecklistPriority


class ChecklistItemUpdate(BaseModel):
    done: bool | None = None
    assigned_to_id: uuid.UUID | None = None
    due_date: date | None = None
    priority: ChecklistPriority | None = None


class CaseServiceView(BaseModel):
    service: ServiceRead | None
    stages: list[str]
    current_stage: str | None
    current_stage_index: int | None
    checklist: list[ChecklistItemRead]

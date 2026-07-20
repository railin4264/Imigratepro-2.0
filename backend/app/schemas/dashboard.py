import uuid
from datetime import date, datetime

from pydantic import BaseModel


class MyDayCase(BaseModel):
    id: uuid.UUID
    case_number: str
    status: str


class MyDayChecklistItem(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    case_number: str
    label: str
    due_date: date | None
    priority: str
    overdue: bool


class MyDayAppointment(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    case_number: str
    appointment_type: str
    scheduled_at: datetime


class MyDayRFE(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    case_number: str
    status: str
    response_due_date: date | None


class MyDayResponse(BaseModel):
    """A per-preparer "today" view: what's assigned to me and what needs
    attention now, in the spirit of a daily standup -- not a general-purpose
    report (see /stats for firm-wide numbers)."""

    assigned_case_count: int
    appointments_today: list[MyDayAppointment]
    checklist_due: list[MyDayChecklistItem]
    open_rfes: list[MyDayRFE]
    cases_ready_for_review: list[MyDayCase]

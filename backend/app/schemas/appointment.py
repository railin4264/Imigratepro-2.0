import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.appointment import AppointmentType


class AppointmentBase(BaseModel):
    appointment_type: AppointmentType
    scheduled_at: datetime
    location: str | None = None
    notes: str | None = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    appointment_type: AppointmentType | None = None
    scheduled_at: datetime | None = None
    location: str | None = None
    notes: str | None = None


class AppointmentRead(AppointmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    reminder_sent: bool
    created_at: datetime
    case_number: str | None = None

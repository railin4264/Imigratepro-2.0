import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.user import UserRole


class UserCreate(BaseModel):
    full_name: str
    email: str
    role: UserRole = UserRole.PARALEGAL
    password: str | None = None
    bar_number: str | None = None
    firm_name: str | None = None
    phone: str | None = None
    mobile_phone: str | None = None
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None

    @field_validator("password")
    @classmethod
    def _password_min_length(cls, value: str | None) -> str | None:
        # Same 8-character floor as the reset/set-password endpoints
        # (auth.py::reset_password, users.py::set_password) -- this is the
        # only password entry point that wasn't enforcing it.
        if value is not None and len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    bar_number: str | None = None
    firm_name: str | None = None
    phone: str | None = None
    mobile_phone: str | None = None
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserWorkload(BaseModel):
    user: UserRead
    assigned_case_count: int
    cases_by_status: dict[str, int]
    open_rfe_count: int
    overdue_checklist_count: int

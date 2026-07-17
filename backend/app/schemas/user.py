import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole


class UserCreate(BaseModel):
    full_name: str
    email: str
    role: UserRole = UserRole.PARALEGAL
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

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ClientBase(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    mobile_phone: str | None = None
    date_of_birth: date | None = None
    country_of_birth: str | None = None
    nationality: str | None = None
    a_number: str | None = None
    passport_number: str | None = None
    ssn: str | None = None
    sex: str | None = None
    marital_status: str | None = None
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    first_name: str | None = None
    last_name: str | None = None


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

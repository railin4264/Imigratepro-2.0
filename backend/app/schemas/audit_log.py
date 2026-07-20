import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    user_id: uuid.UUID | None
    user_name: str | None = None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    details: dict | None

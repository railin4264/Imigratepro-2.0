import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus, DocumentType


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID | None
    case_id: uuid.UUID | None
    document_type: DocumentType
    status: DocumentStatus
    original_filename: str
    content_type: str | None
    created_at: datetime


class DocumentDetail(DocumentRead):
    extracted_data: dict | None = None


class DocumentUpdate(BaseModel):
    document_type: DocumentType | None = None
    client_id: uuid.UUID | None = None


class ApplyToClientRequest(BaseModel):
    fields: list[str]

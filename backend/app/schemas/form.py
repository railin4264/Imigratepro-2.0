import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.form import GeneratedFormStatus


class FormTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    edition_date: str | None = None


class ShowIfCondition(BaseModel):
    field: str
    equals: str


class FieldSchemaEntry(BaseModel):
    name: str
    type: str
    label: str
    page: int | None = None
    on_value: str | None = None
    options: list[str] | None = None
    show_if: list[ShowIfCondition] | None = None


class FormTemplateSchema(BaseModel):
    code: str
    name: str
    fields: list[FieldSchemaEntry]


class GeneratedFormCreate(BaseModel):
    form_code: str


class GeneratedFormRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    form_template_id: uuid.UUID
    status: GeneratedFormStatus
    created_at: datetime
    access_token: str
    client_link_enabled: bool


class ReviewFinding(BaseModel):
    severity: str
    field_label: str
    issue: str


class AiReview(BaseModel):
    overall_assessment: str
    findings: list[ReviewFinding]


class GeneratedFormDetail(GeneratedFormRead):
    data: dict[str, str] = {}
    form_code: str
    ai_review: AiReview | None = None
    ai_reviewed_at: datetime | None = None


class GeneratedFormUpdate(BaseModel):
    data: dict[str, str]


class PublicFormView(BaseModel):
    form_code: str
    form_name: str
    case_number: str
    fields: list[FieldSchemaEntry]
    data: dict[str, str]

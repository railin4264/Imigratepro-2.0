import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.form import FormCategory, GeneratedFormStatus

# The largest real form in the catalog (I-485) has 736 fields (see README);
# 2000 gives headroom for future forms without leaving the field effectively
# unbounded. 20,000 chars per value is far beyond any legitimate form field
# (even a long narrative answer) -- both exist to cap how much a single
# request can force into the `data` JSON column and into pypdf's rendering
# pass, not because any real form needs them.
_MAX_FORM_FIELDS = 2000
_MAX_FIELD_VALUE_LENGTH = 20_000


class FormTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    edition_date: str | None = None
    category: FormCategory = FormCategory.GENERAL


class FormTemplateCategoryGroup(BaseModel):
    category: FormCategory
    forms: list[FormTemplateRead]


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
    form_code: str
    status: GeneratedFormStatus
    created_at: datetime
    access_token: str
    client_link_enabled: bool
    uscis_receipt_number: str | None = None
    uscis_status_checked_at: datetime | None = None


class ReviewFinding(BaseModel):
    severity: str
    field_label: str
    issue: str


class AiReview(BaseModel):
    overall_assessment: str
    findings: list[ReviewFinding]


class GeneratedFormDetail(GeneratedFormRead):
    data: dict[str, str] = {}
    ai_review: AiReview | None = None
    ai_reviewed_at: datetime | None = None
    uscis_status_raw: dict | None = None


class ReceiptNumberUpdate(BaseModel):
    uscis_receipt_number: str | None = None

    @field_validator("uscis_receipt_number")
    @classmethod
    def _normalize(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().upper()
        if not value:
            return None
        if len(value) > 20:
            raise ValueError("Receipt number is too long")
        return value


class GeneratedFormUpdate(BaseModel):
    data: dict[str, str]
    # Only ever sent by the public client-portal wizard (see PublicFormView) --
    # the internal editor has no concept of a step and always omits this.
    client_wizard_step: int | None = None

    @field_validator("data")
    @classmethod
    def _bounded_data(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > _MAX_FORM_FIELDS:
            raise ValueError(f"Too many fields (max {_MAX_FORM_FIELDS})")
        for field_value in value.values():
            if len(field_value) > _MAX_FIELD_VALUE_LENGTH:
                raise ValueError(f"Field value too long (max {_MAX_FIELD_VALUE_LENGTH} characters)")
        return value


class PublicFormView(BaseModel):
    form_code: str
    form_name: str
    case_number: str
    fields: list[FieldSchemaEntry]
    data: dict[str, str]
    client_wizard_step: int = 0

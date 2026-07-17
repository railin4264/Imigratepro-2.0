import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import DbSession
from app.core.config import settings
from app.models.case import Case
from app.models.form import FormTemplate, GeneratedForm, GeneratedFormStatus
from app.schemas.form import (
    FormTemplateRead,
    FormTemplateSchema,
    GeneratedFormCreate,
    GeneratedFormDetail,
    GeneratedFormRead,
    GeneratedFormUpdate,
)
from app.services import form_review_ai
from app.services.form_data import build_case_context, resolve_source
from app.services.pdf_filler import fill_pdf_form

router = APIRouter(tags=["forms"])


def _detail(generated: GeneratedForm, template: FormTemplate) -> GeneratedFormDetail:
    return GeneratedFormDetail(
        **GeneratedFormRead.model_validate(generated).model_dump(),
        data=generated.data or {},
        form_code=template.code,
        ai_review=generated.ai_review,
        ai_reviewed_at=generated.ai_reviewed_at,
    )


def _initial_data(db, template: FormTemplate, case: Case) -> dict[str, str]:
    """Every field on the form gets an entry (blank by default), overlaid with
    whatever the autofill map can resolve from the case's petitioner/beneficiary/
    attorney data. This dict *is* the electronic form -- the frontend editor
    reads and writes it directly, one entry per PDF field."""

    data = {field["name"]: "" for field in template.field_schema or []}

    context = build_case_context(db, case)
    for entry in template.autofill_map or []:
        value = resolve_source(context, entry["source"])
        if "match_value" in entry:
            # Checkbox tied to an enum-like field (e.g. sex, marital status):
            # only check it if the resolved value equals this option.
            if value == entry["match_value"]:
                data[entry["pdf_field"]] = entry["set_value"]
        elif value:
            data[entry["pdf_field"]] = value

    return data


def _render_pdf(template: FormTemplate, generated: GeneratedForm) -> None:
    template_path = settings.FORM_TEMPLATES_DIR / template.pdf_template_path
    output_path = settings.GENERATED_FORMS_DIR / f"{generated.id}.pdf"
    fill_pdf_form(template_path, output_path, generated.data or {})
    generated.output_pdf_path = str(output_path)
    generated.status = GeneratedFormStatus.GENERATED


@router.get("/form-templates", response_model=list[FormTemplateRead])
def list_form_templates(db: DbSession):
    return db.query(FormTemplate).order_by(FormTemplate.code).all()


@router.get("/form-templates/{code}/schema", response_model=FormTemplateSchema)
def get_form_template_schema(code: str, db: DbSession):
    template = db.query(FormTemplate).filter_by(code=code).one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail=f"Unknown form template '{code}'")
    return FormTemplateSchema(code=template.code, name=template.name, fields=template.field_schema or [])


@router.get("/cases/{case_id}/forms", response_model=list[GeneratedFormRead])
def list_generated_forms(case_id: uuid.UUID, db: DbSession):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return (
        db.query(GeneratedForm)
        .filter(GeneratedForm.case_id == case_id)
        .order_by(GeneratedForm.created_at.desc())
        .all()
    )


@router.post("/cases/{case_id}/forms", response_model=GeneratedFormRead, status_code=201)
def generate_form(case_id: uuid.UUID, payload: GeneratedFormCreate, db: DbSession):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    template = db.query(FormTemplate).filter_by(code=payload.form_code).one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail=f"Unknown form template '{payload.form_code}'")
    if not template.pdf_template_path:
        raise HTTPException(status_code=422, detail="This template has no PDF file configured")

    generated = GeneratedForm(
        case_id=case.id,
        form_template_id=template.id,
        status=GeneratedFormStatus.DRAFT,
        data=_initial_data(db, template, case),
    )
    db.add(generated)
    db.commit()
    db.refresh(generated)

    _render_pdf(template, generated)
    db.commit()
    db.refresh(generated)

    return generated


@router.get("/forms/{generated_form_id}", response_model=GeneratedFormDetail)
def get_generated_form(generated_form_id: uuid.UUID, db: DbSession):
    generated = db.get(GeneratedForm, generated_form_id)
    if not generated:
        raise HTTPException(status_code=404, detail="Generated form not found")
    template = db.get(FormTemplate, generated.form_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Form template not found")
    return _detail(generated, template)


@router.patch("/forms/{generated_form_id}", response_model=GeneratedFormRead)
def update_generated_form(generated_form_id: uuid.UUID, payload: GeneratedFormUpdate, db: DbSession):
    """Save edits to the electronic form and re-render the PDF from the updated data."""

    generated = db.get(GeneratedForm, generated_form_id)
    if not generated:
        raise HTTPException(status_code=404, detail="Generated form not found")
    template = db.get(FormTemplate, generated.form_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Form template not found")

    generated.data = {**(generated.data or {}), **payload.data}
    _render_pdf(template, generated)
    db.commit()
    db.refresh(generated)

    return generated


@router.post("/forms/{generated_form_id}/review", response_model=GeneratedFormDetail)
def review_generated_form(generated_form_id: uuid.UUID, db: DbSession):
    """Ask Claude to cross-check this form's answers against the case's client
    records and flag inconsistencies for a human to double-check -- a review
    aid, not a legal determination."""

    generated = db.get(GeneratedForm, generated_form_id)
    if not generated:
        raise HTTPException(status_code=404, detail="Generated form not found")
    template = db.get(FormTemplate, generated.form_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Form template not found")
    if not form_review_ai.is_configured():
        raise HTTPException(
            status_code=503,
            detail="AI review is not configured: set ANTHROPIC_API_KEY in backend/.env",
        )

    labels_by_name = {field["name"]: field["label"] for field in template.field_schema or []}
    answers = {
        labels_by_name.get(name, name): value for name, value in (generated.data or {}).items() if value
    }
    context = build_case_context(db, generated.case)
    reference = {role: info for role, info in context.items() if role != "case" and info}

    try:
        result = form_review_ai.review_form(
            form_code=template.code,
            form_name=template.name,
            case_number=generated.case.case_number,
            reference=reference,
            answers=answers,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Review failed: {exc}") from exc

    generated.ai_review = result
    generated.ai_reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(generated)

    return _detail(generated, template)


@router.get("/forms/{generated_form_id}/download")
def download_generated_form(generated_form_id: uuid.UUID, db: DbSession):
    generated = db.get(GeneratedForm, generated_form_id)
    if not generated or not generated.output_pdf_path:
        raise HTTPException(status_code=404, detail="Generated form not found")

    template = db.get(FormTemplate, generated.form_template_id)
    filename = f"{template.code}_{generated.case_id}.pdf" if template else f"{generated.id}.pdf"
    return FileResponse(generated.output_pdf_path, media_type="application/pdf", filename=filename)

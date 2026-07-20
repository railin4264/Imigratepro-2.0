from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.deps import DbSession
from app.core.config import settings
from app.core.rate_limit import check_rate_limit
from app.models.case import ParticipantRole
from app.models.document import Document
from app.models.form import FormTemplate, GeneratedForm
from app.models.notification import NotificationType
from app.schemas.document import DocumentRead
from app.schemas.form import GeneratedFormUpdate, PublicFormView
from app.schemas.timeline import CaseTimelineResponse, TimelineStepRead
from app.services.notifications import notify
from app.services.pdf_filler import fill_pdf_form
from app.services.storage import save_upload
from app.services.timeline import build_case_timeline

router = APIRouter(prefix="/public/forms", tags=["public"])


def _get_active_generated_form(token: str, db: DbSession) -> GeneratedForm:
    # Rate-limited per token, not per IP: the token is already unguessable
    # (24 random bytes), so this isn't an anti-brute-force control -- it caps
    # how much PDF-regeneration/disk-write work one client-portal session can
    # force on the server (see PUBLIC_FORM_RATE_LIMIT_* in core/config.py).
    if not check_rate_limit(
        f"public-form:{token}",
        settings.PUBLIC_FORM_RATE_LIMIT_PER_TOKEN,
        settings.PUBLIC_FORM_RATE_LIMIT_WINDOW_SECONDS,
    ):
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down and try again shortly.")

    generated = db.query(GeneratedForm).filter_by(access_token=token).one_or_none()
    if not generated or not generated.client_link_enabled:
        raise HTTPException(status_code=404, detail="Link not found or no longer active")
    return generated


@router.get("/{token}", response_model=PublicFormView)
def get_public_form(token: str, db: DbSession):
    generated = _get_active_generated_form(token, db)
    template = db.get(FormTemplate, generated.form_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Form template not found")

    return PublicFormView(
        form_code=template.code,
        form_name=template.name,
        case_number=generated.case.case_number,
        fields=template.field_schema or [],
        data=generated.data or {},
        client_wizard_step=generated.client_wizard_step,
    )


@router.patch("/{token}", response_model=PublicFormView)
def update_public_form(token: str, payload: GeneratedFormUpdate, db: DbSession):
    generated = _get_active_generated_form(token, db)
    template = db.get(FormTemplate, generated.form_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Form template not found")

    generated.data = {**(generated.data or {}), **payload.data}
    if payload.client_wizard_step is not None:
        generated.client_wizard_step = payload.client_wizard_step

    template_path = settings.FORM_TEMPLATES_DIR / template.pdf_template_path
    output_path = settings.GENERATED_FORMS_DIR / f"{generated.id}.pdf"
    fill_pdf_form(template_path, output_path, generated.data or {})
    generated.output_pdf_path = str(output_path)

    db.commit()
    db.refresh(generated)

    return PublicFormView(
        form_code=template.code,
        form_name=template.name,
        case_number=generated.case.case_number,
        fields=template.field_schema or [],
        data=generated.data or {},
        client_wizard_step=generated.client_wizard_step,
    )


@router.get("/{token}/timeline", response_model=CaseTimelineResponse)
def get_public_case_timeline(token: str, db: DbSession):
    generated = _get_active_generated_form(token, db)
    steps = build_case_timeline(generated.case)
    return CaseTimelineResponse(
        case_number=generated.case.case_number,
        steps=[TimelineStepRead(key=s.key, status=s.status) for s in steps],
    )


@router.get("/{token}/documents", response_model=list[DocumentRead])
def list_public_documents(token: str, db: DbSession):
    generated = _get_active_generated_form(token, db)
    return db.query(Document).filter(Document.case_id == generated.case_id).order_by(Document.created_at.desc()).all()


@router.post("/{token}/documents", response_model=DocumentRead, status_code=201)
async def upload_public_document(
    token: str,
    db: DbSession,
    file: UploadFile = File(...),
    role: str | None = Form(None),
):
    generated = _get_active_generated_form(token, db)

    client_id = None
    if role and role in ParticipantRole._value2member_map_:
        participant = next((p for p in generated.case.participants if p.role.value == role), None)
        if participant:
            client_id = participant.client_id

    try:
        path, _size = await save_upload(file, settings.UPLOADED_DOCUMENTS_DIR / str(generated.case_id))
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    document = Document(
        client_id=client_id,
        case_id=generated.case_id,
        original_filename=file.filename or "upload",
        storage_path=str(path),
        content_type=file.content_type,
    )
    db.add(document)
    notify(
        db,
        NotificationType.DOCUMENT_UPLOADED,
        f"New document uploaded for {generated.case.case_number}: {document.original_filename}",
        case_id=generated.case_id,
    )
    db.commit()
    db.refresh(document)
    return document

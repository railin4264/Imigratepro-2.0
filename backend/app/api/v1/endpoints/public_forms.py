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


def _attorney_only_field_names(template: FormTemplate) -> set[str]:
    return {
        entry["pdf_field"]
        for entry in template.autofill_map or []
        if str(entry.get("source", "")).startswith("attorney.")
    }


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

    real_field_names = {f["name"] for f in template.field_schema or []}
    unknown = [name for name in payload.data if name not in real_field_names]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown field(s) for this form: {sorted(unknown)}")

    # The client wizard's autosave always echoes the ENTIRE form back,
    # including attorney-owned fields it never showed the client -- so
    # silently stripping those (rather than rejecting the request) is what
    # keeps a normal autosave from breaking.
    locked_field_names = _attorney_only_field_names(template)
    editable_data = {k: v for k, v in payload.data.items() if k not in locked_field_names}

    generated.data = {**(generated.data or {}), **editable_data}
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


def _get_form_participant_roles(template: FormTemplate) -> set[str]:
    """
    Extract the participant roles (petitioner, beneficiary, etc.) that are
    involved in the given form template by looking at its autofill map.
    """
    roles = set()
    for entry in (template.autofill_map or []):
        source = str(entry.get("source", ""))
        parts = source.split(".")
        if parts:
            role_name = parts[0]
            if role_name in ParticipantRole._value2member_map_:
                roles.add(role_name)
    return roles


@router.get("/{token}/documents", response_model=list[DocumentRead])
def list_public_documents(token: str, db: DbSession):
    # FORM TOKEN SCOPING: A public form token should only expose documents associated
    # with the participant roles relevant to this specific form, not all documents in the case.
    generated = _get_active_generated_form(token, db)
    template = db.get(FormTemplate, generated.form_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Form template not found")

    allowed_roles = _get_form_participant_roles(template)
    # If the form has no mapped participant roles, fallback to all roles to avoid breaking the wizard.
    if not allowed_roles:
        allowed_roles = {r.value for r in ParticipantRole}

    allowed_client_ids = [
        p.client_id for p in generated.case.participants if p.role.value in allowed_roles
    ]

    return (
        db.query(Document)
        .filter(
            Document.case_id == generated.case_id,
            Document.client_id.in_(allowed_client_ids),
        )
        .order_by(Document.created_at.desc())
        .all()
    )


@router.post("/{token}/documents", response_model=DocumentRead, status_code=201)
async def upload_public_document(
    token: str,
    db: DbSession,
    file: UploadFile = File(...),
    role: str | None = Form(None),
):
    generated = _get_active_generated_form(token, db)
    template = db.get(FormTemplate, generated.form_template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Form template not found")

    allowed_roles = _get_form_participant_roles(template)
    if not allowed_roles:
        allowed_roles = {r.value for r in ParticipantRole}

    # If the provided upload role is not in the form's allowed roles,
    # default to 'beneficiary' if allowed, or the first allowed role to avoid breaking the wizard.
    if not role or role not in allowed_roles:
        if "beneficiary" in allowed_roles:
            role = "beneficiary"
        else:
            role = sorted(list(allowed_roles))[0]

    client_id = None
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


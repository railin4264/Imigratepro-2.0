import uuid
from datetime import date

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.deps import CurrentUser, DbSession, RequireOwnerOrAdmin, require_case_access, require_case_access_read
from app.core.config import settings
from app.models.case import Case
from app.models.client import Client
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.notification import NotificationType
from app.schemas.document import ApplyToClientRequest, DocumentDetail, DocumentRead, DocumentUpdate
from app.services import document_ai
from app.services.audit import log_action
from app.services.notifications import notify
from app.services.storage import save_upload

router = APIRouter(tags=["documents"])

# Extracted fields that are safe to copy straight onto a Client record.
_CLIENT_APPLICABLE_FIELDS = {
    "first_name",
    "last_name",
    "date_of_birth",
    "country_of_birth",
    "nationality",
    "passport_number",
    "a_number",
}


@router.get("/documents", response_model=list[DocumentRead])
def list_documents(
    db: DbSession,
    case_id: uuid.UUID | None = None,
    client_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(Document)
    if case_id:
        query = query.filter(Document.case_id == case_id)
    if client_id:
        query = query.filter(Document.client_id == client_id)
    return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/documents/ai-status")
def ai_status():
    return {"configured": document_ai.is_configured()}


@router.get("/cases/{case_id}/documents", response_model=list[DocumentRead])
def list_case_documents(case_id: uuid.UUID, db: DbSession, skip: int = 0, limit: int = 100):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return (
        db.query(Document)
        .filter(Document.case_id == case_id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("/cases/{case_id}/documents", response_model=DocumentRead, status_code=201)
async def upload_case_document(
    case_id: uuid.UUID,
    db: DbSession,
    file: UploadFile = File(...),
    client_id: uuid.UUID | None = Form(None),
    document_type: str | None = Form(None),
):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if client_id and not db.get(Client, client_id):
        raise HTTPException(status_code=404, detail="Client not found")

    doc_type = DocumentType.OTHER
    if document_type and document_type in DocumentType._value2member_map_:
        doc_type = DocumentType(document_type)

    try:
        path, _size = await save_upload(file, settings.UPLOADED_DOCUMENTS_DIR / str(case_id))
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    document = Document(
        client_id=client_id,
        case_id=case_id,
        document_type=doc_type,
        original_filename=file.filename or "upload",
        storage_path=str(path),
        content_type=file.content_type,
    )
    db.add(document)
    notify(
        db,
        NotificationType.DOCUMENT_UPLOADED,
        f"New document uploaded for {case.case_number}: {document.original_filename}",
        case_id=case.id,
    )
    db.commit()
    db.refresh(document)
    return document


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document(document_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.case_id:
        require_case_access_read(case_id=document.case_id, current_user=current_user, db=db)
    return document


@router.patch("/documents/{document_id}", response_model=DocumentDetail)
def update_document(document_id: uuid.UUID, payload: DocumentUpdate, db: DbSession, current_user: CurrentUser):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.case_id:
        require_case_access(case_id=document.case_id, current_user=current_user, db=db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(document, field, value)
    log_action(db, current_user, "document.updated", "document", document.id, {"filename": document.original_filename})
    db.commit()
    db.refresh(document)
    return document


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: uuid.UUID, db: DbSession, requester: RequireOwnerOrAdmin):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.case_id:
        require_case_access(case_id=document.case_id, current_user=requester, db=db)
    log_action(
        db, requester, "document.deleted", "document", document.id, {"filename": document.original_filename}
    )
    db.delete(document)
    db.commit()


@router.post("/documents/{document_id}/extract", response_model=DocumentDetail)
def extract_document(document_id: uuid.UUID, db: DbSession, current_user: CurrentUser):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.case_id:
        require_case_access(case_id=document.case_id, current_user=current_user, db=db)
    if not document_ai.is_configured():
        raise HTTPException(
            status_code=503,
            detail="AI extraction is not configured: set ANTHROPIC_API_KEY in backend/.env",
        )

    document.status = DocumentStatus.PROCESSING
    db.commit()

    try:
        with open(document.storage_path, "rb") as f:
            file_bytes = f.read()
        data = document_ai.extract_document_data(file_bytes, document.content_type)
    except Exception as exc:
        document.status = DocumentStatus.FAILED
        document.extracted_data = {"error": str(exc)}
        db.commit()
        raise HTTPException(status_code=502, detail=f"Extraction failed: {exc}") from exc

    document.extracted_data = data
    document.status = DocumentStatus.EXTRACTED
    doc_type = data.get("document_type")
    if doc_type in DocumentType._value2member_map_:
        document.document_type = DocumentType(doc_type)
    db.commit()
    db.refresh(document)
    return document


@router.post("/documents/{document_id}/apply-to-client", response_model=DocumentDetail)
def apply_to_client(document_id: uuid.UUID, payload: ApplyToClientRequest, db: DbSession, current_user: CurrentUser):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.case_id:
        require_case_access(case_id=document.case_id, current_user=current_user, db=db)
    if not document.client_id:
        raise HTTPException(status_code=400, detail="This document isn't linked to a client")
    if not document.extracted_data:
        raise HTTPException(status_code=400, detail="No extracted data to apply -- run extraction first")

    client = db.get(Client, document.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    for field in payload.fields:
        if field not in _CLIENT_APPLICABLE_FIELDS:
            continue
        value = document.extracted_data.get(field)
        if not value:
            continue
        if field == "date_of_birth":
            try:
                value = date.fromisoformat(value)
            except ValueError:
                continue
        setattr(client, field, value)

    db.commit()
    db.refresh(document)
    return document

import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.api.deps import DbSession, CurrentUser
from app.models.e_signature import ESignature
from app.models.form import GeneratedForm
from app.models.document import Document
from app.schemas.e_signature import ESignatureCreate, ESignatureRead, ESignatureVerifyResult
from app.services.e_signature import create_signature, verify_signature

router = APIRouter(tags=["e-signatures"])


@router.post("/e-signatures", response_model=ESignatureRead, status_code=status.HTTP_201_CREATED)
def sign_document_or_form(
    payload: ESignatureCreate,
    db: DbSession,
    current_user: CurrentUser,
    request: Request,
):
    """Sign a GeneratedForm or a Document.

    Captures client request metadata (IP address, user agent) and computes the current PDF hash.
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        signature = create_signature(
            db=db,
            user=current_user,
            form_id=payload.form_id,
            document_id=payload.document_id,
            signer_type=payload.signer_type,
            signer_name=payload.signer_name,
            signer_email=payload.signer_email,
            signature_method=payload.signature_method,
            signature_value=payload.signature_value,
            signature_image_path=payload.signature_image_path,
            ip_address=ip_address,
            user_agent=user_agent,
            consent_text=payload.consent_text,
            client_id=payload.client_id,
        )
        db.commit()
        db.refresh(signature)
        return signature
    except ValueError as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except FileNotFoundError as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))


@router.get("/e-signatures", response_model=list[ESignatureRead])
def list_signatures(
    db: DbSession,
    form_id: uuid.UUID | None = None,
    document_id: uuid.UUID | None = None,
):
    """List electronic signatures.

    Optionally filters by form_id or document_id.
    """
    query = db.query(ESignature)
    if form_id:
        query = query.filter(ESignature.form_id == form_id)
    if document_id:
        query = query.filter(ESignature.document_id == document_id)
    return query.all()


@router.get("/e-signatures/{id}")
def get_signature(
    id: uuid.UUID,
    db: DbSession,
    download: bool = False,
):
    """Retrieve e-signature verification status, or download the signed file if download=True."""
    signature = db.get(ESignature, id)
    if not signature:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signature not found")

    if download:
        # Resolve PDF/file path
        if signature.form_id:
            form = db.get(GeneratedForm, signature.form_id)
            if not form or not form.output_pdf_path:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signed form PDF not found")
            pdf_path = form.output_pdf_path
            filename = f"signed_{form.form_code}_{form.id}.pdf"
        elif signature.document_id:
            doc = db.get(Document, signature.document_id)
            if not doc or not doc.storage_path:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signed document file not found")
            pdf_path = doc.storage_path
            filename = f"signed_{doc.original_filename}"
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No document associated with signature")

        path = Path(pdf_path)
        if not path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signed file not found on disk")

        return FileResponse(
            path=path,
            filename=filename,
            media_type="application/pdf"
        )

    # Otherwise return verification JSON
    try:
        if signature.form_id:
            verifications = verify_signature(db, form_id=signature.form_id)
        else:
            verifications = verify_signature(db, document_id=signature.document_id)

        for res in verifications:
            if res["signature"].id == signature.id:
                # ESignatureVerifyResult structure
                return ESignatureVerifyResult(
                    signature=ESignatureRead.model_validate(res["signature"]),
                    current_hash=res["current_hash"],
                    changed=res["changed"]
                )
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verification failed")

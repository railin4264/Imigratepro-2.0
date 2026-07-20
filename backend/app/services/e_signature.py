import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.e_signature import ESignature, SignerType, SignatureMethod
from app.models.form import GeneratedForm
from app.models.document import Document
from app.models.user import User
from app.services.audit import log_action


def compute_file_hash(path: str | Path) -> str:
    """Compute the SHA-256 hash of a file's content."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found at {path}")
    
    sha256 = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def create_signature(
    db: Session,
    *,
    user: User,
    form_id: uuid.UUID | None = None,
    document_id: uuid.UUID | None = None,
    signer_type: str,
    signer_name: str,
    signer_email: str,
    signature_method: str,
    signature_value: str,
    signature_image_path: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    consent_text: str,
    client_id: uuid.UUID | None = None,
) -> ESignature:
    """Create an e-signature record for a form or document, computing the current hash of the file.

    Emits an audit log entry on creation.
    """
    if (form_id is None) == (document_id is None):
        raise ValueError("Must provide either form_id or document_id, not both or neither.")

    # Validate signer_type and signature_method are valid enums
    try:
        sig_type_enum = SignerType(signer_type)
    except ValueError:
        raise ValueError(f"Invalid signer_type: '{signer_type}'. Must be one of {[e.value for e in SignerType]}")

    try:
        sig_method_enum = SignatureMethod(signature_method)
    except ValueError:
        raise ValueError(f"Invalid signature_method: '{signature_method}'. Must be one of {[e.value for e in SignatureMethod]}")

    # Determine file path based on what's being signed
    if form_id:
        form = db.get(GeneratedForm, form_id)
        if not form:
            raise ValueError(f"GeneratedForm with ID {form_id} not found.")
        if not form.output_pdf_path:
            raise ValueError("Form PDF has not been generated yet.")
        pdf_path = form.output_pdf_path
        entity_type = "form"
        entity_id = form_id
        action = "form.signed"
    else:
        doc = db.get(Document, document_id)
        if not doc:
            raise ValueError(f"Document with ID {document_id} not found.")
        if not doc.storage_path:
            raise ValueError("Document file path is not configured.")
        pdf_path = doc.storage_path
        entity_type = "document"
        entity_id = document_id
        action = "document.signed"

    # Compute PDF hash at signing time
    doc_hash = compute_file_hash(pdf_path)

    # For drawn signatures, store the SHA-256 hash of the signature value (e.g. coordinates or image data) if it isn't already a 64-char hash
    final_sig_value = signature_value
    if sig_method_enum == SignatureMethod.DRAWN and len(signature_value) != 64:
        final_sig_value = hashlib.sha256(signature_value.encode("utf-8")).hexdigest()

    # Create the e-signature record
    signature = ESignature(
        form_id=form_id,
        document_id=document_id,
        signer_type=sig_type_enum,
        signer_name=signer_name,
        signer_email=signer_email,
        signed_at=datetime.now(timezone.utc),
        signature_method=sig_method_enum,
        signature_value=final_sig_value,
        signature_image_path=signature_image_path,
        ip_address=ip_address,
        user_agent=user_agent,
        consent_text=consent_text,
        document_hash=doc_hash,
        user_id=user.id if user else None,
        client_id=client_id,
    )

    db.add(signature)
    db.flush()

    # Log action to audit trail
    log_action(
        db=db,
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details={
            "signer_name": signer_name,
            "signer_email": signer_email,
            "signer_type": signer_type,
            "document_hash": doc_hash,
            "signature_method": signature_method,
            "signature_id": str(signature.id)
        },
        ip_address=ip_address,
    )

    return signature


def verify_signature(
    db: Session,
    *,
    form_id: uuid.UUID | None = None,
    document_id: uuid.UUID | None = None,
) -> list[dict]:
    """Verify signatures for a form or document.

    Re-computes the current PDF/file hash to check if the document has changed since signing.
    Returns list of dicts: [{"signature": ESignature, "current_hash": str | None, "changed": bool}]
    """
    if (form_id is None) == (document_id is None):
        raise ValueError("Must provide either form_id or document_id, not both or neither.")

    if form_id:
        signatures = db.query(ESignature).filter(ESignature.form_id == form_id).all()
        form = db.get(GeneratedForm, form_id)
        pdf_path = form.output_pdf_path if form else None
    else:
        signatures = db.query(ESignature).filter(ESignature.document_id == document_id).all()
        doc = db.get(Document, document_id)
        pdf_path = doc.storage_path if doc else None

    # Re-compute current hash
    current_hash = None
    if pdf_path:
        try:
            current_hash = compute_file_hash(pdf_path)
        except Exception:
            # File missing or unreadable
            current_hash = None

    results = []
    for sig in signatures:
        # If current_hash is None (file deleted/missing), it means verification cannot be completed successfully, so changed = True
        changed = (current_hash is None) or (sig.document_hash != current_hash)
        results.append({
            "signature": sig,
            "current_hash": current_hash,
            "changed": changed
        })

    return results

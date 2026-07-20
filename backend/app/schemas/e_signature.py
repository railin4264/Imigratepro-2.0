import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.e_signature import SignerType, SignatureMethod


class ESignatureCreate(BaseModel):
    form_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None
    signer_type: str = Field(..., description="Must be 'client', 'attorney', or 'preparer'")
    signer_name: str = Field(..., min_length=1)
    signer_email: str = Field(..., min_length=1)
    signature_method: str = Field(..., description="Must be 'drawn', 'typed', or 'accepted'")
    signature_value: str = Field(..., min_length=1, description="Typed signature name or base64/hashed coordinates")
    signature_image_path: str | None = None
    consent_text: str = Field(..., min_length=1, description="The legal consent agreement/disclaimer text")
    client_id: uuid.UUID | None = None

    @field_validator("signer_type")
    @classmethod
    def validate_signer_type(cls, v: str) -> str:
        if v not in [e.value for e in SignerType]:
            raise ValueError(f"signer_type must be one of: {[e.value for e in SignerType]}")
        return v

    @field_validator("signature_method")
    @classmethod
    def validate_signature_method(cls, v: str) -> str:
        if v not in [e.value for e in SignatureMethod]:
            raise ValueError(f"signature_method must be one of: {[e.value for e in SignatureMethod]}")
        return v

    @field_validator("consent_text")
    @classmethod
    def validate_consent_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("consent_text must not be empty or blank")
        return v


class ESignatureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    form_id: uuid.UUID | None
    document_id: uuid.UUID | None
    signer_type: SignerType
    signer_name: str
    signer_email: str
    signed_at: datetime
    signature_method: SignatureMethod
    signature_value: str
    signature_image_path: str | None
    ip_address: str | None
    user_agent: str | None
    consent_text: str
    document_hash: str
    user_id: uuid.UUID | None
    client_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ESignatureVerifyResult(BaseModel):
    signature: ESignatureRead
    current_hash: str | None
    changed: bool

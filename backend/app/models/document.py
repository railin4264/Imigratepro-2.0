import enum
import uuid

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class DocumentType(str, enum.Enum):
    PASSPORT = "passport"
    BIRTH_CERTIFICATE = "birth_certificate"
    MARRIAGE_CERTIFICATE = "marriage_certificate"
    I94 = "i94"
    PHOTO_ID = "photo_id"
    EVIDENCE = "evidence"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EXTRACTED = "extracted"
    FAILED = "failed"


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An uploaded file (evidence, ID, certificate) optionally processed by AI extraction."""

    __tablename__ = "documents"

    client_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clients.id"), nullable=True, index=True)
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cases.id"), nullable=True, index=True)

    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), default=DocumentType.OTHER)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED)

    original_filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    extracted_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    client: Mapped["Client"] = relationship(back_populates="documents")
    case: Mapped["Case"] = relationship(back_populates="documents")

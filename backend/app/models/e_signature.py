import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SignerType(str, enum.Enum):
    CLIENT = "client"
    ATTORNEY = "attorney"
    PREPARER = "preparer"


class SignatureMethod(str, enum.Enum):
    DRAWN = "drawn"
    TYPED = "typed"
    ACCEPTED = "accepted"


class ESignature(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "e_signatures"

    form_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("generated_forms.id", ondelete="SET NULL"), nullable=True, index=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )

    signer_type: Mapped[SignerType] = mapped_column(Enum(SignerType), index=True)
    signer_name: Mapped[str] = mapped_column(String(255))
    signer_email: Mapped[str] = mapped_column(String(255))
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    signature_method: Mapped[SignatureMethod] = mapped_column(Enum(SignatureMethod))
    signature_value: Mapped[str] = mapped_column(String(64))  # Hashed signature or typed name
    signature_image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    consent_text: Mapped[str] = mapped_column(Text)
    document_hash: Mapped[str] = mapped_column(String(64))  # SHA-256 hash of PDF

    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    client_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships (lazy-loaded by default, or you can query manually)
    form: Mapped["GeneratedForm | None"] = relationship()
    document: Mapped["Document | None"] = relationship()
    user: Mapped["User | None"] = relationship()
    client: Mapped["Client | None"] = relationship()

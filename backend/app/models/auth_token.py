import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RefreshToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A long-lived token that can be exchanged for a new short-lived access
    token, so a session survives longer than ACCESS_TOKEN_EXPIRE_MINUTES
    without keeping a broadly-scoped JWT alive for weeks. Stored as a SHA-256
    hash (`token_hash`), never the raw token -- a DB leak shouldn't hand out
    usable sessions. Rotated on every use (see app/core/security.py) so a
    stolen-and-replayed refresh token gets invalidated the next time the
    legitimate client uses theirs."""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship()


class PasswordResetToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A one-time-use token emailed to a user to let them set a new password
    without knowing the old one. Stored hashed for the same reason as
    RefreshToken. `used_at` is set the moment it's redeemed so it can't be
    replayed even before it expires."""

    __tablename__ = "password_reset_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship()

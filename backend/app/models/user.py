import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Nullable: staff can exist purely for case-assignment purposes without
    # ever being given a login (set via POST /users/{id}/password).
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.PARALEGAL)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Account lockout after repeated failed logins (see app/api/v1/endpoints/auth.py).
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Attorney-of-record details, used to fill representative forms (e.g. G-28)
    bar_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    firm_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mobile_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address_line: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

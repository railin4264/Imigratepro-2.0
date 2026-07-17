from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Client(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A person involved in one or more immigration cases (applicant, petitioner, or beneficiary)."""

    __tablename__ = "clients"

    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mobile_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    country_of_birth: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    a_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    passport_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ssn: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # "male" / "female" -- matches the USCIS form checkbox options we autofill from this.
    sex: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # "single" / "married" / "divorced" / "widowed" / "separated" / "annulled"
    marital_status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    address_line: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)

    documents: Mapped[list["Document"]] = relationship(back_populates="client")
    case_links: Mapped[list["CaseParticipant"]] = relationship(back_populates="client")

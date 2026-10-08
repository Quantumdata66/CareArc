"""Patient SQLAlchemy 2.0 ORM Model."""

from datetime import date
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.vital import Vital
    from app.models.note import ClinicalNote
    from app.models.appointment import Appointment


class Patient(Base, TimestampMixin):
    """Patient entity representing clinical demographics and admission profile."""

    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(32), nullable=False)
    room: Mapped[str] = mapped_column(String(64), nullable=False)
    condition: Mapped[str] = mapped_column(String(255), nullable=False)
    admitted: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    weight: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, default="N/A")
    
    # Contact Information
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships (Cascade Delete)
    vitals: Mapped[List["Vital"]] = relationship(
        "Vital",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="Vital.timestamp.asc()",
        lazy="selectin",
    )
    notes: Mapped[List["ClinicalNote"]] = relationship(
        "ClinicalNote",
        back_populates="patient",
        cascade="all, delete-orphan",
        order_by="ClinicalNote.timestamp.desc()",
        lazy="selectin",
    )
    appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment",
        back_populates="patient",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def contact(self) -> dict[str, Optional[str]]:
        """Helper property formatting contact info for nested API serialization."""
        return {
            "phone": self.phone,
            "email": self.email,
            "emergencyContact": self.emergency_contact,
        }

    def __repr__(self) -> str:
        return f"<Patient(id='{self.id}', name='{self.name}', room='{self.room}')>"

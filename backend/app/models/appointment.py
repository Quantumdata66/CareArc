"""Appointment SQLAlchemy 2.0 ORM Model."""

from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient


class Appointment(Base, TimestampMixin):
    """Appointment entity for clinical consultations, follow-ups, and check-ups."""

    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, index=True)
    patient_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    appointment_type: Mapped[str] = mapped_column(String(128), nullable=False)
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    appointment_time: Mapped[str] = mapped_column(String(16), nullable=False)  # "09:00"
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Relationship to Patient
    patient: Mapped["Patient"] = relationship("Patient", back_populates="appointments")

    # Composite Index for Date and Completion State Queries
    __table_args__ = (
        Index("idx_appointments_date_completed", "appointment_date", "is_completed"),
        Index("idx_appointments_patient_date", "patient_id", "appointment_date"),
    )

    @property
    def patient_name(self) -> Optional[str]:
        """Access patient name via eager-loaded relationship."""
        return self.patient.name if self.patient else None

    @property
    def name(self) -> str:
        """Denormalized patient name for frontend response compatibility."""
        return self.patient.name if self.patient else ""

    @property
    def type(self) -> str:
        """Alias for appointment_type."""
        return self.appointment_type

    @property
    def date(self) -> date:
        """Alias for appointment_date."""
        return self.appointment_date

    @property
    def time(self) -> str:
        """Alias for appointment_time."""
        return self.appointment_time

    @property
    def duration(self) -> int:
        """Alias for duration_minutes."""
        return self.duration_minutes


    def __repr__(self) -> str:
        return (
            f"<Appointment(id='{self.id}', patient_id='{self.patient_id}', "
            f"date='{self.appointment_date}', is_completed={self.is_completed})>"
        )

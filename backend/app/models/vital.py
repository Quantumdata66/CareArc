"""Vital Signs Time-Series SQLAlchemy 2.0 ORM Model."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient


class Vital(Base, TimestampMixin):
    """Vital entity representing timestamped physiological measurements."""

    __tablename__ = "vitals"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, index=True)
    patient_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Core Vitals Measurements
    heart_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    systolic_bp: Mapped[int] = mapped_column(Integer, nullable=False)
    diastolic_bp: Mapped[int] = mapped_column(Integer, nullable=False)
    oxygen: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    temperature: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    respiratory_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recorded_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Relationship to Patient
    patient: Mapped["Patient"] = relationship("Patient", back_populates="vitals")

    # Composite Index for Time-Series Analysis
    __table_args__ = (
        Index("idx_vitals_patient_timestamp_desc", "patient_id", text("timestamp DESC")),
        Index("idx_vitals_patient_timestamp_asc", "patient_id", text("timestamp ASC")),
    )

    @property
    def blood_pressure(self) -> dict[str, int]:
        """Format flat database systolic/diastolic columns into nested dictionary for API."""
        return {
            "systolic": self.systolic_bp,
            "diastolic": self.diastolic_bp,
        }

    def __repr__(self) -> str:
        return (
            f"<Vital(id='{self.id}', patient_id='{self.patient_id}', "
            f"timestamp='{self.timestamp}', heart_rate={self.heart_rate})>"
        )

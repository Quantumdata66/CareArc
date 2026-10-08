"""Clinical Note SQLAlchemy 2.0 ORM Model."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient


class ClinicalNote(Base, TimestampMixin):
    """ClinicalNote entity for medical observations, treatments, and reviews."""

    __tablename__ = "clinical_notes"

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
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="observation",
        index=True,
    )
    author: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Relationship to Patient
    patient: Mapped["Patient"] = relationship("Patient", back_populates="notes")

    # Composite Index for Chronological Note Retrieval
    __table_args__ = (
        Index("idx_notes_patient_timestamp_desc", "patient_id", text("timestamp DESC")),
    )

    def __repr__(self) -> str:
        return (
            f"<ClinicalNote(id='{self.id}', patient_id='{self.patient_id}', "
            f"type='{self.type}', author='{self.author}')>"
        )

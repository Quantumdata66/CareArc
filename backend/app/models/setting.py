"""Clinical Thresholds and Facility Profile SQLAlchemy 2.0 ORM Models."""

from typing import Any, List, Optional
from decimal import Decimal
from sqlalchemy import Boolean, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ClinicalThreshold(Base, TimestampMixin):
    """Clinical normal baseline range configuration for patient monitoring."""

    __tablename__ = "clinical_thresholds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vital_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    min_value: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    max_value: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    systolic_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    systolic_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ClinicalThreshold(vital_name='{self.vital_name}', "
            f"min={self.min_value}, max={self.max_value})>"
        )


class FacilityProfile(Base, TimestampMixin):
    """Clinical Facility and Ward Configuration."""

    __tablename__ = "facility_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default="DEFAULT_FACILITY")
    facility_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_name: Mapped[str] = mapped_column(String(255), nullable=False)
    facility_code: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # Contact & Location
    emergency_phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    primary_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bed_capacity: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Protocols & Intelligence Settings
    active_protocol: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    vitals_interval: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    delta_engine_window: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    auto_handover: Mapped[bool] = mapped_column(Boolean, default=True)
    critical_alert_escalation: Mapped[bool] = mapped_column(Boolean, default=True)
    specialties: Mapped[Optional[List[Any]]] = mapped_column(JSON, nullable=True, default=list)

    @property
    def facility_id(self) -> str:
        return self.facility_code

    @facility_id.setter
    def facility_id(self, value: str) -> None:
        self.facility_code = value

    def __repr__(self) -> str:
        return f"<FacilityProfile(id='{self.id}', facility_name='{self.facility_name}')>"


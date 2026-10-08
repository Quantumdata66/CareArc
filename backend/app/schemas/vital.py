"""Vital Signs Pydantic Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import Field, model_validator
from app.schemas.base import BaseSchema


class BloodPressureSchema(BaseSchema):
    """Nested blood pressure measurements."""
    systolic: int = Field(..., description="Systolic blood pressure (mmHg)", ge=40, le=300)
    diastolic: int = Field(..., description="Diastolic blood pressure (mmHg)", ge=20, le=200)


class VitalBase(BaseSchema):
    """Base vital sign measurement fields."""
    heart_rate: int = Field(..., description="Heart rate in beats per minute (BPM)", ge=20, le=300)
    blood_pressure: BloodPressureSchema = Field(..., description="Nested systolic and diastolic BP")
    oxygen: float = Field(..., description="Blood oxygen saturation SpO2 (%)", ge=50.0, le=100.0)
    temperature: float = Field(..., description="Body temperature in Celsius (°C)", ge=25.0, le=45.0)
    respiratory_rate: Optional[int] = Field(None, description="Respiratory rate (brpm)", ge=4, le=80)
    recorded_by: Optional[str] = Field(None, description="Staff member who recorded the vital")


class VitalCreate(BaseSchema):
    """Request schema for recording a new vital reading.

    Supports both nested blood_pressure object and flat systolic/diastolic form fields.
    """
    heart_rate: int = Field(..., description="Heart rate in beats per minute (BPM)", ge=20, le=300)
    blood_pressure: Optional[BloodPressureSchema] = None
    systolic: Optional[int] = Field(None, ge=40, le=300)
    diastolic: Optional[int] = Field(None, ge=20, le=200)
    oxygen: float = Field(..., description="Blood oxygen saturation SpO2 (%)", ge=50.0, le=100.0)
    temperature: float = Field(..., description="Body temperature in Celsius (°C)", ge=25.0, le=45.0)
    respiratory_rate: Optional[int] = Field(None, description="Respiratory rate (brpm)", ge=4, le=80)
    recorded_by: Optional[str] = Field(None, description="Staff member who recorded the vital")
    timestamp: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def assemble_blood_pressure(cls, data: dict) -> dict:
        """Allow flat 'systolic' and 'diastolic' form keys to populate blood_pressure object."""
        if isinstance(data, dict):
            bp = data.get("bloodPressure") or data.get("blood_pressure")
            if not bp and "systolic" in data and "diastolic" in data:
                data["blood_pressure"] = {
                    "systolic": data.get("systolic"),
                    "diastolic": data.get("diastolic"),
                }
        return data


class VitalResponse(VitalBase):
    """Response schema for vital signs records."""
    id: str = Field(..., description="Unique Vital ID (e.g. VIT-4N2L8X1B)")
    patient_id: str = Field(..., description="Associated Patient ID")
    timestamp: datetime = Field(..., description="ISO 8601 recording timestamp")

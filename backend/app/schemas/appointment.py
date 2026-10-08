"""Appointment Pydantic Schemas."""

import datetime as dt
from typing import Optional
from pydantic import Field, model_validator
from app.schemas.base import BaseSchema


class AppointmentBase(BaseSchema):
    """Base appointment fields."""
    type: str = Field(..., description="Type of visit (Consultation, Follow-up, Check-up)")
    date: dt.date = Field(..., description="Scheduled appointment date (YYYY-MM-DD)")
    time: str = Field(..., description="Scheduled appointment time (HH:mm, e.g. '09:00')")
    duration: int = Field(30, description="Scheduled duration in minutes", ge=5, le=480)


class AppointmentCreate(AppointmentBase):
    """Request schema for booking an appointment."""
    patient_id: str = Field(..., description="ID of the patient for this appointment")
    name: Optional[str] = Field(None, description="Optional patient name if passed by client")

    @model_validator(mode="before")
    @classmethod
    def map_aliases(cls, data: dict) -> dict:
        """Support both frontend shorthand keys and backend schema keys."""
        if isinstance(data, dict):
            if "appointmentType" in data and "type" not in data:
                data["type"] = data.get("appointmentType")
            if "appointmentDate" in data and "date" not in data:
                data["date"] = data.get("appointmentDate")
            if "appointmentTime" in data and "time" not in data:
                data["time"] = data.get("appointmentTime")
            if "durationMinutes" in data and "duration" not in data:
                data["duration"] = data.get("durationMinutes")
        return data


class AppointmentUpdate(BaseSchema):
    """Request schema for rescheduling or modifying an appointment."""
    type: Optional[str] = None
    date: Optional[dt.date] = None
    time: Optional[str] = None
    duration: Optional[int] = None
    is_completed: Optional[bool] = None


class AppointmentResponse(AppointmentBase):
    """Response schema for appointment records formatted for frontend consumption."""
    id: str = Field(..., description="Unique Appointment ID (e.g. APT-5X7K2M9D)")
    patient_id: str = Field(..., description="Associated Patient ID")
    name: str = Field(..., description="Denormalized Patient Name")
    is_completed: bool = Field(False, description="Whether the appointment has been completed")

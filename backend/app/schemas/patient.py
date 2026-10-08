"""Patient Pydantic Schemas."""

import datetime as dt
from typing import Optional
from pydantic import Field, model_validator
from app.schemas.base import BaseSchema
from app.schemas.vital import VitalCreate, VitalResponse


class PatientContactSchema(BaseSchema):
    """Patient emergency and direct contact details."""
    phone: Optional[str] = Field(None, description="Primary contact phone number")
    email: Optional[str] = Field(None, description="Primary email address")
    emergency_contact: Optional[str] = Field(None, description="Designated emergency contact name and phone")


class PatientBase(BaseSchema):
    """Core patient demographic and admission profile."""
    name: str = Field(..., description="Full name of the patient", min_length=1, max_length=255)
    age: int = Field(..., description="Patient age in years", ge=0, le=130)
    gender: str = Field(..., description="Gender (Female, Male, Other)")
    room: str = Field(..., description="Ward room or bed assignment", min_length=1, max_length=64)
    condition: str = Field(..., description="Primary clinical condition or diagnosis", min_length=1, max_length=255)
    admitted: dt.date = Field(..., description="Admission date (YYYY-MM-DD)")
    weight: Optional[str] = Field("N/A", description="Patient body weight (e.g. '160lbs')")


class PatientCreate(PatientBase):
    """Request schema for registering a new patient."""
    phone: Optional[str] = None
    email: Optional[str] = None
    emergency_contact: Optional[str] = None
    contact: Optional[PatientContactSchema] = None
    initial_vitals: Optional[VitalCreate] = None

    @model_validator(mode="before")
    @classmethod
    def extract_flat_contact_fields(cls, data: dict) -> dict:
        """Allow both nested 'contact' object and flat phone/email fields."""
        if isinstance(data, dict):
            contact_obj = data.get("contact")
            if isinstance(contact_obj, dict):
                if "phone" not in data and "phone" in contact_obj:
                    data["phone"] = contact_obj.get("phone")
                if "email" not in data and "email" in contact_obj:
                    data["email"] = contact_obj.get("email")
                if "emergency_contact" not in data and "emergencyContact" in contact_obj:
                    data["emergency_contact"] = contact_obj.get("emergencyContact")
                elif "emergency_contact" not in data and "emergency_contact" in contact_obj:
                    data["emergency_contact"] = contact_obj.get("emergency_contact")
        return data


class PatientUpdate(BaseSchema):
    """Request schema for updating patient details."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    age: Optional[int] = Field(None, ge=0, le=130)
    gender: Optional[str] = None
    room: Optional[str] = None
    condition: Optional[str] = None
    admitted: Optional[dt.date] = None
    weight: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    emergency_contact: Optional[str] = None
    contact: Optional[PatientContactSchema] = None


class PatientResponse(PatientBase):
    """Response schema for patient profiles with contact and derived status."""
    id: str = Field(..., description="Unique Patient ID (e.g. PT-001, PT-8K3F9J2A)")
    contact: Optional[PatientContactSchema] = None
    status: Optional[str] = Field("Stable", description="Derived clinical acuity status (Review, Watch, Improving, Stable)")
    latest_vital: Optional[VitalResponse] = Field(None, description="Most recent vital signs reading if available")

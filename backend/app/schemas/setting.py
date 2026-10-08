"""Clinical Thresholds and Facility Profile Pydantic Schemas."""

from typing import List, Optional
from pydantic import Field
from app.schemas.base import BaseSchema


class ThresholdRangeSchema(BaseSchema):
    """Min and max baseline bounds for a vital parameter."""
    min: float = Field(..., description="Minimum baseline reference value")
    max: float = Field(..., description="Maximum baseline reference value")


class BloodPressureThresholdSchema(BaseSchema):
    """Blood pressure specific threshold ranges."""
    min: float = Field(..., description="General diastolic low threshold")
    max: float = Field(..., description="General systolic high threshold")
    systolic_min: Optional[float] = Field(None, description="Systolic low threshold")
    systolic_max: Optional[float] = Field(None, description="Systolic high threshold")


class ThresholdsSchema(BaseSchema):
    """Aggregate normal reference ranges for vital signs monitoring."""
    heart_rate: ThresholdRangeSchema = Field(..., description="Heart rate reference range (BPM)")
    blood_pressure: BloodPressureThresholdSchema = Field(..., description="Blood pressure reference range (mmHg)")
    oxygen: ThresholdRangeSchema = Field(..., description="Blood oxygen saturation reference range (%)")
    temperature: ThresholdRangeSchema = Field(..., description="Body temperature reference range (°C)")


class FacilityProfileSchema(BaseSchema):
    """Clinical Facility and Ward Configuration."""
    facility_name: str = Field(..., description="Hospital or medical center name")
    unit_name: str = Field(..., description="Clinical unit or ward name")
    facility_id: str = Field("FAC-4B-LAGOS", description="Unique facility identifier code")
    emergency_phone: Optional[str] = Field(None, description="Emergency contact phone number")
    primary_email: Optional[str] = Field(None, description="Ward clinical email address")
    address: Optional[str] = Field(None, description="Physical location or building address")
    bed_capacity: Optional[str] = Field(None, description="Inpatient bed capacity description")
    active_protocol: Optional[str] = Field(None, description="Active monitoring protocol name")
    vitals_interval: Optional[str] = Field("4 hours", description="Standard vitals check interval")
    delta_engine_window: Optional[str] = Field("12 hours", description="Delta trajectory calculation window")
    ai_model: Optional[str] = Field("GPT-4o-mini Clinical Engine", description="Configured clinical AI engine")
    auto_handover: bool = Field(True, description="Enable automated shift handover summaries")
    critical_alert_escalation: bool = Field(True, description="Enable critical alert escalation")
    specialties: List[str] = Field(default_factory=list, description="List of clinical specialties managed")

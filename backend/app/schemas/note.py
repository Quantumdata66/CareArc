"""Clinical Note Pydantic Schemas."""

from datetime import datetime
from typing import Optional
from pydantic import Field
from app.schemas.base import BaseSchema


class NoteBase(BaseSchema):
    """Base clinical note fields."""
    content: str = Field(..., description="Clinical documentation text or medical observations", min_length=1)
    type: str = Field("observation", description="Note category (observation, treatment, review, handover)")
    author: Optional[str] = Field("Staff Clinician", description="Author name or clinician title")


class NoteCreate(BaseSchema):
    """Request schema for adding a clinical note."""
    content: str = Field(..., min_length=1)
    type: Optional[str] = Field("observation")
    author: Optional[str] = Field("Staff Clinician")
    timestamp: Optional[datetime] = None


class NoteResponse(NoteBase):
    """Response schema for clinical notes."""
    id: str = Field(..., description="Unique Note ID (e.g. NOTE-9M1Q4P7C)")
    patient_id: str = Field(..., description="Associated Patient ID")
    timestamp: datetime = Field(..., description="ISO 8601 creation timestamp")

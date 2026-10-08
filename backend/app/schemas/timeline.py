"""Patient Timeline Pydantic Schemas."""

from datetime import datetime
from typing import Any, Dict, Union
from pydantic import Field
from app.schemas.base import BaseSchema
from app.schemas.vital import VitalResponse
from app.schemas.note import NoteResponse


class TimelineEventResponse(BaseSchema):
    """Unified chronological event combining vital recordings and clinical notes."""
    type: str = Field(..., description="Event type ('vital' or 'note')")
    timestamp: datetime = Field(..., description="ISO 8601 event timestamp")
    title: str = Field(..., description="Display title for the event timeline")
    data: Union[VitalResponse, NoteResponse, Dict[str, Any]] = Field(
        ...,
        description="Event payload (VitalResponse or NoteResponse object)",
    )

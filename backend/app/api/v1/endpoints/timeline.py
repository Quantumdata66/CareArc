"""Unified Patient Timeline REST API Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.note import NoteResponse
from app.schemas.timeline import TimelineEventResponse
from app.schemas.vital import VitalResponse
from app.services import note_service, vital_service

router = APIRouter()


@router.get(
    "/patients/{patient_id}/timeline",
    response_model=List[TimelineEventResponse],
    status_code=status.HTTP_200_OK,
    summary="Get patient unified event timeline",
    description="Retrieve a combined, chronologically interleaved stream of vital readings and clinical notes.",
)
async def get_patient_timeline(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[TimelineEventResponse]:
    vitals = await vital_service.get_patient_vitals(db=db, patient_id=patient_id)
    notes = await note_service.get_patient_notes(db=db, patient_id=patient_id)

    timeline_events: List[TimelineEventResponse] = []

    for v in vitals:
        timeline_events.append(
            TimelineEventResponse(
                type="vital",
                timestamp=v.timestamp,
                title="Vitals recorded",
                data=VitalResponse.model_validate(v),
            )
        )

    for n in notes:
        timeline_events.append(
            TimelineEventResponse(
                type="note",
                timestamp=n.timestamp,
                title="Note added",
                data=NoteResponse.model_validate(n),
            )
        )

    # Sort descending: newest events first
    timeline_events.sort(key=lambda event: event.timestamp, reverse=True)
    return timeline_events

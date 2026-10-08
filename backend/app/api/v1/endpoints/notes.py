"""Clinical Notes REST API Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.note import NoteCreate, NoteResponse
from app.services import note_service

router = APIRouter()


@router.get(
    "/patients/{patient_id}/notes",
    response_model=List[NoteResponse],
    status_code=status.HTTP_200_OK,
    summary="List patient clinical notes",
    description="Retrieve all clinical notes for a patient in descending chronological order.",
)
async def list_patient_notes(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[NoteResponse]:
    notes = await note_service.get_patient_notes(db=db, patient_id=patient_id)
    return [NoteResponse.model_validate(n) for n in notes]


@router.post(
    "/patients/{patient_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create clinical note",
    description="Record a clinical observation, treatment update, or review note for a patient.",
)
async def create_patient_note(
    patient_id: str,
    note_in: NoteCreate,
    db: AsyncSession = Depends(get_db),
) -> NoteResponse:
    note = await note_service.create_note(db=db, patient_id=patient_id, note_in=note_in)
    return NoteResponse.model_validate(note)


@router.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete clinical note",
    description="Delete a clinical note by its unique identifier.",
)
async def delete_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    await note_service.delete_note(db=db, note_id=note_id)


@router.delete(
    "/patients/{patient_id}/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete clinical note for patient",
    description="Delete a clinical note within patient scope.",
)
async def delete_patient_note(
    patient_id: str,
    note_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    await note_service.delete_note(db=db, note_id=note_id)

"""Clinical Notes Service Layer.

Provides business logic for documenting, retrieving, and managing patient clinical notes.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException
from app.core.ids import generate_id
from app.models.note import ClinicalNote
from app.schemas.note import NoteCreate
from app.services.patient_service import get_patient_by_id


async def get_patient_notes(
    db: AsyncSession,
    patient_id: str,
) -> List[ClinicalNote]:
    """Retrieve all clinical notes for a patient in reverse-chronological order (DESC).

    Args:
        db: Asynchronous database session.
        patient_id: Unique patient identifier.

    Returns:
        List of ClinicalNote models ordered by timestamp DESC.

    Raises:
        EntityNotFoundException: If the patient does not exist.
    """
    # Ensure patient exists
    await get_patient_by_id(db=db, patient_id=patient_id)

    query = (
        select(ClinicalNote)
        .where(ClinicalNote.patient_id == patient_id)
        .order_by(ClinicalNote.timestamp.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_note(
    db: AsyncSession,
    patient_id: str,
    note_in: NoteCreate,
) -> ClinicalNote:
    """Create and persist a new clinical note for a patient.

    Args:
        db: Asynchronous database session.
        patient_id: Target patient identifier.
        note_in: Validated NoteCreate payload.

    Returns:
        The newly persisted ClinicalNote model.

    Raises:
        EntityNotFoundException: If the patient does not exist.
    """
    # Ensure patient exists
    await get_patient_by_id(db=db, patient_id=patient_id)

    timestamp = note_in.timestamp or datetime.now(timezone.utc)
    note_type = note_in.type or "observation"
    author = note_in.author or "Staff Clinician"

    note = ClinicalNote(
        id=generate_id("NOTE"),
        patient_id=patient_id,
        timestamp=timestamp,
        content=note_in.content,
        type=note_type,
        author=author,
    )

    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


async def delete_note(
    db: AsyncSession,
    note_id: str,
) -> None:
    """Delete a specific clinical note by ID.

    Args:
        db: Asynchronous database session.
        note_id: Unique note identifier.

    Raises:
        EntityNotFoundException: If the clinical note does not exist.
    """
    query = select(ClinicalNote).where(ClinicalNote.id == note_id)
    result = await db.execute(query)
    note = result.scalars().first()

    if not note:
        raise EntityNotFoundException(entity_name="ClinicalNote", entity_id=note_id)

    await db.delete(note)
    await db.commit()

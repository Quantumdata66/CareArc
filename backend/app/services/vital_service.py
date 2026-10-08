"""Vital Signs Service Layer.

Provides business logic for recording, retrieving, and analyzing time-series patient vitals.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException
from app.core.ids import generate_id
from app.models.patient import Patient
from app.models.vital import Vital
from app.schemas.vital import VitalCreate
from app.services.patient_service import get_patient_by_id


async def get_patient_vitals(
    db: AsyncSession,
    patient_id: str,
) -> List[Vital]:
    """Retrieve all vital readings for a patient in chronological order (ASC).

    Args:
        db: Asynchronous database session.
        patient_id: Unique patient identifier.

    Returns:
        List of Vital models ordered by timestamp ASC.

    Raises:
        EntityNotFoundException: If the patient does not exist.
    """
    # Ensure patient exists
    await get_patient_by_id(db=db, patient_id=patient_id)

    query = (
        select(Vital)
        .where(Vital.patient_id == patient_id)
        .order_by(Vital.timestamp.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_latest_vital(
    db: AsyncSession,
    patient_id: str,
) -> Optional[Vital]:
    """Retrieve the most recent vital sign reading for a patient.

    Args:
        db: Asynchronous database session.
        patient_id: Unique patient identifier.

    Returns:
        The latest Vital model or None if no vitals are recorded.

    Raises:
        EntityNotFoundException: If the patient does not exist.
    """
    # Ensure patient exists
    await get_patient_by_id(db=db, patient_id=patient_id)

    query = (
        select(Vital)
        .where(Vital.patient_id == patient_id)
        .order_by(Vital.timestamp.desc())
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalars().first()


async def create_vital(
    db: AsyncSession,
    patient_id: str,
    vital_in: VitalCreate,
) -> Vital:
    """Record a new vital sign entry for a patient.

    Args:
        db: Asynchronous database session.
        patient_id: Target patient identifier.
        vital_in: Validated VitalCreate payload (handles flat or nested BP).

    Returns:
        The newly persisted Vital model.

    Raises:
        EntityNotFoundException: If the patient does not exist.
    """
    # Verify patient existence
    await get_patient_by_id(db=db, patient_id=patient_id)

    # Extract systolic and diastolic blood pressure
    if vital_in.blood_pressure:
        systolic = vital_in.blood_pressure.systolic
        diastolic = vital_in.blood_pressure.diastolic
    elif vital_in.systolic is not None and vital_in.diastolic is not None:
        systolic = vital_in.systolic
        diastolic = vital_in.diastolic
    else:
        raise ValueError("Both systolic and diastolic blood pressure values must be provided.")

    timestamp = vital_in.timestamp or datetime.now(timezone.utc)

    vital = Vital(
        id=generate_id("VIT"),
        patient_id=patient_id,
        timestamp=timestamp,
        heart_rate=vital_in.heart_rate,
        systolic_bp=systolic,
        diastolic_bp=diastolic,
        oxygen=vital_in.oxygen,
        temperature=vital_in.temperature,
        respiratory_rate=vital_in.respiratory_rate,
        recorded_by=vital_in.recorded_by,
    )

    db.add(vital)
    await db.commit()
    await db.refresh(vital)
    return vital


async def delete_vital(
    db: AsyncSession,
    vital_id: str,
) -> None:
    """Delete a specific vital reading by ID.

    Args:
        db: Asynchronous database session.
        vital_id: Unique vital identifier.

    Raises:
        EntityNotFoundException: If the vital does not exist.
    """
    query = select(Vital).where(Vital.id == vital_id)
    result = await db.execute(query)
    vital = result.scalars().first()

    if not vital:
        raise EntityNotFoundException(entity_name="Vital", entity_id=vital_id)

    await db.delete(vital)
    await db.commit()

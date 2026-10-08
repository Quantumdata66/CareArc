"""Appointment Service Layer.

Handles appointment booking, calendar retrieval, status updates, and patient joins.
"""

from datetime import date
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import EntityNotFoundException
from app.core.ids import generate_id
from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services.patient_service import get_patient_by_id


async def get_appointments(
    db: AsyncSession,
    date_filter: Optional[date] = None,
    patient_id: Optional[str] = None,
    is_completed: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Appointment]:
    """Retrieve appointments with optional filters and eager-loaded patient info.

    Args:
        db: Asynchronous database session.
        date_filter: Optional appointment date to filter by (YYYY-MM-DD).
        patient_id: Optional patient identifier filter.
        is_completed: Optional boolean to filter completed or pending appointments.
        skip: Pagination offset.
        limit: Max records to return.

    Returns:
        List of Appointment models ordered by date and time ascending.
    """
    query = select(Appointment).options(selectinload(Appointment.patient))

    if date_filter is not None:
        query = query.where(Appointment.appointment_date == date_filter)

    if patient_id is not None:
        query = query.where(Appointment.patient_id == patient_id)

    if is_completed is not None:
        query = query.where(Appointment.is_completed == is_completed)

    query = query.order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_appointment_by_id(
    db: AsyncSession,
    appointment_id: str,
) -> Appointment:
    """Retrieve a single appointment by ID.

    Args:
        db: Asynchronous database session.
        appointment_id: Unique appointment identifier.

    Returns:
        The matched Appointment model.

    Raises:
        EntityNotFoundException: If the appointment does not exist.
    """
    query = (
        select(Appointment)
        .options(selectinload(Appointment.patient))
        .where(Appointment.id == appointment_id)
    )
    result = await db.execute(query)
    appointment = result.scalars().first()

    if not appointment:
        raise EntityNotFoundException(entity_name="Appointment", entity_id=appointment_id)

    return appointment


async def create_appointment(
    db: AsyncSession,
    appointment_in: AppointmentCreate,
) -> Appointment:
    """Schedule a new appointment for a patient.

    Args:
        db: Asynchronous database session.
        appointment_in: Validated AppointmentCreate payload.

    Returns:
        The newly created and persisted Appointment model.

    Raises:
        EntityNotFoundException: If the referenced patient does not exist.
    """
    # Verify patient exists
    await get_patient_by_id(db=db, patient_id=appointment_in.patient_id)

    appointment = Appointment(
        id=generate_id("APT"),
        patient_id=appointment_in.patient_id,
        appointment_type=appointment_in.type,
        appointment_date=appointment_in.date,
        appointment_time=appointment_in.time,
        duration_minutes=appointment_in.duration,
        is_completed=False,
    )

    db.add(appointment)
    await db.commit()
    return await get_appointment_by_id(db=db, appointment_id=appointment.id)


async def update_appointment(
    db: AsyncSession,
    appointment_id: str,
    appointment_update: AppointmentUpdate,
) -> Appointment:
    """Update details of an existing appointment.

    Args:
        db: Asynchronous database session.
        appointment_id: Unique appointment identifier.
        appointment_update: Validated fields to update.

    Returns:
        The updated Appointment model.

    Raises:
        EntityNotFoundException: If the appointment does not exist.
    """
    appointment = await get_appointment_by_id(db=db, appointment_id=appointment_id)

    if appointment_update.type is not None:
        appointment.appointment_type = appointment_update.type
    if appointment_update.date is not None:
        appointment.appointment_date = appointment_update.date
    if appointment_update.time is not None:
        appointment.appointment_time = appointment_update.time
    if appointment_update.duration is not None:
        appointment.duration_minutes = appointment_update.duration
    if appointment_update.is_completed is not None:
        appointment.is_completed = appointment_update.is_completed

    await db.commit()
    return await get_appointment_by_id(db=db, appointment_id=appointment_id)


async def mark_appointment_completed(
    db: AsyncSession,
    appointment_id: str,
) -> Appointment:
    """Mark an appointment as completed.

    Args:
        db: Asynchronous database session.
        appointment_id: Unique appointment identifier.

    Returns:
        The updated Appointment model with is_completed=True.

    Raises:
        EntityNotFoundException: If the appointment does not exist.
    """
    appointment = await get_appointment_by_id(db=db, appointment_id=appointment_id)
    appointment.is_completed = True
    await db.commit()
    return await get_appointment_by_id(db=db, appointment_id=appointment_id)


async def delete_appointment(
    db: AsyncSession,
    appointment_id: str,
) -> None:
    """Cancel and delete an appointment.

    Args:
        db: Asynchronous database session.
        appointment_id: Unique appointment identifier.

    Raises:
        EntityNotFoundException: If the appointment does not exist.
    """
    appointment = await get_appointment_by_id(db=db, appointment_id=appointment_id)
    await db.delete(appointment)
    await db.commit()

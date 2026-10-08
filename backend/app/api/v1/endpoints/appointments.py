"""Appointments REST API Endpoints."""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
)
from app.services import appointment_service

router = APIRouter()


@router.get(
    "",
    response_model=List[AppointmentResponse],
    status_code=status.HTTP_200_OK,
    summary="List appointments",
    description="Retrieve scheduled appointments with optional filtering by date, patient, and completion state.",
)
async def list_appointments(
    date_filter: Optional[date] = Query(None, alias="date", description="Filter by date (YYYY-MM-DD)"),
    patient_id: Optional[str] = Query(None, alias="patientId", description="Filter by Patient ID"),
    is_completed: Optional[bool] = Query(None, alias="isCompleted", description="Filter by completion status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
) -> List[AppointmentResponse]:
    appointments = await appointment_service.get_appointments(
        db=db,
        date_filter=date_filter,
        patient_id=patient_id,
        is_completed=is_completed,
        skip=skip,
        limit=limit,
    )
    return [AppointmentResponse.model_validate(a) for a in appointments]


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a new appointment",
    description="Schedule a consultation, follow-up, or check-up appointment for a patient.",
)
async def create_appointment(
    appointment_in: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    appointment = await appointment_service.create_appointment(db=db, appointment_in=appointment_in)
    return AppointmentResponse.model_validate(appointment)


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get appointment by ID",
)
async def get_appointment(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    appointment = await appointment_service.get_appointment_by_id(db=db, appointment_id=appointment_id)
    return AppointmentResponse.model_validate(appointment)


@router.patch(
    "/{appointment_id}/complete",
    response_model=AppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark appointment completed",
    description="Flag an appointment as completed.",
)
async def complete_appointment(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    appointment = await appointment_service.mark_appointment_completed(db=db, appointment_id=appointment_id)
    return AppointmentResponse.model_validate(appointment)


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Modify appointment",
    description="Reschedule or update details of an existing appointment.",
)
async def update_appointment(
    appointment_id: str,
    appointment_update: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    appointment = await appointment_service.update_appointment(
        db=db,
        appointment_id=appointment_id,
        appointment_update=appointment_update,
    )
    return AppointmentResponse.model_validate(appointment)


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel appointment",
    description="Cancel and remove an appointment.",
)
async def delete_appointment(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    await appointment_service.delete_appointment(db=db, appointment_id=appointment_id)

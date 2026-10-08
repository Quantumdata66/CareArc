"""Patient REST API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.services import patient_service

router = APIRouter()


@router.get(
    "",
    response_model=List[PatientResponse],
    status_code=status.HTTP_200_OK,
    summary="List all patients",
    description="Retrieve patient directory with optional text search filter and pagination.",
)
async def list_patients(
    search: Optional[str] = Query(None, description="Search query for name, room, condition, or ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> List[PatientResponse]:
    return await patient_service.get_patients(db=db, search=search, skip=skip, limit=limit)


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient",
    description="Register a patient and optionally record initial baseline vitals atomically in one transaction.",
)
async def create_patient(
    patient_in: PatientCreate,
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    return await patient_service.create_patient(db=db, patient_in=patient_in)


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient by ID",
    description="Retrieve full patient record by unique patient identifier.",
)
async def get_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    patient = await patient_service.get_patient_by_id(db=db, patient_id=patient_id)
    latest_vital_dto = None
    derived_status = "No Data"
    if patient.vitals:
        from app.schemas.vital import VitalResponse
        from app.services import delta_engine_service
        latest_vital_orm = patient.vitals[-1]
        latest_vital_dto = VitalResponse.model_validate(latest_vital_orm)
        deltas = delta_engine_service.compute_deltas(patient.vitals)
        derived_status = delta_engine_service.derive_patient_status(
            deltas=deltas,
            latest_vitals=latest_vital_orm,
        )

    resp = PatientResponse.model_validate(patient)
    resp.latest_vital = latest_vital_dto
    resp.status = derived_status
    return resp



@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
    summary="Update patient record (Full)",
)
async def update_patient_full(
    patient_id: str,
    patient_update: PatientUpdate,
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    return await patient_service.update_patient(db=db, patient_id=patient_id, patient_update=patient_update)


@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
    summary="Update patient record (Partial)",
)
async def update_patient_partial(
    patient_id: str,
    patient_update: PatientUpdate,
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    return await patient_service.update_patient(db=db, patient_id=patient_id, patient_update=patient_update)


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a patient",
    description="Deletes patient and cascades to all associated vitals, notes, and appointments.",
)
async def delete_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    await patient_service.delete_patient(db=db, patient_id=patient_id)

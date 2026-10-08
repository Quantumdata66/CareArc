"""Vital Signs REST API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.vital import VitalCreate, VitalResponse
from app.services import delta_engine_service, vital_service

router = APIRouter()


@router.get(
    "/{patient_id}/vitals",
    response_model=List[VitalResponse],
    status_code=status.HTTP_200_OK,
    summary="Get patient vitals trajectory",
    description="Retrieve all time-series vital records for a patient in ascending chronological order.",
)
async def list_patient_vitals(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[VitalResponse]:
    vitals = await vital_service.get_patient_vitals(db=db, patient_id=patient_id)
    return [VitalResponse.model_validate(v) for v in vitals]


@router.post(
    "/{patient_id}/vitals",
    response_model=VitalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new vital sign measurement",
    description="Record a timestamped vital reading for a patient with nested or flat blood pressure inputs.",
)
async def create_patient_vital(
    patient_id: str,
    vital_in: VitalCreate,
    db: AsyncSession = Depends(get_db),
) -> VitalResponse:
    vital = await vital_service.create_vital(db=db, patient_id=patient_id, vital_in=vital_in)
    return VitalResponse.model_validate(vital)


@router.get(
    "/{patient_id}/vitals/latest",
    response_model=Optional[VitalResponse],
    status_code=status.HTTP_200_OK,
    summary="Get patient's latest vital reading",
    description="Retrieve the single most recent vital record for a patient.",
)
async def get_latest_patient_vital(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
) -> Optional[VitalResponse]:
    vital = await vital_service.get_latest_vital(db=db, patient_id=patient_id)
    if not vital:
        return None
    return VitalResponse.model_validate(vital)


@router.get(
    "/{patient_id}/deltas",
    status_code=status.HTTP_200_OK,
    summary="Calculate patient vital deltas and triage status",
    description="Computes rate-of-change deltas between the last two readings and derives acuity classification.",
)
async def get_patient_deltas(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
):
    vitals = await vital_service.get_patient_vitals(db=db, patient_id=patient_id)
    latest_vital = vitals[-1] if vitals else None
    deltas = delta_engine_service.compute_deltas(vitals)
    derived_status = delta_engine_service.derive_patient_status(
        deltas=deltas,
        latest_vitals=latest_vital,
    )
    latest_update = delta_engine_service.generate_latest_update(deltas=deltas)

    return {
        "patientId": patient_id,
        "deltas": deltas,
        "status": derived_status,
        "latestUpdate": latest_update,
    }


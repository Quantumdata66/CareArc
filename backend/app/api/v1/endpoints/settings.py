"""Clinical Settings and Facility Profile REST API Endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.setting import FacilityProfileSchema, ThresholdsSchema
from app.services import setting_service

router = APIRouter()


@router.get(
    "/thresholds",
    response_model=ThresholdsSchema,
    status_code=status.HTTP_200_OK,
    summary="Get clinical thresholds",
    description="Retrieve the configured baseline reference ranges for normal vital signs.",
)
async def get_clinical_thresholds(
    db: AsyncSession = Depends(get_db),
) -> ThresholdsSchema:
    return await setting_service.get_thresholds(db=db)


@router.put(
    "/thresholds",
    response_model=ThresholdsSchema,
    status_code=status.HTTP_200_OK,
    summary="Update clinical thresholds",
    description="Modify baseline reference ranges for patient vital monitoring.",
)
async def update_clinical_thresholds(
    thresholds_in: ThresholdsSchema,
    db: AsyncSession = Depends(get_db),
) -> ThresholdsSchema:
    return await setting_service.update_thresholds(db=db, thresholds_in=thresholds_in)


@router.get(
    "/profile",
    response_model=FacilityProfileSchema,
    status_code=status.HTTP_200_OK,
    summary="Get facility profile",
    description="Retrieve facility metadata, active protocols, and monitoring configurations.",
)
async def get_facility_profile(
    db: AsyncSession = Depends(get_db),
) -> FacilityProfileSchema:
    return await setting_service.get_facility_profile(db=db)


@router.put(
    "/profile",
    response_model=FacilityProfileSchema,
    status_code=status.HTTP_200_OK,
    summary="Update facility profile",
    description="Modify facility metadata, active ward protocols, and clinical settings.",
)
async def update_facility_profile(
    profile_in: FacilityProfileSchema,
    db: AsyncSession = Depends(get_db),
) -> FacilityProfileSchema:
    return await setting_service.update_facility_profile(db=db, profile_in=profile_in)

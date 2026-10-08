"""Clinical Settings and Facility Profile Service Layer."""

from decimal import Decimal
from typing import Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import ClinicalThreshold, FacilityProfile
from app.schemas.setting import (
    BloodPressureThresholdSchema,
    FacilityProfileSchema,
    ThresholdRangeSchema,
    ThresholdsSchema,
)

DEFAULT_THRESHOLDS = {
    "heart_rate": {"min": 60.0, "max": 100.0},
    "blood_pressure": {"min": 60.0, "max": 140.0, "systolic_min": 90.0, "systolic_max": 140.0},
    "oxygen": {"min": 95.0, "max": 100.0},
    "temperature": {"min": 36.5, "max": 37.5},
}


async def get_thresholds(db: AsyncSession) -> ThresholdsSchema:
    """Retrieve normal vital signs reference ranges, initializing defaults if missing."""
    query = select(ClinicalThreshold)
    result = await db.execute(query)
    rows = result.scalars().all()

    threshold_map: Dict[str, ClinicalThreshold] = {row.vital_name: row for row in rows}

    # Initialize defaults if table is empty
    if not threshold_map:
        for name, vals in DEFAULT_THRESHOLDS.items():
            ct = ClinicalThreshold(
                vital_name=name,
                min_value=Decimal(str(vals["min"])),
                max_value=Decimal(str(vals["max"])),
                systolic_min=Decimal(str(vals["systolic_min"])) if "systolic_min" in vals else None,
                systolic_max=Decimal(str(vals["systolic_max"])) if "systolic_max" in vals else None,
            )
            db.add(ct)
            threshold_map[name] = ct
        await db.commit()

    hr = threshold_map.get("heart_rate")
    bp = threshold_map.get("blood_pressure")
    ox = threshold_map.get("oxygen")
    temp = threshold_map.get("temperature")

    return ThresholdsSchema(
        heart_rate=ThresholdRangeSchema(
            min=float(hr.min_value) if hr else 60.0,
            max=float(hr.max_value) if hr else 100.0,
        ),
        blood_pressure=BloodPressureThresholdSchema(
            min=float(bp.min_value) if bp else 60.0,
            max=float(bp.max_value) if bp else 140.0,
            systolic_min=float(bp.systolic_min) if bp and bp.systolic_min is not None else 90.0,
            systolic_max=float(bp.systolic_max) if bp and bp.systolic_max is not None else 140.0,
        ),
        oxygen=ThresholdRangeSchema(
            min=float(ox.min_value) if ox else 95.0,
            max=float(ox.max_value) if ox else 100.0,
        ),
        temperature=ThresholdRangeSchema(
            min=float(temp.min_value) if temp else 36.5,
            max=float(temp.max_value) if temp else 37.5,
        ),
    )


async def update_thresholds(
    db: AsyncSession,
    thresholds_in: ThresholdsSchema,
) -> ThresholdsSchema:
    """Update normal vital signs reference ranges."""
    # Ensure existing rows
    await get_thresholds(db)

    query = select(ClinicalThreshold)
    result = await db.execute(query)
    threshold_map = {row.vital_name: row for row in result.scalars().all()}

    if "heart_rate" in threshold_map:
        threshold_map["heart_rate"].min_value = Decimal(str(thresholds_in.heart_rate.min))
        threshold_map["heart_rate"].max_value = Decimal(str(thresholds_in.heart_rate.max))

    if "blood_pressure" in threshold_map:
        threshold_map["blood_pressure"].min_value = Decimal(str(thresholds_in.blood_pressure.min))
        threshold_map["blood_pressure"].max_value = Decimal(str(thresholds_in.blood_pressure.max))
        if thresholds_in.blood_pressure.systolic_min is not None:
            threshold_map["blood_pressure"].systolic_min = Decimal(str(thresholds_in.blood_pressure.systolic_min))
        if thresholds_in.blood_pressure.systolic_max is not None:
            threshold_map["blood_pressure"].systolic_max = Decimal(str(thresholds_in.blood_pressure.systolic_max))

    if "oxygen" in threshold_map:
        threshold_map["oxygen"].min_value = Decimal(str(thresholds_in.oxygen.min))
        threshold_map["oxygen"].max_value = Decimal(str(thresholds_in.oxygen.max))

    if "temperature" in threshold_map:
        threshold_map["temperature"].min_value = Decimal(str(thresholds_in.temperature.min))
        threshold_map["temperature"].max_value = Decimal(str(thresholds_in.temperature.max))

    await db.commit()
    return await get_thresholds(db)


async def get_facility_profile(db: AsyncSession) -> FacilityProfileSchema:
    """Retrieve facility and ward profile, initializing default if absent."""
    query = select(FacilityProfile).where(FacilityProfile.id == "DEFAULT_FACILITY")
    result = await db.execute(query)
    profile = result.scalars().first()

    if not profile:
        profile = FacilityProfile(
            id="DEFAULT_FACILITY",
            facility_name="CareArc Lagos Central Hospital",
            unit_name="Intensive Care & Monitoring Unit 4B",
            facility_code="FAC-4B-LAGOS",
            emergency_phone="+234 800 227 3272",
            primary_email="icu4b@carearc.health",
            address="14 Clinical Way, Victoria Island, Lagos",
            bed_capacity="24 Beds (18 Active)",
            active_protocol="Acute Care Trajectory Protocol v3.2",
            vitals_interval="4 hours",
            delta_engine_window="12 hours",
            ai_model="GPT-4o-mini Clinical Engine",
            auto_handover=True,
            critical_alert_escalation=True,
            specialties=["Critical Care", "Internal Medicine", "Cardiology", "Pulmonology"],
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return FacilityProfileSchema.model_validate(profile)


async def update_facility_profile(
    db: AsyncSession,
    profile_in: FacilityProfileSchema,
) -> FacilityProfileSchema:
    """Update facility and ward profile."""
    query = select(FacilityProfile).where(FacilityProfile.id == "DEFAULT_FACILITY")
    result = await db.execute(query)
    profile = result.scalars().first()

    if not profile:
        await get_facility_profile(db)
        result = await db.execute(query)
        profile = result.scalars().first()

    profile.facility_name = profile_in.facility_name
    profile.unit_name = profile_in.unit_name
    profile.facility_code = profile_in.facility_id
    profile.emergency_phone = profile_in.emergency_phone
    profile.primary_email = profile_in.primary_email
    profile.address = profile_in.address
    profile.bed_capacity = profile_in.bed_capacity
    profile.active_protocol = profile_in.active_protocol
    profile.vitals_interval = profile_in.vitals_interval
    profile.delta_engine_window = profile_in.delta_engine_window
    profile.ai_model = profile_in.ai_model
    profile.auto_handover = profile_in.auto_handover
    profile.critical_alert_escalation = profile_in.critical_alert_escalation
    profile.specialties = profile_in.specialties

    await db.commit()
    await db.refresh(profile)
    return FacilityProfileSchema.model_validate(profile)

"""Patient Service Layer.

Encapsulates patient registration, querying, updating, deletion, and atomic onboarding transactions.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import EntityNotFoundException
from app.core.ids import generate_patient_id, generate_vital_id
from app.models.patient import Patient
from app.models.vital import Vital
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.schemas.vital import VitalResponse
from app.services import delta_engine_service


async def get_patients(
    db: AsyncSession,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[PatientResponse]:
    """Retrieve all patients with optional text search and pagination."""
    query = (
        select(Patient)
        .options(selectinload(Patient.vitals))
        .offset(skip)
        .limit(limit)
        .order_by(Patient.admitted.desc(), Patient.name.asc())
    )

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Patient.name.ilike(search_pattern),
                Patient.room.ilike(search_pattern),
                Patient.condition.ilike(search_pattern),
                Patient.id.ilike(search_pattern),
            )
        )

    result = await db.execute(query)
    patients = result.scalars().all()

    # Transform ORM models to PatientResponse DTOs including latestVital and derived status
    patient_responses: List[PatientResponse] = []
    for patient in patients:
        latest_vital_dto = None
        derived_status = "No Data"
        if patient.vitals:
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
        patient_responses.append(resp)

    return patient_responses



async def get_patient_by_id(db: AsyncSession, patient_id: str) -> Patient:
    """Retrieve a single patient by ID or raise EntityNotFoundException."""
    query = (
        select(Patient)
        .options(
            selectinload(Patient.vitals),
            selectinload(Patient.notes),
            selectinload(Patient.appointments),
        )
        .where(Patient.id == patient_id)
    )
    result = await db.execute(query)
    patient = result.scalar_one_or_none()

    if not patient:
        raise EntityNotFoundException(
            message=f"Patient with ID '{patient_id}' not found.",
            details={"patientId": patient_id},
        )

    return patient


async def create_patient(db: AsyncSession, patient_in: PatientCreate) -> PatientResponse:
    """Atomically create a new patient and optional initial baseline vitals."""
    new_patient_id = generate_patient_id()

    # 1. Instantiate Patient entity
    new_patient = Patient(
        id=new_patient_id,
        name=patient_in.name,
        age=patient_in.age,
        gender=patient_in.gender,
        room=patient_in.room,
        condition=patient_in.condition,
        admitted=patient_in.admitted,
        weight=patient_in.weight or "N/A",
        phone=patient_in.phone,
        email=patient_in.email,
        emergency_contact=patient_in.emergency_contact,
    )
    db.add(new_patient)

    # 2. If initial vitals provided, create them atomically in the same transaction
    latest_vital_dto: Optional[VitalResponse] = None
    if patient_in.initial_vitals:
        v_in = patient_in.initial_vitals
        bp = v_in.blood_pressure
        if not bp and (v_in.systolic and v_in.diastolic):
            sys_val = v_in.systolic
            dia_val = v_in.diastolic
        elif bp:
            sys_val = bp.systolic
            dia_val = bp.diastolic
        else:
            sys_val = 120
            dia_val = 80

        initial_vital = Vital(
            id=generate_vital_id(),
            patient_id=new_patient_id,
            timestamp=v_in.timestamp or datetime.now(timezone.utc),
            heart_rate=v_in.heart_rate,
            systolic_bp=sys_val,
            diastolic_bp=dia_val,
            oxygen=v_in.oxygen,
            temperature=v_in.temperature,
            respiratory_rate=v_in.respiratory_rate,
            recorded_by=v_in.recorded_by or "Onboarding Registration",
        )
        db.add(initial_vital)
        await db.flush()
        latest_vital_dto = VitalResponse.model_validate(initial_vital)

    # Commit both patient and optional vital in a single atomic database transaction
    await db.commit()
    await db.refresh(new_patient)

    response = PatientResponse.model_validate(new_patient)
    response.latest_vital = latest_vital_dto
    return response


async def update_patient(
    db: AsyncSession, patient_id: str, patient_update: PatientUpdate
) -> PatientResponse:
    """Update patient demographic and contact fields."""
    patient = await get_patient_by_id(db, patient_id)

    update_data = patient_update.model_dump(exclude_unset=True)

    # Handle nested contact updates if provided
    if "contact" in update_data and update_data["contact"] is not None:
        contact_dict = update_data.pop("contact")
        if "phone" in contact_dict:
            patient.phone = contact_dict["phone"]
        if "email" in contact_dict:
            patient.email = contact_dict["email"]
        if "emergencyContact" in contact_dict or "emergency_contact" in contact_dict:
            patient.emergency_contact = contact_dict.get("emergencyContact") or contact_dict.get("emergency_contact")

    for field, value in update_data.items():
        if hasattr(patient, field) and value is not None:
            setattr(patient, field, value)

    await db.commit()
    await db.refresh(patient)
    return PatientResponse.model_validate(patient)


async def delete_patient(db: AsyncSession, patient_id: str) -> None:
    """Delete a patient record, triggering database cascading deletes on children."""
    patient = await get_patient_by_id(db, patient_id)
    await db.delete(patient)
    await db.commit()

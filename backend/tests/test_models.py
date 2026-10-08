"""Milestone 3 SQLAlchemy ORM Model Tests."""

from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models import (
    Base,
    Patient,
    Vital,
    ClinicalNote,
    Appointment,
    ClinicalThreshold,
    FacilityProfile,
)


def test_metadata_contains_all_tables():
    """Verify that all 6 tables are registered in SQLAlchemy metadata."""
    table_names = Base.metadata.tables.keys()
    assert "patients" in table_names
    assert "vitals" in table_names
    assert "clinical_notes" in table_names
    assert "appointments" in table_names
    assert "clinical_thresholds" in table_names
    assert "facility_profiles" in table_names


@pytest.mark.asyncio
async def test_patient_and_relationships_crud():
    """Verify Patient creation, child entity relationships, and cascade delete."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Create tables in memory
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        # 1. Create Patient
        patient = Patient(
            id="PT-TEST001",
            name="Amina Yusuf",
            age=54,
            gender="Female",
            room="Room 4B",
            condition="Respiratory symptoms, Fever",
            admitted=date(2026, 7, 20),
            weight="160lbs",
            phone="+234 801 234 5678",
            email="amina@example.com",
            emergency_contact="Fatima Yusuf — +234 802 345 6789",
        )
        session.add(patient)
        await session.commit()

        # 2. Add Vital, Note, Appointment to Patient
        vital = Vital(
            id="VIT-TEST001",
            patient_id="PT-TEST001",
            timestamp=datetime(2026, 7, 26, 8, 0, tzinfo=timezone.utc),
            heart_rate=75,
            systolic_bp=120,
            diastolic_bp=80,
            oxygen=Decimal("97.0"),
            temperature=Decimal("37.4"),
            respiratory_rate=18,
            recorded_by="Nurse Fatima",
        )
        note = ClinicalNote(
            id="NOTE-TEST001",
            patient_id="PT-TEST001",
            timestamp=datetime(2026, 7, 26, 8, 30, tzinfo=timezone.utc),
            content="Patient stable on oral medication.",
            type="observation",
            author="Dr. Sarah Chen",
        )
        appointment = Appointment(
            id="APT-TEST001",
            patient_id="PT-TEST001",
            appointment_type="Follow-up",
            appointment_date=date(2026, 7, 28),
            appointment_time="09:00",
            duration_minutes=30,
            is_completed=False,
        )

        session.add_all([vital, note, appointment])
        await session.commit()

    # 3. Query Patient and verify properties & relationships
    async with session_factory() as session:
        result = await session.execute(
            select(Patient).where(Patient.id == "PT-TEST001")
        )
        saved_patient = result.scalar_one()

        assert saved_patient.name == "Amina Yusuf"
        assert saved_patient.contact["phone"] == "+234 801 234 5678"
        assert len(saved_patient.vitals) == 1
        assert saved_patient.vitals[0].blood_pressure == {"systolic": 120, "diastolic": 80}
        assert len(saved_patient.notes) == 1
        assert len(saved_patient.appointments) == 1
        assert saved_patient.appointments[0].patient_name == "Amina Yusuf"

    # 4. Verify Cascade Deletion
    async with session_factory() as session:
        result = await session.execute(
            select(Patient).where(Patient.id == "PT-TEST001")
        )
        patient_to_delete = result.scalar_one()
        await session.delete(patient_to_delete)
        await session.commit()

        # Confirm child vitals are deleted
        vitals_result = await session.execute(
            select(Vital).where(Vital.patient_id == "PT-TEST001")
        )
        assert vitals_result.scalars().all() == []

    await engine.dispose()


@pytest.mark.asyncio
async def test_thresholds_and_facility_profile():
    """Verify ClinicalThreshold and FacilityProfile persistence."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        threshold = ClinicalThreshold(
            vital_name="heartRate",
            min_value=Decimal("60.0"),
            max_value=Decimal("100.0"),
        )
        profile = FacilityProfile(
            id="DEFAULT_FACILITY",
            facility_name="CareArc Center",
            unit_name="Ward 4B",
            facility_code="FAC-4B",
            specialties=["Cardiovascular", "Respiratory"],
        )
        session.add_all([threshold, profile])
        await session.commit()

    async with session_factory() as session:
        t_result = await session.execute(
            select(ClinicalThreshold).where(ClinicalThreshold.vital_name == "heartRate")
        )
        saved_threshold = t_result.scalar_one()
        assert saved_threshold.min_value == Decimal("60.0")

        p_result = await session.execute(
            select(FacilityProfile).where(FacilityProfile.id == "DEFAULT_FACILITY")
        )
        saved_profile = p_result.scalar_one()
        assert saved_profile.facility_name == "CareArc Center"
        assert "Cardiovascular" in saved_profile.specialties

    await engine.dispose()

"""Milestone 12 Database Seeder Integration Tests."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.seed import seed_database
from app.models import Base
from app.models.appointment import Appointment
from app.models.note import ClinicalNote
from app.models.patient import Patient
from app.models.setting import ClinicalThreshold, FacilityProfile
from app.models.vital import Vital


@pytest.mark.asyncio
async def test_seed_database_execution():
    """Test that seed_database populates all 6 tables and is idempotent."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    test_sessionmaker = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_sessionmaker() as session:
        # Run seeder
        await seed_database(session)

        # Verify Patients
        patients = (await session.execute(select(Patient))).scalars().all()
        assert len(patients) == 5
        patient_ids = {p.id for p in patients}
        assert "PT-001" in patient_ids
        assert "PT-005" in patient_ids

        # Verify Vitals
        vitals = (await session.execute(select(Vital))).scalars().all()
        assert len(vitals) == 31

        # Verify Notes
        notes = (await session.execute(select(ClinicalNote))).scalars().all()
        assert len(notes) == 17

        # Verify Appointments
        appointments = (await session.execute(select(Appointment))).scalars().all()
        assert len(appointments) == 10

        # Verify Thresholds & Profile
        thresholds = (await session.execute(select(ClinicalThreshold))).scalars().all()
        assert len(thresholds) == 4

        profile = (await session.execute(select(FacilityProfile))).scalars().first()
        assert profile is not None
        assert profile.facility_code == "FAC-4B-LAGOS"

        # Idempotency check: Running seed_database again should not duplicate rows
        await seed_database(session)
        patients_after = (await session.execute(select(Patient))).scalars().all()
        assert len(patients_after) == 5

    await test_engine.dispose()

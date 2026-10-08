"""Milestone 9 Clinical Delta Engine Service & Endpoint Integration Tests."""

from datetime import datetime, timezone, timedelta
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.main import app
from app.models import Base
from app.services.delta_engine_service import (
    compute_deltas,
    derive_patient_status,
    generate_latest_update,
)


@pytest.fixture
async def test_db_session():
    """Create an isolated in-memory SQLite database and override get_db."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    test_sessionmaker = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with test_sessionmaker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield test_sessionmaker
    app.dependency_overrides.clear()
    await test_engine.dispose()


def test_compute_deltas_and_classifications():
    """Unit test delta calculations and direction/severity mapping."""
    t1 = datetime(2026, 8, 1, 8, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)

    vitals = [
        {
            "timestamp": t1.isoformat(),
            "heartRate": 80,
            "oxygen": 98.0,
            "temperature": 37.0,
            "respiratoryRate": 16,
            "bloodPressure": {"systolic": 120, "diastolic": 80},
        },
        {
            "timestamp": t2.isoformat(),
            "heartRate": 100,  # +20 bpm (+25% -> significant, increasing)
            "oxygen": 92.0,    # -6% SpO2 (-6.1% -> moderate, decreasing)
            "temperature": 38.5,  # +1.5 C (+4.1% -> minimal/moderate)
            "respiratoryRate": 24, # +8 brpm (+50% -> significant, increasing)
            "bloodPressure": {"systolic": 140, "diastolic": 90},
        },
    ]

    deltas = compute_deltas(vitals)
    assert deltas is not None
    assert len(deltas) == 5  # HR, O2, Temp, Resp, BP

    hr_delta = next(d for d in deltas if d["vital"] == "heartRate")
    assert hr_delta["change"] == 20.0
    assert hr_delta["percentChange"] == 25.0
    assert hr_delta["direction"] == "increasing"
    assert hr_delta["severity"] == "significant"

    bp_delta = next(d for d in deltas if d["vital"] == "bloodPressure")
    assert bp_delta["change"] == "+20.0/+10.0"

    # Status derivation: Latest has HR=100 (normal upper bound is 100), O2=92 (out of range <95), Resp=24 (>20 out of range)
    # Significant worsening in HR (increasing) and RespRate (increasing)
    # Out of range AND significant worsening -> "Review"
    status = derive_patient_status(deltas=deltas, latest_vitals=vitals[1])
    assert status == "Review"


def test_derive_patient_status_states():
    """Test all 4 triage status classifications: Review, Watch, Improving, Stable."""
    # 1. No data
    assert derive_patient_status(deltas=None, latest_vitals=None) == "No Data"

    # 2. Single reading (no deltas) -> Stable
    single_vital = {"heartRate": 72, "oxygen": 98.0, "temperature": 36.8, "respiratoryRate": 14}
    assert derive_patient_status(deltas=None, latest_vitals=single_vital) == "Stable"

    # 3. Improving: HR dropping from 110 to 75 (-31.8% significant decreasing), Temp 39.0 -> 36.8, within normal range now
    improving_deltas = [
        {
            "vital": "heartRate",
            "direction": "decreasing",
            "severity": "significant",
            "change": -35.0,
            "percentChange": -31.8,
        },
        {
            "vital": "temperature",
            "direction": "decreasing",
            "severity": "moderate",
            "change": -2.2,
            "percentChange": -5.6,
        },
    ]
    improving_latest = {"heartRate": 75, "oxygen": 99.0, "temperature": 36.8, "respiratoryRate": 16}
    assert derive_patient_status(deltas=improving_deltas, latest_vitals=improving_latest) == "Improving"

    # 4. Watch: Out of range (O2=93%) but without significant worsening
    mild_deltas = [
        {
            "vital": "oxygen",
            "direction": "stable",
            "severity": "minimal",
            "change": 0.0,
            "percentChange": 0.0,
        }
    ]
    watch_latest = {"heartRate": 75, "oxygen": 93.0, "temperature": 36.8, "respiratoryRate": 16}
    assert derive_patient_status(deltas=mild_deltas, latest_vitals=watch_latest) == "Watch"


@pytest.mark.asyncio
async def test_patient_deltas_endpoint(test_db_session):
    """Test GET /api/v1/patients/{id}/deltas returns computed deltas and status."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create Patient
        p_res = await client.post(
            "/api/v1/patients",
            json={
                "name": "Tunde Bakare",
                "age": 60,
                "gender": "Male",
                "room": "Room 6B",
                "condition": "Acute pneumonia",
                "admitted": "2026-08-14",
            },
        )
        patient_id = p_res.json()["id"]

        # Add 2 vitals
        t1 = datetime(2026, 8, 14, 6, 0, 0, tzinfo=timezone.utc)
        t2 = datetime(2026, 8, 14, 12, 0, 0, tzinfo=timezone.utc)

        await client.post(
            f"/api/v1/patients/{patient_id}/vitals",
            json={
                "heartRate": 75,
                "systolic": 120,
                "diastolic": 80,
                "oxygen": 97.0,
                "temperature": 37.0,
                "timestamp": t1.isoformat(),
            },
        )

        await client.post(
            f"/api/v1/patients/{patient_id}/vitals",
            json={
                "heartRate": 115,  # Significant worsening
                "systolic": 145,
                "diastolic": 95,
                "oxygen": 91.0,   # Out of range (<95%) & worsening
                "temperature": 39.2, # Fever worsening
                "timestamp": t2.isoformat(),
            },
        )

        # Query deltas endpoint
        delta_res = await client.get(f"/api/v1/patients/{patient_id}/deltas")
        assert delta_res.status_code == 200
        data = delta_res.json()
        assert data["patientId"] == patient_id
        assert data["status"] == "Review"
        assert len(data["deltas"]) >= 4
        assert "Heart Rate ↑ +40" in data["latestUpdate"] or "Blood Oxygen" in data["latestUpdate"]

"""Milestone 11 Patient Timeline API Integration Tests."""

from datetime import datetime, timezone, timedelta
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.main import app
from app.models import Base


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


@pytest.mark.asyncio
async def test_interleaved_patient_timeline(test_db_session):
    """Test retrieving unified timeline with interleaved vitals and notes ordered DESC."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create Patient
        p_res = await client.post(
            "/api/v1/patients",
            json={
                "name": "Folake Adeleke",
                "age": 29,
                "gender": "Female",
                "room": "Room 4A",
                "condition": "Postpartum observation",
                "admitted": "2026-08-16",
            },
        )
        assert p_res.status_code == 201
        patient_id = p_res.json()["id"]

        # 2. Add Vital at 08:00
        t1 = datetime(2026, 8, 16, 8, 0, 0, tzinfo=timezone.utc)
        await client.post(
            f"/api/v1/patients/{patient_id}/vitals",
            json={
                "heartRate": 74,
                "systolic": 118,
                "diastolic": 76,
                "oxygen": 98.0,
                "temperature": 36.6,
                "timestamp": t1.isoformat(),
            },
        )

        # 3. Add Clinical Note at 10:30
        t2 = datetime(2026, 8, 16, 10, 30, 0, tzinfo=timezone.utc)
        await client.post(
            f"/api/v1/patients/{patient_id}/notes",
            json={
                "content": "Patient resting comfortably. Infant breastfeeding well.",
                "type": "observation",
                "author": "Midwife Ada",
                "timestamp": t2.isoformat(),
            },
        )

        # 4. Add Vital at 14:00
        t3 = datetime(2026, 8, 16, 14, 0, 0, tzinfo=timezone.utc)
        await client.post(
            f"/api/v1/patients/{patient_id}/vitals",
            json={
                "heartRate": 78,
                "systolic": 120,
                "diastolic": 78,
                "oxygen": 98.5,
                "temperature": 36.7,
                "timestamp": t3.isoformat(),
            },
        )

        # 5. Fetch Timeline
        timeline_res = await client.get(f"/api/v1/patients/{patient_id}/timeline")
        assert timeline_res.status_code == 200
        events = timeline_res.json()
        assert len(events) == 3

        # Must be in DESC order: Event 1 (14:00 vital), Event 2 (10:30 note), Event 3 (08:00 vital)
        assert events[0]["type"] == "vital"
        assert events[0]["title"] == "Vitals recorded"
        assert events[0]["data"]["heartRate"] == 78

        assert events[1]["type"] == "note"
        assert events[1]["title"] == "Note added"
        assert "breastfeeding" in events[1]["data"]["content"]

        assert events[2]["type"] == "vital"
        assert events[2]["data"]["heartRate"] == 74

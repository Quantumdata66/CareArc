"""Milestone 6 Vitals API & Service Layer Integration Tests."""

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
async def test_record_and_list_vitals(test_db_session):
    """Test recording vitals with nested BP and retrieving chronological trajectory."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create a Patient first
        patient_res = await client.post(
            "/api/v1/patients",
            json={
                "name": "Ibrahim Bello",
                "age": 42,
                "gender": "Male",
                "room": "Room 2A",
                "condition": "Post-op monitoring",
                "admitted": "2026-08-01",
            },
        )
        assert patient_res.status_code == 201
        patient_id = patient_res.json()["id"]

        # 2. Check latest vitals before any are recorded
        latest_empty_res = await client.get(f"/api/v1/patients/{patient_id}/vitals/latest")
        assert latest_empty_res.status_code == 200
        assert latest_empty_res.json() is None

        # 3. Post first vital reading with nested bloodPressure
        t1 = datetime(2026, 8, 1, 8, 0, 0, tzinfo=timezone.utc)
        vital1_payload = {
            "heartRate": 76,
            "bloodPressure": {"systolic": 120, "diastolic": 80},
            "oxygen": 98.5,
            "temperature": 36.8,
            "respiratoryRate": 16,
            "recordedBy": "Nurse Chioma",
            "timestamp": t1.isoformat(),
        }
        v1_res = await client.post(f"/api/v1/patients/{patient_id}/vitals", json=vital1_payload)
        assert v1_res.status_code == 201
        v1_data = v1_res.json()
        assert v1_data["id"].startswith("VIT-")
        assert v1_data["patientId"] == patient_id
        assert v1_data["heartRate"] == 76
        assert v1_data["bloodPressure"]["systolic"] == 120
        assert v1_data["bloodPressure"]["diastolic"] == 80
        assert v1_data["oxygen"] == 98.5

        # 4. Post second vital reading with flat systolic & diastolic
        t2 = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
        vital2_payload = {
            "heartRate": 82,
            "systolic": 125,
            "diastolic": 82,
            "oxygen": 97.0,
            "temperature": 37.1,
            "respiratoryRate": 18,
            "recordedBy": "Dr. Adeleke",
            "timestamp": t2.isoformat(),
        }
        v2_res = await client.post(f"/api/v1/patients/{patient_id}/vitals", json=vital2_payload)
        assert v2_res.status_code == 201
        v2_data = v2_res.json()
        assert v2_data["bloodPressure"]["systolic"] == 125
        assert v2_data["bloodPressure"]["diastolic"] == 82

        # 5. List vitals -> must be in ASCENDING chronological order
        list_res = await client.get(f"/api/v1/patients/{patient_id}/vitals")
        assert list_res.status_code == 200
        vitals_list = list_res.json()
        assert len(vitals_list) == 2
        assert vitals_list[0]["heartRate"] == 76
        assert vitals_list[1]["heartRate"] == 82

        # 6. Get latest vital
        latest_res = await client.get(f"/api/v1/patients/{patient_id}/vitals/latest")
        assert latest_res.status_code == 200
        latest_data = latest_res.json()
        assert latest_data["heartRate"] == 82
        assert latest_data["bloodPressure"]["systolic"] == 125


@pytest.mark.asyncio
async def test_vitals_patient_not_found_and_validation(test_db_session):
    """Test 404 for non-existent patient and 422 for invalid vital inputs."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Non-existent patient list
        res = await client.get("/api/v1/patients/PT-DOESNOTEXIST/vitals")
        assert res.status_code == 404

        # Non-existent patient post
        post_res = await client.post(
            "/api/v1/patients/PT-DOESNOTEXIST/vitals",
            json={
                "heartRate": 80,
                "systolic": 120,
                "diastolic": 80,
                "oxygen": 98.0,
                "temperature": 36.5,
            },
        )
        assert post_res.status_code == 404

        # Create valid patient
        p_res = await client.post(
            "/api/v1/patients",
            json={
                "name": "Emeka Obi",
                "age": 28,
                "gender": "Male",
                "room": "Room 1C",
                "condition": "Observation",
                "admitted": "2026-08-05",
            },
        )
        p_id = p_res.json()["id"]

        # Invalid heart rate (out of bounds)
        bad_hr_res = await client.post(
            f"/api/v1/patients/{p_id}/vitals",
            json={
                "heartRate": 10,  # Below minimum 20
                "systolic": 120,
                "diastolic": 80,
                "oxygen": 98.0,
                "temperature": 36.5,
            },
        )
        assert bad_hr_res.status_code == 422

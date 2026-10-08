"""Milestone 5 Patient API & Service Layer Integration Tests."""

from datetime import date
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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
async def test_create_and_get_patient(test_db_session):
    """Test POST /api/v1/patients and GET /api/v1/patients/{id}."""
    payload = {
        "name": "Amina Yusuf",
        "age": 54,
        "gender": "Female",
        "room": "Room 4B",
        "condition": "Respiratory symptoms, Fever",
        "admitted": "2026-07-20",
        "weight": "160lbs",
        "contact": {
            "phone": "+234 801 234 5678",
            "email": "amina.yusuf@email.com",
            "emergencyContact": "Fatima Yusuf — +234 802 345 6789",
        },
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create Patient
        res = await client.post("/api/v1/patients", json=payload)
        assert res.status_code == 201
        created = res.json()
        assert created["id"].startswith("PT-")
        assert created["name"] == "Amina Yusuf"
        assert created["contact"]["emergencyContact"] == "Fatima Yusuf — +234 802 345 6789"
        patient_id = created["id"]

        # 2. Get Patient by ID
        get_res = await client.get(f"/api/v1/patients/{patient_id}")
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["id"] == patient_id
        assert data["room"] == "Room 4B"


@pytest.mark.asyncio
async def test_create_patient_with_atomic_initial_vitals(test_db_session):
    """Test atomic onboarding of Patient + Initial Vitals in POST /api/v1/patients."""
    payload = {
        "name": "Bello Kasim",
        "age": "38",  # String coercion
        "gender": "Male",
        "room": "Room 5D",
        "condition": "Observation — Chest Pain",
        "admitted": "2026-07-28",
        "weight": "185lbs",
        "phone": "+234 807 890 1234",
        "email": "bello.kasim@email.com",
        "initialVitals": {
            "heartRate": 88,
            "systolic": 130,
            "diastolic": 85,
            "oxygen": 96.0,
            "temperature": 37.2,
            "respiratoryRate": 18,
            "recordedBy": "Dr. Sarah Chen",
        },
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/patients", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Bello Kasim"
        assert data["age"] == 38
        assert data["latestVital"] is not None
        assert data["latestVital"]["heartRate"] == 88
        assert data["latestVital"]["bloodPressure"] == {"systolic": 130, "diastolic": 85}


@pytest.mark.asyncio
async def test_list_and_search_patients(test_db_session):
    """Test GET /api/v1/patients with search filter."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create 2 patients
        await client.post(
            "/api/v1/patients",
            json={
                "name": "John Okafor",
                "age": 62,
                "gender": "Male",
                "room": "Room 7A",
                "condition": "Cardiac Arrhythmia",
                "admitted": "2026-07-18",
            },
        )
        await client.post(
            "/api/v1/patients",
            json={
                "name": "Mary Adebayo",
                "age": 47,
                "gender": "Female",
                "room": "Room 2C",
                "condition": "Post-Surgery Recovery",
                "admitted": "2026-07-22",
            },
        )

        # List all
        all_res = await client.get("/api/v1/patients")
        assert all_res.status_code == 200
        assert len(all_res.json()) == 2

        # Search for "Okafor"
        search_res = await client.get("/api/v1/patients?search=Okafor")
        assert search_res.status_code == 200
        results = search_res.json()
        assert len(results) == 1
        assert results[0]["name"] == "John Okafor"


@pytest.mark.asyncio
async def test_update_and_delete_patient(test_db_session):
    """Test PATCH /api/v1/patients/{id} and DELETE /api/v1/patients/{id}."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create
        create_res = await client.post(
            "/api/v1/patients",
            json={
                "name": "Chidinma Eze",
                "age": 71,
                "gender": "Female",
                "room": "Room 1A",
                "condition": "Hypertension",
                "admitted": "2026-07-15",
            },
        )
        patient_id = create_res.json()["id"]

        # 2. Patch room & condition
        patch_res = await client.patch(
            f"/api/v1/patients/{patient_id}",
            json={"room": "ICU-3", "condition": "Hypertension, Monitored"},
        )
        assert patch_res.status_code == 200
        updated = patch_res.json()
        assert updated["room"] == "ICU-3"
        assert updated["condition"] == "Hypertension, Monitored"

        # 3. Delete
        del_res = await client.delete(f"/api/v1/patients/{patient_id}")
        assert del_res.status_code == 204

        # 4. Verify Not Found
        get_res = await client.get(f"/api/v1/patients/{patient_id}")
        assert get_res.status_code == 404
        assert get_res.json()["error"] is True

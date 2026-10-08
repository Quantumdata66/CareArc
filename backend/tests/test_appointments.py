"""Milestone 8 Appointments API & Service Layer Integration Tests."""

from datetime import date
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
async def test_appointment_lifecycle_and_filters(test_db_session):
    """Test creating, filtering, completing, modifying, and deleting appointments."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create Patient
        p_res = await client.post(
            "/api/v1/patients",
            json={
                "name": "Kelechi Nnamdi",
                "age": 48,
                "gender": "Male",
                "room": "Room 5A",
                "condition": "Hypertension review",
                "admitted": "2026-08-12",
            },
        )
        assert p_res.status_code == 201
        patient_id = p_res.json()["id"]

        # 2. Book an Appointment
        apt_payload = {
            "patientId": patient_id,
            "type": "Consultation",
            "date": "2026-08-15",
            "time": "10:30",
            "duration": 45,
        }
        create_res = await client.post("/api/v1/appointments", json=apt_payload)
        assert create_res.status_code == 201
        apt = create_res.json()
        assert apt["id"].startswith("APT-")
        assert apt["patientId"] == patient_id
        assert apt["name"] == "Kelechi Nnamdi"  # Denormalized patient name
        assert apt["type"] == "Consultation"
        assert apt["date"] == "2026-08-15"
        assert apt["time"] == "10:30"
        assert apt["duration"] == 45
        assert apt["isCompleted"] is False
        apt_id = apt["id"]

        # 3. Filter appointments by date and patientId
        filter_res = await client.get(f"/api/v1/appointments?date=2026-08-15&patientId={patient_id}")
        assert filter_res.status_code == 200
        items = filter_res.json()
        assert len(items) == 1
        assert items[0]["id"] == apt_id

        # 4. Mark appointment as completed
        comp_res = await client.patch(f"/api/v1/appointments/{apt_id}/complete")
        assert comp_res.status_code == 200
        assert comp_res.json()["isCompleted"] is True

        # 5. Filter by isCompleted=false -> should return 0 items
        filter_pending_res = await client.get("/api/v1/appointments?isCompleted=false")
        assert filter_pending_res.status_code == 200
        assert len(filter_pending_res.json()) == 0

        # 6. Reschedule / modify appointment
        update_res = await client.patch(
            f"/api/v1/appointments/{apt_id}",
            json={"time": "11:00", "duration": 60},
        )
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["time"] == "11:00"
        assert updated["duration"] == 60

        # 7. Cancel and delete appointment
        del_res = await client.delete(f"/api/v1/appointments/{apt_id}")
        assert del_res.status_code == 204

        # 8. Verify deletion
        get_res = await client.get(f"/api/v1/appointments/{apt_id}")
        assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_appointment_validation_and_errors(test_db_session):
    """Test 404 when booking for invalid patient and invalid appointment id."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Non-existent patient booking
        res = await client.post(
            "/api/v1/appointments",
            json={
                "patientId": "PT-NONEXISTENT",
                "type": "Follow-up",
                "date": "2026-08-20",
                "time": "14:00",
            },
        )
        assert res.status_code == 404

        # Non-existent appointment operations
        assert (await client.get("/api/v1/appointments/APT-NOTFOUND")).status_code == 404
        assert (await client.patch("/api/v1/appointments/APT-NOTFOUND/complete")).status_code == 404
        assert (await client.delete("/api/v1/appointments/APT-NOTFOUND")).status_code == 404

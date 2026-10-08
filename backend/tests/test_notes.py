"""Milestone 7 Clinical Notes API & Service Layer Integration Tests."""

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
async def test_create_list_and_delete_notes(test_db_session):
    """Test creating, listing in DESC order, and deleting clinical notes."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create Patient
        p_res = await client.post(
            "/api/v1/patients",
            json={
                "name": "Ngozi Eze",
                "age": 35,
                "gender": "Female",
                "room": "Room 3C",
                "condition": "Post-cesarean recovery",
                "admitted": "2026-08-10",
            },
        )
        assert p_res.status_code == 201
        patient_id = p_res.json()["id"]

        # 2. Add first note
        t1 = datetime(2026, 8, 10, 9, 0, 0, tzinfo=timezone.utc)
        note1_res = await client.post(
            f"/api/v1/patients/{patient_id}/notes",
            json={
                "content": "Patient reports moderate abdominal tenderness. Vitals stable.",
                "type": "observation",
                "author": "Nurse Amaka",
                "timestamp": t1.isoformat(),
            },
        )
        assert note1_res.status_code == 201
        n1 = note1_res.json()
        assert n1["id"].startswith("NOTE-")
        assert n1["patientId"] == patient_id
        assert n1["type"] == "observation"
        assert n1["author"] == "Nurse Amaka"

        # 3. Add second note later
        t2 = datetime(2026, 8, 10, 14, 0, 0, tzinfo=timezone.utc)
        note2_res = await client.post(
            f"/api/v1/patients/{patient_id}/notes",
            json={
                "content": "Pain managed with prescribed analgesics. Ambulated with assistance.",
                "type": "treatment",
                "author": "Dr. Okafor",
                "timestamp": t2.isoformat(),
            },
        )
        assert note2_res.status_code == 201
        n2 = note2_res.json()
        assert n2["type"] == "treatment"

        # 4. List notes -> Must be in DESCENDING order (n2 first, then n1)
        list_res = await client.get(f"/api/v1/patients/{patient_id}/notes")
        assert list_res.status_code == 200
        notes_list = list_res.json()
        assert len(notes_list) == 2
        assert notes_list[0]["id"] == n2["id"]
        assert notes_list[1]["id"] == n1["id"]

        # 5. Delete note 1
        del_res = await client.delete(f"/api/v1/notes/{n1['id']}")
        assert del_res.status_code == 204

        # 6. Verify list now only contains note 2
        list_after_res = await client.get(f"/api/v1/patients/{patient_id}/notes")
        assert list_after_res.status_code == 200
        remaining_notes = list_after_res.json()
        assert len(remaining_notes) == 1
        assert remaining_notes[0]["id"] == n2["id"]


@pytest.mark.asyncio
async def test_notes_error_cases(test_db_session):
    """Test 404 for non-existent patient and note deletion."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Non-existent patient get notes
        res = await client.get("/api/v1/patients/PT-NONEXISTENT/notes")
        assert res.status_code == 404

        # Non-existent patient post note
        post_res = await client.post(
            "/api/v1/patients/PT-NONEXISTENT/notes",
            json={"content": "Some clinical note"},
        )
        assert post_res.status_code == 404

        # Delete non-existent note
        del_res = await client.delete("/api/v1/notes/NOTE-DOESNOTEXIST")
        assert del_res.status_code == 404

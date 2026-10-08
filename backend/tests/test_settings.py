"""Milestone 10 Settings & Facility Profile API Integration Tests."""

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
async def test_clinical_thresholds_endpoints(test_db_session):
    """Test retrieving and updating baseline clinical thresholds."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Get default thresholds
        get_res = await client.get("/api/v1/settings/thresholds")
        assert get_res.status_code == 200
        thresholds = get_res.json()
        assert thresholds["heartRate"]["min"] == 60.0
        assert thresholds["heartRate"]["max"] == 100.0
        assert thresholds["oxygen"]["min"] == 95.0
        assert thresholds["temperature"]["min"] == 36.5

        # 2. Update thresholds
        update_payload = {
            "heartRate": {"min": 55.0, "max": 105.0},
            "bloodPressure": {"min": 60.0, "max": 135.0, "systolicMin": 90.0, "systolicMax": 135.0},
            "oxygen": {"min": 94.0, "max": 100.0},
            "temperature": {"min": 36.0, "max": 37.8},
        }
        put_res = await client.put("/api/v1/settings/thresholds", json=update_payload)
        assert put_res.status_code == 200
        updated = put_res.json()
        assert updated["heartRate"]["min"] == 55.0
        assert updated["heartRate"]["max"] == 105.0
        assert updated["oxygen"]["min"] == 94.0


@pytest.mark.asyncio
async def test_facility_profile_endpoints(test_db_session):
    """Test retrieving and updating clinical facility profile."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Get default profile
        get_res = await client.get("/api/v1/settings/profile")
        assert get_res.status_code == 200
        profile = get_res.json()
        assert profile["facilityName"] == "CareArc Lagos Central Hospital"
        assert profile["unitName"] == "Intensive Care & Monitoring Unit 4B"
        assert profile["facilityId"] == "FAC-4B-LAGOS"
        assert "Critical Care" in profile["specialties"]

        # 2. Update profile
        profile["facilityName"] = "CareArc Victoria Hospital"
        profile["bedCapacity"] = "32 Beds (28 Active)"
        profile["specialties"] = ["Critical Care", "Neurology"]

        put_res = await client.put("/api/v1/settings/profile", json=profile)
        assert put_res.status_code == 200
        updated_profile = put_res.json()
        assert updated_profile["facilityName"] == "CareArc Victoria Hospital"
        assert updated_profile["bedCapacity"] == "32 Beds (28 Active)"
        assert len(updated_profile["specialties"]) == 2

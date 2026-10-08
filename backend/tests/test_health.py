"""Milestone 1 Foundation Verification Test."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.ids import generate_patient_id, generate_vital_id, generate_note_id, generate_appointment_id


@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify that the health check endpoint returns 200 and healthy status."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "CareArc" in data["service"]


@pytest.mark.asyncio
async def test_root_endpoint():
    """Verify root endpoint returns welcome message and docs URL."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["docsUrl"] == "/docs"


def test_id_generator_prefixes():
    """Verify ID generator produces valid clinical prefixes and lengths."""
    patient_id = generate_patient_id()
    vital_id = generate_vital_id()
    note_id = generate_note_id()
    appointment_id = generate_appointment_id()

    assert patient_id.startswith("PT-")
    assert vital_id.startswith("VIT-")
    assert note_id.startswith("NOTE-")
    assert appointment_id.startswith("APT-")

    # Verify suffix length (8 characters after prefix)
    assert len(patient_id.split("-")[1]) == 8
    assert len(vital_id.split("-")[1]) == 8
    assert len(note_id.split("-")[1]) == 8
    assert len(appointment_id.split("-")[1]) == 8

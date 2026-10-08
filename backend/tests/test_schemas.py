"""Milestone 4 Pydantic v2 Schema Tests."""

from datetime import date, datetime, timezone
import pytest
from pydantic import ValidationError

from app.schemas import (
    PatientCreate,
    PatientResponse,
    VitalCreate,
    VitalResponse,
    NoteCreate,
    NoteResponse,
    AppointmentCreate,
    AppointmentResponse,
    ThresholdsSchema,
)


def test_vital_schema_camelcase_and_nested_blood_pressure():
    """Verify that VitalResponse outputs camelCase and nested bloodPressure."""
    vital_data = {
        "id": "VIT-12345678",
        "patient_id": "PT-12345678",
        "timestamp": datetime(2026, 9, 7, 10, 0, tzinfo=timezone.utc),
        "heart_rate": 78,
        "blood_pressure": {"systolic": 120, "diastolic": 80},
        "oxygen": 98.0,
        "temperature": 36.6,
        "respiratory_rate": 18,
        "recorded_by": "Nurse Fatima",
    }
    vital = VitalResponse(**vital_data)
    dumped = vital.model_dump(by_alias=True)

    # Check camelCase keys matching frontend expectations
    assert "patientId" in dumped
    assert "heartRate" in dumped
    assert "bloodPressure" in dumped
    assert dumped["bloodPressure"] == {"systolic": 120, "diastolic": 80}
    assert dumped["patientId"] == "PT-12345678"
    assert dumped["heartRate"] == 78


def test_vital_create_from_flat_form_fields():
    """Verify VitalCreate accepts flat systolic and diastolic form fields."""
    flat_form = {
        "heartRate": 85,
        "systolic": "130",
        "diastolic": "85",
        "oxygen": "96.5",
        "temperature": "37.1",
        "respiratoryRate": "19",
    }
    vital = VitalCreate(**flat_form)
    assert vital.heart_rate == 85
    assert vital.blood_pressure.systolic == 130
    assert vital.blood_pressure.diastolic == 85
    assert vital.oxygen == 96.5
    assert vital.temperature == 37.1
    assert vital.respiratory_rate == 19


def test_patient_create_string_coercion_and_initial_vitals():
    """Verify PatientCreate coerces string inputs and accepts atomic initialVitals."""
    payload = {
        "name": "Bello Kasim",
        "age": "38",  # String from HTML input
        "gender": "Male",
        "room": "Room 5D",
        "condition": "Observation — Chest Pain",
        "admitted": "2026-07-28",
        "weight": "185lbs",
        "phone": "+234 807 890 1234",
        "email": "bello@example.com",
        "initialVitals": {
            "heartRate": "88",
            "systolic": "130",
            "diastolic": "85",
            "oxygen": "96.0",
            "temperature": "37.2",
        },
    }
    patient = PatientCreate(**payload)
    assert patient.name == "Bello Kasim"
    assert patient.age == 38  # Coerced to integer
    assert patient.admitted == date(2026, 7, 28)
    assert patient.initial_vitals is not None
    assert patient.initial_vitals.heart_rate == 88
    assert patient.initial_vitals.blood_pressure.systolic == 130


def test_patient_response_camelcase_serialization():
    """Verify PatientResponse serializes to exact React contract."""
    data = {
        "id": "PT-001",
        "name": "Amina Yusuf",
        "age": 54,
        "gender": "Female",
        "room": "Room 4B",
        "condition": "Respiratory symptoms, Fever",
        "admitted": date(2026, 7, 20),
        "weight": "160lbs",
        "contact": {
            "phone": "+234 801 234 5678",
            "email": "amina@example.com",
            "emergency_contact": "Fatima Yusuf",
        },
        "status": "Review",
    }
    patient = PatientResponse(**data)
    dumped = patient.model_dump(by_alias=True)

    assert dumped["id"] == "PT-001"
    assert dumped["contact"]["emergencyContact"] == "Fatima Yusuf"
    assert dumped["status"] == "Review"


def test_appointment_create_and_response():
    """Verify Appointment schema aliases and patient name projection."""
    create_payload = {
        "patientId": "PT-001",
        "type": "Consultation",
        "date": "2026-09-08",
        "time": "14:00",
        "duration": "45",
    }
    apt_create = AppointmentCreate(**create_payload)
    assert apt_create.patient_id == "PT-001"
    assert apt_create.duration == 45

    resp_data = {
        "id": "APT-001",
        "patient_id": "PT-001",
        "name": "Amina Yusuf",
        "type": "Consultation",
        "date": date(2026, 9, 8),
        "time": "14:00",
        "duration": 45,
        "is_completed": False,
    }
    apt_resp = AppointmentResponse(**resp_data)
    dumped = apt_resp.model_dump(by_alias=True)

    assert dumped["patientId"] == "PT-001"
    assert dumped["name"] == "Amina Yusuf"
    assert dumped["isCompleted"] is False


def test_schema_validation_rejections():
    """Verify invalid clinical data is rejected with ValidationError."""
    # Oxygen > 100%
    with pytest.raises(ValidationError):
        VitalCreate(
            heartRate=80,
            systolic=120,
            diastolic=80,
            oxygen=105.0,  # Invalid
            temperature=37.0,
        )

    # Empty patient name
    with pytest.raises(ValidationError):
        PatientCreate(
            name="",  # Invalid min_length
            age=30,
            gender="Male",
            room="Room 1",
            condition="Stable",
            admitted=date.today(),
        )

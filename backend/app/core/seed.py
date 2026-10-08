"""Database Seeder Module.

Populates PostgreSQL with the complete CareArc clinical audit dataset (PT-001 to PT-005),
longitudinal time-series vitals (worsening, fluctuating, improving, stable),
clinical notes, scheduled appointments, and facility configurations.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.models.appointment import Appointment
from app.models.note import ClinicalNote
from app.models.patient import Patient
from app.models.setting import ClinicalThreshold, FacilityProfile
from app.models.vital import Vital

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

# ═══════════════════════════════════════════════════════════════
# 1. Patients Seed Dataset
# ═══════════════════════════════════════════════════════════════
PATIENTS_DATA = [
    {
        "id": "PT-001",
        "name": "Amina Yusuf",
        "age": 54,
        "gender": "Female",
        "room": "Room 4B",
        "condition": "Respiratory symptoms, Fever",
        "admitted": date(2026, 7, 20),
        "weight": "160lbs",
        "phone": "+234 801 234 5678",
        "email": "amina.yusuf@email.com",
        "emergency_contact": "Fatima Yusuf — +234 802 345 6789",
    },
    {
        "id": "PT-002",
        "name": "John Okafor",
        "age": 62,
        "gender": "Male",
        "room": "Room 7A",
        "condition": "Cardiac Arrhythmia",
        "admitted": date(2026, 7, 18),
        "weight": "185lbs",
        "phone": "+234 803 456 7890",
        "email": "john.okafor@email.com",
        "emergency_contact": "Grace Okafor — +234 804 567 8901",
    },
    {
        "id": "PT-003",
        "name": "Mary Adebayo",
        "age": 47,
        "gender": "Female",
        "room": "Room 2C",
        "condition": "Post-Surgery Recovery",
        "admitted": date(2026, 7, 22),
        "weight": "145lbs",
        "phone": "+234 805 678 9012",
        "email": "mary.adebayo@email.com",
        "emergency_contact": "Tunde Adebayo — +234 806 789 0123",
    },
    {
        "id": "PT-004",
        "name": "Bello Kasim",
        "age": 38,
        "gender": "Male",
        "room": "Room 5D",
        "condition": "Observation — Chest Pain",
        "admitted": date(2026, 7, 28),
        "weight": "175lbs",
        "phone": "+234 807 890 1234",
        "email": "bello.kasim@email.com",
        "emergency_contact": "Halima Kasim — +234 808 901 2345",
    },
    {
        "id": "PT-005",
        "name": "Chidinma Eze",
        "age": 71,
        "gender": "Female",
        "room": "Room 1A",
        "condition": "Hypertension, Diabetes Management",
        "admitted": date(2026, 7, 15),
        "weight": "155lbs",
        "phone": "+234 809 012 3456",
        "email": "chidinma.eze@email.com",
        "emergency_contact": "Emeka Eze — +234 810 123 4567",
    },
]

# ═══════════════════════════════════════════════════════════════
# 2. Vitals Seed Dataset (31 time-series readings)
# ═══════════════════════════════════════════════════════════════
VITALS_DATA = [
    # PT-001 (Worsening Trajectory)
    {"id": "VIT-001", "patient_id": "PT-001", "timestamp": "2026-07-26T08:00:00Z", "heart_rate": 75, "systolic_bp": 120, "diastolic_bp": 80, "oxygen": Decimal("97.0"), "temperature": Decimal("37.4"), "respiratory_rate": 18, "recorded_by": "Nurse Fatima"},
    {"id": "VIT-002", "patient_id": "PT-001", "timestamp": "2026-07-26T14:00:00Z", "heart_rate": 80, "systolic_bp": 122, "diastolic_bp": 82, "oxygen": Decimal("96.0"), "temperature": Decimal("37.6"), "respiratory_rate": 19, "recorded_by": "Nurse Fatima"},
    {"id": "VIT-003", "patient_id": "PT-001", "timestamp": "2026-07-26T20:00:00Z", "heart_rate": 85, "systolic_bp": 125, "diastolic_bp": 84, "oxygen": Decimal("95.0"), "temperature": Decimal("37.8"), "respiratory_rate": 20, "recorded_by": "Nurse James"},
    {"id": "VIT-004", "patient_id": "PT-001", "timestamp": "2026-07-27T08:00:00Z", "heart_rate": 88, "systolic_bp": 128, "diastolic_bp": 85, "oxygen": Decimal("94.0"), "temperature": Decimal("38.0"), "respiratory_rate": 21, "recorded_by": "Nurse Fatima"},
    {"id": "VIT-005", "patient_id": "PT-001", "timestamp": "2026-07-27T14:00:00Z", "heart_rate": 92, "systolic_bp": 130, "diastolic_bp": 86, "oxygen": Decimal("93.0"), "temperature": Decimal("38.2"), "respiratory_rate": 22, "recorded_by": "Dr. Sarah Chen"},
    {"id": "VIT-006", "patient_id": "PT-001", "timestamp": "2026-07-27T20:00:00Z", "heart_rate": 98, "systolic_bp": 132, "diastolic_bp": 88, "oxygen": Decimal("92.0"), "temperature": Decimal("38.4"), "respiratory_rate": 23, "recorded_by": "Nurse James"},
    {"id": "VIT-007", "patient_id": "PT-001", "timestamp": "2026-07-28T08:00:00Z", "heart_rate": 102, "systolic_bp": 135, "diastolic_bp": 90, "oxygen": Decimal("91.0"), "temperature": Decimal("38.5"), "respiratory_rate": 24, "recorded_by": "Nurse Fatima"},
    {"id": "VIT-008", "patient_id": "PT-001", "timestamp": "2026-07-28T14:00:00Z", "heart_rate": 125, "systolic_bp": 138, "diastolic_bp": 92, "oxygen": Decimal("90.0"), "temperature": Decimal("38.7"), "respiratory_rate": 25, "recorded_by": "Dr. Sarah Chen"},

    # PT-002 (Fluctuating Arrhythmia)
    {"id": "VIT-009", "patient_id": "PT-002", "timestamp": "2026-07-26T08:00:00Z", "heart_rate": 72, "systolic_bp": 130, "diastolic_bp": 85, "oxygen": Decimal("96.0"), "temperature": Decimal("37.0"), "respiratory_rate": 17, "recorded_by": "Nurse Fatima"},
    {"id": "VIT-010", "patient_id": "PT-002", "timestamp": "2026-07-26T14:00:00Z", "heart_rate": 110, "systolic_bp": 145, "diastolic_bp": 92, "oxygen": Decimal("95.0"), "temperature": Decimal("37.1"), "respiratory_rate": 18, "recorded_by": "Dr. Sarah Chen"},
    {"id": "VIT-011", "patient_id": "PT-002", "timestamp": "2026-07-26T20:00:00Z", "heart_rate": 68, "systolic_bp": 125, "diastolic_bp": 80, "oxygen": Decimal("97.0"), "temperature": Decimal("37.0"), "respiratory_rate": 16, "recorded_by": "Nurse James"},
    {"id": "VIT-012", "patient_id": "PT-002", "timestamp": "2026-07-27T08:00:00Z", "heart_rate": 85, "systolic_bp": 135, "diastolic_bp": 88, "oxygen": Decimal("96.0"), "temperature": Decimal("37.1"), "respiratory_rate": 17, "recorded_by": "Nurse Fatima"},
    {"id": "VIT-013", "patient_id": "PT-002", "timestamp": "2026-07-27T14:00:00Z", "heart_rate": 120, "systolic_bp": 150, "diastolic_bp": 95, "oxygen": Decimal("94.0"), "temperature": Decimal("37.2"), "respiratory_rate": 19, "recorded_by": "Dr. Sarah Chen"},
    {"id": "VIT-014", "patient_id": "PT-002", "timestamp": "2026-07-27T20:00:00Z", "heart_rate": 75, "systolic_bp": 128, "diastolic_bp": 82, "oxygen": Decimal("96.0"), "temperature": Decimal("37.0"), "respiratory_rate": 17, "recorded_by": "Nurse James"},
    {"id": "VIT-015", "patient_id": "PT-002", "timestamp": "2026-07-28T08:00:00Z", "heart_rate": 90, "systolic_bp": 138, "diastolic_bp": 90, "oxygen": Decimal("95.0"), "temperature": Decimal("37.1"), "respiratory_rate": 18, "recorded_by": "Nurse Fatima"},

    # PT-003 (Improving Post-Surgery)
    {"id": "VIT-016", "patient_id": "PT-003", "timestamp": "2026-07-22T08:00:00Z", "heart_rate": 105, "systolic_bp": 140, "diastolic_bp": 90, "oxygen": Decimal("93.0"), "temperature": Decimal("38.3"), "respiratory_rate": 24, "recorded_by": "Nurse James"},
    {"id": "VIT-017", "patient_id": "PT-003", "timestamp": "2026-07-22T20:00:00Z", "heart_rate": 100, "systolic_bp": 138, "diastolic_bp": 88, "oxygen": Decimal("94.0"), "temperature": Decimal("38.1"), "respiratory_rate": 23, "recorded_by": "Nurse Fatima"},
    {"id": "VIT-018", "patient_id": "PT-003", "timestamp": "2026-07-23T08:00:00Z", "heart_rate": 95, "systolic_bp": 135, "diastolic_bp": 86, "oxygen": Decimal("95.0"), "temperature": Decimal("37.8"), "respiratory_rate": 22, "recorded_by": "Nurse James"},
    {"id": "VIT-019", "patient_id": "PT-003", "timestamp": "2026-07-24T08:00:00Z", "heart_rate": 88, "systolic_bp": 130, "diastolic_bp": 84, "oxygen": Decimal("96.0"), "temperature": Decimal("37.5"), "respiratory_rate": 20, "recorded_by": "Nurse Fatima"},
    {"id": "VIT-020", "patient_id": "PT-003", "timestamp": "2026-07-25T08:00:00Z", "heart_rate": 82, "systolic_bp": 125, "diastolic_bp": 80, "oxygen": Decimal("97.0"), "temperature": Decimal("37.2"), "respiratory_rate": 18, "recorded_by": "Dr. Sarah Chen"},
    {"id": "VIT-021", "patient_id": "PT-003", "timestamp": "2026-07-26T08:00:00Z", "heart_rate": 78, "systolic_bp": 120, "diastolic_bp": 78, "oxygen": Decimal("97.0"), "temperature": Decimal("37.0"), "respiratory_rate": 17, "recorded_by": "Nurse Fatima"},
    {"id": "VIT-022", "patient_id": "PT-003", "timestamp": "2026-07-28T08:00:00Z", "heart_rate": 76, "systolic_bp": 118, "diastolic_bp": 76, "oxygen": Decimal("98.0"), "temperature": Decimal("36.8"), "respiratory_rate": 16, "recorded_by": "Nurse James"},

    # PT-004 (New Patient Observation)
    {"id": "VIT-023", "patient_id": "PT-004", "timestamp": "2026-07-28T14:00:00Z", "heart_rate": 88, "systolic_bp": 130, "diastolic_bp": 85, "oxygen": Decimal("96.0"), "temperature": Decimal("37.2"), "respiratory_rate": 18, "recorded_by": "Dr. Sarah Chen"},
    {"id": "VIT-024", "patient_id": "PT-004", "timestamp": "2026-07-28T20:00:00Z", "heart_rate": 85, "systolic_bp": 128, "diastolic_bp": 84, "oxygen": Decimal("96.0"), "temperature": Decimal("37.1"), "respiratory_rate": 18, "recorded_by": "Nurse James"},
    {"id": "VIT-025", "patient_id": "PT-004", "timestamp": "2026-07-29T06:00:00Z", "heart_rate": 82, "systolic_bp": 126, "diastolic_bp": 82, "oxygen": Decimal("97.0"), "temperature": Decimal("37.0"), "respiratory_rate": 17, "recorded_by": "Nurse Fatima"},

    # PT-005 (Stable Chronic Hypertension)
    {"id": "VIT-026", "patient_id": "PT-005", "timestamp": "2026-07-20T08:00:00Z", "heart_rate": 78, "systolic_bp": 148, "diastolic_bp": 92, "oxygen": Decimal("96.0"), "temperature": Decimal("36.9"), "respiratory_rate": 18, "recorded_by": "Nurse Fatima"},
    {"id": "VIT-027", "patient_id": "PT-005", "timestamp": "2026-07-21T08:00:00Z", "heart_rate": 76, "systolic_bp": 145, "diastolic_bp": 90, "oxygen": Decimal("96.0"), "temperature": Decimal("37.0"), "respiratory_rate": 17, "recorded_by": "Nurse James"},
    {"id": "VIT-028", "patient_id": "PT-005", "timestamp": "2026-07-22T08:00:00Z", "heart_rate": 80, "systolic_bp": 150, "diastolic_bp": 94, "oxygen": Decimal("95.0"), "temperature": Decimal("37.0"), "respiratory_rate": 18, "recorded_by": "Nurse Fatima"},
    {"id": "VIT-029", "patient_id": "PT-005", "timestamp": "2026-07-24T08:00:00Z", "heart_rate": 77, "systolic_bp": 146, "diastolic_bp": 91, "oxygen": Decimal("96.0"), "temperature": Decimal("36.9"), "respiratory_rate": 17, "recorded_by": "Dr. Sarah Chen"},
    {"id": "VIT-030", "patient_id": "PT-005", "timestamp": "2026-07-26T08:00:00Z", "heart_rate": 79, "systolic_bp": 148, "diastolic_bp": 92, "oxygen": Decimal("96.0"), "temperature": Decimal("37.0"), "respiratory_rate": 18, "recorded_by": "Nurse James"},
    {"id": "VIT-031", "patient_id": "PT-005", "timestamp": "2026-07-28T08:00:00Z", "heart_rate": 76, "systolic_bp": 145, "diastolic_bp": 90, "oxygen": Decimal("96.0"), "temperature": Decimal("37.0"), "respiratory_rate": 18, "recorded_by": "Nurse Fatima"},
]

# ═══════════════════════════════════════════════════════════════
# 3. Clinical Notes Seed Dataset (17 notes)
# ═══════════════════════════════════════════════════════════════
NOTES_DATA = [
    # PT-001
    {"id": "NOTE-001", "patient_id": "PT-001", "timestamp": "2026-07-26T08:30:00Z", "type": "observation", "author": "Dr. Sarah Chen", "content": "Patient admitted with dry cough and low-grade fever. Vitals within normal limits on admission. Started on oral antibiotics."},
    {"id": "NOTE-002", "patient_id": "PT-001", "timestamp": "2026-07-27T09:00:00Z", "type": "review", "author": "Dr. Sarah Chen", "content": "Fever persisting despite antibiotics. Patient reports worsening cough, now productive. Heart rate trending upward. Ordered chest X-ray and blood cultures."},
    {"id": "NOTE-003", "patient_id": "PT-001", "timestamp": "2026-07-27T15:00:00Z", "type": "treatment", "author": "Nurse Fatima", "content": "Switched from oral to IV antibiotics. Supplemental oxygen started at 2L via nasal cannula."},
    {"id": "NOTE-004", "patient_id": "PT-001", "timestamp": "2026-07-28T08:30:00Z", "type": "observation", "author": "Nurse Fatima", "content": "Patient reports increasing shortness of breath overnight. SpO₂ declining despite supplemental oxygen. Escalated to senior registrar for review."},

    # PT-002
    {"id": "NOTE-005", "patient_id": "PT-002", "timestamp": "2026-07-26T09:00:00Z", "type": "observation", "author": "Dr. Sarah Chen", "content": "Patient under observation for recurrent palpitations. Baseline ECG shows irregular rhythm. Cardiology consult requested."},
    {"id": "NOTE-006", "patient_id": "PT-002", "timestamp": "2026-07-26T14:30:00Z", "type": "observation", "author": "Nurse Fatima", "content": "Episode of rapid heart rate recorded at 110 bpm during routine check. Patient reports feeling lightheaded. Resolved spontaneously after 20 minutes."},
    {"id": "NOTE-007", "patient_id": "PT-002", "timestamp": "2026-07-27T15:00:00Z", "type": "treatment", "author": "Dr. Sarah Chen", "content": "Another tachycardic episode — HR peaked at 120 bpm. Cardiology reviewed. Started on beta-blocker. Monitor response over 24 hours."},

    # PT-003
    {"id": "NOTE-008", "patient_id": "PT-003", "timestamp": "2026-07-22T10:00:00Z", "type": "observation", "author": "Nurse James", "content": "Post-operative day 0. Patient returned from surgery (appendectomy). Vitals elevated as expected post-anaesthesia. Pain managed with IV paracetamol."},
    {"id": "NOTE-009", "patient_id": "PT-003", "timestamp": "2026-07-23T09:00:00Z", "type": "review", "author": "Dr. Sarah Chen", "content": "Post-op day 1. Patient mobilising with assistance. Wound site clean, no signs of infection. Vitals improving. Transitioned to oral pain relief."},
    {"id": "NOTE-010", "patient_id": "PT-003", "timestamp": "2026-07-25T08:30:00Z", "type": "review", "author": "Dr. Sarah Chen", "content": "Post-op day 3. Steady improvement. Patient eating well, mobilising independently. Vitals approaching baseline. Discharge planning initiated."},
    {"id": "NOTE-011", "patient_id": "PT-003", "timestamp": "2026-07-28T09:00:00Z", "type": "review", "author": "Dr. Sarah Chen", "content": "Post-op day 6. All vitals within normal range. Wound healing well. Cleared for discharge tomorrow pending final review."},

    # PT-004
    {"id": "NOTE-012", "patient_id": "PT-004", "timestamp": "2026-07-28T14:30:00Z", "type": "observation", "author": "Dr. Sarah Chen", "content": "Patient presented to A&E with acute chest pain radiating to left arm. Onset 2 hours ago during physical activity. No prior cardiac history. ECG and troponin ordered. Admitted for observation."},
    {"id": "NOTE-013", "patient_id": "PT-004", "timestamp": "2026-07-28T21:00:00Z", "type": "review", "author": "Nurse James", "content": "Initial troponin result negative. ECG shows no acute ST changes. Pain subsided after rest. Continue monitoring. Repeat troponin at 6 hours."},

    # PT-005
    {"id": "NOTE-014", "patient_id": "PT-005", "timestamp": "2026-07-15T09:00:00Z", "type": "observation", "author": "Dr. Sarah Chen", "content": "Patient admitted for hypertensive crisis. BP 180/110 on arrival. IV antihypertensives administered. Blood glucose elevated at 14.2 mmol/L — diabetes medication adjusted."},
    {"id": "NOTE-015", "patient_id": "PT-005", "timestamp": "2026-07-18T08:00:00Z", "type": "review", "author": "Dr. Sarah Chen", "content": "BP stabilising around 148/92. Still above target but significant improvement from admission. Oral antihypertensives adjusted. Dietitian referral made."},
    {"id": "NOTE-016", "patient_id": "PT-005", "timestamp": "2026-07-24T08:00:00Z", "type": "review", "author": "Dr. Sarah Chen", "content": "BP remains consistently around 145-150/90-94. Medication compliance confirmed. Blood glucose well-controlled on current regimen. Continue current management, review in 3 days."},
    {"id": "NOTE-017", "patient_id": "PT-005", "timestamp": "2026-07-28T08:30:00Z", "type": "handover", "author": "Nurse Fatima", "content": "Stable. BP 145/90, glucose 7.8 mmol/L. Patient comfortable. Discussed discharge plan — pending home BP monitoring arrangement."},
]

# ═══════════════════════════════════════════════════════════════
# 4. Appointments Seed Dataset (10 bookings)
# ═══════════════════════════════════════════════════════════════
def get_appointment_seed_data() -> list[dict]:
    today = date.today()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)

    return [
        {"id": "APT-001", "patient_id": "PT-001", "appointment_type": "Follow-up", "appointment_date": today, "appointment_time": "09:00", "duration_minutes": 30, "is_completed": True},
        {"id": "APT-002", "patient_id": "PT-001", "appointment_type": "Consultation", "appointment_date": tomorrow, "appointment_time": "10:00", "duration_minutes": 45, "is_completed": False},
        {"id": "APT-003", "patient_id": "PT-002", "appointment_type": "Consultation", "appointment_date": today, "appointment_time": "10:30", "duration_minutes": 45, "is_completed": True},
        {"id": "APT-004", "patient_id": "PT-002", "appointment_type": "Check-up", "appointment_date": tomorrow, "appointment_time": "14:00", "duration_minutes": 30, "is_completed": False},
        {"id": "APT-005", "patient_id": "PT-003", "appointment_type": "Check-up", "appointment_date": today, "appointment_time": "12:00", "duration_minutes": 30, "is_completed": True},
        {"id": "APT-006", "patient_id": "PT-003", "appointment_type": "Follow-up", "appointment_date": next_week, "appointment_time": "11:00", "duration_minutes": 30, "is_completed": False},
        {"id": "APT-007", "patient_id": "PT-004", "appointment_type": "Consultation", "appointment_date": today, "appointment_time": "14:00", "duration_minutes": 45, "is_completed": False},
        {"id": "APT-008", "patient_id": "PT-004", "appointment_type": "Follow-up", "appointment_date": tomorrow, "appointment_time": "15:30", "duration_minutes": 30, "is_completed": False},
        {"id": "APT-009", "patient_id": "PT-005", "appointment_type": "Follow-up", "appointment_date": today, "appointment_time": "15:30", "duration_minutes": 30, "is_completed": False},
        {"id": "APT-010", "patient_id": "PT-005", "appointment_type": "Check-up", "appointment_date": tomorrow, "appointment_time": "16:30", "duration_minutes": 30, "is_completed": False},
    ]


async def seed_database(db: AsyncSession) -> None:
    """Execute complete database seeding with clinical audit dataset."""
    logger.info("Checking existing seed data in database...")

    # 1. Seed Patients
    existing_patients = await db.execute(select(Patient))
    if not existing_patients.scalars().first():
        logger.info("Seeding patients (PT-001 through PT-005)...")
        for p in PATIENTS_DATA:
            db.add(Patient(**p))
        await db.flush()

    # 2. Seed Vitals
    existing_vitals = await db.execute(select(Vital))
    if not existing_vitals.scalars().first():
        logger.info("Seeding 31 time-series vitals...")
        for v in VITALS_DATA:
            db.add(
                Vital(
                    id=v["id"],
                    patient_id=v["patient_id"],
                    timestamp=datetime.fromisoformat(v["timestamp"].replace("Z", "+00:00")),
                    heart_rate=v["heart_rate"],
                    systolic_bp=v["systolic_bp"],
                    diastolic_bp=v["diastolic_bp"],
                    oxygen=v["oxygen"],
                    temperature=v["temperature"],
                    respiratory_rate=v["respiratory_rate"],
                    recorded_by=v["recorded_by"],
                )
            )
        await db.flush()

    # 3. Seed Notes
    existing_notes = await db.execute(select(ClinicalNote))
    if not existing_notes.scalars().first():
        logger.info("Seeding 17 clinical notes...")
        for n in NOTES_DATA:
            db.add(
                ClinicalNote(
                    id=n["id"],
                    patient_id=n["patient_id"],
                    timestamp=datetime.fromisoformat(n["timestamp"].replace("Z", "+00:00")),
                    type=n["type"],
                    author=n["author"],
                    content=n["content"],
                )
            )
        await db.flush()

    # 4. Seed Appointments
    existing_appointments = await db.execute(select(Appointment))
    if not existing_appointments.scalars().first():
        logger.info("Seeding 10 clinical appointments...")
        for a in get_appointment_seed_data():
            db.add(Appointment(**a))
        await db.flush()

    # 5. Seed Thresholds
    existing_thresholds = await db.execute(select(ClinicalThreshold))
    if not existing_thresholds.scalars().first():
        logger.info("Seeding clinical baseline thresholds...")
        defaults = [
            ClinicalThreshold(vital_name="heart_rate", min_value=Decimal("60.0"), max_value=Decimal("100.0")),
            ClinicalThreshold(vital_name="blood_pressure", min_value=Decimal("60.0"), max_value=Decimal("140.0"), systolic_min=Decimal("90.0"), systolic_max=Decimal("140.0")),
            ClinicalThreshold(vital_name="oxygen", min_value=Decimal("95.0"), max_value=Decimal("100.0")),
            ClinicalThreshold(vital_name="temperature", min_value=Decimal("36.5"), max_value=Decimal("37.5")),
        ]
        db.add_all(defaults)
        await db.flush()

    # 6. Seed Facility Profile
    existing_profile = await db.execute(select(FacilityProfile))
    if not existing_profile.scalars().first():
        logger.info("Seeding facility profile...")
        profile = FacilityProfile(
            id="DEFAULT_FACILITY",
            facility_name="CareArc Lagos Central Hospital",
            unit_name="Intensive Care & Monitoring Unit 4B",
            facility_code="FAC-4B-LAGOS",
            emergency_phone="+234 800 227 3272",
            primary_email="icu4b@carearc.health",
            address="14 Clinical Way, Victoria Island, Lagos",
            bed_capacity="24 Beds (18 Active)",
            active_protocol="Acute Care Trajectory Protocol v3.2",
            vitals_interval="4 hours",
            delta_engine_window="12 hours",
            ai_model="GPT-4o-mini Clinical Engine",
            auto_handover=True,
            critical_alert_escalation=True,
            specialties=["Critical Care", "Internal Medicine", "Cardiology", "Pulmonology"],
        )
        db.add(profile)
        await db.flush()

    await db.commit()
    logger.info("CareArc database seeding completed successfully.")


async def main():
    """CLI Entry point for database seeding."""
    async with AsyncSessionLocal() as session:
        await seed_database(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

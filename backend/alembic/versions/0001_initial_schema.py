"""Initial CareArc Database Schema.

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-09-07 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Patients Table
    op.create_table(
        "patients",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(length=32), nullable=False),
        sa.Column("room", sa.String(length=64), nullable=False),
        sa.Column("condition", sa.String(length=255), nullable=False),
        sa.Column("admitted", sa.Date(), nullable=False),
        sa.Column("weight", sa.String(length=64), nullable=True, server_default="N/A"),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("emergency_contact", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_patients_id", "patients", ["id"], unique=False)
    op.create_index("ix_patients_name", "patients", ["name"], unique=False)
    op.create_index("ix_patients_admitted", "patients", ["admitted"], unique=False)

    # 2. Create Vitals Table (Time-Series)
    op.create_table(
        "vitals",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("patient_id", sa.String(length=32), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("heart_rate", sa.Integer(), nullable=False),
        sa.Column("systolic_bp", sa.Integer(), nullable=False),
        sa.Column("diastolic_bp", sa.Integer(), nullable=False),
        sa.Column("oxygen", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("temperature", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("respiratory_rate", sa.Integer(), nullable=True),
        sa.Column("recorded_by", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vitals_id", "vitals", ["id"], unique=False)
    op.create_index("ix_vitals_patient_id", "vitals", ["patient_id"], unique=False)
    op.create_index("ix_vitals_timestamp", "vitals", ["timestamp"], unique=False)
    op.create_index("idx_vitals_patient_timestamp_desc", "vitals", ["patient_id", sa.text("timestamp DESC")])
    op.create_index("idx_vitals_patient_timestamp_asc", "vitals", ["patient_id", sa.text("timestamp ASC")])

    # 3. Create Clinical Notes Table
    op.create_table(
        "clinical_notes",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("patient_id", sa.String(length=32), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False, server_default="observation"),
        sa.Column("author", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clinical_notes_id", "clinical_notes", ["id"], unique=False)
    op.create_index("ix_clinical_notes_patient_id", "clinical_notes", ["patient_id"], unique=False)
    op.create_index("ix_clinical_notes_timestamp", "clinical_notes", ["timestamp"], unique=False)
    op.create_index("idx_notes_patient_timestamp_desc", "clinical_notes", ["patient_id", sa.text("timestamp DESC")])

    # 4. Create Appointments Table
    op.create_table(
        "appointments",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("patient_id", sa.String(length=32), nullable=False),
        sa.Column("appointment_type", sa.String(length=128), nullable=False),
        sa.Column("appointment_date", sa.Date(), nullable=False),
        sa.Column("appointment_time", sa.String(length=16), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_appointments_id", "appointments", ["id"], unique=False)
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"], unique=False)
    op.create_index("ix_appointments_appointment_date", "appointments", ["appointment_date"], unique=False)
    op.create_index("idx_appointments_date_completed", "appointments", ["appointment_date", "is_completed"])
    op.create_index("idx_appointments_patient_date", "appointments", ["patient_id", "appointment_date"])

    # 5. Create Clinical Thresholds Table
    op.create_table(
        "clinical_thresholds",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vital_name", sa.String(length=64), nullable=False),
        sa.Column("min_value", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("max_value", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("systolic_min", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("systolic_max", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vital_name"),
    )
    op.create_index("ix_clinical_thresholds_vital_name", "clinical_thresholds", ["vital_name"], unique=True)

    # 6. Create Facility Profiles Table
    op.create_table(
        "facility_profiles",
        sa.Column("id", sa.String(length=64), nullable=False, server_default="DEFAULT_FACILITY"),
        sa.Column("facility_name", sa.String(length=255), nullable=False),
        sa.Column("unit_name", sa.String(length=255), nullable=False),
        sa.Column("facility_code", sa.String(length=64), nullable=False),
        sa.Column("emergency_phone", sa.String(length=64), nullable=True),
        sa.Column("primary_email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("bed_capacity", sa.String(length=64), nullable=True),
        sa.Column("active_protocol", sa.String(length=255), nullable=True),
        sa.Column("vitals_interval", sa.String(length=64), nullable=True),
        sa.Column("delta_engine_window", sa.String(length=64), nullable=True),
        sa.Column("ai_model", sa.String(length=128), nullable=True),
        sa.Column("auto_handover", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("critical_alert_escalation", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("specialties", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("facility_profiles")
    op.drop_table("clinical_thresholds")
    op.drop_table("appointments")
    op.drop_table("clinical_notes")
    op.drop_table("vitals")
    op.drop_table("patients")

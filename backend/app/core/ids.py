"""Unified cryptographically secure prefixed identifier generator for CareArc entities.

Generates human-readable, URL-safe, non-ambiguous medical identifiers:
- Patient:       PT-XXXXXXXX (e.g. PT-8K3F9J2A)
- Vital:         VIT-XXXXXXXX (e.g. VIT-4N2L8X1B)
- Clinical Note: NOTE-XXXXXXXX (e.g. NOTE-9M1Q4P7C)
- Appointment:   APT-XXXXXXXX (e.g. APT-5X7K2M9D)
"""

import secrets

# Non-ambiguous uppercase alphanumeric charset (omits 0, O, 1, I, L to prevent clinical transcription errors)
CLINICAL_CHARSET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def generate_id(prefix: str, length: int = 8) -> str:
    """Generate a prefixed random identifier using the clinical charset.

    Args:
        prefix: Entity prefix (e.g. 'PT', 'VIT', 'NOTE', 'APT').
        length: Random suffix character length (default 8).

    Returns:
        Formatted string ID, e.g. 'PT-8K3F9J2A'.
    """
    suffix = "".join(secrets.choice(CLINICAL_CHARSET) for _ in range(length))
    return f"{prefix.upper()}-{suffix}"


def generate_patient_id() -> str:
    """Generate a unique Patient identifier (e.g., PT-8K3F9J2A)."""
    return generate_id("PT")


def generate_vital_id() -> str:
    """Generate a unique Vital identifier (e.g., VIT-4N2L8X1B)."""
    return generate_id("VIT")


def generate_note_id() -> str:
    """Generate a unique Clinical Note identifier (e.g., NOTE-9M1Q4P7C)."""
    return generate_id("NOTE")


def generate_appointment_id() -> str:
    """Generate a unique Appointment identifier (e.g., APT-5X7K2M9D)."""
    return generate_id("APT")

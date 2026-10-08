"""Clinical Delta Engine Service.

Python implementation of the CareArc Longitudinal Trajectory & Delta Engine.
Calculates rates of change between chronological vitals, evaluates clinical
reference bounds, and derives patient acuity triage classifications
(Review, Watch, Improving, Stable).
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

# Standard clinical normal reference ranges
DEFAULT_NORMAL_RANGES: Dict[str, Dict[str, float]] = {
    "heartRate": {"min": 60.0, "max": 100.0},
    "oxygen": {"min": 95.0, "max": 100.0},
    "temperature": {"min": 36.5, "max": 37.5},
    "respiratoryRate": {"min": 12.0, "max": 20.0},
}

VITAL_CONFIG = {
    "heartRate": {"label": "Heart Rate", "unit": "bpm"},
    "oxygen": {"label": "Blood Oxygen", "unit": "%"},
    "temperature": {"label": "Temperature", "unit": "°C"},
    "respiratoryRate": {"label": "Resp. Rate", "unit": "brpm"},
}


def _to_float(val: Any) -> Optional[float]:
    """Safely convert Decimal, int, or float to float."""
    if val is None:
        return None
    if isinstance(val, (int, float, Decimal)):
        return float(val)
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def compute_deltas(vitals: List[Any]) -> Optional[List[Dict[str, Any]]]:
    """Compute rate of change between the last two chronological vital sign readings.

    Args:
        vitals: List of Vital models or vital sign dictionaries.

    Returns:
        List of computed delta metrics or None if fewer than 2 records exist.
    """
    if not vitals or len(vitals) < 2:
        return None

    # Helper to extract timestamp
    def get_timestamp(v: Any) -> datetime:
        if isinstance(v, dict):
            ts = v.get("timestamp")
        else:
            ts = getattr(v, "timestamp", None)
        if isinstance(ts, str):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return ts or datetime.min

    # Sort ascending chronologically
    sorted_vitals = sorted(vitals, key=get_timestamp)
    previous = sorted_vitals[-2]
    latest = sorted_vitals[-1]

    def get_attr(obj: Any, key: str) -> Any:
        if isinstance(obj, dict):
            # Support both camelCase and snake_case keys
            snake_key = {
                "heartRate": "heart_rate",
                "oxygen": "oxygen",
                "temperature": "temperature",
                "respiratoryRate": "respiratory_rate",
                "bloodPressure": "blood_pressure",
            }.get(key, key)
            return obj.get(key) if key in obj else obj.get(snake_key)
        return getattr(obj, {
            "heartRate": "heart_rate",
            "oxygen": "oxygen",
            "temperature": "temperature",
            "respiratoryRate": "respiratory_rate",
            "bloodPressure": "blood_pressure",
        }.get(key, key), None)

    deltas: List[Dict[str, Any]] = []

    for key, config in VITAL_CONFIG.items():
        from_val = _to_float(get_attr(previous, key))
        to_val = _to_float(get_attr(latest, key))

        if from_val is None or to_val is None:
            continue

        change = round(to_val - from_val, 1)
        percent_change = round((change / from_val) * 100, 1) if from_val != 0 else 0.0

        if abs(change) < 1.0:
            direction = "stable"
        elif change > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        abs_pct = abs(percent_change)
        if abs_pct >= 15.0:
            severity = "significant"
        elif abs_pct >= 5.0:
            severity = "moderate"
        else:
            severity = "minimal"

        deltas.append({
            "vital": key,
            "label": config["label"],
            "unit": config["unit"],
            "from": from_val,
            "to": to_val,
            "change": change,
            "percentChange": percent_change,
            "direction": direction,
            "severity": severity,
        })

    # Blood pressure handling
    prev_bp = get_attr(previous, "bloodPressure")
    latest_bp = get_attr(latest, "bloodPressure")

    if prev_bp and latest_bp:
        def get_bp_val(bp_obj: Any, sub_key: str) -> Optional[float]:
            if isinstance(bp_obj, dict):
                return _to_float(bp_obj.get(sub_key))
            return _to_float(getattr(bp_obj, sub_key, None))

        prev_sys = get_bp_val(prev_bp, "systolic")
        latest_sys = get_bp_val(latest_bp, "systolic")
        prev_dia = get_bp_val(prev_bp, "diastolic")
        latest_dia = get_bp_val(latest_bp, "diastolic")

        if prev_sys is not None and latest_sys is not None and prev_dia is not None and latest_dia is not None:
            sys_change = round(latest_sys - prev_sys, 1)
            dia_change = round(latest_dia - prev_dia, 1)

            sys_pct = round((sys_change / prev_sys) * 100, 1) if prev_sys != 0 else 0.0
            dia_pct = round((dia_change / prev_dia) * 100, 1) if prev_dia != 0 else 0.0

            sys_dir = "stable" if abs(sys_change) < 1.0 else ("increasing" if sys_change > 0 else "decreasing")
            dia_dir = "stable" if abs(dia_change) < 1.0 else ("increasing" if dia_change > 0 else "decreasing")

            sys_sev = "significant" if abs(sys_pct) >= 15.0 else ("moderate" if abs(sys_pct) >= 5.0 else "minimal")
            dia_sev = "significant" if abs(dia_pct) >= 15.0 else ("moderate" if abs(dia_pct) >= 5.0 else "minimal")

            sys_sign = "+" if sys_change > 0 else ""
            dia_sign = "+" if dia_change > 0 else ""

            deltas.append({
                "vital": "bloodPressure",
                "label": "Blood Pressure",
                "unit": "mmHg",
                "change": f"{sys_sign}{sys_change}/{dia_sign}{dia_change}",
                "percentChange": sys_pct,
                "direction": sys_dir,
                "severity": sys_sev,
            })

    return deltas


def derive_patient_status(
    deltas: Optional[List[Dict[str, Any]]],
    latest_vitals: Optional[Any],
    normal_ranges: Optional[Dict[str, Dict[str, float]]] = None,
) -> str:
    """Derive patient triage status classification (Review, Watch, Improving, Stable, or No Data).

    Args:
        deltas: List of calculated vital deltas.
        latest_vitals: The most recent Vital record.
        normal_ranges: Optional custom threshold reference ranges.

    Returns:
        Status string: 'Review' | 'Watch' | 'Improving' | 'Stable' | 'No Data'
    """
    if not latest_vitals:
        return "No Data"
    if deltas is None:
        return "Stable"

    ranges = normal_ranges or DEFAULT_NORMAL_RANGES

    # Check for significant worsening
    has_significant_worsening = any(
        (d.get("severity") == "significant" and d.get("direction") == "increasing" and d.get("vital") in ("heartRate", "temperature", "respiratoryRate"))
        or (d.get("severity") == "significant" and d.get("direction") == "decreasing" and d.get("vital") == "oxygen")
        for d in deltas
    )

    # Check for significant/moderate improvement
    has_significant_improvement = any(
        (d.get("severity") in ("moderate", "significant") and d.get("direction") == "decreasing" and d.get("vital") in ("heartRate", "temperature", "respiratoryRate"))
        or (d.get("severity") in ("moderate", "significant") and d.get("direction") == "increasing" and d.get("vital") == "oxygen")
        for d in deltas
    )

    # Check out-of-range bounds on latest vitals
    def extract_val(key: str) -> Optional[float]:
        if isinstance(latest_vitals, dict):
            snake = {
                "heartRate": "heart_rate",
                "oxygen": "oxygen",
                "temperature": "temperature",
                "respiratoryRate": "respiratory_rate",
            }.get(key, key)
            val = latest_vitals.get(key) if key in latest_vitals else latest_vitals.get(snake)
        else:
            attr = {
                "heartRate": "heart_rate",
                "oxygen": "oxygen",
                "temperature": "temperature",
                "respiratoryRate": "respiratory_rate",
            }.get(key, key)
            val = getattr(latest_vitals, attr, None)
        return _to_float(val)

    out_of_range = False
    for vital_key, r in ranges.items():
        v = extract_val(vital_key)
        if v is not None:
            if v < r["min"] or v > r["max"]:
                out_of_range = True
                break

    # Decision Matrix
    if out_of_range and has_significant_worsening:
        return "Review"
    elif out_of_range or has_significant_worsening:
        return "Watch"
    elif has_significant_improvement and not out_of_range:
        return "Improving"
    else:
        return "Stable"


def generate_latest_update(
    deltas: Optional[List[Dict[str, Any]]],
    latest_note: Optional[Any] = None,
) -> str:
    """Generate human-readable clinical change summary."""
    if not deltas or len(deltas) == 0:
        return "No data yet"

    summary_parts = []
    for delta in deltas:
        if delta.get("severity") == "minimal":
            continue
        direction = delta.get("direction")
        arrow = "↑" if direction == "increasing" else ("↓" if direction == "decreasing" else "→")
        change = delta.get("change")
        sign = "+" if isinstance(change, (int, float)) and change > 0 else ""
        label = delta.get("label", "")
        unit = delta.get("unit", "")
        summary_parts.append(f"{label} {arrow} {sign}{change} {unit}")

    if not summary_parts:
        if latest_note:
            content = getattr(latest_note, "content", "") if not isinstance(latest_note, dict) else latest_note.get("content", "")
            return content[:80] + "..." if len(content) > 80 else content
        return "No significant changes to report"

    return " · ".join(summary_parts)

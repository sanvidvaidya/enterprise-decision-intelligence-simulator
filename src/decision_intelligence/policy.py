"""Versioned, maker-checker governance for deterministic scoring policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
from typing import Any
from uuid import uuid4

from decision_intelligence.database import DEFAULT_DATABASE_PATH, connect


@dataclass(frozen=True)
class ParameterDefinition:
    label: str
    category: str
    description: str
    minimum: float
    maximum: float
    step: float


PARAMETER_DEFINITIONS: dict[str, ParameterDefinition] = {
    "medium_risk_threshold": ParameterDefinition("Medium-risk score", "Risk bands", "Minimum score classified Medium.", 1, 99, 1),
    "high_risk_threshold": ParameterDefinition("High-risk score", "Risk bands", "Minimum score classified High.", 1, 100, 1),
    "usage_decline_moderate_threshold": ParameterDefinition("Moderate usage decline", "Usage", "Month-over-month decline that triggers the moderate rule.", 0, 1, 0.01),
    "usage_decline_moderate_points": ParameterDefinition("Moderate decline points", "Usage", "Points for a moderate active-user decline.", 0, 100, 1),
    "usage_decline_high_threshold": ParameterDefinition("Severe usage decline", "Usage", "Month-over-month decline that triggers the severe rule.", 0, 1, 0.01),
    "usage_decline_high_points": ParameterDefinition("Severe decline points", "Usage", "Points for a severe active-user decline.", 0, 100, 1),
    "seat_engagement_low_threshold": ParameterDefinition("Very-low seat engagement", "Usage", "Active-seat ratio below this value receives the larger penalty.", 0, 1, 0.01),
    "seat_engagement_low_points": ParameterDefinition("Very-low engagement points", "Usage", "Points for very-low seat engagement.", 0, 100, 1),
    "seat_engagement_medium_threshold": ParameterDefinition("Low seat engagement", "Usage", "Active-seat ratio below this value receives the smaller penalty.", 0, 1, 0.01),
    "seat_engagement_medium_points": ParameterDefinition("Low engagement points", "Usage", "Points for low seat engagement.", 0, 100, 1),
    "critical_support_points": ParameterDefinition("Critical support points", "Support", "Points when unresolved Critical tickets exist.", 0, 100, 1),
    "renewal_near_days": ParameterDefinition("Near renewal window", "Renewal", "Days defining the nearest renewal window.", 0, 365, 1),
    "renewal_near_points": ParameterDefinition("Near renewal points", "Renewal", "Points inside the nearest renewal window.", 0, 100, 1),
    "renewal_mid_days": ParameterDefinition("Mid renewal window", "Renewal", "Days defining the middle renewal window.", 0, 365, 1),
    "renewal_mid_points": ParameterDefinition("Mid renewal points", "Renewal", "Points inside the middle renewal window.", 0, 100, 1),
    "renewal_far_days": ParameterDefinition("Far renewal window", "Renewal", "Days defining the farthest renewal window.", 0, 730, 1),
    "renewal_far_points": ParameterDefinition("Far renewal points", "Renewal", "Points inside the farthest renewal window.", 0, 100, 1),
    "high_acv_threshold": ParameterDefinition("High ACV threshold", "Commercial exposure", "ACV that receives the larger exposure weight.", 0, 10_000_000, 1_000),
    "high_acv_points": ParameterDefinition("High ACV points", "Commercial exposure", "Exposure points above the high threshold.", 0, 100, 1),
    "medium_acv_threshold": ParameterDefinition("Medium ACV threshold", "Commercial exposure", "ACV that receives the smaller exposure weight.", 0, 10_000_000, 1_000),
    "medium_acv_points": ParameterDefinition("Medium ACV points", "Commercial exposure", "Exposure points above the medium threshold.", 0, 100, 1),
}

DEFAULT_POLICY: dict[str, float] = {
    "medium_risk_threshold": 30,
    "high_risk_threshold": 55,
    "usage_decline_moderate_threshold": 0.15,
    "usage_decline_moderate_points": 18,
    "usage_decline_high_threshold": 0.30,
    "usage_decline_high_points": 30,
    "seat_engagement_low_threshold": 0.40,
    "seat_engagement_low_points": 15,
    "seat_engagement_medium_threshold": 0.60,
    "seat_engagement_medium_points": 8,
    "critical_support_points": 30,
    "renewal_near_days": 30,
    "renewal_near_points": 20,
    "renewal_mid_days": 60,
    "renewal_mid_points": 12,
    "renewal_far_days": 90,
    "renewal_far_points": 6,
    "high_acv_threshold": 100_000,
    "high_acv_points": 10,
    "medium_acv_threshold": 50_000,
    "medium_acv_points": 5,
}

INTEGER_PARAMETERS = {
    name
    for name in PARAMETER_DEFINITIONS
    if name.endswith("_points") or name.endswith("_days")
} | {"medium_risk_threshold", "high_risk_threshold"}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_policy(parameters: dict[str, float]) -> list[str]:
    """Return every policy defect so the UI can explain why saving is blocked."""

    errors: list[str] = []
    missing = set(PARAMETER_DEFINITIONS) - set(parameters)
    extra = set(parameters) - set(PARAMETER_DEFINITIONS)
    if missing:
        errors.append("Missing parameters: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("Unknown parameters: " + ", ".join(sorted(extra)))
    for name, definition in PARAMETER_DEFINITIONS.items():
        if name not in parameters:
            continue
        value = parameters[name]
        if not isfinite(value) or not definition.minimum <= value <= definition.maximum:
            errors.append(f"{definition.label} must be between {definition.minimum:g} and {definition.maximum:g}.")
        elif name in INTEGER_PARAMETERS and not float(value).is_integer():
            errors.append(f"{definition.label} must be a whole number.")
    if not missing:
        if parameters["medium_risk_threshold"] >= parameters["high_risk_threshold"]:
            errors.append("The Medium-risk threshold must be below the High-risk threshold.")
        if parameters["usage_decline_moderate_threshold"] >= parameters["usage_decline_high_threshold"]:
            errors.append("The moderate usage-decline threshold must be below the severe threshold.")
        if parameters["seat_engagement_low_threshold"] >= parameters["seat_engagement_medium_threshold"]:
            errors.append("The very-low seat threshold must be below the low-seat threshold.")
        if not parameters["renewal_near_days"] < parameters["renewal_mid_days"] < parameters["renewal_far_days"]:
            errors.append("Renewal windows must increase from Near to Mid to Far.")
        if parameters["medium_acv_threshold"] >= parameters["high_acv_threshold"]:
            errors.append("The Medium ACV threshold must be below the High ACV threshold.")
    return errors


def ensure_default_policy(database_path: str | Path = DEFAULT_DATABASE_PATH) -> str:
    """Seed the documented V1 policy exactly once for an initialized database."""

    with connect(database_path) as connection:
        active = connection.execute(
            "SELECT policy_version_id FROM policy_versions WHERE policy_status = 'Active'"
        ).fetchone()
        if active:
            return active["policy_version_id"]
        existing = connection.execute("SELECT COUNT(*) FROM policy_versions").fetchone()[0]
        if existing:
            return ""
        version_id = str(uuid4())
        now = utc_timestamp()
        connection.execute(
            """INSERT INTO policy_versions
               (policy_version_id, version_number, policy_name, policy_status,
                created_at, created_by, rationale, activated_at)
               VALUES (?, 1, 'Baseline renewal-risk policy', 'Active', ?,
                       'System bootstrap', 'Documented deterministic baseline.', ?)""",
            (version_id, now, now),
        )
        connection.executemany(
            "INSERT INTO policy_parameters VALUES (?, ?, ?)",
            [(version_id, name, value) for name, value in DEFAULT_POLICY.items()],
        )
    return version_id


def get_active_policy(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> tuple[str | None, dict[str, float]]:
    with connect(database_path) as connection:
        row = connection.execute(
            """SELECT policy_version_id FROM policy_versions
                WHERE policy_status = 'Active' ORDER BY version_number DESC LIMIT 1"""
        ).fetchone()
        if not row:
            return None, DEFAULT_POLICY.copy()
        parameters = connection.execute(
            "SELECT parameter_name, parameter_value FROM policy_parameters WHERE policy_version_id = ?",
            (row["policy_version_id"],),
        ).fetchall()
    policy = DEFAULT_POLICY.copy()
    policy.update({item["parameter_name"]: item["parameter_value"] for item in parameters})
    return row["policy_version_id"], policy


def get_policy_parameters(
    policy_version_id: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> dict[str, float]:
    with connect(database_path) as connection:
        rows = connection.execute(
            "SELECT parameter_name, parameter_value FROM policy_parameters WHERE policy_version_id = ?",
            (policy_version_id,),
        ).fetchall()
    if not rows:
        raise ValueError(f"Unknown policy version ID: {policy_version_id}")
    return {row["parameter_name"]: row["parameter_value"] for row in rows}


def list_policy_versions(database_path: str | Path = DEFAULT_DATABASE_PATH) -> list[dict[str, Any]]:
    with connect(database_path) as connection:
        rows = connection.execute(
            """SELECT p.*, a.decision, a.decided_at, a.decided_by, a.decision_notes
                 FROM policy_versions p
                 LEFT JOIN policy_approvals a USING (policy_version_id)
                ORDER BY p.version_number DESC"""
        ).fetchall()
    return [dict(row) for row in rows]


def create_policy_draft(
    policy_name: str,
    parameters: dict[str, float],
    created_by: str,
    rationale: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> str:
    errors = validate_policy(parameters)
    if errors:
        raise ValueError(" ".join(errors))
    if not policy_name.strip() or not created_by.strip() or not rationale.strip():
        raise ValueError("Policy name, creator, and rationale are required")
    version_id = str(uuid4())
    with connect(database_path) as connection:
        version_number = connection.execute(
            "SELECT COALESCE(MAX(version_number), 0) + 1 FROM policy_versions"
        ).fetchone()[0]
        connection.execute(
            """INSERT INTO policy_versions
               (policy_version_id, version_number, policy_name, policy_status,
                created_at, created_by, rationale)
               VALUES (?, ?, ?, 'Draft', ?, ?, ?)""",
            (version_id, version_number, policy_name.strip(), utc_timestamp(), created_by.strip(), rationale.strip()),
        )
        connection.executemany(
            "INSERT INTO policy_parameters VALUES (?, ?, ?)",
            [(version_id, name, float(value)) for name, value in parameters.items()],
        )
    return version_id


def decide_policy(
    policy_version_id: str,
    decision: str,
    decided_by: str,
    notes: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> None:
    """Approve/activate or reject a draft using a separate reviewer identity."""

    if decision not in {"Approved", "Rejected"}:
        raise ValueError("Decision must be Approved or Rejected")
    if not decided_by.strip() or not notes.strip():
        raise ValueError("Reviewer and decision notes are required")
    now = utc_timestamp()
    with connect(database_path) as connection:
        policy = connection.execute(
            "SELECT * FROM policy_versions WHERE policy_version_id = ?", (policy_version_id,)
        ).fetchone()
        if not policy:
            raise ValueError(f"Unknown policy version ID: {policy_version_id}")
        if policy["policy_status"] != "Draft":
            raise ValueError("Only Draft policies can be reviewed")
        if policy["created_by"].casefold() == decided_by.strip().casefold():
            raise ValueError("Maker-checker control requires a reviewer other than the policy creator")
        if decision == "Approved":
            connection.execute(
                "UPDATE policy_versions SET policy_status = 'Retired' WHERE policy_status = 'Active'"
            )
            connection.execute(
                """UPDATE policy_versions SET policy_status = 'Active', activated_at = ?
                    WHERE policy_version_id = ?""",
                (now, policy_version_id),
            )
        else:
            connection.execute(
                "UPDATE policy_versions SET policy_status = 'Rejected' WHERE policy_version_id = ?",
                (policy_version_id,),
            )
        connection.execute(
            """INSERT INTO policy_approvals
               (policy_approval_id, policy_version_id, decision, decided_at, decided_by, decision_notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (str(uuid4()), policy_version_id, decision, now, decided_by.strip(), notes.strip()),
        )


def policy_editor_rows(parameters: dict[str, float]) -> list[dict[str, Any]]:
    """Return stable metadata rows for a governed UI editor."""

    return [
        {
            "parameter_name": name,
            "category": definition.category,
            "label": definition.label,
            "value": parameters[name],
            "description": definition.description,
            "minimum": definition.minimum,
            "maximum": definition.maximum,
        }
        for name, definition in PARAMETER_DEFINITIONS.items()
    ]


def preview_policy_impact(
    proposed_parameters: dict[str, float],
    as_of=None,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> dict[str, Any]:
    """Replay the portfolio under a draft without changing the active policy."""

    errors = validate_policy(proposed_parameters)
    if errors:
        raise ValueError(" ".join(errors))
    from decision_intelligence.risk_engine import assess_all_customers

    _, current_parameters = get_active_policy(database_path)
    current = assess_all_customers(as_of, database_path, current_parameters)
    proposed = assess_all_customers(as_of, database_path, proposed_parameters)
    proposed_by_customer = {item["customer"]["customer_id"]: item for item in proposed}
    rows = []
    for baseline in current:
        customer_id = baseline["customer"]["customer_id"]
        candidate = proposed_by_customer[customer_id]
        contract = baseline["contract"] or {}
        rows.append(
            {
                "customer_id": customer_id,
                "customer_name": baseline["customer"]["customer_name"],
                "segment": baseline["customer"]["segment"],
                "annual_contract_value": contract.get("annual_contract_value", 0),
                "current_score": baseline["risk_score"],
                "proposed_score": candidate["risk_score"],
                "score_delta": candidate["risk_score"] - baseline["risk_score"],
                "current_level": baseline["risk_level"],
                "proposed_level": candidate["risk_level"],
                "classification_changed": baseline["risk_level"] != candidate["risk_level"],
            }
        )
    changed = [row for row in rows if row["classification_changed"]]
    return {
        "rows": rows,
        "customers_changed": len(changed),
        "acv_reclassified": sum(row["annual_contract_value"] for row in changed),
        "average_score_delta": sum(row["score_delta"] for row in rows) / max(len(rows), 1),
    }

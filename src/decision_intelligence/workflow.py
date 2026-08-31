"""Persistent decision workflow services for assessments, actions, and scenarios."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from decision_intelligence.database import DEFAULT_DATABASE_PATH, connect, create_database
from decision_intelligence.policy import ensure_default_policy, get_active_policy
from decision_intelligence.risk_engine import assess_all_customers


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def snapshot_portfolio(
    as_of: date | None = None,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> dict[str, Any]:
    """Persist a point-in-time assessment and every factor for the portfolio."""

    as_of = as_of or date.today()
    create_database(database_path)
    ensure_default_policy(database_path)
    policy_version_id, _ = get_active_policy(database_path)
    assessments = assess_all_customers(as_of, database_path)
    timestamp = utc_timestamp()
    with connect(database_path) as connection:
        for assessment in assessments:
            assessment_id = str(uuid4())
            connection.execute(
                """INSERT INTO risk_assessments
                   (assessment_id, customer_id, assessed_at, as_of_date, risk_score, risk_level)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    assessment_id,
                    assessment["customer"]["customer_id"],
                    timestamp,
                    as_of.isoformat(),
                    assessment["risk_score"],
                    assessment["risk_level"],
                ),
            )
            connection.executemany(
                """INSERT INTO risk_factor_results
                   (factor_result_id, assessment_id, factor_name, points, explanation,
                    evidence_record_ids_json, recommended_action)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        str(uuid4()),
                        assessment_id,
                        factor["name"],
                        factor["points"],
                        factor["explanation"],
                        json.dumps(factor["evidence_record_ids"]),
                        factor["recommended_action"],
                    )
                    for factor in assessment["factors"]
                ],
            )
            if policy_version_id:
                connection.execute(
                    "INSERT INTO assessment_policy_versions VALUES (?, ?)",
                    (assessment_id, policy_version_id),
                )
    return {
        "assessed_at": timestamp,
        "as_of_date": as_of.isoformat(),
        "customers_assessed": len(assessments),
    }


def assessment_history(
    customer_id: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[dict[str, Any]]:
    with connect(database_path) as connection:
        rows = connection.execute(
            """SELECT rowid AS assessment_sequence, assessment_id, assessed_at,
                      as_of_date, risk_score, risk_level
                 FROM risk_assessments
                WHERE customer_id = ?
                ORDER BY rowid""",
            (customer_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_scenario(
    customer_id: str,
    scenario: dict[str, Any],
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> str:
    """Save a reproducible set of assumptions and its deterministic result."""

    scenario_id = str(uuid4())
    with connect(database_path) as connection:
        connection.execute(
            """INSERT INTO scenario_runs
               (scenario_run_id, customer_id, created_at, baseline_score,
                simulated_score, simulated_level, assumptions_json, result_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                scenario_id,
                customer_id,
                utc_timestamp(),
                scenario["baseline"]["risk_score"],
                scenario["simulated"]["risk_score"],
                scenario["simulated"]["risk_level"],
                json.dumps(scenario["assumptions"], sort_keys=True),
                json.dumps(scenario["simulated"], sort_keys=True),
            ),
        )
    return scenario_id


def list_scenarios(
    customer_id: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[dict[str, Any]]:
    with connect(database_path) as connection:
        rows = connection.execute(
            """SELECT scenario_run_id, created_at, baseline_score, simulated_score,
                      simulated_level, assumptions_json
                 FROM scenario_runs
                WHERE customer_id = ? ORDER BY created_at DESC""",
            (customer_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_action(
    customer_id: str,
    action_text: str,
    owner: str,
    priority: str,
    due_date: date | str,
    evidence_record_ids: list[str] | None = None,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> str:
    """Assign a renewal intervention with ownership and a due date."""

    if not action_text.strip() or not owner.strip():
        raise ValueError("Action text and owner are required")
    if priority not in {"Low", "Medium", "High", "Critical"}:
        raise ValueError("Unknown priority")
    due_date_text = due_date.isoformat() if isinstance(due_date, date) else date.fromisoformat(due_date).isoformat()
    action_id = str(uuid4())
    with connect(database_path) as connection:
        connection.execute(
            """INSERT INTO account_actions
               (action_id, customer_id, action_text, owner, priority, due_date,
                action_status, created_at, evidence_record_ids_json)
               VALUES (?, ?, ?, ?, ?, ?, 'Open', ?, ?)""",
            (
                action_id,
                customer_id,
                action_text.strip(),
                owner.strip(),
                priority,
                due_date_text,
                utc_timestamp(),
                json.dumps(evidence_record_ids or []),
            ),
        )
    return action_id


def update_action_status(
    action_id: str,
    status: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> None:
    if status not in {"Open", "In Progress", "Blocked", "Completed"}:
        raise ValueError("Unknown action status")
    completed_at = utc_timestamp() if status == "Completed" else None
    with connect(database_path) as connection:
        cursor = connection.execute(
            "UPDATE account_actions SET action_status = ?, completed_at = ? WHERE action_id = ?",
            (status, completed_at, action_id),
        )
        if cursor.rowcount != 1:
            raise ValueError(f"Unknown action ID: {action_id}")


def list_actions(
    customer_id: str | None = None,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[dict[str, Any]]:
    query = """SELECT a.*, c.customer_name
                 FROM account_actions a JOIN customers c USING (customer_id)"""
    parameters: tuple[str, ...] = ()
    if customer_id:
        query += " WHERE a.customer_id = ?"
        parameters = (customer_id,)
    query += " ORDER BY CASE a.action_status WHEN 'Completed' THEN 1 ELSE 0 END, a.due_date, a.created_at"
    with connect(database_path) as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [dict(row) for row in rows]


def log_decision(
    customer_id: str,
    event_type: str,
    actor: str,
    notes: str,
    related_action_id: str | None = None,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> str:
    """Append a human decision to the auditable customer timeline."""

    if not event_type.strip() or not actor.strip() or not notes.strip():
        raise ValueError("Event type, actor, and notes are required")
    event_id = str(uuid4())
    with connect(database_path) as connection:
        connection.execute(
            """INSERT INTO decision_events
               (decision_event_id, customer_id, event_type, event_at, actor, notes, related_action_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (event_id, customer_id, event_type.strip(), utc_timestamp(), actor.strip(), notes.strip(), related_action_id),
        )
    return event_id


def list_decisions(
    customer_id: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[dict[str, Any]]:
    with connect(database_path) as connection:
        rows = connection.execute(
            """SELECT * FROM decision_events WHERE customer_id = ?
                ORDER BY event_at DESC""",
            (customer_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def evidence_records(
    record_ids: list[str],
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[dict[str, Any]]:
    """Resolve factor evidence IDs back to exact operational source rows."""

    table_by_prefix = {
        "USE-": ("product_usage_events", "usage_event_id"),
        "TKT-": ("support_tickets", "ticket_id"),
        "CON-": ("contracts", "contract_id"),
        "CUS-": ("customers", "customer_id"),
    }
    records: list[dict[str, Any]] = []
    with connect(database_path) as connection:
        for record_id in record_ids:
            match = next((value for prefix, value in table_by_prefix.items() if record_id.startswith(prefix)), None)
            if match:
                table, identifier = match
                row = connection.execute(
                    f"SELECT * FROM {table} WHERE {identifier} = ?", (record_id,)
                ).fetchone()
                if row:
                    record = dict(row)
                    record["source_table"] = table
                    records.append(record)
    return records

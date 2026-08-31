"""Explain score changes and combine operational and human events over time."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from decision_intelligence.database import DEFAULT_DATABASE_PATH, connect


def _assessment_factors(connection, assessment_id: str) -> dict[str, dict[str, Any]]:
    rows = connection.execute(
        """SELECT factor_name, points, explanation, evidence_record_ids_json,
                  recommended_action
             FROM risk_factor_results WHERE assessment_id = ?""",
        (assessment_id,),
    ).fetchall()
    return {
        row["factor_name"]: {
            "points": row["points"],
            "explanation": row["explanation"],
            "evidence_record_ids": json.loads(row["evidence_record_ids_json"]),
            "recommended_action": row["recommended_action"],
        }
        for row in rows
    }


def risk_change_history(
    customer_id: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[dict[str, Any]]:
    """Explain every score transition using factor-level snapshot differences."""

    with connect(database_path) as connection:
        assessments = connection.execute(
            """SELECT r.rowid AS assessment_sequence, r.*, p.version_number, p.policy_name
                 FROM risk_assessments r
                 LEFT JOIN assessment_policy_versions ap USING (assessment_id)
                 LEFT JOIN policy_versions p USING (policy_version_id)
                WHERE r.customer_id = ?
                ORDER BY r.rowid""",
            (customer_id,),
        ).fetchall()
        previous_score: int | None = None
        previous_factors: dict[str, dict[str, Any]] = {}
        changes: list[dict[str, Any]] = []
        for assessment in assessments:
            current_factors = _assessment_factors(connection, assessment["assessment_id"])
            added = sorted(set(current_factors) - set(previous_factors))
            removed = sorted(set(previous_factors) - set(current_factors))
            modified = sorted(
                name
                for name in set(current_factors) & set(previous_factors)
                if current_factors[name]["points"] != previous_factors[name]["points"]
            )
            evidence_ids = sorted(
                {
                    record_id
                    for name in added + modified
                    for record_id in current_factors[name]["evidence_record_ids"]
                }
                | {
                    record_id
                    for name in removed
                    for record_id in previous_factors[name]["evidence_record_ids"]
                }
            )
            delta = None if previous_score is None else assessment["risk_score"] - previous_score
            parts = []
            if previous_score is None:
                parts.append("Baseline assessment established")
            elif delta == 0:
                parts.append("Score unchanged")
            elif delta > 0:
                parts.append(f"Score increased by {delta} point(s)")
            else:
                parts.append(f"Score decreased by {abs(delta)} point(s)")
            if added:
                parts.append("added: " + ", ".join(added))
            if removed:
                parts.append("removed: " + ", ".join(removed))
            if modified:
                descriptions = [
                    f"{name} {previous_factors[name]['points']}→{current_factors[name]['points']}"
                    for name in modified
                ]
                parts.append("reweighted: " + ", ".join(descriptions))
            policy_label = (
                f"v{assessment['version_number']} · {assessment['policy_name']}"
                if assessment["version_number"] is not None
                else "Unversioned baseline"
            )
            changes.append(
                {
                    "assessment_id": assessment["assessment_id"],
                    "assessed_at": assessment["assessed_at"],
                    "as_of_date": assessment["as_of_date"],
                    "risk_score": assessment["risk_score"],
                    "risk_level": assessment["risk_level"],
                    "score_delta": delta,
                    "factors_added": added,
                    "factors_removed": removed,
                    "factors_reweighted": modified,
                    "evidence_record_ids": evidence_ids,
                    "policy": policy_label,
                    "change_explanation": "; ".join(parts) + ".",
                }
            )
            previous_score = assessment["risk_score"]
            previous_factors = current_factors
    return changes


def customer_event_timeline(
    customer_id: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[dict[str, Any]]:
    """Combine machine observations, workflow activity, and human decisions."""

    events: list[dict[str, Any]] = []
    with connect(database_path) as connection:
        for row in connection.execute(
            """SELECT usage_event_id, event_date, active_users, seats_purchased,
                      feature_adoption_pct FROM product_usage_events
                WHERE customer_id = ? ORDER BY event_date""",
            (customer_id,),
        ):
            events.append(
                {
                    "event_at": row["event_date"],
                    "event_type": "Product usage",
                    "title": f"{row['active_users']} of {row['seats_purchased']} seats active",
                    "detail": f"Feature adoption {row['feature_adoption_pct']:.1f}%.",
                    "record_id": row["usage_event_id"],
                    "source": "Product analytics",
                }
            )
        for row in connection.execute(
            """SELECT ticket_id, opened_at, resolved_at, priority, ticket_status,
                      ticket_summary FROM support_tickets
                WHERE customer_id = ? ORDER BY opened_at""",
            (customer_id,),
        ):
            events.append(
                {
                    "event_at": row["opened_at"],
                    "event_type": "Support ticket",
                    "title": f"{row['priority']} ticket opened",
                    "detail": f"{row['ticket_summary']} Status: {row['ticket_status']}.",
                    "record_id": row["ticket_id"],
                    "source": "Support desk",
                }
            )
            if row["resolved_at"]:
                events.append(
                    {
                        "event_at": row["resolved_at"],
                        "event_type": "Support resolution",
                        "title": f"Ticket {row['ticket_id']} resolved",
                        "detail": row["ticket_summary"],
                        "record_id": row["ticket_id"],
                        "source": "Support desk",
                    }
                )
        for row in connection.execute(
            "SELECT contract_id, renewal_date, annual_contract_value FROM contracts WHERE customer_id = ?",
            (customer_id,),
        ):
            events.append(
                {
                    "event_at": row["renewal_date"],
                    "event_type": "Renewal milestone",
                    "title": f"${row['annual_contract_value']:,.0f} contract renewal",
                    "detail": "Contractual renewal date.",
                    "record_id": row["contract_id"],
                    "source": "Contract system",
                }
            )
        for row in connection.execute(
            """SELECT assessment_id, assessed_at, risk_score, risk_level FROM risk_assessments
                WHERE customer_id = ? ORDER BY assessed_at""",
            (customer_id,),
        ):
            events.append(
                {
                    "event_at": row["assessed_at"],
                    "event_type": "Risk assessment",
                    "title": f"{row['risk_level']} risk · {row['risk_score']}/100",
                    "detail": "Persisted deterministic assessment.",
                    "record_id": row["assessment_id"],
                    "source": "Risk engine",
                }
            )
        for row in connection.execute(
            """SELECT scenario_run_id, created_at, baseline_score, simulated_score,
                      assumptions_json FROM scenario_runs WHERE customer_id = ?""",
            (customer_id,),
        ):
            events.append(
                {
                    "event_at": row["created_at"],
                    "event_type": "Scenario",
                    "title": f"Scenario {row['baseline_score']}→{row['simulated_score']}",
                    "detail": row["assumptions_json"],
                    "record_id": row["scenario_run_id"],
                    "source": "Scenario Lab",
                }
            )
        for row in connection.execute(
            """SELECT action_id, created_at, completed_at, action_text, owner, action_status
                 FROM account_actions WHERE customer_id = ?""",
            (customer_id,),
        ):
            events.append(
                {
                    "event_at": row["created_at"],
                    "event_type": "Action",
                    "title": f"Action assigned to {row['owner']}",
                    "detail": f"{row['action_text']} Status: {row['action_status']}.",
                    "record_id": row["action_id"],
                    "source": "Account workflow",
                }
            )
            if row["completed_at"]:
                events.append(
                    {
                        "event_at": row["completed_at"],
                        "event_type": "Action completed",
                        "title": row["action_text"],
                        "detail": f"Completed by {row['owner']}.",
                        "record_id": row["action_id"],
                        "source": "Account workflow",
                    }
                )
        for row in connection.execute(
            """SELECT decision_event_id, event_at, event_type, actor, notes
                 FROM decision_events WHERE customer_id = ?""",
            (customer_id,),
        ):
            events.append(
                {
                    "event_at": row["event_at"],
                    "event_type": "Human decision",
                    "title": f"{row['event_type']} · {row['actor']}",
                    "detail": row["notes"],
                    "record_id": row["decision_event_id"],
                    "source": "Decision log",
                }
            )
        for row in connection.execute(
            """SELECT p.capacity_plan_id, p.created_at, p.created_by,
                      i.intervention, i.factor_name, i.estimated_hours, i.estimated_cost
                 FROM capacity_plan_items i
                 JOIN capacity_plans p USING (capacity_plan_id)
                WHERE i.customer_id = ? AND i.selected = 1""",
            (customer_id,),
        ):
            events.append(
                {
                    "event_at": row["created_at"],
                    "event_type": "Capacity allocation",
                    "title": row["intervention"],
                    "detail": (
                        f"Funded by {row['created_by']} for {row['factor_name']}; "
                        f"{row['estimated_hours']:g} hours and ${row['estimated_cost']:,.0f}."
                    ),
                    "record_id": row["capacity_plan_id"],
                    "source": "Capacity Planner",
                }
            )
    return sorted(events, key=lambda event: (event["event_at"], event["record_id"]), reverse=True)

"""Deterministic allocation of scarce intervention capacity across a portfolio."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from decision_intelligence.database import DEFAULT_DATABASE_PATH, connect
from decision_intelligence.policy import get_active_policy
from decision_intelligence.risk_engine import assess_all_customers


@dataclass(frozen=True)
class InterventionSpec:
    intervention: str
    delivery_team: str
    estimated_hours: float
    estimated_cost: float
    support_slots_required: int = 0
    enablement_slots_required: int = 0


INTERVENTION_CATALOG = {
    "Declining product usage": InterventionSpec(
        "Adoption recovery sprint", "Customer Success", 6, 750, enablement_slots_required=1
    ),
    "Low seat engagement": InterventionSpec(
        "Administrator enablement workshop", "Customer Success", 4, 400, enablement_slots_required=1
    ),
    "Unresolved critical support": InterventionSpec(
        "Critical-ticket recovery escalation", "Support Engineering", 8, 1_500, support_slots_required=1
    ),
    "Renewal approaching": InterventionSpec(
        "Renewal stakeholder alignment", "Account Management", 3, 250
    ),
}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _candidates(
    as_of: date,
    database_path: str | Path,
    policy: dict[str, float],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for assessment in assess_all_customers(as_of, database_path, policy):
        customer = assessment["customer"]
        contract = assessment["contract"] or {}
        acv = float(contract.get("annual_contract_value", 0))
        renewal_date = contract.get("renewal_date")
        days_to_renewal = (date.fromisoformat(renewal_date) - as_of).days if renewal_date else 365
        urgency_multiplier = 1 + max(0, min(90, 90 - days_to_renewal)) / 90
        for factor in assessment["factors"]:
            spec = INTERVENTION_CATALOG.get(factor["name"])
            if not spec:
                continue
            addressable_points = int(factor["points"])
            decision_value = addressable_points * acv * urgency_multiplier / max(spec.estimated_hours, 1) / 1_000
            candidates.append(
                {
                    "customer_id": customer["customer_id"],
                    "customer_name": customer["customer_name"],
                    "segment": customer["segment"],
                    "account_manager": customer["account_manager_name"],
                    "risk_level": assessment["risk_level"],
                    "risk_score": assessment["risk_score"],
                    "annual_contract_value": acv,
                    "renewal_date": renewal_date,
                    "days_to_renewal": days_to_renewal,
                    "factor_name": factor["name"],
                    "intervention": spec.intervention,
                    "delivery_team": spec.delivery_team,
                    "estimated_hours": spec.estimated_hours,
                    "estimated_cost": spec.estimated_cost,
                    "support_slots_required": spec.support_slots_required,
                    "enablement_slots_required": spec.enablement_slots_required,
                    "addressable_points": addressable_points,
                    "decision_value": round(decision_value, 2),
                    "evidence_record_ids": factor["evidence_record_ids"],
                    "recommended_action": factor["recommended_action"],
                }
            )
    return sorted(
        candidates,
        key=lambda item: (
            -item["decision_value"],
            -item["annual_contract_value"],
            item["customer_name"],
            item["intervention"],
        ),
    )


def plan_interventions(
    *,
    available_hours: float,
    available_budget: float,
    support_slots: int,
    enablement_slots: int,
    as_of: date | None = None,
    max_interventions_per_customer: int = 2,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    policy: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Allocate capacity using a stable value-per-hour portfolio heuristic.

    The score is not a predicted return. It combines addressable rule points,
    contract exposure, renewal urgency, and estimated effort for prioritization.
    """

    if min(available_hours, available_budget, support_slots, enablement_slots) < 0:
        raise ValueError("Capacity inputs must not be negative")
    if max_interventions_per_customer < 1:
        raise ValueError("max_interventions_per_customer must be at least one")
    as_of = as_of or date.today()
    policy_version_id, active_policy = get_active_policy(database_path)
    policy = policy or active_policy
    candidates = _candidates(as_of, database_path, policy)
    remaining_hours = float(available_hours)
    remaining_budget = float(available_budget)
    remaining_support = int(support_slots)
    remaining_enablement = int(enablement_slots)
    customer_counts: dict[str, int] = {}
    items: list[dict[str, Any]] = []
    for rank, candidate in enumerate(candidates, start=1):
        reasons = []
        customer_count = customer_counts.get(candidate["customer_id"], 0)
        if customer_count >= max_interventions_per_customer:
            reasons.append("customer intervention limit")
        if candidate["estimated_hours"] > remaining_hours:
            reasons.append("insufficient hours")
        if candidate["estimated_cost"] > remaining_budget:
            reasons.append("insufficient budget")
        if candidate["support_slots_required"] > remaining_support:
            reasons.append("no support escalation slot")
        if candidate["enablement_slots_required"] > remaining_enablement:
            reasons.append("no enablement slot")
        selected = not reasons
        item = {
            **candidate,
            "priority_rank": rank,
            "selected": selected,
            "deferral_reason": None if selected else "; ".join(reasons),
        }
        items.append(item)
        if selected:
            remaining_hours -= candidate["estimated_hours"]
            remaining_budget -= candidate["estimated_cost"]
            remaining_support -= candidate["support_slots_required"]
            remaining_enablement -= candidate["enablement_slots_required"]
            customer_counts[candidate["customer_id"]] = customer_count + 1
    selected_items = [item for item in items if item["selected"]]
    selected_customers = {item["customer_id"] for item in selected_items}
    acv_by_customer = {
        item["customer_id"]: item["annual_contract_value"] for item in selected_items
    }
    return {
        "as_of_date": as_of.isoformat(),
        "policy_version_id": policy_version_id,
        "constraints": {
            "available_hours": float(available_hours),
            "available_budget": float(available_budget),
            "support_slots": int(support_slots),
            "enablement_slots": int(enablement_slots),
            "max_interventions_per_customer": max_interventions_per_customer,
        },
        "summary": {
            "selected_count": len(selected_items),
            "customers_covered": len(selected_customers),
            "hours_allocated": sum(item["estimated_hours"] for item in selected_items),
            "budget_allocated": sum(item["estimated_cost"] for item in selected_items),
            "support_slots_used": sum(item["support_slots_required"] for item in selected_items),
            "enablement_slots_used": sum(item["enablement_slots_required"] for item in selected_items),
            "addressable_points": sum(item["addressable_points"] for item in selected_items),
            "acv_covered": sum(acv_by_customer.values()),
        },
        "items": items,
    }


def save_capacity_plan(
    plan: dict[str, Any],
    created_by: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> str:
    if not created_by.strip():
        raise ValueError("Plan owner is required")
    plan_id = str(uuid4())
    constraints = plan["constraints"]
    summary = plan["summary"]
    with connect(database_path) as connection:
        connection.execute(
            """INSERT INTO capacity_plans
               (capacity_plan_id, created_at, created_by, as_of_date, available_hours,
                available_budget, support_slots, enablement_slots, selected_count,
                hours_allocated, budget_allocated, acv_covered, policy_version_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                plan_id,
                utc_timestamp(),
                created_by.strip(),
                plan["as_of_date"],
                constraints["available_hours"],
                constraints["available_budget"],
                constraints["support_slots"],
                constraints["enablement_slots"],
                summary["selected_count"],
                summary["hours_allocated"],
                summary["budget_allocated"],
                summary["acv_covered"],
                plan["policy_version_id"],
            ),
        )
        connection.executemany(
            """INSERT INTO capacity_plan_items
               (capacity_plan_item_id, capacity_plan_id, customer_id, priority_rank,
                selected, factor_name, intervention, delivery_team, estimated_hours,
                estimated_cost, support_slots_required, enablement_slots_required,
                addressable_points, decision_value, evidence_record_ids_json, deferral_reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    str(uuid4()),
                    plan_id,
                    item["customer_id"],
                    item["priority_rank"],
                    int(item["selected"]),
                    item["factor_name"],
                    item["intervention"],
                    item["delivery_team"],
                    item["estimated_hours"],
                    item["estimated_cost"],
                    item["support_slots_required"],
                    item["enablement_slots_required"],
                    item["addressable_points"],
                    item["decision_value"],
                    json.dumps(item["evidence_record_ids"]),
                    item["deferral_reason"],
                )
                for item in plan["items"]
            ],
        )
    return plan_id


def list_capacity_plans(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[dict[str, Any]]:
    with connect(database_path) as connection:
        rows = connection.execute(
            "SELECT * FROM capacity_plans ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def capacity_plan_items(
    capacity_plan_id: str,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> list[dict[str, Any]]:
    with connect(database_path) as connection:
        rows = connection.execute(
            """SELECT i.*, c.customer_name FROM capacity_plan_items i
                 JOIN customers c USING (customer_id)
                WHERE capacity_plan_id = ? ORDER BY priority_rank""",
            (capacity_plan_id,),
        ).fetchall()
    return [dict(row) for row in rows]

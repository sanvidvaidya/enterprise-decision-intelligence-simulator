"""Deterministic, evidence-backed renewal-risk scoring and simulations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from decision_intelligence.database import DEFAULT_DATABASE_PATH, connect
from decision_intelligence.policy import DEFAULT_POLICY, get_active_policy


@dataclass(frozen=True)
class RiskFactor:
    """One transparent contribution to a renewal-risk score."""

    name: str
    points: int
    explanation: str
    evidence_record_ids: list[str]
    recommended_action: str


def risk_level(score: int, policy: dict[str, float] | None = None) -> str:
    """Map the documented score bands to their human-readable label."""

    policy = policy or DEFAULT_POLICY
    if score >= policy["high_risk_threshold"]:
        return "High"
    if score >= policy["medium_risk_threshold"]:
        return "Medium"
    return "Low"


def _customer_context(customer_id: str, database_path: str | Path) -> dict[str, Any]:
    with connect(database_path) as connection:
        customer = connection.execute(
            """SELECT c.*, am.full_name AS account_manager_name,
                      am.email AS account_manager_email
               FROM customers c
               JOIN account_managers am
                 ON am.account_manager_id = c.account_manager_id
              WHERE c.customer_id = ?""",
            (customer_id,),
        ).fetchone()
        if customer is None:
            raise ValueError(f"Unknown customer ID: {customer_id}")
        contract = connection.execute(
            "SELECT * FROM contracts WHERE customer_id = ? ORDER BY renewal_date LIMIT 1",
            (customer_id,),
        ).fetchone()
        usage = connection.execute(
            """SELECT * FROM product_usage_events
                WHERE customer_id = ? ORDER BY event_date DESC LIMIT 2""",
            (customer_id,),
        ).fetchall()
        tickets = connection.execute(
            """SELECT * FROM support_tickets
                WHERE customer_id = ?
                  AND ticket_status IN ('Open', 'In Progress')
                ORDER BY opened_at DESC""",
            (customer_id,),
        ).fetchall()
    return {
        "customer": dict(customer),
        "contract": dict(contract) if contract else None,
        "usage": [dict(row) for row in usage],
        "tickets": [dict(row) for row in tickets],
    }


def _factor_list(
    context: dict[str, Any],
    as_of: date,
    *,
    latest_active_users: int | None = None,
    resolve_critical: bool = False,
    renewal_extension_days: int = 0,
    policy: dict[str, float] | None = None,
) -> list[RiskFactor]:
    policy = policy or DEFAULT_POLICY
    factors: list[RiskFactor] = []
    usage = context["usage"]
    if len(usage) == 2:
        latest, previous = usage[0], usage[1]
        active_users = latest["active_users"] if latest_active_users is None else latest_active_users
        decline = (previous["active_users"] - active_users) / max(previous["active_users"], 1)
        if decline >= policy["usage_decline_high_threshold"]:
            factors.append(
                RiskFactor(
                    "Declining product usage",
                    int(policy["usage_decline_high_points"]),
                    f"Active users declined {decline:.0%} from {previous['active_users']} "
                    f"to {active_users} in the latest month.",
                    [previous["usage_event_id"], latest["usage_event_id"]],
                    "Schedule a usage-review meeting and agree an adoption recovery plan.",
                )
            )
        elif decline >= policy["usage_decline_moderate_threshold"]:
            factors.append(
                RiskFactor(
                    "Declining product usage",
                    int(policy["usage_decline_moderate_points"]),
                    f"Active users declined {decline:.0%} in the latest month.",
                    [previous["usage_event_id"], latest["usage_event_id"]],
                    "Review adoption barriers with the customer administrator.",
                )
            )

        penetration = active_users / latest["seats_purchased"]
        if penetration < policy["seat_engagement_low_threshold"]:
            factors.append(
                RiskFactor(
                    "Low seat engagement",
                    int(policy["seat_engagement_low_points"]),
                    f"Only {penetration:.0%} of purchased seats were active in the latest month.",
                    [latest["usage_event_id"]],
                    "Identify inactive teams and run targeted enablement sessions.",
                )
            )
        elif penetration < policy["seat_engagement_medium_threshold"]:
            factors.append(
                RiskFactor(
                    "Low seat engagement",
                    int(policy["seat_engagement_medium_points"]),
                    f"Only {penetration:.0%} of purchased seats were active in the latest month.",
                    [latest["usage_event_id"]],
                    "Share an adoption dashboard and propose administrator training.",
                )
            )

    critical = [ticket for ticket in context["tickets"] if ticket["priority"] == "Critical"]
    if critical and not resolve_critical:
        factors.append(
            RiskFactor(
                "Unresolved critical support",
                int(policy["critical_support_points"]),
                f"{len(critical)} critical ticket(s) remain unresolved.",
                [ticket["ticket_id"] for ticket in critical],
                "Escalate to support leadership, assign an owner, and send the customer a resolution timeline.",
            )
        )

    contract = context["contract"]
    if contract:
        renewal = date.fromisoformat(contract["renewal_date"]) + timedelta(days=renewal_extension_days)
        days = (renewal - as_of).days
        points = (
            int(policy["renewal_near_points"])
            if days <= policy["renewal_near_days"]
            else int(policy["renewal_mid_points"])
            if days <= policy["renewal_mid_days"]
            else int(policy["renewal_far_points"])
            if days <= policy["renewal_far_days"]
            else 0
        )
        if points:
            factors.append(
                RiskFactor(
                    "Renewal approaching",
                    points,
                    f"Renewal is in {days} day(s) on {renewal.isoformat()}.",
                    [contract["contract_id"]],
                    "Confirm renewal stakeholders, commercial timeline, and success criteria this week.",
                )
            )
        acv = contract["annual_contract_value"]
        points = (
            int(policy["high_acv_points"])
            if acv >= policy["high_acv_threshold"]
            else int(policy["medium_acv_points"])
            if acv >= policy["medium_acv_threshold"]
            else 0
        )
        if points:
            factors.append(
                RiskFactor(
                    "High contract value",
                    points,
                    f"Annual contract value is ${acv:,.0f}.",
                    [contract["contract_id"]],
                    "Create an executive account plan and involve the renewal sponsor.",
                )
            )
    return factors


def _assessment(
    context: dict[str, Any], factors: list[RiskFactor], policy: dict[str, float]
) -> dict[str, Any]:
    score = min(100, sum(factor.points for factor in factors))
    return {
        "customer": context["customer"],
        "contract": context["contract"],
        "risk_score": score,
        "risk_level": risk_level(score, policy),
        "factors": [asdict(factor) for factor in factors],
        "recommended_actions": list(dict.fromkeys(factor.recommended_action for factor in factors)),
    }


def assess_customer(
    customer_id: str,
    as_of: date | None = None,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    policy: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Return a fully explainable renewal assessment for one customer."""

    as_of = as_of or date.today()
    if policy is None:
        _, policy = get_active_policy(database_path)
    context = _customer_context(customer_id, database_path)
    return _assessment(context, _factor_list(context, as_of, policy=policy), policy)


def simulate_customer(
    customer_id: str,
    as_of: date | None = None,
    *,
    usage_recovery_pct: int = 0,
    resolve_critical: bool = False,
    renewal_extension_days: int = 0,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    policy: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Compare the current score with explicit, reversible what-if assumptions.

    ``usage_recovery_pct`` is the percentage of currently inactive purchased seats
    made active in the scenario. It never edits operational source records.
    """

    if not 0 <= usage_recovery_pct <= 100:
        raise ValueError("usage_recovery_pct must be between 0 and 100")
    if renewal_extension_days < 0:
        raise ValueError("renewal_extension_days must not be negative")

    as_of = as_of or date.today()
    if policy is None:
        _, policy = get_active_policy(database_path)
    context = _customer_context(customer_id, database_path)
    baseline = _assessment(context, _factor_list(context, as_of, policy=policy), policy)
    active_override: int | None = None
    if context["usage"]:
        latest = context["usage"][0]
        inactive_seats = max(0, latest["seats_purchased"] - latest["active_users"])
        active_override = min(
            latest["seats_purchased"],
            latest["active_users"] + round(inactive_seats * usage_recovery_pct / 100),
        )
    simulated = _assessment(
        context,
        _factor_list(
            context,
            as_of,
            latest_active_users=active_override,
            resolve_critical=resolve_critical,
            renewal_extension_days=renewal_extension_days,
            policy=policy,
        ),
        policy,
    )
    return {
        "baseline": baseline,
        "simulated": simulated,
        "assumptions": {
            "usage_recovery_pct": usage_recovery_pct,
            "resolve_critical": resolve_critical,
            "renewal_extension_days": renewal_extension_days,
            "simulated_latest_active_users": active_override,
        },
    }


def assess_all_customers(
    as_of: date | None = None,
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    policy: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Return the entire portfolio ordered from highest to lowest risk."""

    if policy is None:
        _, policy = get_active_policy(database_path)
    with connect(database_path) as connection:
        customer_ids = [
            row[0]
            for row in connection.execute(
                "SELECT customer_id FROM customers ORDER BY customer_name"
            )
        ]
    return sorted(
        (assess_customer(customer_id, as_of, database_path, policy) for customer_id in customer_ids),
        key=lambda result: (result["risk_score"], result["customer"]["customer_name"]),
        reverse=True,
    )

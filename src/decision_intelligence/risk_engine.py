"""Deterministic, evidence-backed renewal-risk scoring."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import date
from typing import Any
from decision_intelligence.database import connect

HIGH_RISK_THRESHOLD = 55
MEDIUM_RISK_THRESHOLD = 30

@dataclass(frozen=True)
class RiskFactor:
    name: str
    points: int
    explanation: str
    evidence_record_ids: list[str]
    recommended_action: str


def _risk_level(score: int) -> str:
    return "High" if score >= HIGH_RISK_THRESHOLD else "Medium" if score >= MEDIUM_RISK_THRESHOLD else "Low"


def assess_customer(customer_id: str, as_of: date | None = None) -> dict[str, Any]:
    """Return a fully explainable renewal assessment for one customer."""
    as_of = as_of or date.today()
    with connect() as con:
        customer = con.execute("""SELECT c.*, am.full_name AS account_manager_name, am.email AS account_manager_email
            FROM customers c JOIN account_managers am ON am.account_manager_id=c.account_manager_id WHERE c.customer_id=?""", (customer_id,)).fetchone()
        if customer is None:
            raise ValueError(f"Unknown customer ID: {customer_id}")
        contract = con.execute("SELECT * FROM contracts WHERE customer_id=? ORDER BY renewal_date LIMIT 1", (customer_id,)).fetchone()
        usage = con.execute("SELECT * FROM product_usage_events WHERE customer_id=? ORDER BY event_date DESC LIMIT 2", (customer_id,)).fetchall()
        tickets = con.execute("SELECT * FROM support_tickets WHERE customer_id=? AND ticket_status IN ('Open','In Progress') ORDER BY opened_at DESC", (customer_id,)).fetchall()

    factors: list[RiskFactor] = []
    if len(usage) == 2:
        latest, previous = usage[0], usage[1]
        decline = (previous["active_users"] - latest["active_users"]) / max(previous["active_users"], 1)
        if decline >= .30:
            factors.append(RiskFactor("Declining product usage", 30, f"Active users declined {decline:.0%} from {previous['active_users']} to {latest['active_users']} in the latest month.", [previous["usage_event_id"], latest["usage_event_id"]], "Schedule a usage-review meeting and agree an adoption recovery plan."))
        elif decline >= .15:
            factors.append(RiskFactor("Declining product usage", 18, f"Active users declined {decline:.0%} in the latest month.", [previous["usage_event_id"], latest["usage_event_id"]], "Review adoption barriers with the customer administrator."))
        penetration = latest["active_users"] / latest["seats_purchased"]
        if penetration < .40:
            factors.append(RiskFactor("Low seat engagement", 15, f"Only {penetration:.0%} of purchased seats were active in the latest month.", [latest["usage_event_id"]], "Identify inactive teams and run targeted enablement sessions."))
        elif penetration < .60:
            factors.append(RiskFactor("Low seat engagement", 8, f"Only {penetration:.0%} of purchased seats were active in the latest month.", [latest["usage_event_id"]], "Share an adoption dashboard and propose administrator training."))
    critical = [ticket for ticket in tickets if ticket["priority"] == "Critical"]
    if critical:
        factors.append(RiskFactor("Unresolved critical support", 30, f"{len(critical)} critical ticket(s) remain unresolved.", [ticket["ticket_id"] for ticket in critical], "Escalate to support leadership, assign an owner, and send the customer a resolution timeline."))
    if contract:
        renewal = date.fromisoformat(contract["renewal_date"])
        days = (renewal - as_of).days
        points = 20 if days <= 30 else 12 if days <= 60 else 6 if days <= 90 else 0
        if points:
            factors.append(RiskFactor("Renewal approaching", points, f"Renewal is in {days} day(s) on {renewal.isoformat()}.", [contract["contract_id"]], "Confirm renewal stakeholders, commercial timeline, and success criteria this week."))
        acv = contract["annual_contract_value"]
        points = 10 if acv >= 100000 else 5 if acv >= 50000 else 0
        if points:
            factors.append(RiskFactor("High contract value", points, f"Annual contract value is ${acv:,.0f}.", [contract["contract_id"]], "Create an executive account plan and involve the renewal sponsor."))
    score = min(100, sum(factor.points for factor in factors))
    return {"customer": dict(customer), "contract": dict(contract) if contract else None, "risk_score": score, "risk_level": _risk_level(score), "factors": [asdict(factor) for factor in factors], "recommended_actions": list(dict.fromkeys(f.recommended_action for f in factors))}


def assess_all_customers(as_of: date | None = None) -> list[dict[str, Any]]:
    with connect() as con:
        customer_ids = [row[0] for row in con.execute("SELECT customer_id FROM customers ORDER BY customer_name")]
    return sorted((assess_customer(customer_id, as_of) for customer_id in customer_ids), key=lambda result: result["risk_score"], reverse=True)
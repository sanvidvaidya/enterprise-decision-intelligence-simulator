"""Live Telemetry & CRM Event Ingestion Engine.

Ingests streaming telemetry, support tickets, contract renewals, and account
modifications directly into the SQLite persistence layer with schema validation,
idempotency, and instant causal risk re-assessment.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from decision_intelligence.causal import extract_customer_causal_state
from decision_intelligence.database import DEFAULT_DATABASE_PATH, connect
from decision_intelligence.risk_engine import assess_customer


@dataclass
class IngestionResult:
    """Outcome of a live event ingestion and real-time risk re-assessment."""

    success: bool
    event_type: str
    event_id: str
    customer_id: str
    message: str
    previous_risk_score: Optional[int]
    new_risk_score: int
    previous_risk_level: Optional[str]
    new_risk_level: str
    score_delta: int
    top_causal_drivers: List[Dict[str, Any]]
    alert_triggered: bool
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _validate_customer_exists(conn, customer_id: str) -> None:
    row = conn.execute(
        "SELECT customer_id FROM customers WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    if not row:
        raise ValueError(f"Customer '{customer_id}' does not exist in portfolio.")


def ingest_usage_event(
    payload: Dict[str, Any],
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> IngestionResult:
    """Ingest live product usage / telemetry event for a customer.

    Payload format:
    {
        "customer_id": "CUS-020",
        "event_date": "2026-09-01",  # YYYY-MM-DD
        "active_users": 42,
        "seats_purchased": 50,
        "sessions": 320,
        "feature_adoption_pct": 74.5,
        "source_system": "segment_telemetry" # optional
    }
    """
    customer_id = payload.get("customer_id")
    if not customer_id:
        raise ValueError("Missing required 'customer_id'")
    event_date = payload.get("event_date")
    if not event_date:
        raise ValueError("Missing required 'event_date'")

    try:
        date.fromisoformat(str(event_date))
    except ValueError:
        raise ValueError(f"Invalid date format '{event_date}', must be YYYY-MM-DD")

    active_users = int(payload.get("active_users", 0))
    seats_purchased = int(payload.get("seats_purchased", 1))
    sessions = int(payload.get("sessions", 0))
    adoption = float(payload.get("feature_adoption_pct", 0.0))
    source_system = payload.get("source_system", "live_telemetry_webhook")

    if active_users < 0:
        raise ValueError("active_users cannot be negative")
    if seats_purchased <= 0:
        raise ValueError("seats_purchased must be greater than zero")
    if sessions < 0:
        raise ValueError("sessions cannot be negative")
    if not (0.0 <= adoption <= 100.0):
        raise ValueError("feature_adoption_pct must be between 0.0 and 100.0")

    with connect(database_path) as conn:
        _validate_customer_exists(conn, customer_id)

        # Baseline assessment prior to update
        try:
            prev_assessment = assess_customer(customer_id, database_path=database_path)
            prev_score = prev_assessment["risk_score"]
            prev_level = prev_assessment["risk_level"]
        except Exception:
            prev_score, prev_level = None, None

        # Upsert usage record
        usage_event_id = payload.get("usage_event_id", f"usage-stream-{uuid.uuid4().hex[:12]}")
        conn.execute(
            """INSERT INTO product_usage_events (
                   usage_event_id, customer_id, event_date, active_users,
                   seats_purchased, sessions, feature_adoption_pct, source_system
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(customer_id, event_date) DO UPDATE SET
                   active_users = excluded.active_users,
                   seats_purchased = excluded.seats_purchased,
                   sessions = excluded.sessions,
                   feature_adoption_pct = excluded.feature_adoption_pct,
                   source_system = excluded.source_system
            """,
            (
                usage_event_id,
                customer_id,
                str(event_date),
                active_users,
                seats_purchased,
                sessions,
                adoption,
                source_system,
            ),
        )
        conn.commit()

        # Instant post-ingestion risk re-assessment
        new_assessment = assess_customer(customer_id, database_path=database_path)
        new_score = new_assessment["risk_score"]
        new_level = new_assessment["risk_level"]
        score_delta = (new_score - prev_score) if prev_score is not None else 0

        # Causal state extraction
        causal_state = extract_customer_causal_state(customer_id, database_path=database_path)
        drivers = [
            {"driver": k, "value": v}
            for k, v in causal_state.items()
            if v > 0
        ]

        alert_triggered = new_level == "High" or score_delta >= 15

        return IngestionResult(
            success=True,
            event_type="usage_telemetry",
            event_id=usage_event_id,
            customer_id=customer_id,
            message="Usage telemetry successfully ingested and risk recomputed.",
            previous_risk_score=prev_score,
            new_risk_score=new_score,
            previous_risk_level=prev_level,
            new_risk_level=new_level,
            score_delta=score_delta,
            top_causal_drivers=drivers,
            alert_triggered=alert_triggered,
            details={
                "active_users": active_users,
                "seats_purchased": seats_purchased,
                "utilization": round(active_users / seats_purchased, 3),
                "sessions": sessions,
                "feature_adoption_pct": adoption,
            },
        )


def ingest_support_ticket(
    payload: Dict[str, Any],
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> IngestionResult:
    """Ingest support ticket creation or status modification.

    Payload format:
    {
        "customer_id": "CUS-020",
        "priority": "Critical",  # Low, Normal, High, Critical
        "ticket_status": "Open", # Open, In Progress, Resolved, Closed
        "ticket_category": "Integration",
        "ticket_summary": "Production webhook signature verification failing.",
        "csat_score": 1,         # 1-5 or null
        "opened_at": "2026-09-02T10:15:00Z", # ISO timestamp
        "resolved_at": null,
        "source_system": "zendesk"
    }
    """
    customer_id = payload.get("customer_id")
    if not customer_id:
        raise ValueError("Missing required 'customer_id'")

    priority = payload.get("priority", "Normal")
    if priority not in ("Low", "Normal", "High", "Critical"):
        raise ValueError(f"Invalid priority '{priority}', must be Low, Normal, High, or Critical")

    status = payload.get("ticket_status", "Open")
    if status not in ("Open", "In Progress", "Resolved", "Closed"):
        raise ValueError(f"Invalid ticket_status '{status}', must be Open, In Progress, Resolved, or Closed")

    ticket_category = payload.get("ticket_category", "General")
    ticket_summary = payload.get("ticket_summary", "Customer support escalation.")
    csat = payload.get("csat_score")
    if csat is not None:
        csat = int(csat)
        if not (1 <= csat <= 5):
            raise ValueError("csat_score must be between 1 and 5")

    opened_at = payload.get("opened_at", datetime.now(timezone.utc).isoformat())
    resolved_at = payload.get("resolved_at")
    source_system = payload.get("source_system", "support_desk_webhook")

    ticket_id = payload.get("ticket_id", f"ticket-stream-{uuid.uuid4().hex[:10]}")

    with connect(database_path) as conn:
        _validate_customer_exists(conn, customer_id)

        try:
            prev_assessment = assess_customer(customer_id, database_path=database_path)
            prev_score = prev_assessment["risk_score"]
            prev_level = prev_assessment["risk_level"]
        except Exception:
            prev_score, prev_level = None, None

        conn.execute(
            """INSERT INTO support_tickets (
                   ticket_id, customer_id, opened_at, resolved_at, priority,
                   ticket_status, ticket_category, csat_score, ticket_summary, source_system
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(ticket_id) DO UPDATE SET
                   resolved_at = excluded.resolved_at,
                   priority = excluded.priority,
                   ticket_status = excluded.ticket_status,
                   csat_score = excluded.csat_score,
                   ticket_summary = excluded.ticket_summary,
                   source_system = excluded.source_system
            """,
            (
                ticket_id,
                customer_id,
                str(opened_at),
                str(resolved_at) if resolved_at else None,
                priority,
                status,
                ticket_category,
                csat,
                ticket_summary,
                source_system,
            ),
        )
        conn.commit()

        new_assessment = assess_customer(customer_id, database_path=database_path)
        new_score = new_assessment["risk_score"]
        new_level = new_assessment["risk_level"]
        score_delta = (new_score - prev_score) if prev_score is not None else 0

        causal_state = extract_customer_causal_state(customer_id, database_path=database_path)
        drivers = [
            {"driver": k, "value": v}
            for k, v in causal_state.items()
            if v > 0
        ]

        alert_triggered = priority == "Critical" or new_level == "High" or score_delta >= 10

        return IngestionResult(
            success=True,
            event_type="support_ticket",
            event_id=ticket_id,
            customer_id=customer_id,
            message=f"Support ticket '{ticket_id}' ({priority}/{status}) ingested.",
            previous_risk_score=prev_score,
            new_risk_score=new_score,
            previous_risk_level=prev_level,
            new_risk_level=new_level,
            score_delta=score_delta,
            top_causal_drivers=drivers,
            alert_triggered=alert_triggered,
            details={
                "priority": priority,
                "ticket_status": status,
                "category": ticket_category,
                "opened_at": opened_at,
                "resolved_at": resolved_at,
            },
        )


def ingest_contract_event(
    payload: Dict[str, Any],
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> IngestionResult:
    """Ingest contract updates, renewals, or ACV modifications."""
    customer_id = payload.get("customer_id")
    if not customer_id:
        raise ValueError("Missing required 'customer_id'")

    with connect(database_path) as conn:
        _validate_customer_exists(conn, customer_id)

        try:
            prev_assessment = assess_customer(customer_id, database_path=database_path)
            prev_score = prev_assessment["risk_score"]
            prev_level = prev_assessment["risk_level"]
        except Exception:
            prev_score, prev_level = None, None

        contract_id = payload.get("contract_id")
        if not contract_id:
            # Look up existing contract for customer
            row = conn.execute(
                "SELECT contract_id FROM contracts WHERE customer_id = ? LIMIT 1",
                (customer_id,),
            ).fetchone()
            if row:
                contract_id = row["contract_id"]
            else:
                contract_id = f"contract-{uuid.uuid4().hex[:8]}"

        acv = float(payload.get("annual_contract_value", 50000.0))
        contract_status = payload.get("contract_status", "Active")
        renewal_date = payload.get("renewal_date", "2026-12-31")
        start_date = payload.get("contract_start_date", "2026-01-01")
        end_date = payload.get("contract_end_date", renewal_date)
        auto_renew = 1 if payload.get("auto_renew", False) else 0

        conn.execute(
            """INSERT INTO contracts (
                   contract_id, customer_id, contract_start_date, contract_end_date,
                   renewal_date, annual_contract_value, currency, contract_status, auto_renew
               ) VALUES (?, ?, ?, ?, ?, ?, 'USD', ?, ?)
               ON CONFLICT(contract_id) DO UPDATE SET
                   contract_end_date = excluded.contract_end_date,
                   renewal_date = excluded.renewal_date,
                   annual_contract_value = excluded.annual_contract_value,
                   contract_status = excluded.contract_status,
                   auto_renew = excluded.auto_renew
            """,
            (
                contract_id,
                customer_id,
                start_date,
                end_date,
                renewal_date,
                acv,
                contract_status,
                auto_renew,
            ),
        )
        conn.commit()

        new_assessment = assess_customer(customer_id, database_path=database_path)
        new_score = new_assessment["risk_score"]
        new_level = new_assessment["risk_level"]
        score_delta = (new_score - prev_score) if prev_score is not None else 0

        causal_state = extract_customer_causal_state(customer_id, database_path=database_path)
        drivers = [{"driver": k, "value": v} for k, v in causal_state.items() if v > 0]

        return IngestionResult(
            success=True,
            event_type="contract_event",
            event_id=contract_id,
            customer_id=customer_id,
            message=f"Contract '{contract_id}' updated (ACV: ${acv:,.2f}, Renewal: {renewal_date}).",
            previous_risk_score=prev_score,
            new_risk_score=new_score,
            previous_risk_level=prev_level,
            new_risk_level=new_level,
            score_delta=score_delta,
            top_causal_drivers=drivers,
            alert_triggered=new_level == "High",
            details={
                "annual_contract_value": acv,
                "renewal_date": renewal_date,
                "contract_status": contract_status,
                "auto_renew": auto_renew,
            },
        )

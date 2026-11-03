"""Event-Stream Time-Travel Replay and Counterfactual Branching Engine.

Reconstructs point-in-time customer states at historical dates without future
data leakage, replays risk trajectories, and simulates counterfactual timeline
divergence when interventions are injected at a historical branching point.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from decision_intelligence.database import DEFAULT_DATABASE_PATH, connect
from decision_intelligence.policy import DEFAULT_POLICY, get_active_policy
from decision_intelligence.risk_engine import (
    RiskFactor,
    _assessment,
    _factor_list,
    risk_level,
)


@dataclass(frozen=True)
class PointInTimeCheckpoint:
    """Reconstructed state and risk assessment at a specific historical date."""

    checkpoint_date: str
    active_users: int
    seats_purchased: int
    active_user_decline_pct: float
    seat_utilization: float
    open_tickets_count: int
    critical_tickets_count: int
    days_to_renewal: int
    risk_score: int
    risk_level: str
    active_factors: list[str]
    is_counterfactual: bool = False


@dataclass(frozen=True)
class StreamEvent:
    """Chronological event in the customer historical stream."""

    event_id: str
    event_date: str
    event_type: str
    title: str
    detail: str
    source_system: str
    is_counterfactual: bool = False


class TimeTravelReplayEngine:
    """Time-travel simulation and branching engine over customer event streams."""

    def __init__(
        self,
        database_path: str | Path = DEFAULT_DATABASE_PATH,
        policy: dict[str, float] | None = None,
    ) -> None:
        self.database_path = database_path
        if policy is None:
            _, self.policy = get_active_policy(database_path)
        else:
            self.policy = policy

    def get_customer_event_stream(
        self,
        customer_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[StreamEvent]:
        """Extract all historical events ordered chronologically."""
        events: list[StreamEvent] = []
        with connect(self.database_path) as connection:
            # Usage events
            for row in connection.execute(
                """SELECT usage_event_id, event_date, active_users, seats_purchased, feature_adoption_pct
                    FROM product_usage_events WHERE customer_id = ? ORDER BY event_date""",
                (customer_id,),
            ):
                events.append(
                    StreamEvent(
                        event_id=row["usage_event_id"],
                        event_date=row["event_date"],
                        event_type="product_usage",
                        title=f"Usage update: {row['active_users']} active users",
                        detail=f"{row['active_users']}/{row['seats_purchased']} seats utilized ({row['feature_adoption_pct']:.0f}% adoption).",
                        source_system="product_analytics",
                    )
                )

            # Support tickets
            for row in connection.execute(
                """SELECT ticket_id, opened_at, resolved_at, priority, ticket_status, ticket_summary
                    FROM support_tickets WHERE customer_id = ? ORDER BY opened_at""",
                (customer_id,),
            ):
                events.append(
                    StreamEvent(
                        event_id=row["ticket_id"],
                        event_date=row["opened_at"][:10],
                        event_type="ticket_opened",
                        title=f"{row['priority']} ticket opened",
                        detail=row["ticket_summary"],
                        source_system="support_desk",
                    )
                )
                if row["resolved_at"]:
                    events.append(
                        StreamEvent(
                            event_id=f"{row['ticket_id']}-res",
                            event_date=row["resolved_at"][:10],
                            event_type="ticket_resolved",
                            title=f"Ticket {row['ticket_id']} resolved",
                            detail=f"Resolved {row['priority']} ticket: {row['ticket_summary']}",
                            source_system="support_desk",
                        )
                    )

            # Contracts
            for row in connection.execute(
                "SELECT contract_id, renewal_date, annual_contract_value FROM contracts WHERE customer_id = ?",
                (customer_id,),
            ):
                events.append(
                    StreamEvent(
                        event_id=row["contract_id"],
                        event_date=row["renewal_date"],
                        event_type="contract_renewal",
                        title=f"Contract renewal milestone (${row['annual_contract_value']:,.0f})",
                        detail="Scheduled contract expiration and renewal date.",
                        source_system="contract_system",
                    )
                )

            # Actions
            for row in connection.execute(
                """SELECT action_id, created_at, completed_at, action_text, owner, action_status
                    FROM account_actions WHERE customer_id = ?""",
                (customer_id,),
            ):
                events.append(
                    StreamEvent(
                        event_id=row["action_id"],
                        event_date=row["created_at"][:10],
                        event_type="action_created",
                        title=f"Action: {row['action_text']}",
                        detail=f"Assigned to {row['owner']} (Status: {row['action_status']}).",
                        source_system="account_workflow",
                    )
                )

        events.sort(key=lambda e: (e.event_date, e.event_id))
        if start_date:
            events = [e for e in events if e.event_date >= start_date]
        if end_date:
            events = [e for e in events if e.event_date <= end_date]
        return events

    def reconstruct_checkpoint(
        self,
        customer_id: str,
        as_of: date,
        active_users_override: int | None = None,
        resolve_critical_override: bool = False,
        renewal_extension_days: int = 0,
    ) -> PointInTimeCheckpoint:
        """Evaluate exact point-in-time customer state without future leakage."""
        as_of_iso = as_of.isoformat()
        with connect(self.database_path) as connection:
            customer = connection.execute(
                "SELECT * FROM customers WHERE customer_id = ?",
                (customer_id,),
            ).fetchone()
            if customer is None:
                raise ValueError(f"Customer not found: {customer_id}")

            contract = connection.execute(
                "SELECT * FROM contracts WHERE customer_id = ? ORDER BY renewal_date LIMIT 1",
                (customer_id,),
            ).fetchone()

            usage_rows = connection.execute(
                """SELECT * FROM product_usage_events
                    WHERE customer_id = ? AND event_date <= ?
                    ORDER BY event_date DESC LIMIT 2""",
                (customer_id, as_of_iso),
            ).fetchall()

            ticket_rows = connection.execute(
                """SELECT * FROM support_tickets
                    WHERE customer_id = ?
                      AND opened_at <= ?
                      AND (resolved_at IS NULL OR resolved_at > ?)
                    ORDER BY opened_at DESC""",
                (customer_id, as_of_iso, as_of_iso),
            ).fetchall()

        context = {
            "customer": dict(customer),
            "contract": dict(contract) if contract else None,
            "usage": [dict(r) for r in usage_rows],
            "tickets": [dict(r) for r in ticket_rows],
        }

        factors = _factor_list(
            context,
            as_of,
            latest_active_users=active_users_override,
            resolve_critical=resolve_critical_override,
            renewal_extension_days=renewal_extension_days,
            policy=self.policy,
        )
        assessment = _assessment(context, factors, self.policy)

        # Compute summary metrics
        if usage_rows:
            latest = usage_rows[0]
            active_u = latest["active_users"] if active_users_override is None else active_users_override
            seats = latest["seats_purchased"]
            util = float(active_u / max(1, seats))
            if len(usage_rows) >= 2:
                prev = usage_rows[1]
                decline = float((prev["active_users"] - active_u) / max(1, prev["active_users"]))
            else:
                decline = 0.0
        else:
            active_u = 0
            seats = 100
            util = 0.0
            decline = 0.0

        open_crit = sum(1 for t in ticket_rows if t["priority"] == "Critical")
        if resolve_critical_override:
            open_crit = 0

        if contract:
            effective_renewal = date.fromisoformat(contract["renewal_date"]) + timedelta(days=renewal_extension_days)
            days = (effective_renewal - as_of).days
        else:
            days = 180

        return PointInTimeCheckpoint(
            checkpoint_date=as_of_iso,
            active_users=active_u,
            seats_purchased=seats,
            active_user_decline_pct=decline,
            seat_utilization=util,
            open_tickets_count=len(ticket_rows),
            critical_tickets_count=open_crit,
            days_to_renewal=days,
            risk_score=assessment["risk_score"],
            risk_level=assessment["risk_level"],
            active_factors=[f["name"] for f in assessment["factors"]],
            is_counterfactual=(
                active_users_override is not None
                or resolve_critical_override
                or renewal_extension_days > 0
            ),
        )

    def replay_factual_trajectory(
        self,
        customer_id: str,
    ) -> list[PointInTimeCheckpoint]:
        """Generate chronological point-in-time checkpoints for all usage dates."""
        with connect(self.database_path) as connection:
            dates = [
                row[0]
                for row in connection.execute(
                    """SELECT DISTINCT event_date FROM product_usage_events
                        WHERE customer_id = ? ORDER BY event_date""",
                    (customer_id,),
                ).fetchall()
            ]

        if not dates:
            dates = [(date.today() - timedelta(days=30 * i)).isoformat() for i in reversed(range(5))]

        checkpoints = []
        for d_str in dates:
            d = date.fromisoformat(d_str)
            checkpoints.append(self.reconstruct_checkpoint(customer_id, d))
        return checkpoints

    def branch_counterfactual_trajectory(
        self,
        customer_id: str,
        branch_date: str,
        intervention_type: str,
        intervention_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Fork reality at branch_date and simulate the counterfactual timeline forward."""
        intervention_params = intervention_params or {}
        branch_d = date.fromisoformat(branch_date)

        # 1. Generate factual checkpoints
        factual_checkpoints = self.replay_factual_trajectory(customer_id)

        # 2. Generate counterfactual checkpoints
        counterfactual_checkpoints: list[PointInTimeCheckpoint] = []
        for cp in factual_checkpoints:
            cp_date = date.fromisoformat(cp.checkpoint_date)
            if cp_date < branch_d:
                # Prior to intervention branch, counterfactual is identical to factual
                counterfactual_checkpoints.append(cp)
            else:
                # Apply intervention adjustments
                active_override = None
                resolve_critical = False
                extension_days = 0

                if intervention_type == "resolve_critical_tickets":
                    resolve_critical = True
                    # Resolving critical blockers also stabilizes users: halves any decline
                    if cp.active_user_decline_pct > 0:
                        recovered = int(round(cp.active_users * 1.25))
                        active_override = min(cp.seats_purchased, recovered)

                elif intervention_type == "seat_enablement_sprint":
                    lift_pct = float(intervention_params.get("lift_pct", 30.0))
                    unused = max(0, cp.seats_purchased - cp.active_users)
                    added_users = int(round(unused * (lift_pct / 100.0)))
                    active_override = min(cp.seats_purchased, cp.active_users + added_users)

                elif intervention_type == "contract_extension":
                    extension_days = int(intervention_params.get("extension_days", 90))

                elif intervention_type == "comprehensive_playbook":
                    resolve_critical = True
                    lift_pct = float(intervention_params.get("lift_pct", 40.0))
                    unused = max(0, cp.seats_purchased - cp.active_users)
                    added_users = int(round(unused * (lift_pct / 100.0)))
                    active_override = min(cp.seats_purchased, cp.active_users + added_users)
                    extension_days = int(intervention_params.get("extension_days", 90))

                cf_cp = self.reconstruct_checkpoint(
                    customer_id,
                    cp_date,
                    active_users_override=active_override,
                    resolve_critical_override=resolve_critical,
                    renewal_extension_days=extension_days,
                )
                counterfactual_checkpoints.append(cf_cp)

        # Calculate outcome comparisons
        latest_factual = factual_checkpoints[-1]
        latest_cf = counterfactual_checkpoints[-1]
        score_reduction = max(0, latest_factual.risk_score - latest_cf.risk_score)

        # Count high risk checkpoints avoided
        factual_high_risk = sum(1 for cp in factual_checkpoints if cp.risk_level == "High")
        cf_high_risk = sum(1 for cp in counterfactual_checkpoints if cp.risk_level == "High")
        high_risk_checkpoints_avoided = max(0, factual_high_risk - cf_high_risk)

        with connect(self.database_path) as connection:
            contract = connection.execute(
                "SELECT annual_contract_value FROM contracts WHERE customer_id = ? ORDER BY renewal_date LIMIT 1",
                (customer_id,),
            ).fetchone()
            acv = float(contract["annual_contract_value"]) if contract else 0.0

        protected_acv = acv if (latest_factual.risk_level == "High" and latest_cf.risk_level in ("Medium", "Low")) else 0.0

        divergence_event = StreamEvent(
            event_id=f"counterfactual-{branch_date}",
            event_date=branch_date,
            event_type="counterfactual_branch",
            title=f"Counterfactual Intervention: {intervention_type}",
            detail=f"Intervention injected on {branch_date}. Simulated forward to test alternative reality.",
            source_system="time_travel_engine",
            is_counterfactual=True,
        )

        all_events = self.get_customer_event_stream(customer_id)
        all_events.append(divergence_event)
        all_events.sort(key=lambda e: (e.event_date, e.event_id))

        trajectory_comparison = []
        for f_cp, c_cp in zip(factual_checkpoints, counterfactual_checkpoints):
            trajectory_comparison.append(
                {
                    "checkpoint_date": f_cp.checkpoint_date,
                    "factual_score": f_cp.risk_score,
                    "factual_level": f_cp.risk_level,
                    "factual_active_users": f_cp.active_users,
                    "factual_critical_tickets": f_cp.critical_tickets_count,
                    "counterfactual_score": c_cp.risk_score,
                    "counterfactual_level": c_cp.risk_level,
                    "counterfactual_active_users": c_cp.active_users,
                    "counterfactual_critical_tickets": c_cp.critical_tickets_count,
                    "score_delta": c_cp.risk_score - f_cp.risk_score,
                }
            )

        return {
            "customer_id": customer_id,
            "branch_date": branch_date,
            "intervention_type": intervention_type,
            "intervention_params": intervention_params,
            "trajectory_comparison": trajectory_comparison,
            "latest_factual": asdict(latest_factual),
            "latest_counterfactual": asdict(latest_cf),
            "impact_summary": {
                "score_reduction": score_reduction,
                "initial_score": latest_factual.risk_score,
                "counterfactual_score": latest_cf.risk_score,
                "high_risk_checkpoints_avoided": high_risk_checkpoints_avoided,
                "protected_acv": protected_acv,
                "contract_acv": acv,
            },
            "event_stream": [asdict(e) for e in all_events],
        }
